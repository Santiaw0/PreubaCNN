import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
from seccion_seguridad import render_seccion_seguridad
from src.loaders import load_all_geodata          # ← esta
from src.components import render_inicio, render_analisis, render_final  # ← esta


# 1. CONFIGURACIÓN
st.set_page_config(page_title="Proyecto CCB", page_icon="🌳", layout="wide")

# 2. CARGA DE DATOS (Se ejecuta una sola vez gracias al cache)
filex, localidades, barrios, CAIS = load_all_geodata()

# 3. SIDEBAR
with st.sidebar:
    #Logo Universidad
    st.image("data/Imagenes/logobar.png", width=150)

    #Menu y opciones
    selected = option_menu(
        menu_title="Proyecto Arbolitos",
        options=["CAIS", "Mapa Localidades", "Analisis"],
        icons=["home", "map", "graph-up"],
        default_index=0,
        styles={"nav-link-selected": {"background-color": "#559C40"}}
    )

    st.markdown("# Descripción\n"
                ""
                "### Participantes \n"
                "drodriguezpr@unbosque.edu.co \n"
                "afigueroafi@unbosque.edu.co \n"
                "tvalderramam@unbosque.edu.co\n"
                "### Tutor \n"
                "atrillerasm@unbosque.edu.co\n"
                )

# 4. NAVEGACIÓN
if selected == "CAIS":
    render_inicio(localidades, CAIS)

elif selected == "Mapa Localidades":
    render_analisis(localidades, CAIS)

elif selected == "Analisis":
    df_raw = pd.read_excel("data/Clima de Negocios 2024/Encuesta Clima de negocios 2024 final anonimizada.xlsx")

    #render_final(filex)
    render_seccion_seguridad(df_raw)