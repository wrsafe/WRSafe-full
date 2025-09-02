# services/auth.py
from __future__ import annotations

import yaml
from pathlib import Path
from typing import Any, Dict, Tuple, Optional

def load_auth(path: str = "config/auth.yaml") -> Dict[str, Any]:
    """
    Laadt je auth-config (users, cookies, roles) uit YAML.
    Bestaat het bestand niet? Dan retour {}.
    """
    p = Path(path)
    if not p.exists():
        return {}
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def setup_authenticator(cfg: Dict[str, Any]):
    """
    Maakt (optioneel) een streamlit-authenticator Authenticate object.
    Als cfg leeg is, returnt (None, cfg).
    """
    try:
        import streamlit_authenticator as stauth
    except Exception:
        # Auth lib niet geïnstalleerd → geen authenticator
        return None, cfg

    if not cfg:
        return None, cfg

    creds = cfg.get("credentials", {})
    cookie = cfg.get("cookie", {}) or {}
    name  = cookie.get("name", "wrsafe_auth")
    key   = cookie.get("key",  "RANDOM_KEY_CHANGE_ME")
    days  = cookie.get("expiry_days", 30)

    try:
        authenticator = stauth.Authenticate(
            creds,
            name,
            key,
            days,
        )
        return authenticator, cfg
    except Exception:
        # Fallback: als config niet klopt, draai zonder auth
        return None, cfg
