# src/components.py
import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_folium import st_folium
from src.loaders import add_markers
from src.analysis import GENEROS, ZONAS_LIST, predecir, COLORES
from seccion_seguridad import render_seccion_seguridad   # ← módulo ECN 2024


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 1 — INICIO / CAIS
# ─────────────────────────────────────────────────────────────────────────────
def render_inicio(localidades, CAIS):
    """Renderiza la sección de Inicio con métricas y mapa de comunidad."""
    st.header("Formulación de Proyectos")
    st.title("Proyecto CCB")
    st.success("Carga de datos exitosa")

    st.subheader("Visualización Geoespacial")
    n = localidades.explore(
        location=[4.629, -74.105],
        zoom_start=11.5,
        style_kwds={
            "fillOpacity": 0.3,
            "weight": 2,
            "color": "darkorange",
            "fillColor": "orange",
        },
        name="Localidades",
    )

    for _, row in CAIS.iterrows():
        add_markers(row, n)

    st_folium(
        n,
        use_container_width=True,
        height=500,
        returned_objects=[],
        key="mapa_localidades",
    )

    st.divider()
    st.subheader("Análisis Estadístico")
    op = st.selectbox("Elija socio", ["Violencia", "genero", "localidad"])
    # (gráficos comentados en el original — se mantienen igual)


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 2 — MAPA LOCALIDADES
# ─────────────────────────────────────────────────────────────────────────────
def render_analisis(localidades, CAIS):
    """Renderiza la sección de Localidades."""
    st.subheader("Visualización por Localidades")

    n = localidades.explore(
        location=[4.629, -74.105],
        zoom_start=12,
        style_kwds={
            "fillOpacity": 0.3,
            "weight": 2,
            "color": "darkorange",
            "fillColor": "orange",
        },
        name="Localidades",
    )

    mapa_data = st_folium(
        n,
        use_container_width=True,
        height=500,
        key="mapa_localidades_analisis",
    )

    # Capturar localidad seleccionada
    localidad_seleccionada = None
    if mapa_data and mapa_data.get("last_active_drawing"):
        props = mapa_data["last_active_drawing"].get("properties", {})
        localidad_seleccionada = props.get("LocCodigo")

    if localidad_seleccionada:
        st.subheader(f"📊 Análisis Localidad No: {localidad_seleccionada}")
        cais_filtrados = CAIS[CAIS["CAIIULOCAL"] == localidad_seleccionada]

        col3, col4 = st.columns(2)
        with col3:
            st.metric("CAIs en la zona", len(cais_filtrados))
            fig = px.bar(cais_filtrados, x="CAINOMBRE", y="CAIEST_PRO", title="Estado de CAIs")
            st.plotly_chart(fig, use_container_width=True)
        with col4:
            fig2 = px.pie(cais_filtrados, names="CAIFUNCION", title="Funciones")
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("👆 Haz clic en una localidad para ver su análisis")

    st.divider()
    st.subheader("Análisis Estadístico")

    col3, col4 = st.columns(2)
    with col3:
        genero = st.selectbox("Selecciona tu género", GENEROS)
    with col4:
        zona = st.selectbox("¿Dónde vas?", ZONAS_LIST)

    hora = st.slider("Hora del día", 0, 23, 14, format="%d:00 h")

    if st.button("Evaluar peligrosidad", use_container_width=True, type="primary"):
        resultado  = predecir(zona, genero, hora)
        nivel      = resultado["nivel"]
        score      = resultado["score"]
        confianza  = resultado["confianza"]
        emoji, color, consejo = COLORES[nivel]

        st.markdown(
            f"""
            <div style="
                background:{color}22; border:2px solid {color};
                border-radius:12px; padding:20px; text-align:center;
            ">
                <h1 style="color:{color}; margin:0">{emoji} Nivel: {nivel}</h1>
                <h2 style="margin:4px 0">Puntuación de riesgo: {score}/100</h2>
                <p style="color:{color}; margin:0">Confianza del modelo: {confianza}%</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            f"**📍 Zona:** {zona}  \n**🕐 Hora:** {hora:02d}:00  \n**👤 Género:** {genero}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# SECCIÓN 3 — ANÁLISIS / SEGURIDAD EMPRESARIAL (ECN 2024)
# ─────────────────────────────────────────────────────────────────────────────

# Ruta al Excel de la encuesta — ajusta si cambia la ubicación
_RUTA_ECN = "data/Encuesta Clima de negocios 2024 final anonimizada.xlsx"


@st.cache_data(show_spinner=False)
def _cargar_ecn(ruta: str) -> pd.DataFrame:
    """Carga el Excel ECN una sola vez y lo guarda en caché."""
    return pd.read_excel(ruta)


def render_final(filex):
    """
    Sección 'Análisis' del menú principal.
    Muestra los 7 gráficos de Seguridad Empresarial ECN 2024.
    """

    # ── Intentar cargar el Excel de forma automática ──────────────────────
    df_raw = None

    try:
        df_raw = _cargar_ecn(_RUTA_ECN)
    except FileNotFoundError:
        # Si no está en la ruta por defecto, pedirle al usuario que lo suba
        st.warning(
            "⚠️ No se encontró el archivo de la ECN 2024 en la ruta configurada.\n\n"
            f"`{_RUTA_ECN}`\n\n"
            "Sube el Excel manualmente para continuar.",
        )
        uploaded = st.file_uploader(
            "📂 Cargar Excel ECN 2024",
            type=["xlsx"],
            key="uploader_ecn",
        )
        if uploaded:
            df_raw = pd.read_excel(uploaded)
        else:
            st.stop()   # Detiene el render hasta que haya datos

    # ── Renderizar los 7 gráficos de seguridad ────────────────────────────
    render_seccion_seguridad(df_raw)