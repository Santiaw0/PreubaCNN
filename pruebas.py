import streamlit as st
from streamlit_option_menu import option_menu

# Importamos nuestras funciones personalizadas
from src.loaders import load_all_geodata
from src.components import render_inicio, render_final, render_analisis


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
    render_final(filex)