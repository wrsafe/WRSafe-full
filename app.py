# app.py
import streamlit as st
from db import init_db
from services.auth_simple import load_cfg, try_login, current_user, current_role, logout

st.set_page_config(page_title="WRSafe – Werkvergunning", layout="wide")

# --- DB init (robuust) ---
init_db()

# --- Config / role ---
cfg = load_cfg()
role = st.session_state.get("role") or current_role(cfg)

# -----------------------
# Sidebar
# -----------------------
with st.sidebar:
    st.markdown("### Navigatie")
    # Altijd zichtbaar
    st.page_link("app.py", label="🏠 Start")
    st.page_link("pages/1_🎫_Nieuwe_Vergunning.py", label="🎫 Nieuwe vergunning")
    st.page_link("pages/3_🔁_Beoordeling_&_Uitvoering.py", label="🔁 Beoordeling & Uitvoering")
    st.page_link("pages/2_📋_Overzicht.py", label="📋 Overzicht")
    st.page_link("pages/4_📄_Rapportage.py", label="📄 Rapportage")

    # Alleen voor beheerders
    if (st.session_state.get("role") or "").lower() == "beheerder":
        st.markdown("---")
        st.markdown("**Beheer**")
        st.page_link("pages/A1_🗂️_Beheer_Betreft.py", label="🗂️ Betreft")                           # 5h
        st.page_link("pages/A2_🗂️_Beheer_Werkgebieden.py", label="🗂️ Werkgebieden")                 # 5i
        st.page_link("pages/A3_🗂️_Beheer_Werkwijzen.py", label="🗂️ Werkwijzen")                     # 5a
        st.page_link("pages/A4_🗂️_Beheer_Gereedschappen.py", label="🗂️ Gereedschappen")             # 5c

        st.page_link("pages/B1_🗂️_Beheer_Risicoklassen.py", label="🗂️ Risicoklassen")               # 5b
        st.page_link("pages/B2_🗂️_Beheer_Risico_Werk.py", label="🗂️ Risico's Werk")                 # 5d
        st.page_link("pages/B3_🗂️_Beheer_Risico_Omgeving.py", label="🗂️ Risico's Omgeving")
        st.page_link("pages/B4_🗂️_Beheer_Maatregelen.py", label="🗂️ Maatregelen")                   # 5z
        st.page_link("pages/B5_🗂️_Beheer_PBMs.py", label="🗂️ PBM's")                                # 5g

        st.page_link("pages/C1_🗂️_Beheer_Locaties.py", label="🗂️ Locaties")                         # 5k
        st.page_link("pages/C2_🗂️_Beheer_Afdelingen.py", label="🗂️ Afdelingen")                     # 5l
        st.page_link("pages/C3_🗂️_Beheer_Ruimten.py", label="🗂️ Ruimten")                           # 5m

        st.page_link("pages/C4_🗂️_Beheer_Verantwoordelijke_Rollen.py", label="🗂️ Verantwoordelijke Rollen")
        st.page_link("pages/C5_🗂️_Beheer_Gebiedseigenaren.py", label="🗂️ Gebiedseigenaren (Loc+Dept)")
        st.page_link("pages/C6_🗂️_Beheer_Systeemeigenaren.py", label="🗂️ Systeemeigenaren (Werkgebied+Asset)")

        #st.page_link("pages/D3_🗂️_Beheer_Werkwijze_Risico.py", label="🗂️ Werkwijze ↔ Risico's")     # 5e
        #st.page_link("pages/D4_🗂️_Beheer_RisicoWerk_→_Maatregelen.py", label="🗂️ Risico Werk → Maatregelen")           # 5f
        #st.page_link("pages/D5_🗂️_Beheer_RisicoOmgeving_→_Maatregelen.py", label="🗂️ Risico Omgeving → Maatregelen")   # 5f

    st.markdown("---")
    st.markdown("### Inloggen")
    user = current_user()
    if not user:
        # Form voorkomt “dubbel rerun”-gedrag en enter‑key issues
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("E‑mail", key="login_email")
            pw = st.text_input("Wachtwoord", type="password", key="login_pw")
            submitted = st.form_submit_button("Log in")
        if submitted:
            ok = try_login((email or "").strip(), pw or "", cfg)
            if ok:
                st.session_state["user"] = ok
                st.session_state["role"] = (cfg.get("roles") or {}).get(ok, "gebruiker")
                st.success("Ingelogd.")
                st.rerun()
            else:
                st.error("Onjuiste e‑mail of wachtwoord.")
    else:
        st.write(f"Ingelogd als **{user}** (rol: **{role}**)")

        if st.button("Logout"):
            logout()
            # schoon sessie‑sporen op
            for k in ("user", "role", "login_email", "login_pw"):
                st.session_state.pop(k, None)
            st.rerun()

st.title("WRSafe – Werkvergunning")
st.caption("Gebruik het menu links om een nieuwe vergunning aan te maken of bestaande te beheren.")
