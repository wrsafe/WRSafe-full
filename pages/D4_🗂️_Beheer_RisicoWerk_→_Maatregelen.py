# pages/D4_🗂️_Beheer_RisicoWerk_→_Maatregelen.py
import streamlit as st
from sqlmodel import select
from db import init_db, get_session
from services.auth_simple import load_cfg, require_role
from services.nav import render_nav
from models import WorkRiskCat, Measure, WorkRiskRule

init_db()
cfg = load_cfg()
require_role(cfg, {"beheerder"})
st.set_page_config(page_title="Beheer – Risico Werk → Maatregelen", layout="wide")
st.header("🛠️ Beheer – Risico Werk → Maatregelen")
render_nav()

# Catalogi laden
with get_session() as s:
    risks = s.exec(
        select(WorkRiskCat).where(WorkRiskCat.active == True).order_by(WorkRiskCat.sort_order, WorkRiskCat.name)
    ).all()
    # Werk risico’s mogen koppelen aan maatregelen met scope == "Werk" (géén PBM)
    measures = s.exec(
        select(Measure).where((Measure.active==True) & (Measure.scope=="Werk")).order_by(Measure.name)
    ).all()
#    measures = s.exec(
#        select(Measure).where(Measure.active == True).order_by(Measure.name)
#    ).all()

rk_names = [r.name for r in risks]
ms_names = [m.name for m in measures]
by_name_risk = {r.name: r for r in risks}
by_id_measure = {m.id: m for m in measures}
by_name_measure = {m.name: m for m in measures}

sel_risk = st.selectbox("Risico (Werk)", rk_names if rk_names else [], index=0 if rk_names else None)
if not sel_risk:
    st.info("Voeg eerst Risico’s en Maatregelen toe.")
    st.stop()

risk_obj = by_name_risk[sel_risk]

# Huidige regels ophalen
with get_session() as s:
    rules = s.exec(
        select(WorkRiskRule)
        .where(WorkRiskRule.risk_id == risk_obj.id)     # let op: risk_id-property (backwards compat)
        .order_by(WorkRiskRule.weight, WorkRiskRule.id)
    ).all()

selected_now = [by_id_measure.get(ru.measure_id).name if by_id_measure.get(ru.measure_id) else f"(id:{ru.measure_id})"
                for ru in rules]
req_map = {
    (by_id_measure.get(ru.measure_id).name if by_id_measure.get(ru.measure_id) else f"(id:{ru.measure_id})"):
    ru.required_override
    for ru in rules
}

new_sel = st.multiselect("Maatregelen voor dit risico (Werk)", ms_names, default=selected_now)

new_required = {}
for name in new_sel:
    current = req_map.get(name)
    label = "default (catalogus)" if current is None else ("verplicht" if current else "optioneel")
    choice = st.selectbox(
        f"{name} – verplichting",
        ["default (catalogus)", "verplicht", "optioneel"],
        index=["default (catalogus)", "verplicht", "optioneel"].index(label),
        key=f"req_{name}"
    )
    new_required[name] = None if choice.startswith("default") else (True if choice == "verplicht" else False)

if st.button("💾 Opslaan regels", type="primary"):
    with get_session() as s:
        # verwijder bestaande regels voor dit risico
        for ru in s.exec(select(WorkRiskRule).where(WorkRiskRule.risk_id == risk_obj.id)).all():
            s.delete(ru)

        # schrijf nieuwe set
        weight = 10
        for name in new_sel:
            m = by_name_measure.get(name)
            if not m:
                continue
            s.add(WorkRiskRule(
                risk_id=risk_obj.id,
                measure_id=m.id,
                required_override=new_required.get(name),
                weight=weight
            ))
            weight += 10
        s.commit()
    st.success("Regels opgeslagen.")
    st.rerun()
