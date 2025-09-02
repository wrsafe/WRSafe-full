import streamlit as st
import yaml
from pathlib import Path
import streamlit_authenticator as stauth
import inspect

st.set_page_config(page_title="Auth Test", layout="centered")

cfg = {}
p = Path("config/auth.yaml")
if not p.exists():
    st.error("config/auth.yaml niet gevonden"); st.stop()
with p.open("r", encoding="utf-8") as f:
    cfg = yaml.safe_load(f) or {}

creds = cfg.get("credentials", {})
cookie = cfg.get("cookie", {}) or {}
cookie_name = cookie.get("name", "wrsafe_auth")
cookie_key  = cookie.get("key",  "RANDOM_KEY")
cookie_days = cookie.get("expiry_days", 30)

st.write("Gebruikers:", list((creds.get("usernames") or {}).keys()))

auth = stauth.Authenticate(
    creds,
    cookie_name,
    cookie_key,
    cookie_days,
)

# Compatibele login-aanroep (werkt met oud én nieuw)
try:
    sig = inspect.signature(auth.login)
    if "fields" in sig.parameters:
        fields = {"Form name": "Login", "Username": "E-mail", "Password": "Wachtwoord"}
        name, auth_status, username = auth.login(fields=fields, location="main")
    else:
        name, auth_status, username = auth.login("Login", "main")
except TypeError:
    fields = {"Form name": "Login", "Username": "E-mail", "Password": "Wachtwoord"}
    name, auth_status, username = auth.login(fields=fields, location="main")

if auth_status:
    st.success(f"Ingelogd als: {username}")
    auth.logout("Logout", "main")
elif auth_status is False:
    st.error("Onjuiste gebruikersnaam of wachtwoord.")
else:
    st.info("Vul je e-mail en wachtwoord in om in te loggen.")
