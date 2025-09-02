# pages/1_🎫_Nieuwe_Vergunning.py  (VERVANGEN)
from sqlalchemy import Engine
import streamlit as st
from datetime import datetime, time
from sqlmodel import Session, select
from db import engine, init_db, get_session
from models import (
    Permit, PermitRiskAction, PermitStep, PermitTool, PermitRisk, PermitMeasure, PermitWorkType, PermitSpace,
    WorkType, RiskClass, Tool, Risk, Measure, WorkSubject, WorkArea,
    SiteLocation, DepartmentUnit, Space,
    WorkRiskCat, EnvRiskCat, WorkRiskRule, EnvRiskRule, ResponsibleRole
)

# --- Init
init_db()
st.set_page_config(page_title="Nieuwe vergunning (wizard)", layout="wide")
from services.nav import render_nav
render_nav()
st.header("🎫 Nieuwe vergunning – Wizard")

# -----------------------
# Helpers
# -----------------------
def dedupe_rows(rows: list[dict]) -> list[dict]:
    seen = set(); out = []
    for r in rows:
        key = (
            (r.get("risk") or "").strip().lower(),
            (r.get("measure") or "").strip().lower(),
            (r.get("responsible") or "").strip().lower(),
        )
        if key in seen: continue
        seen.add(key); out.append(r)
    return out

def get_state():
    if "wizard" not in st.session_state:
        st.session_state["wizard"] = {
            # Stap 1 - Aanvraag werk
            "title": "",
            "applicant_name": "",
            "applicant_team": "",
            "applicant_org": "",
            "location": "",
            "department": "",
            "spaces": [],
            "space_custom": "",
            "subject": None,
            "work_area": None,
            "risk_class": None,
            "asset": "",
            "reason": "",
            "start_date": datetime.today().date(),
            "start_time": time(8, 0),
            "end_date": datetime.today().date(),
            "end_time": time(17, 0),

            # Stap 2 - Uitvoering
            "worktypes": [], "worktype_custom": "",
            "tools": [],     "tool_custom": "",

            # Stap 3 - TRA Werk
            "risks_work": [],
            "work_actions": [],
            "pbms_work": [],

            # Stap 4 - TRA Omgeving
            "risks_env": [],
            "env_actions": [],
            "pbms_env": [],

            # Stap 5 - Overzicht en opslaan
            "remarks": "",
        }
    return st.session_state["wizard"]

W = get_state()

# Gemeenschappelijke helper: regels → rijen
def prefill_actions_from_rules(category: str, chosen_names: list[str]) -> list[dict]:
    rows: list[dict] = []
    if not chosen_names:
        return rows
    with get_session() as s:
        if category == "Werk":
            cats = s.exec(select(WorkRiskCat).where(WorkRiskCat.name.in_(chosen_names))).all()
            rules = s.exec(select(WorkRiskRule).where(WorkRiskRule.risk_id.in_([c.id for c in cats])).order_by(WorkRiskRule.weight)).all()
        else:
            cats = s.exec(select(EnvRiskCat).where(EnvRiskCat.name.in_(chosen_names))).all()
            rules = s.exec(select(EnvRiskRule).where(EnvRiskRule.risk_id.in_([c.id for c in cats])).order_by(EnvRiskRule.weight)).all()

        mids = list({ru.measure_id for ru in rules})
        measures = s.exec(select(Measure).where(Measure.id.in_(mids))).all()
        m_by_id = {m.id: m for m in measures}

        cat_by_id = {c.id: c for c in cats}
        for ru in rules:
            m = m_by_id.get(ru.measure_id)
            if not m: continue
            risk_name = cat_by_id.get(ru.risk_id).name
            resp = m.default_responsible or ("Houder" if category == "Werk" else "Verstrekker-Gebied")
            rows.append({"risk": risk_name, "measure": m.name, "responsible": resp, "source": "rule"})
    return rows

# ===== Kleine helper voor vrije lijstinvoer via data_editor =====
def _clean_list(values: list[str]) -> list[str]:
    seen, out = set(), []
    for v in (values or []):
        vv = (v or "").strip()
        if not vv:
            continue
        key = vv.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(vv)
    return out

def list_editor(values: list[str], label: str, *, suggestions: list[str] | None, key: str, help: str = "") -> list[str]:
    if suggestions:
        st.caption(f"Suggesties: {', '.join(suggestions[:15])}{'…' if len(suggestions) > 15 else ''}")
    df = st.data_editor(
        [{"waarde": v} for v in (values or [])],
        key=key,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "waarde": st.column_config.TextColumn(label, help=help, max_chars=120),
        },
    )
    return _clean_list([row.get("waarde", "") for row in df])

def _dedupe_keep_order(items: list[str]) -> list[str]:
    seen = set(); out = []
    for v in items or []:
        vv = (v or "").strip()
        if not vv: 
            continue
        key = vv.lower()
        if key in seen:
            continue
        seen.add(key); out.append(vv)
    return out

def checklist_select(label: str, options: list[str], key_prefix: str, selected_init: list[str] | None = None, cols: int = 3) -> list[str]:
    """
    Toon alle opties als checkboxen, met filter + 'Alles'/'Geen'.
    Bewaart selectie in st.session_state[f"{key_prefix}_selected"].
    """
    if selected_init is None: selected_init = []
    # init state 1x met geldige keuzes
    if f"{key_prefix}_selected" not in st.session_state:
        st.session_state[f"{key_prefix}_selected"] = [x for x in selected_init if x in options]

    st.markdown(f"**{label}**")
    q = st.text_input("Filter", key=f"{key_prefix}_q", placeholder=f"Filter {label.lower()}...")
    filtered = [o for o in options if (q or "").strip().lower() in o.lower()] if q else options

    bcol = st.columns([1,1,6])
    if bcol[0].button("Alles", key=f"{key_prefix}_all"):
        # alleen gefilterde items inschakelen
        cur = set(st.session_state[f"{key_prefix}_selected"])
        cur.update(filtered)
        st.session_state[f"{key_prefix}_selected"] = _dedupe_keep_order(list(cur))
    if bcol[1].button("Geen", key=f"{key_prefix}_none"):
        cur = set(st.session_state[f"{key_prefix}_selected"])
        for o in filtered:
            cur.discard(o)
        st.session_state[f"{key_prefix}_selected"] = _dedupe_keep_order(list(cur))

    # render checkboxes
    sel_set = set(st.session_state[f"{key_prefix}_selected"])
    cols_obj = st.columns(cols)
    for i, opt in enumerate(filtered):
        chk_key = f"{key_prefix}_chk_{opt}"
        # init checkbox-key afgeleid van huidige selectie
        if chk_key not in st.session_state:
            st.session_state[chk_key] = (opt in sel_set)
        # checkbox tonen
        new_val = cols_obj[i % cols].checkbox(opt, key=chk_key)
        # stel bij in selectie
        if new_val:
            sel_set.add(opt)
        else:
            sel_set.discard(opt)

    # sync back naar hoofdselected
    st.session_state[f"{key_prefix}_selected"] = _dedupe_keep_order(list(sel_set))
    return st.session_state[f"{key_prefix}_selected"]

# -----------------------
# Voorraad uit beheer
# -----------------------
with get_session() as s:
    locs     = s.exec(select(SiteLocation).where(SiteLocation.active==True).order_by(SiteLocation.sort_order, SiteLocation.name)).all()
    deps     = s.exec(select(DepartmentUnit).where(DepartmentUnit.active==True).order_by(DepartmentUnit.sort_order, DepartmentUnit.name)).all()
    spaces   = s.exec(select(Space).where(Space.active==True).order_by(Space.sort_order, Space.name)).all()
    subjects = s.exec(select(WorkSubject).where(WorkSubject.active==True).order_by(WorkSubject.sort_order, WorkSubject.name)).all()
    areas    = s.exec(select(WorkArea).where(WorkArea.active==True).order_by(WorkArea.sort_order, WorkArea.name)).all()
    wtypes   = s.exec(select(WorkType).where(WorkType.active==True).order_by(WorkType.sort_order, WorkType.name)).all()
    tools    = s.exec(select(Tool).where(Tool.active==True).order_by(Tool.sort_order, Tool.name)).all()
    rcs      = s.exec(select(RiskClass).where(RiskClass.active==True).order_by(RiskClass.sort_order, RiskClass.name)).all()
    wr_cats  = s.exec(select(WorkRiskCat).where(WorkRiskCat.active==True).order_by(WorkRiskCat.sort_order, WorkRiskCat.name)).all()
    er_cats  = s.exec(select(EnvRiskCat).where(EnvRiskCat.active==True).order_by(EnvRiskCat.sort_order, EnvRiskCat.name)).all()
    roles_all= s.exec(select(ResponsibleRole).where(ResponsibleRole.active==True).order_by(ResponsibleRole.sort_order, ResponsibleRole.name)).all()
    work_meas  = s.exec(select(Measure).where((Measure.active==True) & (Measure.scope=="Werk")).order_by(Measure.name)).all()
    env_meas   = s.exec(select(Measure).where((Measure.active==True) & (Measure.scope=="Omgeving")).order_by(Measure.name)).all()
    # pbms       = s.exec(select(PBM).where(PBM.active==True).order_by(PBM.sort_order, PBM.name)).all()
    # PBM's uit Measure 
    pbm_measures = s.exec(select(Measure).where((Measure.active==True) & (Measure.scope=="PBM")).order_by(Measure.name)).all()

# Namenlijsten
loc_names   = [x.name for x in locs]
dep_names   = [x.name for x in deps]
space_names = [x.name for x in spaces]
subj_names  = [x.name for x in subjects]
area_names  = [x.name for x in areas]
wt_names    = [x.name for x in wtypes]
tool_names  = [x.name for x in tools]
rc_names    = [x.name for x in rcs]
work_risk_names = [r.name for r in wr_cats]
env_risk_names  = [r.name for r in er_cats]
work_meas_names = [m.name for m in work_meas]
env_meas_names  = [m.name for m in env_meas]
# pbm_names       = [p.name for p in pbms]
RESP_OPTIONS    = [rr.name for rr in roles_all] or ["Houder","Verstrekker-Gebied","Verstrekker-Systeem","SHE","Specialist","Coördinator"]
pbm_names       = [m.name for m in pbm_measures]

# -----------------------
# Tabs (nieuw): TRA Werk / TRA Omgeving
# -----------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "1) Aanvraag werk", "2) Uitvoering",
    "3) TRA Werk", "4) TRA Omgeving",
    "5) Overzicht & Opslaan"
])


# ***************** TAB 1 (aanvraag + locatie/afdeling/ruimten + tijden) *****************
with tab1:
    st.session_state.setdefault("wiz_title", W.get("title", ""))
    st.session_state.setdefault("wiz_asset", W.get("asset", ""))
    st.subheader("Stap 1 – Aanvrager & Werkzaamheden")
    W["title"] = st.text_input("Titel / Omschrijving*", key="wiz_title")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Aanvrager**")
        W["applicant_name"] = st.text_input("Naam aanvrager", value=W["applicant_name"])
        W["applicant_team"] = st.text_input("Team / Afdeling (aanvrager)", value=W["applicant_team"])
        W["applicant_org"]  = st.text_input("Contractor (indien van toepassing)", value=W["applicant_org"])

        st.markdown("**Locatie werkzaamheden**")
        W["location"] = st.selectbox("Location*", loc_names,
                                     index=loc_names.index(W["location"]) if W["location"] in loc_names else (0 if loc_names else None))
        W["department"] = st.selectbox("Department*", dep_names,
                                       index=dep_names.index(W["department"]) if W["department"] in dep_names else (0 if dep_names else None))

    st.markdown("**Ruimte(n)**")

    # Checklist met filter + Alles/Geen (toon alle beheerruimtes)
    selected_spaces = checklist_select(
        label="Ruimten (beheerlijst)",
        options=space_names,    # alle beheerde ruimtes
        key_prefix="space_ck",
        selected_init=[x for x in (W.get("spaces") or []) if x in space_names],
        cols=4,                 # aantal kolommen met checkboxes, pas aan naar wens
    )

    # Vrije invoer (Enter) voor niet-beheerde ruimtes
    def _add_space_free():
        nm = (st.session_state.get("space_add_free") or "").strip()
        if not nm:
            return
        free = W.setdefault("spaces_free", [])
        if nm not in free and nm not in selected_spaces:
            free.append(nm)
        st.session_state["space_add_free"] = ""

    st.text_input(
        "Eigen ruimte (vrije tekst) – druk Enter",
        key="space_add_free",
        on_change=_add_space_free,
    )

    # Combineer beheerde + vrije keuzes tot één lijst voor opslag
    free_spaces = [x for x in W.get("spaces_free", []) if x not in space_names]
    W["spaces"] = _dedupe_keep_order(list(selected_spaces) + free_spaces)

    st.caption("Gekozen ruimten: " + (", ".join(W["spaces"]) if W["spaces"] else "—"))

    with c2:
        st.markdown("**Werkzaamheden**")
        # 🔁 Reden van het werk: verplicht keuzeveld (geen vrije tekst)
        REASONS = ["Gepland", "Storing"]
        # init-state fallback
        if W.get("reason") not in REASONS:
            W["reason"] = REASONS[0]
        W["reason"] = st.selectbox("Reden van het werk*", REASONS,
                                   index=REASONS.index(W["reason"]))

        W["subject"] = st.selectbox("Betreft*", subj_names,
                                    index=subj_names.index(W["subject"]) if W["subject"] in subj_names else (0 if subj_names else None))
        W["asset"] = st.text_input("Installatie / Systeem / Onderwerp", key="wiz_asset")
        W["work_area"] = st.selectbox("Werkgebied*", area_names,
                                      index=area_names.index(W["work_area"]) if W["work_area"] in area_names else (0 if area_names else None))
        W["risk_class"] = st.selectbox("Risicoklasse*", rc_names,
                                       index=rc_names.index(W["risk_class"]) if W["risk_class"] in rc_names else (0 if rc_names else None))

        d1, d2 = st.columns(2)
        with d1:
            W["start_date"] = st.date_input("Startdatum*", value=W["start_date"])
            W["start_time"] = st.time_input("Starttijd*", value=W["start_time"])
        with d2:
            W["end_date"]   = st.date_input("Einddatum*", value=W["end_date"])
            W["end_time"]   = st.time_input("Eindtijd*", value=W["end_time"])

    st.caption("Velden met * zijn verplicht.")


# ***************** TAB 2 (Werkwijzen/Gereedschappen) *****************
with tab2:
    st.subheader("Stap 2 – Uitvoering")

    # === Werkstappen / deeltaken — eenvoudig invoerveld + knop (robust, geen SessionState error) ===
    st.markdown("**Beschrijving werkzaamheden (in stappen / deeltaken)**")

    # --- init state ---
    W.setdefault("steps", [])
    st.session_state.setdefault("new_step_input", "")
    st.session_state.setdefault("bulk_steps_input", "")

    # --- deferred actions: verwerk 'Toevoegen' vóórdat widgets gerenderd worden ---
    if st.session_state.pop("ADD_SINGLE_STEP", False):
        txt = (st.session_state.get("new_step_input") or "").strip()
        if txt:
            W["steps"].append(txt)
        # leeg maken mag nu (vóór render widgets)
        st.session_state["new_step_input"] = ""
        st.rerun()

    if st.session_state.pop("ADD_BULK_STEPS", False):
        bulk = st.session_state.get("bulk_steps_input") or ""
        lines = [ln.strip() for ln in bulk.splitlines() if ln.strip()]
        if lines:
            W["steps"].extend(lines)
        st.session_state["bulk_steps_input"] = ""
        st.rerun()

    # --- helpers om flags te zetten (worden aangeroepen door buttons) ---
    def _queue_add_single():
        st.session_state["ADD_SINGLE_STEP"] = True

    def _queue_add_bulk():
        st.session_state["ADD_BULK_STEPS"] = True

    # --- UI: enkele stap ---
    new_step = st.text_input(
        "Nieuwe stap / deeltaak",
        key="new_step_input",
        placeholder="Bijv. Werkgebied afzetten",
    )
    st.button("➕ Toevoegen", key="add_step_btn", on_click=_queue_add_single)

    # --- UI: bulk stappen ---
    with st.expander("Meerdere stappen in één keer toevoegen"):
        st.text_area(
            "Zet elke stap op een nieuwe regel",
            key="bulk_steps_input",
            height=120,
            placeholder="Stap 1\nStap 2\nStap 3",
        )
        st.button("➕ Voeg bovenstaande regels toe", key="add_bulk_steps_btn", on_click=_queue_add_bulk)

    # --- lijst tonen met verplaats/verwijder ---
    if W["steps"]:
        st.write("**Huidige stappen:**")
        # gebruik range(len()) i.p.v. enumerate direct in combinatie met mutaties
        for i in range(len(W["steps"])):
            s = W["steps"][i]
            cols = st.columns([6, 1, 1, 1])  # tekst | ↑ | ↓ | 🗑
            cols[0].write(f"{i+1}. {s}")
            if cols[1].button("↑", key=f"step_up_{i}", help="Omhoog") and i > 0:
                W["steps"][i-1], W["steps"][i] = W["steps"][i], W["steps"][i-1]
                st.rerun()
            if cols[2].button("↓", key=f"step_down_{i}", help="Omlaag") and i < len(W["steps"])-1:
                W["steps"][i+1], W["steps"][i] = W["steps"][i], W["steps"][i+1]
                st.rerun()
            if cols[3].button("🗑️", key=f"step_del_{i}", help="Verwijderen"):
                W["steps"].pop(i)
                st.rerun()
    else:
        st.caption("Nog geen stappen toegevoegd. Voeg bovenaan je eerste stap toe.")

    st.caption("Tip: beschrijf elke deeltaak apart; dit helpt bij de Taak Risico Analyse (TRA).")
    st.markdown("---")

    # ------- Werkwijzen (checklist) -------
    selected_wt = checklist_select(
        label="Werkwijzen (beheerlijst)",
        options=wt_names,                      # alle werkwijzen tonen
        key_prefix="wt_ck",
        selected_init=[x for x in (W.get("worktypes") or []) if x in wt_names],
        cols=3,                                # aantal kolommen met vinkjes
    )

    # Vrije invoer (Enter) voor extra werkwijze
    def _add_wt_free():
        nm = (st.session_state.get("wt_add_free") or "").strip()
        if not nm: return
        free = W.setdefault("worktypes_free", [])
        if nm not in free and nm not in selected_wt:
            free.append(nm)
        st.session_state["wt_add_free"] = ""

    st.text_input("Eigen werkwijze (vrije tekst) – druk Enter", key="wt_add_free", on_change=_add_wt_free)

    # Combineer beheerde + vrije werkwijzen
    free_wt = [x for x in W.get("worktypes_free", []) if x not in wt_names]
    W["worktypes"] = _dedupe_keep_order(list(selected_wt) + free_wt)

    st.caption("Gekozen werkwijzen: " + (", ".join(W["worktypes"]) if W["worktypes"] else "—"))

    st.markdown("---")

    # ------- Gereedschappen (checklist) -------
    selected_tools = checklist_select(
        label="Gereedschappen (beheerlijst)",
        options=tool_names,                    # alle tools tonen
        key_prefix="tool_ck",
        selected_init=[x for x in (W.get("tools") or []) if x in tool_names],
        cols=3,
    )

    def _add_tool_free():
        nm = (st.session_state.get("tool_add_free") or "").strip()
        if not nm: return
        free = W.setdefault("tools_free", [])
        if nm not in free and nm not in selected_tools:
            free.append(nm)
        st.session_state["tool_add_free"] = ""

    st.text_input("Eigen gereedschap (vrije tekst) – druk Enter", key="tool_add_free", on_change=_add_tool_free)

    free_tools = [x for x in W.get("tools_free", []) if x not in tool_names]
    W["tools"] = _dedupe_keep_order(list(selected_tools) + free_tools)

    st.caption("Gekozen gereedschappen: " + (", ".join(W["tools"]) if W["tools"] else "—"))


# ***************** TAB 3: TRA Werk *****************
with tab3:
    st.subheader("Stap 3 – TRA Werk")

    # --- Risico's Werk ---
    selected_wr = checklist_select(
        label="Risico’s Werk",
        options=work_risk_names,
        key_prefix="wr_ck",
        selected_init=[x for x in (W.get("risks_work") or []) if x in work_risk_names],
        cols=2,
    )

    def _add_wr_free():
        nm = (st.session_state.get("wr_add_free") or "").strip()
        if not nm: return
        free = W.setdefault("risks_work_free", [])
        if nm not in free and nm not in selected_wr:
            free.append(nm)
        st.session_state["wr_add_free"] = ""

    st.text_input("Eigen risico (vrije tekst) – druk Enter", key="wr_add_free", on_change=_add_wr_free)
    free_wr = [x for x in W.get("risks_work_free", []) if x not in work_risk_names]
    W["risks_work"] = _dedupe_keep_order(list(selected_wr) + free_wr)

    st.caption("Gekozen risico’s werk: " + (", ".join(W["risks_work"]) if W["risks_work"] else "—"))

    st.markdown("---")

    # --- Maatregelen Werk ---
    selected_mw = checklist_select(
        label="Maatregelen Werk",
        options=work_meas_names,
        key_prefix="mw_ck",
        selected_init=[x for x in (W.get("measures_work") or []) if x in work_meas_names],
        cols=2,
    )

    def _add_mw_free():
        nm = (st.session_state.get("mw_add_free") or "").strip()
        if not nm: return
        free = W.setdefault("measures_work_free", [])
        if nm not in free and nm not in selected_mw:
            free.append(nm)
        st.session_state["mw_add_free"] = ""

    st.text_input("Eigen maatregel (vrije tekst) – druk Enter", key="mw_add_free", on_change=_add_mw_free)
    free_mw = [x for x in W.get("measures_work_free", []) if x not in work_meas_names]
    W["measures_work"] = _dedupe_keep_order(list(selected_mw) + free_mw)

    st.caption("Gekozen maatregelen werk: " + (", ".join(W["measures_work"]) if W["measures_work"] else "—"))

    st.markdown("---")

    # --- PBM’s Werk ---
    selected_pw = checklist_select(
        label="PBM’s Werk",
        options=pbm_names,
        key_prefix="pw_ck",
        selected_init=[x for x in (W.get("pbms_work") or []) if x in pbm_names],
        cols=2,
    )

    def _add_pw_free():
        nm = (st.session_state.get("pw_add_free") or "").strip()
        if not nm: return
        free = W.setdefault("pbms_work_free", [])
        if nm not in free and nm not in selected_pw:
            free.append(nm)
        st.session_state["pw_add_free"] = ""

    st.text_input("Eigen PBM (vrije tekst) – druk Enter", key="pw_add_free", on_change=_add_pw_free)
    free_pw = [x for x in W.get("pbms_work_free", []) if x not in pbm_names]
    W["pbms_work"] = _dedupe_keep_order(list(selected_pw) + free_pw)

    st.caption("Gekozen PBM’s werk: " + (", ".join(W["pbms_work"]) if W["pbms_work"] else "—"))


# ***************** TAB 4: TRA Omgeving *****************
with tab4:
    st.subheader("Stap 4 – TRA Omgeving")

    # --- Risico's Omgeving ---
    selected_er = checklist_select(
        label="Risico’s Omgeving",
        options=env_risk_names,
        key_prefix="er_ck",
        selected_init=[x for x in (W.get("risks_env") or []) if x in env_risk_names],
        cols=2,
    )

    def _add_er_free():
        nm = (st.session_state.get("er_add_free") or "").strip()
        if not nm: return
        free = W.setdefault("risks_env_free", [])
        if nm not in free and nm not in selected_er:
            free.append(nm)
        st.session_state["er_add_free"] = ""

    st.text_input("Eigen risico (vrije tekst) – druk Enter", key="er_add_free", on_change=_add_er_free)
    free_er = [x for x in W.get("risks_env_free", []) if x not in env_risk_names]
    W["risks_env"] = _dedupe_keep_order(list(selected_er) + free_er)

    st.caption("Gekozen risico’s omgeving: " + (", ".join(W["risks_env"]) if W["risks_env"] else "—"))

    st.markdown("---")

    # --- Maatregelen Omgeving ---
    selected_me = checklist_select(
        label="Maatregelen Omgeving",
        options=env_meas_names,
        key_prefix="me_ck",
        selected_init=[x for x in (W.get("measures_env") or []) if x in env_meas_names],
        cols=2,
    )

    def _add_me_free():
        nm = (st.session_state.get("me_add_free") or "").strip()
        if not nm: return
        free = W.setdefault("measures_env_free", [])
        if nm not in free and nm not in selected_me:
            free.append(nm)
        st.session_state["me_add_free"] = ""

    st.text_input("Eigen maatregel (vrije tekst) – druk Enter", key="me_add_free", on_change=_add_me_free)
    free_me = [x for x in W.get("measures_env_free", []) if x not in env_meas_names]
    W["measures_env"] = _dedupe_keep_order(list(selected_me) + free_me)

    st.caption("Gekozen maatregelen omgeving: " + (", ".join(W["measures_env"]) if W["measures_env"] else "—"))

    st.markdown("---")

    # --- PBM’s Omgeving ---
    selected_pe = checklist_select(
        label="PBM’s Omgeving",
        options=pbm_names,
        key_prefix="pe_ck",
        selected_init=[x for x in (W.get("pbms_env") or []) if x in pbm_names],
        cols=2,
    )

    def _add_pe_free():
        nm = (st.session_state.get("pe_add_free") or "").strip()
        if not nm: return
        free = W.setdefault("pbms_env_free", [])
        if nm not in free and nm not in selected_pe:
            free.append(nm)
        st.session_state["pe_add_free"] = ""

    st.text_input("Eigen PBM (vrije tekst) – druk Enter", key="pe_add_free", on_change=_add_pe_free)
    free_pe = [x for x in W.get("pbms_env_free", []) if x not in pbm_names]
    W["pbms_env"] = _dedupe_keep_order(list(selected_pe) + free_pe)

    st.caption("Gekozen PBM’s omgeving: " + (", ".join(W["pbms_env"]) if W["pbms_env"] else "—"))


# ***************** TAB 5: Overzicht & Opslaan *****************
with tab5:
    st.subheader("Stap 5 – Overzicht & Opslaan")

    # ── Validatie ────────────────────────────────────────────────────────────────
    errors = []
    if not W["title"].strip():      errors.append("Titel is verplicht.")
    if not W["subject"]:            errors.append("Betreft is verplicht.")
    if not W["location"]:           errors.append("Location is verplicht.")
    if not W["department"]:         errors.append("Department is verplicht.")
    if not W["work_area"]:          errors.append("Werkgebied is verplicht.")
    if not W["risk_class"]:         errors.append("Risicoklasse is verplicht.")
    if not W.get("reason"):         errors.append("Reden van het werk is verplicht.")

    start_dt = datetime.combine(W["start_date"], W["start_time"])
    end_dt   = datetime.combine(W["end_date"],   W["end_time"])
    if end_dt <= start_dt:          errors.append("Einddatum/tijd moet na start liggen.")

    for e in errors:
        st.error(e)

    # ── Overzicht (compact) ─────────────────────────────────────────────────────
    st.markdown("### Aanvrager")
    st.write(f"- **Naam:** {W.get('applicant_name') or '—'}")
    st.write(f"- **Team/Afdeling:** {W.get('applicant_team') or '—'}")
    st.write(f"- **Contractor:** {W.get('applicant_org') or '—'}")

    st.markdown("### Werkgegevens")
    st.write(f"- **Betreft:** {W.get('subject') or '—'}")
    st.write(f"- **Werkgebied:** {W.get('work_area') or '—'}")
    st.write(f"- **Locatie:** {W.get('location') or '—'}")
    st.write(f"- **Afdeling:** {W.get('department') or '—'}")
    st.write(f"- **Reden van het werk:** {W.get('reason') or '—'}")
    st.write(f"- **Risicoklasse:** {W.get('risk_class') or '—'}")
    st.write(f"- **Start:** {start_dt.strftime('%d-%m-%Y %H:%M')}")
    st.write(f"- **Einde:** {end_dt.strftime('%d-%m-%Y %H:%M')}")

    st.markdown("### Ruimtes / Werkwijzen / Gereedschappen")
    st.write("- **Ruimtes:** " + (", ".join(W.get("spaces", [])) or "—"))
    st.write("- **Werkwijzen:** " + (", ".join(W.get("worktypes", [])) or "—"))
    st.write("- **Gereedschappen:** " + (", ".join(W.get("tools", [])) or "—"))

    st.markdown("### TRA – Werk")
    st.write("- **Risico’s (Werk):** " + (", ".join(W.get("risks_work", [])) or "—"))
    st.write("- **Maatregelen (Werk):** " + (", ".join(W.get("measures_work", [])) or "—"))
    st.write("- **PBM’s (Werk):** " + (", ".join(W.get("pbms_work", [])) or "—"))

    st.markdown("### TRA – Omgeving")
    st.write("- **Risico’s (Omgeving):** " + (", ".join(W.get("risks_env", [])) or "—"))
    st.write("- **Maatregelen (Omgeving):** " + (", ".join(W.get("measures_env", [])) or "—"))
    st.write("- **PBM’s (Omgeving):** " + (", ".join(W.get("pbms_env", [])) or "—"))

    # ── Opslaan ─────────────────────────────────────────────────────────────────
    if st.button("Opslaan als CONCEPT", disabled=bool(errors), type="primary"):
        from sqlmodel import Session, select
        from models import (
            Permit, PermitMeasure, PermitRisk, PermitTool, PermitWorkType,
            PermitSpace, PermitRiskAction, Measure, Risk, Space, WorkType, Tool,
            # als je stappen opslaat:
            PermitStep
        )

        with Session(engine) as s:
            # 1) hoofdrecord
            p = Permit(
                title=W["title"].strip(),
                location=(W.get("location") or "").strip(),
                department=(W.get("department") or "").strip(),
                work_area=(W.get("work_area") or "").strip(),
                applicant_name=(W.get("applicant_name") or "").strip(),
                applicant_team=(W.get("applicant_team") or "").strip(),
                applicant_org=(W.get("applicant_org") or "").strip(),
                reason=(W.get("reason") or "").strip(),
                subject=(W.get("subject") or "").strip(),
                asset=(W.get("asset") or "").strip(),
                start_dt=start_dt,
                end_dt=end_dt,
                status="Concept",
                risk_class=W.get("risk_class"),
            )
            s.add(p)
            s.flush()        # ← ID toekennen zonder commit
            pid = p.id       # ← cache het id en gebruik deze verder overal

            # 2) werkstappen (als je PermitStep model hebt)
            for i, desc in enumerate(W.get("steps", []) or [], start=1):
                d = (desc or "").strip()
                if d:
                    s.add(PermitStep(permit_id=pid, order=i, description=d))

            # 3) ruimtes
            #    - 'spaces' bevat zowel beheerlijst als vrije invoer (zoals je eerder combineerde)
            space_names = [x.name for x in s.exec(select(Space)).all()]
            space_by_name = {x.name: x for x in s.exec(select(Space).where(Space.name.in_(space_names))).all()}
            added_spaces = set()
            for nm in (W.get("spaces") or []):
                nm = (nm or "").strip()
                if not nm or nm in added_spaces:
                    continue
                rec = PermitSpace(permit_id=pid)
                if nm in space_by_name:
                    rec.space_id = space_by_name[nm].id
                else:
                    rec.custom_name = nm
                s.add(rec)
                added_spaces.add(nm)

            # 4) werkwijzen
            wt_all = s.exec(select(WorkType)).all()
            wt_by_name = {w.name: w for w in wt_all}
            seen = set()
            for nm in (W.get("worktypes") or []):
                nm = (nm or "").strip()
                if not nm or nm in seen:
                    continue
                rec = PermitWorkType(permit_id=pid)
                if nm in wt_by_name:
                    rec.worktype_id = wt_by_name[nm].id
                else:
                    rec.custom_name = nm
                s.add(rec)
                seen.add(nm)

            # 5) gereedschappen
            tool_all = s.exec(select(Tool)).all()
            tool_by_name = {t.name: t for t in tool_all}
            seen_t = set()
            for nm in (W.get("tools") or []):
                nm = (nm or "").strip()
                if not nm or nm in seen_t:
                    continue
                rec = PermitTool(permit_id=pid)
                if nm in tool_by_name:
                    rec.tool_id = tool_by_name[nm].id
                else:
                    rec.custom_name = nm
                s.add(rec)
                seen_t.add(nm)

            # 6) risico’s (catalogus)
            risk_all = s.exec(select(Risk).where(Risk.active == True)).all()
            risk_by_name = {r.name: r for r in risk_all}
            for nm in (W.get("risks_work") or []):
                r = risk_by_name.get(nm)
                if r:
                    s.add(PermitRisk(permit_id=pid, risk_id=r.id, category="Werk"))
            for nm in (W.get("risks_env") or []):
                r = risk_by_name.get(nm)
                if r:
                    s.add(PermitRisk(permit_id=pid, risk_id=r.id, category="Omgeving"))

            # 7) maatregelen (vrije + catalogus) → als PermitMeasure/PermitRiskAction/PBM’s etc.
            #    hieronder een simpele variant: alles als PermitMeasure (required=True)
            #    Pas aan naar jouw gewenste opslag (bijv. scheiding Werk/Omgeving/PBM).
            added_measures = set()
            for nm in (W.get("measures_work") or []):
                nm = (nm or "").strip()
                if nm and nm not in added_measures:
                    s.add(PermitMeasure(permit_id=pid, description=nm, required=True))
                    added_measures.add(nm)
            for nm in (W.get("measures_env") or []):
                nm = (nm or "").strip()
                if nm and nm not in added_measures:
                    s.add(PermitMeasure(permit_id=pid, description=nm, required=True))
                    added_measures.add(nm)
            for nm in (W.get("pbms_work") or []):
                nm = (nm or "").strip()
                if nm and nm not in added_measures:
                    s.add(PermitMeasure(permit_id=pid, description=nm, required=True))
                    added_measures.add(nm)
            for nm in (W.get("pbms_env") or []):
                nm = (nm or "").strip()
                if nm and nm not in added_measures:
                    s.add(PermitMeasure(permit_id=pid, description=nm, required=True))
                    added_measures.add(nm)

            # 8) klaar
            s.commit()

        st.success(f"Vergunning #{pid} opgeslagen als **Concept**.")
        st.session_state.pop("wizard", None)
        st.rerun()