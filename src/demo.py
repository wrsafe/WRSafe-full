import streamlit as st
def is_demo(): return bool(st.secrets.get("demo", {}).get("ephemeral_copy"))
def disabled(feature: str): return bool(st.secrets.get("demo", {}).get(feature, False))
