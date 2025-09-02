# pages/B5_🗂️_Beheer_PBMs.py
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
st.set_page_config(page_title="Beheer – PBM’s", layout="wide")
render_nav()

with get_session() as s:
    roles = s.exec(select(ResponsibleRole).where(ResponsibleRole.active == True).order_by(ResponsibleRole.sort_order, ResponsibleRole.name)).all()
role_options = ["—"] + [r.name for r in roles]

column_order = ["name", "default_responsible", "default_required", "active", "id"]
column_config = {
    "id":                   st.column_config.NumberColumn("ID", width="small"),
    "name":                 st.column_config.TextColumn("PBM", required=True),
    "default_responsible":  st.column_config.SelectboxColumn("Default verantwoordelijke", options=role_options),
    "default_required":     st.column_config.CheckboxColumn("Default = verplicht"),
    "active":               st.column_config.CheckboxColumn("Actief", width="small"),
}

render_catalog_admin(
    Model=Measure,
    title="🗂️ Beheer – PBM’s",
    column_config=column_config,
    column_order=column_order,
    default_sort=[("name","asc")],
    filters={"scope": "PBM"},                 # alleen PBM’s tonen
    defaults_on_add={"scope": "PBM"},         # nieuwe items zijn altijd PBM
    page_size=20,
    allow_add=True,
    allow_delete=False,
    unique_field="name",
)
