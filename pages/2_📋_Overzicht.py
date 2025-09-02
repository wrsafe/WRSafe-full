# pages/2_📋_Overzicht.py
import streamlit as st
from sqlmodel import Session, select
from datetime import datetime

from db import engine, init_db
from services.nav import render_nav
from models import (
    Permit, PermitSpace, Space,
    SiteLocation, DepartmentUnit, Measure, PermitMeasure,
    PermitStep
)

# --- Setup ---
st.set_page_config(page_title="Overzicht vergunningen", layout="wide")
init_db()
render_nav()

st.header("📋 Overzicht vergunningen")

# --- Filters laden ---
with Session(engine) as s:
    # unieke waarden voor filters
    all_permits = s.exec(select(Permit)).all()
    all_statuses = sorted({p.status for p in all_permits if p.status})
    all_locations = s.exec(
        select(SiteLocation).where(SiteLocation.active == True).order_by(SiteLocation.sort_order, SiteLocation.name)
    ).all()
    all_departments = s.exec(
        select(DepartmentUnit).where(DepartmentUnit.active == True).order_by(DepartmentUnit.sort_order, DepartmentUnit.name)
    ).all()
    all_reasons = sorted({(p.reason or "").strip() for p in all_permits if (p.reason or "").strip()})

# --- Filter UI ---
colf1, colf2, colf3, colf4, colf5, colf6, colf7, colf8 = st.columns([2,2,2,2,2,2,2,2])
with colf1:
    status_filter = st.multiselect("Status", options=all_statuses, default=[])
with colf2:
    location_filter = st.selectbox(
        "Location", options=["— alle —"] + [x.name for x in all_locations], index=0)
with colf3:
    department_filter = st.selectbox(
        "Department", options=["— alle —"] + [x.name for x in all_departments], index=0)
with colf4:
    area_owner_filter = st.text_input("Gebiedseigenaar (filter)", "")
with colf5:
    system_owner_filter = st.text_input("Systeemeigenaar (filter)", "")
with colf6:
    sort_latest_first = st.checkbox("Nieuwste eerst", value=True)
with colf7:
    reason_filter = st.selectbox("Reden", options=["— alle —"] + all_reasons, index=0)
with colf8:
    pbm_filter = st.selectbox("PBM", options=["— alle —", "Met PBM", "Zonder PBM"], index=0)

sort_latest_first = st.checkbox("Nieuwste eerst", value=True)

# --- PBM-naamset (uit catalogus Measure[scope='PBM']) ---
with Session(engine) as s:
    pbm_names = {m.name for m in s.exec(select(Measure).where((Measure.active == True) & (Measure.scope == "PBM"))).all()}

# --- Filters toepassen op permits (basis) ---
def permit_matches_base(p: Permit) -> bool:
    if status_filter and p.status not in status_filter:
        return False
    if location_filter != "— alle —" and (p.location or "") != location_filter:
        return False
    if department_filter != "— alle —" and (p.department or "") != department_filter:
        return False
    if area_owner_filter and area_owner_filter.lower() not in (p.area_owner or "").lower():
        return False
    if system_owner_filter and system_owner_filter.lower() not in (p.system_owner or "").lower():
        return False
    if reason_filter != "— alle —" and (p.reason or "") != reason_filter:
        return False
    return True

permits = [p for p in all_permits if permit_matches_base(p)]

# --- Bepaal PBM per permit in bulk ---
permit_ids = [p.id for p in permits if p.id is not None]
pbm_flag_by_permit: dict[int, bool] = {}
with Session(engine) as s:
    if permit_ids:
        pm_all = s.exec(select(PermitMeasure).where(PermitMeasure.permit_id.in_(permit_ids))).all()
        # check per permit of er een PermitMeasure voorkomt waarvan de omschrijving in pbm_names zit
        for pm in pm_all:
            if pm.permit_id is None:
                continue
            has = pm.description in pbm_names
            if has:
                pbm_flag_by_permit[pm.permit_id] = True
        # vul False voor overige ids die niet in pbm_flag_by_permit staan
        for pid in permit_ids:
            pbm_flag_by_permit.setdefault(pid, False)

# --- PBM-filter toepassen ---
def pbm_matches(pid: int) -> bool:
    if pbm_filter == "— alle —":
        return True
    if pbm_filter == "Met PBM":
        return bool(pbm_flag_by_permit.get(pid, False))
    # "Zonder PBM"
    return not bool(pbm_flag_by_permit.get(pid, False))

permits = [p for p in permits if pbm_matches(p.id or -1)]

# --- Stappen-per-permit in bulk tellen ---
permit_ids = [p.id for p in permits if p.id is not None]
steps_count_by_permit: dict[int, int] = {}
with Session(engine) as s:
    if permit_ids:
        steps_all = s.exec(select(PermitStep).where(PermitStep.permit_id.in_(permit_ids))).all()
        for stp in steps_all:
            steps_count_by_permit[stp.permit_id] = steps_count_by_permit.get(stp.permit_id, 0) + 1
    for pid in permit_ids:
        steps_count_by_permit.setdefault(pid, 0)

# --- Sorteren ---
permits.sort(key=lambda p: (p.start_dt or datetime.min, p.id or 0), reverse=sort_latest_first)

# --- Tabel vullen ---
rows = []
with Session(engine) as s2:
    # prefetch ruimtes per permit
    for p in permits:
        # Ruimtes (catalogus + vrije invoer)
        ps = s2.exec(select(PermitSpace).where(PermitSpace.permit_id == p.id)).all()
        ids = [x.space_id for x in ps if x.space_id]
        names = [r.name for r in s2.exec(select(Space).where(Space.id.in_(ids))).all()] if ids else []
        custom = [x.custom_name for x in ps if x.custom_name]
        rooms_summary = ", ".join([*names, *[c for c in custom if c]]) or "—"

        rows.append({
            "ID": p.id,
            "Titel": p.title,
            "Betreft": p.subject,
            "Werkgebied": p.work_area,
            "Installatie/Systeem": p.asset,
            "Location": p.location,
            "Department": p.department,
            "Ruimtes": rooms_summary,
            "Aanvrager": p.applicant_name,
            "Team/Afdeling": p.applicant_team,
            "Contractor": p.applicant_org,
            "Risicoklasse": p.risk_class,
            "Start": p.start_dt,
            "Einde": p.end_dt,
            "Reden": p.reason or "—",
            "PBM": "✓" if pbm_flag_by_permit.get(p.id or -1, False) else "—",
            "Stappen": steps_count_by_permit.get(p.id or -1, 0),
            "Gebiedseigenaar": p.area_owner or "—",
            "Systeemeigenaar": p.system_owner or "—",
            "Status": p.status,
        })

if rows:
    # Kolomvolgorde met smalle kolommen eerst (Streamlit bepaalt breedte automatisch;
    # korte labels helpen om deze kolommen compact te houden)
    order = [
        "ID", "Status", "Start", "Einde", "Titel",
        "Reden", "Betreft", "Werkgebied",
        "Location", "Department", "Ruimtes",
        "Risicoklasse", "PBM", "Stappen",
        "Aanvrager", "Team/Afdeling", "Contractor",
    ]
    st.dataframe(
        rows,
        use_container_width=True,
        hide_index=True,
        column_order=order,
        column_config={
            "ID": st.column_config.Column("ID", width="small"),
            "Status": st.column_config.Column("Status", width="small"),
        }
    )
else:
    st.info("Geen vergunningen die voldoen aan de huidige filters.")
