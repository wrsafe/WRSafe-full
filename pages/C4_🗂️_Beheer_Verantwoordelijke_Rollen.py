# pages/C4_🗂️_Beheer_Verantwoordelijke_Rollen.py
import streamlit as st
from services.auth_simple import load_cfg, require_role
from services.ui_admin import render_catalog_admin
from services.nav import render_nav
from db import init_db
from models import ResponsibleRole

init_db()
cfg = load_cfg()
require_role(cfg, {"beheerder"})
st.set_page_config(page_title="Beheer – Verantwoordelijke Rollen", layout="wide")
render_nav()

# Kolomdefinities
column_order = ["name", "applies_to", "active", "sort_order", "id"]
column_config = {
    "id":         st.column_config.NumberColumn("ID", width="small", help="Uniek ID"),
    "name":       st.column_config.TextColumn("Naam", required=True),
    "applies_to": st.column_config.SelectboxColumn(
        "Toepassing", options=["Beide", "Werk", "Omgeving"], help="Waarop deze rol van toepassing is"
    ),
    "sort_order": st.column_config.NumberColumn("Volgorde", min_value=0, step=1, format="%d", width="small"),
    "active":     st.column_config.CheckboxColumn("Actief", width="small"),
}

render_catalog_admin(
    Model=ResponsibleRole,
    title="🛠️ Beheer – Verantwoordelijke Rollen",
    column_config=column_config,
    column_order=column_order,
    default_sort=[("sort_order","asc"), ("name","asc")],
    page_size=20,
    allow_add=True,
    allow_delete=False,
    unique_field="name",
)
