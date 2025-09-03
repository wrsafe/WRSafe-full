# services/auth_simple.py
from __future__ import annotations
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from werkzeug.security import check_password_hash
import streamlit as st

AUTH_PATH = "config/auth.yaml"

# services/auth_simple.py
import yaml, streamlit as st
from pathlib import Path

def load_cfg():
    """
    Leest auth-config uit:
    1) st.secrets['auth']['yaml']  (Cloud voorkeursplek)
    2) st.secrets['auth_yaml']     (fallback)
    3) lokaal bestand config/auth.yaml (lokaal ontwikkelen)
    """
    # 1) Cloud (voorkeur)
    raw = st.secrets.get("auth", {}).get("yaml")
    if not raw:
        # 2) fallback
        raw = st.secrets.get("auth_yaml")
    if raw:
        return yaml.safe_load(raw)

    # 3) lokaal bestand als fallback
    p = Path("config/auth.yaml")
    if p.exists():
        return yaml.safe_load(p.read_text(encoding="utf-8"))

    raise RuntimeError("Geen auth-config gevonden in Secrets of config/auth.yaml")

def try_login(email: str, password: str, cfg: Dict[str, Any]) -> Optional[str]:
    """Valideer login op basis van auth.yaml (zelfde schema als streamlit-authenticator)."""
    email = (email or "").strip()
    if not email or not password:
        return None

    users = ((cfg.get("credentials") or {}).get("usernames") or {})
    u = users.get(email)
    if not isinstance(u, dict):
        return None

    pw_hash = u.get("password")
    # Eenvoudige sanity-check op werkzeug hash formaat "method$salt$hash"
    if not (isinstance(pw_hash, str) and pw_hash.count("$") >= 2):
        return None

    return email if check_password_hash(pw_hash, password) else None

def current_user() -> Optional[str]:
    return st.session_state.get("user")

def current_role(cfg: Dict[str, Any]) -> str:
    user = current_user()
    return (cfg.get("roles") or {}).get(user, "gebruiker") if user else "gebruiker"

def require_role(cfg: Dict[str, Any], allowed: set[str]):
    role = current_role(cfg)
    if role not in allowed:
        st.error("Je hebt geen toegang tot deze pagina.")
        st.stop()

def logout():
    # Schoon alle auth-gerelateerde keys op
    for k in ("user", "role", "login_email", "login_pw"):
        st.session_state.pop(k, None)
