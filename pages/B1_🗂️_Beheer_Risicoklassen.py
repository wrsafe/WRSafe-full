# pages/B1_🗂️_Beheer_Risicoklassen.py
import streamlit as st
from services.auth_simple import load_cfg, require_role
from services.nav import render_nav
from services.ui_admin import render_catalog_admin
from db import init_db
from models import RiskClass

init_db()
cfg = load_cfg()
require_role(cfg, {"beheerder"})
st.set_page_config(page_title="Beheer – Risicoklassen", layout="wide")
render_nav()

column_order = ["name", "active", "sort_order", "id"]
column_config = {
    "id":         st.column_config.NumberColumn("ID", width="small", help="Uniek ID"),
    "name":       st.column_config.TextColumn("Naam", required=True),
    "sort_order": st.column_config.NumberColumn("Volgorde", min_value=0, step=1, format="%d", width="small"),
    "active":     st.column_config.CheckboxColumn("Actief", width="small"),
}

render_catalog_admin(
    Model=RiskClass,
    title="🛠️ Beheer – Risicoklassen",
    column_config=column_config,
    column_order=column_order,
    default_sort=[("sort_order","asc"), ("name","asc")],
    page_size=20,
    allow_add=True,
    allow_delete=False,
    unique_field="name",
)
