# services/authz.py
import streamlit as st

DEFAULT_ROLE = "gebruiker"

def current_role() -> str:
    # Als je streamlit-authenticator gebruikt, zet je in app.py na login:
    # st.session_state["role"] = cfg.get("roles", {}).get(username, "gebruiker")
    return st.session_state.get("role", DEFAULT_ROLE)

def require_role(allowed: set[str], message: str = "Je hebt geen toegang tot deze pagina."):
    role = current_role()
    if role not in allowed:
        st.error(message)
        st.stop()
