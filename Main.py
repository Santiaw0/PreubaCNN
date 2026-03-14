"""
main.py
───────
Punto de entrada de la app CANOPY.
Solo configura Streamlit, carga datos y enruta a cada sección.
"""

import streamlit as st
from streamlit_option_menu import option_menu

from src.loaders import load_all_geodata
from src.components import (
    render_servicio_ayuda,
    render_riesgo_local,
    render_analisis,
    render_bacano,
)

# ── 1. Configuración ──────────────────────────────────────────────────────────
st.set_page_config(page_title="CANOPY", page_icon="🌳", layout="wide")

# ── 2. Carga de geodatos (una sola vez gracias al caché) ──────────────────────
localidades, CAIS = load_all_geodata()

# ── 3. Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("data/Imagenes/logoCanipypng.png", width=550)

    selected = option_menu(
        menu_title="Random Forest",
        options=["Servicio de Ayuda", "Riesgo Local", "Análisis", "BACANO"],
        icons=["house-heart", "map", "graph-up", "stars"],
        default_index=0,
        styles={"nav-link-selected": {"background-color": "#559C40"}},
    )

    st.markdown(
        "### Participantes \n"
        "drodriguezpr@unbosque.edu.co \n"
        "afigueroafi@unbosque.edu.co \n"
        "tvalderramam@unbosque.edu.co\n"
        "### Tutor \n"
        "atrillerasm@unbosque.edu.co"
    )
    st.image("data/Imagenes/logobar.png", width=150)


# ── 4. Navegación ─────────────────────────────────────────────────────────────
if selected == "Servicio de Ayuda":
    render_servicio_ayuda(localidades, CAIS)

elif selected == "Riesgo Local":
    render_riesgo_local(localidades, CAIS)

elif selected == "Análisis":
    render_analisis()

elif selected == "BACANO":
    render_bacano()