import streamlit as st
from db import engine, init_db
from services.nav import render_nav

# --- Setup ---
init_db()
st.set_page_config(page_title="Rapportage - PDF export", layout="wide")
st.header('📄 Rapportage - PDf export')
render_nav()
