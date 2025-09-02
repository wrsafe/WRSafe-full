# pages/3_🔁_Beoordeling_&_Uitvoering.py
import streamlit as st
from datetime import datetime
from pathlib import Path
from sqlmodel import Session, select
from db import engine, init_db
from models import (
    Permit, PermitMeasure, Measure,
    ApprovalStep, ApprovalLog, PermitStep,
    PermitWorkType, WorkType, PermitTool, Tool,
    PermitSpace, Space, PermitRisk, Risk
)
from services.pdf_export import export_permit_pdf
from services.nav import render_nav
from services.owners import resolve_area_owner, resolve_system_owner

init_db()
st.set_page_config(page_title="Beoordeling & Uitvoering", layout="wide")
render_nav()

st.header("🔁 Beoordeling & Uitvoering")

# --- Laden van vergunning ---
pid = st.number_input("Vergunning ID", min_value=1, step=1)
col_load = st.columns([1,1,6])
if col_load[0].button("Laden", type="primary"):
    st.session_state["permit_id"] = int(pid)
if col_load[1].button("Exporteer PDF"):
    with Session(engine) as s:
        p = s.get(Permit, int(pid))
        if not p:
            st.error("Vergunning niet gevonden.")
        else:
            out = Path(f"permit_{p.id}.pdf")
            export_permit_pdf(p, out)
            st.download_button("Download PDF", data=open(out, "rb"), file_name=out.name, mime="application/pdf")

if not st.session_state.get("permit_id"):
    st.info("Voer een ID in en klik **Laden**."); st.stop()

with Session(engine) as s:
    p = s.get(Permit, st.session_state["permit_id"])
if not p:
    st.error("Vergunning niet gevonden."); st.stop()

# ===== Kop en status (compact) =====
st.subheader(f"#{p.id} – {p.title}")
st.markdown(f"### Status: **{p.status}**")

# ===== Aanvrager (compacte tabel) =====
st.markdown("**Aanvrager**")
st.dataframe(
    {"Naam": [p.applicant_name or "—"],
     "Team/Afdeling": [p.applicant_team or "—"],
     "Contractor": [p.applicant_org or "—"]},
    use_container_width=True,
    hide_index=True
)

area_owner = resolve_area_owner(p.location, p.department) # or "—"
system_owner = resolve_system_owner(p.work_area, getattr(p, "asset", None)) # or "—"
she_owner = "SHE" if p.risk_class == "Hoog" else "—"
specialist_owner = "Nog te bepalen"  # of later koppeling via extra tabel

# === Eigenaren: verplicht invullen + beheer-links ===
from services.owners import resolve_area_owner, resolve_system_owner

st.markdown("**Verstrekkers**")

# Automatische suggesties (al eerder bepaald in je code)
auto_area_owner   = area_owner      # resolve_area_owner(p.location, p.department)
auto_system_owner = system_owner    # resolve_system_owner(p.work_area, getattr(p, "asset", None))

# UI-waarden initialiseren: bestaande waarde op permit > suggestie > leeg
st.session_state.setdefault("area_owner_input",   (p.area_owner or auto_area_owner or ""))
st.session_state.setdefault("system_owner_input", (p.system_owner or auto_system_owner or ""))

col_own = st.columns([5,5,2,2])
with col_own[0]:
    area_owner_val = st.text_input(
        "Gebiedseigenaar (verplicht)",
        key="area_owner_input",
        placeholder="Naam/team van gebiedseigenaar"
    )
    if not auto_area_owner:
        st.warning("Geen automatische match voor Gebiedseigenaar. Gebruik ✏️ Beheer om een mapping toe te voegen.", icon="⚠️")

with col_own[1]:
    system_owner_val = st.text_input(
        "Systeemeigenaar (verplicht)",
        key="system_owner_input",
        placeholder="Naam/team van systeemeigenaar"
    )
    if not auto_system_owner:
        st.warning("Geen automatische match voor Systeemeigenaar. Gebruik ✏️ Beheer om een mapping toe te voegen.", icon="⚠️")

st.subheader("Werkzaamheden & Verstrekkers")

# Definieer de rijen als (label, waarde)
work_rows = [
    ("Titel", p.title or "—"),
    ("Status", p.status or "—"),
    ("Aanvrager", p.applicant_name or "—"),
    ("Team / Afdeling", p.applicant_team or "—"),
    ("Contractor", p.applicant_org or "—"),
    ("Locatie", p.location or "—"),
    ("Afdeling", p.department or "—"),
    ("Verstrekker – Gebiedseigenaar (auto)", area_owner),
    ("Werkgebied", p.work_area or "—"),
    ("Installatie / Systeem", getattr(p, "asset", None) or "—"),
    ("Verstrekker – Systeemeigenaar", system_owner),
    ("Verstrekker – SHE (bij hoog risico)", she_owner),
    ("Verstrekker – Specialist", specialist_owner),
    ("Reden van het werk", p.reason or "—"),
    ("Risicoklasse", p.risk_class or "—"),
    ("Start", p.start_dt.strftime("%d-%m-%Y %H:%M") if p.start_dt else "—"),
    ("Einde", p.end_dt.strftime("%d-%m-%Y %H:%M") if p.end_dt else "—"),
]

st.dataframe(
    {"Omschrijving": [r[0] for r in work_rows],
     "Inhoud": [r[1] for r in work_rows]},
    use_container_width=True,
    hide_index=True
)

# ===== Werkzaamheden =====
with Session(engine) as s:
    # Ruimtes
    ps = s.exec(select(PermitSpace).where(PermitSpace.permit_id == p.id)).all()
    space_ids = [x.space_id for x in ps if x.space_id]
    cat_names = [r.name for r in s.exec(select(Space).where(Space.id.in_(space_ids))).all()] if space_ids else []
    custom = [x.custom_name for x in ps if x.custom_name]
    spaces_txt = ", ".join([*cat_names, *[c for c in custom if c]]) or "—"
    # Werkwijzen / Gereedschappen
    p_wt = s.exec(select(PermitWorkType).where(PermitWorkType.permit_id==p.id)).all()
    wt_ids = [x.worktype_id for x in p_wt if x.worktype_id]
    wt_names = [w.name for w in s.exec(select(WorkType).where(WorkType.id.in_(wt_ids))).all()] if wt_ids else []
    wt_custom = [x.custom_name for x in p_wt if x.custom_name]
    p_tl = s.exec(select(PermitTool).where(PermitTool.permit_id==p.id)).all()
    tl_ids = [x.tool_id for x in p_tl if x.tool_id]
    tl_names = [t.name for t in s.exec(select(Tool).where(Tool.id.in_(tl_ids))).all()] if tl_ids else []
    tl_custom = [x.custom_name for x in p_tl if x.custom_name]
    # Stappen
    steps = s.exec(select(PermitStep).where(PermitStep.permit_id == p.id).order_by(PermitStep.order, PermitStep.id)).all()

if steps:
    st.markdown("**Werkstappen / Deeltaken**")
    st.dataframe(
        {"Stap": [f"{s.order}. {s.description}" for s in steps]},
        use_container_width=True,
        hide_index=True
    )

# ===== Risico's (Werk & Omgeving) + maatregelen met namen =====
with Session(engine) as s:
    # Werk-risico's: joinen op Risk voor naam; val terug op vrije tekst (risk_name)
    rw = s.exec(
        select(PermitRisk, Risk.name)
        .join(Risk, Risk.id == PermitRisk.risk_id, isouter=True)
        .where((PermitRisk.permit_id == p.id) & (PermitRisk.category == "Werk"))
        .order_by(PermitRisk.id)
    ).all()
    risk_names_work = [(rname or pr.risk_name or "—") for pr, rname in rw]

    # Omgeving-risico's
    re = s.exec(
        select(PermitRisk, Risk.name)
        .join(Risk, Risk.id == PermitRisk.risk_id, isouter=True)
        .where((PermitRisk.permit_id == p.id) & (PermitRisk.category == "Omgeving"))
        .order_by(PermitRisk.id)
    ).all()
    risk_names_env = [(rname or pr.risk_name or "—") for pr, rname in re]

    measures = s.exec(select(PermitMeasure).where(PermitMeasure.permit_id == p.id)).all()

st.markdown("**Risico’s & Maatregelen**")
colw, cole = st.columns(2)
with colw:
    st.caption("Risico’s – Werk")
    st.dataframe({"Risico": risk_names_work or ["—"]},
                 use_container_width=True, hide_index=True)
with cole:
    st.caption("Risico’s – Omgeving")
    st.dataframe({"Risico": risk_names_env or ["—"]},
                 use_container_width=True, hide_index=True)

if measures:
    st.caption("Maatregelen / PBM’s")
    st.dataframe({"Omschrijving": [m.description for m in measures]},
                 use_container_width=True, hide_index=True)

st.divider()

# ===== Goedkeuringsketen =====
st.subheader("Goedkeuringsketen (door aanvrager in te vullen)")
DEFAULT_STEPS = [
    (10, "Verstrekker_Gebied",   "Verstrekker – Gebiedseigenaar", True),
    (20, "Verstrekker_Systeem",  "Verstrekker – Systeem/Installatie-eigenaar", True),
    (30, "SHE",                  "SHE (bij hoog risico)", True),
    (40, "IV_BMI",               "Installatieverantwoordelijke (BMI)", False),
    (50, "WG_Coordinator",       "Werkvergunningcoördinator", True),
]
with Session(engine) as s:
    steps_exist = s.exec(select(ApprovalStep).where(ApprovalStep.permit_id==p.id)).all()
    if not steps_exist and st.button("Standaard stappen toevoegen"):
        for order, role, label, req in DEFAULT_STEPS:
            s.add(ApprovalStep(permit_id=p.id, step_order=order, role_type=role, display_name=label, required=req))
        s.commit(); st.success("Stappen toegevoegd."); st.rerun()

with Session(engine) as s:
    steps = s.exec(select(ApprovalStep).where(ApprovalStep.permit_id==p.id).order_by(ApprovalStep.step_order)).all()
if steps:
    for stp in steps:
        cols = st.columns([6,3,2,2])

        # Suggestie op basis van roltype en ingevulde/gesuggereerde eigenaren
        suggested = None
        if stp.role_type == "Verstrekker_Gebied":
            suggested = (st.session_state.get("area_owner_input") or auto_area_owner or None)
        elif stp.role_type == "Verstrekker_Systeem":
            suggested = (st.session_state.get("system_owner_input") or auto_system_owner or None)

        cols[0].write(
            f"**{stp.display_name}**  \n_{stp.role_type}_  \n{'(verplicht)' if stp.required else '(optioneel)'}" +
            (f"\n\n_Suggestie:_ {suggested}" if suggested else "")
        )

        approver = cols[1].text_input(
            "Naam",
            key=f"appr_{stp.id}",
            placeholder=(suggested or "")
        )
        decision = cols[2].selectbox("Actie", ["— kies —","Approve","Reject"], key=f"act_{stp.id}")

        if cols[3].button("Opslaan", key=f"save_{stp.id}"):
            if decision not in ("Approve","Reject"):
                st.warning("Kies eerst een actie.")
            elif not approver.strip():
                st.warning("Vul een naam in.")
            else:
                with Session(engine) as s2:
                    s2.add(ApprovalLog(
                        permit_id=p.id, step_order=stp.step_order,
                        approver_name=approver.strip(),
                        decision="Approved" if decision=="Approve" else "Rejected"
                    ))
                    s2.commit()
                st.success("Beslissing opgeslagen."); st.rerun()
else:
    st.caption("Nog geen stappen aanwezig.")

st.divider()

# ===== Status-acties =====
ALLOWED_TRANSITIONS = {
    "Concept":        ["Ingediend"],
    "Ingediend":      ["InBeoordeling"],
    "InBeoordeling":  ["Goedgekeurd", "Afgewezen"],
    "Goedgekeurd":    ["UitvoerGestart"],
    "UitvoerGestart": ["UitvoerGereed"],
    "UitvoerGereed":  ["Gesloten"],
    "Afgewezen":      [],
    "Gesloten":       []
}

def can_go(current: str, target: str) -> bool:
    return target in ALLOWED_TRANSITIONS.get(current, [])

def all_required_measures_checked(permit_id: int) -> bool:
    with Session(engine) as s:
        rows = s.exec(select(PermitMeasure).where((PermitMeasure.permit_id==permit_id) & (PermitMeasure.required==True))).all()
    return all(r.checked_at for r in rows) if rows else True

def approvals_complete(permit_id: int) -> bool:
    with Session(engine) as s:
        steps = s.exec(select(ApprovalStep).where((ApprovalStep.permit_id==permit_id) & (ApprovalStep.required==True))).all()
        if not steps: return True
        for stp in steps:
            log = s.exec(select(ApprovalLog).where(
                (ApprovalLog.permit_id == permit_id) &
                (ApprovalLog.step_order == stp.step_order) &
                (ApprovalLog.decision == "Approved")
            ).order_by(ApprovalLog.at.desc())).first()
            if not log: return False
        return True

# Labels compacter + 'Opnemen' → 'In beoordeling'
BUTTONS = [
    ("Indienen",          "Ingediend"),
    ("In beoordeling",    "InBeoordeling"),
    ("Goedkeuren",        "Goedgekeurd"),
    ("Afwijzen",          "Afgewezen"),
    ("Start uitvoer",     "UitvoerGestart"),
    ("Afronden uitvoer",  "UitvoerGereed"),
    ("Sluiten",           "Gesloten"),
]
cols = st.columns(len(BUTTONS))
clicked = None
for i, (lab, target) in enumerate(BUTTONS):
    enabled = can_go(p.status, target)
    if target == "UitvoerGestart" and enabled:
        enabled = all_required_measures_checked(p.id) and approvals_complete(p.id)
    if cols[i].button(lab, disabled=not enabled):
        clicked = target

if clicked:
    with Session(engine) as s:
        perm = s.get(Permit, p.id)

        # ✋ Verplichte eigenaren bij INDienen
        if clicked == "Ingediend":
            ao = (st.session_state.get("area_owner_input") or "").strip()
            so = (st.session_state.get("system_owner_input") or "").strip()
            if not ao or not so:
                st.error("Vul eerst zowel **Gebiedseigenaar** als **Systeemeigenaar** in (of beheer de mapping).")
                st.stop()
            # Sla de gekozen/ingevulde eigenaren op de vergunning
            perm.area_owner = ao
            perm.system_owner = so

        # bestaande guards
        if not can_go(perm.status, clicked):
            st.warning("Overgang niet toegestaan."); st.stop()
        if clicked == "UitvoerGestart":
            if not all_required_measures_checked(perm.id):
                st.error("Eerst alle verplichte maatregelen afvinken."); st.stop()
            if not approvals_complete(perm.id):
                st.error("Niet alle vereiste goedkeuringen akkoord."); st.stop()

        perm.status = clicked
        s.add(perm); s.commit()

    st.success(f"Status → **{clicked}**"); st.rerun()
