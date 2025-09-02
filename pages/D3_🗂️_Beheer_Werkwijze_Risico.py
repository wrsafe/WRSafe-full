# pages/D3_🗂️_Beheer_Werkwijze_Risico.py
import streamlit as st
from sqlmodel import select
from services.auth_simple import load_cfg, require_role
from services.nav import render_nav
from db import init_db, get_session
from models import WorkType, Risk, WorkTypeRisk

init_db()
cfg = load_cfg()
require_role(cfg, {"beheerder"})
st.set_page_config(page_title="Beheer – Werkwijze ↔ Risico's", layout="wide")
render_nav()

st.header("🛠️ Beheer – Werkwijze ↔ Risico's")

# -----------------------
# Voorraad uit beheer
# -----------------------
with get_session() as s:
    worktypes = s.exec(
        select(WorkType).where(WorkType.active == True).order_by(WorkType.sort_order, WorkType.name)
    ).all()
    risks = s.exec(
        select(Risk).where(Risk.active == True).order_by(Risk.category, Risk.sort_order, Risk.name)
    ).all()

wt_names = [w.name for w in worktypes]
wt_by_name = {w.name: w for w in worktypes}

# Combineer risicolabel met categorie voor duidelijke weergave
def risk_label(r: Risk) -> str:
    return f"{r.name}  ({r.category})"

risk_labels = [risk_label(r) for r in risks]
risk_by_label = {risk_label(r): r for r in risks}

left, right = st.columns([4, 8])
with left:
    sel_wt_name = st.selectbox("Werkwijze", options=wt_names, index=0 if wt_names else None)

if not sel_wt_name:
    st.info("Voeg eerst **Werkwijzen** en **Risico’s** toe in Beheer.")
    st.stop()

sel_wt = wt_by_name[sel_wt_name]

# -----------------------
# Huidige koppelingen
# -----------------------
with get_session() as s:
    current_links = s.exec(
        select(WorkTypeRisk).where(WorkTypeRisk.worktype_id == sel_wt.id)
    ).all()
current_risk_ids = {lk.risk_id for lk in current_links}
current_labels = [risk_label(r) for r in risks if r.id in current_risk_ids]

# Filters voor snelle selectie
fc1, fc2, fc3 = st.columns([2,2,8])
with fc1:
    show_w = st.checkbox("Toon Werk", value=True)
with fc2:
    show_o = st.checkbox("Toon Omgeving", value=True)

filtered_labels = [
    lbl for lbl in risk_labels
    if ((show_w and "(Werk)" in lbl) or (show_o and "(Omgeving)" in lbl))
]

# Multiselect
new_selected_labels = st.multiselect(
    "Koppel risico's aan deze werkwijze",
    options=filtered_labels if (show_w or show_o) else [],
    default=[lbl for lbl in current_labels if lbl in filtered_labels],
    help="Selecteer één of meer risico’s (Werk en/of Omgeving)."
)

# -----------------------
# Opslaan koppelingen
# -----------------------
if st.button("💾 Opslaan koppelingen", type="primary"):
    new_selected_ids = {risk_by_label[lbl].id for lbl in new_selected_labels}

    with get_session() as s:
        # Bestaande links ophalen (nogmaals binnen sessie)
        existing = s.exec(
            select(WorkTypeRisk).where(WorkTypeRisk.worktype_id == sel_wt.id)
        ).all()

        # Verwijder die niet meer geselecteerd zijn
        for link in existing:
            if link.risk_id not in new_selected_ids:
                s.delete(link)

        # Voeg nieuwe toe die nog niet bestonden
        existing_ids = {lk.risk_id for lk in existing}
        for rid in new_selected_ids - existing_ids:
            s.add(WorkTypeRisk(worktype_id=sel_wt.id, risk_id=rid))

        s.commit()

    st.success("Koppelingen opgeslagen.")
    st.rerun()

# -----------------------
# Tabel met huidige koppelingen (compact)
# -----------------------
with get_session() as s:
    # Lees opnieuw voor actuele stand
    links = s.exec(select(WorkTypeRisk).where(WorkTypeRisk.worktype_id == sel_wt.id)).all()
    risk_map = {r.id: r for r in risks}  # reeds geladen, hergebruik
    table_rows = []
    for lk in sorted(links, key=lambda x: (risk_map.get(x.risk_id).category if risk_map.get(x.risk_id) else "", risk_map.get(x.risk_id).name if risk_map.get(x.risk_id) else "")):
        r = risk_map.get(lk.risk_id)
        if not r:
            continue
        table_rows.append({
            "Risico": r.name,
            "Categorie": r.category,
            "Risk ID": r.id,
        })

st.markdown("### Gekoppelde risico’s")
if not table_rows:
    st.info("Nog geen risico’s gekoppeld aan deze werkwijze.")
else:
    st.data_editor(
        table_rows,
        hide_index=True,
        use_container_width=True,
        disabled=True,
        column_config={
            "Risico":    st.column_config.TextColumn("Risico"),
            "Categorie": st.column_config.TextColumn("Categorie", width="small"),
            "Risk ID":   st.column_config.NumberColumn("Risk ID", width="small"),
        },
        column_order=["Risico", "Categorie", "Risk ID"],
    )
