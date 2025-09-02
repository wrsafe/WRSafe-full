# pages/A2_🗂️_Beheer_Werkgebieden.py
import streamlit as st
from services.nav import render_nav
from services.ui_admin import render_catalog_admin
from services.auth_simple import load_cfg, require_role
from db import init_db
from models import WorkArea

st.set_page_config(page_title="Beheer – Werkgebieden", layout="wide")
init_db(); render_nav()
cfg = load_cfg(); require_role(cfg, {"beheerder"})

columns = [
    {"key": "name",       "label": "Naam"},
    {"key": "active",     "label": "Actief"},
    {"key": "sort_order", "label": "Volgorde"},
    {"key": "id",         "label": "ID"},
]
column_config = {
    "id":         st.column_config.NumberColumn("ID", width="small", help="Uniek ID"),
    "sort_order": st.column_config.NumberColumn("Volgorde", width="small", help="Sorteer-/weergavevolgorde"),
    "active":     st.column_config.CheckboxColumn("Actief", width="small"),
    "name":       st.column_config.TextColumn("Naam"),
}
try:
    render_catalog_admin(
        Model=WorkArea,
        title="🗂️ Beheer – Werkgebieden",
        page_size=20,
        columns=columns,
        column_config=column_config,
        default_sort=[("sort_order", "asc"), ("name", "asc")],
    )
except TypeError:
    render_catalog_admin(Model=WorkArea, title="🗂️ Beheer – Werkgebieden", page_size=20)
