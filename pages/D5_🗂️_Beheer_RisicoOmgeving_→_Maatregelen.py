# pages/D5_🗂️_Beheer_RisicoOmgeving_→_Maatregelen.py
import streamlit as st
from sqlmodel import select
from db import init_db, get_session
from services.nav import render_nav
from services.auth_simple import load_cfg, require_role
from models import EnvRiskCat, EnvRiskRule, Measure

st.set_page_config(page_title="Beheer – Risico Omgeving → Maatregelen", layout="wide")
init_db()
render_nav()
cfg = load_cfg()
require_role(cfg, {"beheerder"})

st.header("🗂️ Beheer – Risico Omgeving → Maatregelen")

# Catalogi
with get_session() as s:
    risks = s.exec(
        select(EnvRiskCat).where(EnvRiskCat.active == True).order_by(EnvRiskCat.sort_order, EnvRiskCat.name)
    ).all()
    measures_env = s.exec(
        select(Measure).where((Measure.active == True) & (Measure.scope == "Omgeving")).order_by(Measure.name)
    ).all()

risk_names = [r.name for r in risks]
meas_names = [m.name for m in measures_env]
meas_by_name = {m.name: m for m in measures_env}
risk_by_name = {r.name: r for r in risks}

# Selectie
col = st.columns([4, 6])
with col[0]:
    sel_risk_name = st.selectbox("Risico (Omgeving)", options=risk_names, index=0 if risk_names else None)

if not sel_risk_name:
    st.info("Voeg eerst risico’s (Omgeving) toe in Beheer.")
    st.stop()

sel_risk = risk_by_name[sel_risk_name]

# Huidige koppelingen ophalen (let op: risk_id property)
with get_session() as s:
    rules = s.exec(
        select(EnvRiskRule)
        .where(EnvRiskRule.risk_id == sel_risk.id)
        .order_by(EnvRiskRule.weight, EnvRiskRule.id)
    ).all()
    current_measure_ids = [ru.measure_id for ru in rules]

default_selected = [m.name for m in measures_env if m.id in current_measure_ids]
selected_names = st.multiselect("Koppel beheersmaatregelen (Omgeving)", options=meas_names, default=default_selected)

# Opties
col2 = st.columns([2, 2, 6])
with col2[0]:
    auto_weight = st.checkbox("Automatische volgorde (1..n)", value=True)
with col2[1]:
    required_default = st.checkbox("Required = default van maatregel aanhouden", value=True)

# Opslaan
if st.button("💾 Opslaan koppelingen", type="primary"):
    with get_session() as s:
        existing = s.exec(select(EnvRiskRule).where(EnvRiskRule.risk_id == sel_risk.id)).all()
        keep_ids = set()

        for name in selected_names:
            m = meas_by_name.get(name)
            if not m:
                continue
            ru = next((x for x in existing if x.measure_id == m.id), None)
            if ru:
                # update required/weight indien gewenst
                if required_default:
                    ru.required_override = None
                keep_ids.add(ru.id)
            else:
                ru = EnvRiskRule(
                    risk_id=sel_risk.id,          # gebruik property i.p.v. envrisk_id
                    measure_id=m.id,
                    required_override=None if required_default else None,
                    weight=100
                )
                s.add(ru); s.flush()
                keep_ids.add(ru.id)

        # verwijder rules die niet meer geselecteerd zijn
        for ru in existing:
            if ru.id not in keep_ids:
                s.delete(ru)

        # automatische volgorde
        if auto_weight:
            new_rules = s.exec(
                select(EnvRiskRule).where(EnvRiskRule.risk_id == sel_risk.id).order_by(EnvRiskRule.id)
            ).all()
            w = 1
            for ru in new_rules:
                ru.weight = w
                s.add(ru)
                w += 1

        s.commit()
    st.success("Koppelingen opgeslagen.")

# Huidige koppelingen tonen
with get_session() as s:
    table = s.exec(
        select(EnvRiskRule, Measure)
        .join(Measure, Measure.id == EnvRiskRule.measure_id)
        .where(EnvRiskRule.risk_id == sel_risk.id)
        .order_by(EnvRiskRule.weight, Measure.name)
    ).all()

st.markdown("### Gekoppelde maatregelen")
if not table:
    st.info("Geen maatregelen gekoppeld aan dit risico.")
else:
    # compactere weergave met column_config
    st.data_editor(
        [
            {
                "Volgorde": ru.weight,
                "Maatregel": m.name,
                "Default verantwoordelijke": m.default_responsible or "—",
                "Scope": m.scope,
            }
            for (ru, m) in table
        ],
        use_container_width=True,
        hide_index=True,
        disabled=True,
        column_config={
            "Volgorde": st.column_config.NumberColumn("Volgorde", width="small", help="Weergavevolgorde (gewicht)"),
            "Maatregel": st.column_config.TextColumn("Maatregel"),
            "Default verantwoordelijke": st.column_config.TextColumn("Default verantwoordelijke"),
            "Scope": st.column_config.TextColumn("Scope"),
        }
    )
