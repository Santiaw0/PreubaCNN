# src/loaders.py
import streamlit as st
import folium  # ← faltaba este import
import base64
import geopandas as gpd
from folium.features import CustomIcon

# Convertir imagen a base64 una sola vez
with open("data/Imagenes/iconopolicamapa.png", "rb") as f:
    IMG_BASE64 = "data:image/png;base64," + base64.b64encode(f.read()).decode("utf-8")

@st.cache_data
def load_all_geodata():
    filex = gpd.read_file("data/mapaejemplo/ComArea_ACS14_f.shp")
    filex['geometry'] = filex['geometry'].simplify(tolerance=0.001)

    localidades = gpd.read_file("data/mapalocalidades/Loca.shp")
    localidades['geometry'] = localidades['geometry'].simplify(tolerance=0.001)

    barrios = gpd.read_file("data/mapabogotabarrios/SECTOR.shp")
    barrios['geometry'] = barrios['geometry'].simplify(tolerance=0.0001)

    CAIS = gpd.read_file("data/mapaCAI/ComandoAtencionInmediata.shp")  # ← archivo correcto

    return filex, localidades, barrios, CAIS  # ← devolver CAIS separado de barrios


def add_markers(row, m):
    iconx = CustomIcon(IMG_BASE64, icon_size=(35, 35), icon_anchor=(17, 17))  # ← base64

    popup_html = f"""
    <div style="font-family: Arial; width: 250px;">
        <h4 style="color: darkblue; margin: 0 0 8px 0;">🛡️ CAI {row['CAINOMBRE']}</h4>
        <hr style="margin: 4px 0">
        <b>📍 Dirección:</b> {row['CAIDIR_SIT']}<br>
        <b>📞 Teléfono:</b> {row['CAITELEFON']}<br>
        <b>🕐 Horario:</b> {row['CAIHORARIO']}<br>
        <b>👤 Contacto:</b> {row['CAICONTACT']}<br>
        <b>⚙️ Función:</b> {row['CAIFUNCION']}<br>
        <b>📋 Estado:</b> {row['CAIEST_PRO']}<br>
        <b>🔧 Servicios:</b> {str(row['CAISERVICI'])[:80]}...<br><br>
        <a href="{row['CAIPWEB']}" target="_blank" style="color: darkblue;">🌐 Ver en web oficial</a>
    </div>
    """
    folium.Marker(
        location=[row['CAILATITUD'], row['CAILONGITU']],
        icon=iconx,
        popup=folium.Popup(popup_html, max_width=280),
        tooltip=f"🛡️ CAI {row['CAINOMBRE']}"
    ).add_to(m)