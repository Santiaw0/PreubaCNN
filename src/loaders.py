# src/loaders.py
"""
loaders.py
──────────
Carga de TODOS los datos del proyecto.
Cada función usa @st.cache_data para no releer en cada interacción.
"""

import base64
import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from folium.features import CustomIcon

# ── Icono de CAI en base64 (se convierte una sola vez al importar) ────────────
with open("data/Imagenes/iconopolicamapa.png", "rb") as f:
    _IMG_BASE64 = "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")


# ── Geodatos ──────────────────────────────────────────────────────────────────
@st.cache_data
def load_all_geodata():
    """Carga y simplifica los shapefiles necesarios."""
    localidades = gpd.read_file("data/mapalocalidades/Loca.shp")
    localidades["geometry"] = localidades["geometry"].simplify(tolerance=0.001)

    CAIS = gpd.read_file("data/mapaCAI/ComandoAtencionInmediata.shp")

    return localidades, CAIS


# ── Encuestas ─────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_ecn() -> pd.DataFrame:
    """Carga la Encuesta de Clima de Negocios 2024."""
    return pd.read_excel(
        "data/Clima de Negocios 2024/"
        "Encuesta Clima de negocios 2024 final anonimizada.xlsx"
    )


@st.cache_data(show_spinner=False)
def load_epv() -> pd.DataFrame:
    """Carga la Encuesta de Percepción y Victimización 2024."""
    return pd.read_excel(
        "data/Percepcion y Victimizacion 2024/Base2024.xlsx"
    )


# ── Marcadores de CAI en el mapa ──────────────────────────────────────────────
def add_markers(row, m: folium.Map) -> None:
    """Añade un marcador de CAI al mapa Folium recibido."""
    icon = CustomIcon(_IMG_BASE64, icon_size=(27, 27), icon_anchor=(17, 17))

    popup_html = f"""
    <div style="font-family:Arial;width:250px;">
        <h4 style="color:darkblue;margin:0 0 8px 0;">🛡️ CAI {row['CAINOMBRE']}</h4>
        <hr style="margin:4px 0">
        <b>📍 Dirección:</b> {row['CAIDIR_SIT']}<br>
        <b>📞 Teléfono:</b>  {row['CAITELEFON']}<br>
        <b>🕐 Horario:</b>   {row['CAIHORARIO']}<br>
        <b>👤 Contacto:</b>  {row['CAICONTACT']}<br>
        <b>⚙️ Función:</b>   {row['CAIFUNCION']}<br>
        <b>📋 Estado:</b>    {row['CAIEST_PRO']}<br>
        <b>🔧 Servicios:</b> {str(row['CAISERVICI'])[:80]}...<br><br>
        <a href="{row['CAIPWEB']}" target="_blank" style="color:darkblue;">
            🌐 Ver en web oficial
        </a>
    </div>
    """
    folium.Marker(
        location=[row["CAILATITUD"], row["CAILONGITU"]],
        icon=icon,
        popup=folium.Popup(popup_html, max_width=280),
        tooltip=f"🛡️ CAI {row['CAINOMBRE']}",
    ).add_to(m)