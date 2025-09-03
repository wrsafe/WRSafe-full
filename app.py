# app.py
import streamlit as st
from pathlib import Path
import shutil, tempfile

from db import init_db
from services.auth_simple import load_cfg, try_login, current_user, current_role, logout

st.set_page_config(page_title="WRSafe – Werkvergunning", layout="wide")

# === DB URL uit Secrets + demo: kopie van seed per gebruiker ===
def _set_db_url():
    # Basis-URL uit Cloud/Lokaal secrets
    db_url = st.secrets["connections"]["wrsafe_db"]["url"]  # bv. sqlite:///data/wrsafe_demo_seed.db

    # Demo-modus: werk op tijdelijke kopie, zodat seed schoon blijft
    if st.secrets.get("demo", {}).get("ephemeral_copy"):
        seed = Path("data/wrsafe_demo_seed.db")
        user = (st.session_state.get("user") or "") or (st.session_state.get("USER", {}).get("username") or "anon")
        tmp = Path(tempfile.gettempdir()) / f"wrsafe_{user}.db"
        if seed.exists() and not tmp.exists():
            shutil.copy(seed, tmp)
        if tmp.exists():
            db_url = f"sqlite:///{tmp}"

    st.session_state["DB_URL"] = db_url

_set_db_url()

# --- DB init (robuust) ---
# Als jouw init_db() geen parameters accepteert en zelf st.session_state["DB_URL"] leest, laat zo.
# Anders: init_db(st.session_state["DB_URL"])
init_db()

# --- Config / role ---
cfg = load_cfg()  # we patchen hieronder services/auth_simple.load_cfg zodat dit uit Secrets kan lezen
role = st.session_state.get("role") or current_role(cfg)

# -----------------------
# Sidebar (whitelist)
# -----------------------
with st.sidebar:
    st.markdown("### Navigatie")
    # Workflow (alle bezoekers)
    st.page_link("app.py", label="🏠 Start")
    st.page_link("pages/1_🎫_Nieuwe_Vergunning.py",      label="🎫 Nieuwe vergunning")
    st.page_link("pages/3_🔁_Beoordeling_&_Uitvoering.py", label="🔁 Beoordeling & Uitvoering")
    st.page_link("pages/2_📋_Overzicht.py",             label="📋 Overzicht")
    # Optioneel: één rapportagepagina laten zien (zo niet, comment uit)
    # st.page_link("pages/4_📄_Rapportage.py",             label="📄 Rapportage")

    # Alleen voor beheerders (klein setje aanzetten voor demo)
    if (st.session_state.get("role") or "").lower() == "beheerder":
        st.markdown("---")
        st.markdown("**Beheer (demo)**")
        st.page_link("pages/B1_🗂️_Beheer_Risicoklassen.py", label="🗂️ Risicoklassen")
        # evt. nog 1–2 erbij:
        # st.page_link("pages/B4_🗂️_Beheer_Maatregelen.py",   label="🗂️ Maatregelen")
        # st.page_link("pages/B5_🗂️_Beheer_PBMs.py",          label="🗂️ PBM's")

    st.markdown("---")
    st.markdown("### Inloggen")

    user = current_user()
    if not user:
        # Form voorkomt “dubbel rerun”-gedrag en enter-issues
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("E-mail", key="login_email")
            pw    = st.text_input("Wachtwoord", type="password", key="login_pw")
            submitted = st.form_submit_button("Log in")
        if submitted:
            ok = try_login((email or "").strip(), pw or "", cfg)
            if ok:
                st.session_state["user"] = ok
                st.session_state["role"] = (cfg.get("roles") or {}).get(ok, "gebruiker")
                st.success("Ingelogd.")
                st.rerun()
            else:
                st.error("Onjuiste e-mail of wachtwoord.")
    else:
        st.write(f"Ingelogd als **{user}** (rol: **{role}**)")
        if st.button("Logout"):
            logout()
            for k in ("user", "role", "login_email", "login_pw"):
                st.session_state.pop(k, None)
            st.rerun()

st.title("WRSafe – Werkvergunning")
st.caption("Gebruik het menu links om een nieuwe vergunning aan te maken of bestaande te beheren.")
