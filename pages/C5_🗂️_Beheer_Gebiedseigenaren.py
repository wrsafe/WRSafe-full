import streamlit as st
from sqlmodel import Session, select
from db import engine, init_db
from services.auth_simple import load_cfg, require_role
from services.nav import render_nav
from models import AreaOwnerMap, SiteLocation, DepartmentUnit

st.set_page_config(page_title="Beheer – Gebiedseigenaren", layout="wide")
init_db(); render_nav()
cfg = load_cfg(); require_role(cfg, {"beheerder"})

st.header("🗂️ Beheer – Gebiedseigenaren (Location + Department → Eigenaar)")

# bronlijsten
with Session(engine) as s:
    locs = s.exec(select(SiteLocation).where(SiteLocation.active==True).order_by(SiteLocation.sort_order, SiteLocation.name)).all()
    deps = s.exec(select(DepartmentUnit).where(DepartmentUnit.active==True).order_by(DepartmentUnit.sort_order, DepartmentUnit.name)).all()
loc_names = [x.name for x in locs]
dep_names = [x.name for x in deps]

# toevoegen
with st.expander("➕ Nieuwe koppeling", expanded=True):
    c = st.columns([3,3,3,2,3])
    with c[0]:
        loc = st.selectbox("Location", loc_names, index=0 if loc_names else None, key="ao_new_loc")
    with c[1]:
        dep = st.selectbox("Department", dep_names, index=0 if dep_names else None, key="ao_new_dep")
    with c[2]:
        owner = st.text_input("Eigenaar (naam/team)", key="ao_new_owner")
    with c[3]:
        order = st.number_input("Volgorde", 0, 9999, 100, step=10, key="ao_new_order")
    with c[4]:
        notes = st.text_input("Notitie (optioneel)", key="ao_new_notes")

    if st.button("Toevoegen", type="primary"):
        if not (loc and dep and owner.strip()):
            st.warning("Location, Department en Eigenaar zijn verplicht.")
        else:
            with Session(engine) as s:
                s.add(AreaOwnerMap(location=loc, department=dep, owner_name=owner.strip(),
                                   sort_order=int(order), active=True, notes=(notes or None)))
                s.commit()
            st.success("Koppeling toegevoegd."); st.rerun()

# lijst/bewerken
with Session(engine) as s:
    rows = s.exec(select(AreaOwnerMap).order_by(AreaOwnerMap.active.desc(), AreaOwnerMap.sort_order, AreaOwnerMap.location, AreaOwnerMap.department)).all()

for r in rows:
    c = st.columns([3,3,3,2,3,1,1])
    c[0].write(r.location)
    c[1].write(r.department)
    new_owner = c[2].text_input("Eigenaar", value=r.owner_name, key=f"ao_owner_{r.id}")
    new_ord   = c[3].number_input("Volg.", value=r.sort_order, key=f"ao_ord_{r.id}")
    new_notes = c[4].text_input("Notitie", value=r.notes or "", key=f"ao_notes_{r.id}")
    new_act   = c[5].checkbox("Actief", value=r.active, key=f"ao_act_{r.id}")
    if c[6].button("💾", key=f"ao_save_{r.id}"):
        with Session(engine) as s:
            rec = s.get(AreaOwnerMap, r.id)
            rec.owner_name = new_owner.strip() or rec.owner_name
            rec.sort_order = int(new_ord or 0)
            rec.notes = (new_notes or None)
            rec.active = bool(new_act)
            s.add(rec); s.commit()
        st.success("Opgeslagen."); st.rerun()
