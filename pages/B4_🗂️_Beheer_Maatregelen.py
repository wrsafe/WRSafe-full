# pages/B4_🗂️_Beheer_Maatregelen.py
import streamlit as st
from sqlmodel import select
from services.auth_simple import load_cfg, require_role
from services.nav import render_nav
from services.ui_admin import render_catalog_admin
from db import init_db, get_session
from models import Measure, ResponsibleRole

init_db()
cfg = load_cfg()
require_role(cfg, {"beheerder"})
st.set_page_config(page_title="Beheer – Maatregelen", layout="wide")
render_nav()

# Snelle scope-filter bovenin (optioneel)
scope_filter = st.segmented_control("Filter op scope", options=["Alle", "Werk", "Omgeving", "PBM"], default="Alle")

# Opties voor default verantwoordelijke
with get_session() as s:
    roles = s.exec(select(ResponsibleRole).where(ResponsibleRole.active == True).order_by(ResponsibleRole.sort_order, ResponsibleRole.name)).all()
role_options = ["—"] + [r.name for r in roles]

column_order = ["name", "scope", "default_responsible", "default_required", "active", "id"]
column_config = {
    "id":                   st.column_config.NumberColumn("ID", width="small", help="Uniek ID"),
    "name":                 st.column_config.TextColumn("Naam", required=True),
    "scope":                st.column_config.SelectboxColumn("Scope", options=["Werk", "Omgeving"]),
    "default_responsible":  st.column_config.SelectboxColumn("Default verantwoordelijke", options=role_options),
    "default_required":     st.column_config.CheckboxColumn("Default = verplicht"),
    "active":               st.column_config.CheckboxColumn("Actief", width="small"),
}

filters = None if scope_filter == "Alle" else {"scope": scope_filter}

render_catalog_admin(
    Model=Measure,
    title="🛠️ Beheer – Maatregelen",
    column_config=column_config,
    column_order=column_order,
    default_sort=[("scope","asc"), ("name","asc")],
    filters=filters,
    page_size=20,
    allow_add=True,
    allow_delete=False,
    unique_field="name",
)
