import streamlit as st
from sqlmodel import Session, select
from db import engine, init_db
from services.auth_simple import load_cfg, require_role
from services.nav import render_nav
from models import SystemOwnerMap, WorkArea

st.set_page_config(page_title="Beheer – Systeemeigenaren", layout="wide")
init_db(); render_nav()
cfg = load_cfg(); require_role(cfg, {"beheerder"})

st.header("🗂️ Beheer – Systeemeigenaren (Werkgebied + Asset-patroon → Eigenaar)")

match_types = ["exact","startswith","contains","glob","regex"]

with Session(engine) as s:
    areas = s.exec(select(WorkArea).where(WorkArea.active==True).order_by(WorkArea.sort_order, WorkArea.name)).all()
area_names = [a.name for a in areas]

with st.expander("➕ Nieuwe koppeling", expanded=True):
    c = st.columns([3,2,3,3,2,3])
    with c[0]:
        wa = st.selectbox("Werkgebied", area_names, index=0 if area_names else None, key="so_new_wa")
    with c[1]:
        mt = st.selectbox("Match-type", match_types, index=2, key="so_new_mt")
    with c[2]:
        patt = st.text_input("Asset-patroon", placeholder="bv. Verlichting* of heftruck", key="so_new_patt")
    with c[3]:
        owner = st.text_input("Eigenaar (naam/team)", key="so_new_owner")
    with c[4]:
        order = st.number_input("Volgorde", 0, 9999, 100, step=10, key="so_new_order")
    with c[5]:
        notes = st.text_input("Notitie (optioneel)", key="so_new_notes")

    if st.button("Toevoegen", type="primary"):
        if not (wa and owner.strip()):                      # ← alleen werkgebied + eigenaar verplicht
            st.warning("Werkgebied en eigenaar zijn verplicht.")
        else:
            with Session(engine) as s:
                s.add(SystemOwnerMap(
                    work_area=wa,
                    match_type=mt,
                    asset_pattern=(patt.strip() or ""),     # ← leeg toegestaan
                    owner_name=owner.strip(),
                    sort_order=int(order),
                    active=True,
                    notes=(notes or None)
                ))
                s.commit()
            st.success("Koppeling toegevoegd."); st.rerun()

with Session(engine) as s:
    rows = s.exec(
        select(SystemOwnerMap)
        .order_by(SystemOwnerMap.active.desc(), SystemOwnerMap.work_area, SystemOwnerMap.sort_order, SystemOwnerMap.id)
    ).all()

for r in rows:
    c = st.columns([3,2,3,3,2,3,1,1])
    c[0].write(r.work_area)
    new_mt   = c[1].selectbox("Type", ["exact","startswith","contains","glob","regex"],
                              index=["exact","startswith","contains","glob","regex"].index(r.match_type), key=f"so_mt_{r.id}")
    display_pat = r.asset_pattern if (r.asset_pattern or "").strip() else "(alle assets)"
    new_pat  = c[2].text_input("Patroon", value=display_pat, key=f"so_patt_{r.id}")
    # wanneer bewaren → vervang "(alle assets)" terug naar lege string:
    save_pat = ("" if new_pat.strip() == "(alle assets)" else new_pat.strip())
    new_owner= c[3].text_input("Eigenaar", value=r.owner_name, key=f"so_owner_{r.id}")
    new_ord  = c[4].number_input("Volg.", value=r.sort_order, key=f"so_ord_{r.id}")
    new_notes= c[5].text_input("Notitie", value=r.notes or "", key=f"so_notes_{r.id}")
    new_act  = c[6].checkbox("Actief", value=r.active, key=f"so_act_{r.id}")
    if c[7].button("💾", key=f"so_save_{r.id}"):
        with Session(engine) as s:
            rec = s.get(SystemOwnerMap, r.id)
            rec.match_type = new_mt
            rec.asset_pattern = save_pat
            rec.owner_name = new_owner.strip() or rec.owner_name
            rec.sort_order = int(new_ord or 0)
            rec.notes = (new_notes or None)
            rec.active = bool(new_act)
            s.add(rec); s.commit()
        st.success("Opgeslagen."); st.rerun()
