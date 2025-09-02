# services/nav.py
import streamlit as st
from services.auth_simple import load_cfg, current_role

def render_nav():
    """Toon de navigatie in de sidebar (op elke pagina aanroepen)."""
    cfg = load_cfg()
    role = current_role(cfg)

    with st.sidebar:
        st.markdown("### Navigatie")

        # Altijd zichtbaar
        st.page_link("app.py", label="🏠 Start")
        st.page_link("pages/1_🎫_Nieuwe_Vergunning.py", label="🎫 Nieuwe vergunning")
        st.page_link("pages/3_🔁_Beoordeling_&_Uitvoering.py", label="🔁 Beoordeling & Uitvoering")
        st.page_link("pages/2_📋_Overzicht.py", label="📋 Overzicht")
        st.page_link("pages/4_📄_Rapportage.py", label="📄 Rapportage")

        # Alleen voor beheerders
        if (role or "").lower() == "beheerder":
            st.markdown("---")
            st.markdown("**Beheer**")
            st.page_link("pages/A1_🗂️_Beheer_Betreft.py", label="🗂️ Betreft")                           # 5h
            st.page_link("pages/A2_🗂️_Beheer_Werkgebieden.py", label="🗂️ Werkgebieden")                 # 5i
            st.page_link("pages/A3_🗂️_Beheer_Werkwijzen.py", label="🗂️ Werkwijzen")                     # 5a
            st.page_link("pages/A4_🗂️_Beheer_Gereedschappen.py", label="🗂️ Gereedschappen")             # 5c

            st.page_link("pages/B1_🗂️_Beheer_Risicoklassen.py", label="🗂️ Risicoklassen")               # 5b
            st.page_link("pages/B2_🗂️_Beheer_Risico_Werk.py", label="🗂️ Risico's Werk")                 # 5d
            st.page_link("pages/B3_🗂️_Beheer_Risico_Omgeving.py", label="🗂️ Risico's Omgeving")
            st.page_link("pages/B4_🗂️_Beheer_Maatregelen.py", label="🗂️ Maatregelen")                   # 5z
            st.page_link("pages/B5_🗂️_Beheer_PBMs.py", label="🗂️ PBM's")                                # 5g

            st.page_link("pages/C1_🗂️_Beheer_Locaties.py", label="🗂️ Locaties")                         # 5k
            st.page_link("pages/C2_🗂️_Beheer_Afdelingen.py", label="🗂️ Afdelingen")                     # 5l
            st.page_link("pages/C3_🗂️_Beheer_Ruimten.py", label="🗂️ Ruimten")                           # 5m

            st.page_link("pages/C4_🗂️_Beheer_Verantwoordelijke_Rollen.py", label="🗂️ Verantwoordelijke Rollen")
            st.page_link("pages/C5_🗂️_Beheer_Gebiedseigenaren.py", label="🗂️ Gebiedseigenaren (Loc+Dept)")
            st.page_link("pages/C6_🗂️_Beheer_Systeemeigenaren.py", label="🗂️ Systeemeigenaren (Werkgebied+Asset)")

            #st.page_link("pages/D3_🗂️_Beheer_Werkwijze_Risico.py", label="🗂️ Werkwijze ↔ Risico's")     # 5e
            #st.page_link("pages/D4_🗂️_Beheer_RisicoWerk_→_Maatregelen.py", label="🗂️ Risico Werk → Maatregelen")           # 5f
            #st.page_link("pages/D5_🗂️_Beheer_RisicoOmgeving_→_Maatregelen.py", label="🗂️ Risico Omgeving → Maatregelen")   # 5f
