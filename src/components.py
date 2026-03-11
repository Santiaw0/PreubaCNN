# src/components.py
import streamlit as st
import plotly.express as px
from streamlit_folium import st_folium
from src.loaders import add_markers
from src.analysis import GENEROS, ZONAS_LIST, predecir, COLORES

def render_inicio(localidades, CAIS):
    """Renderiza la sección de Inicio con métricas y mapa de comunidad."""
    st.header('Formulación de Proyectos')
    st.title("Proyecto CCB")
    st.success("Carga de datos exitosa")

    st.subheader('Visualización Geoespacial')
    n = localidades.explore(
        location=[4.629, -74.105],
        zoom_start=11.5,
        style_kwds={
            "fillOpacity": 0.3,
            "weight": 2,
            "color": "darkorange",
            "fillColor": "orange"
        },
        name="Localidades"
    )

    for _, row in CAIS.iterrows():
        add_markers(row, n)

    st_folium(n, use_container_width=True, height=500, returned_objects=[], key="mapa_localidades")  # ← esto faltaba

    st.divider()
    # Sección de selección de gráficos
    st.subheader('Análisis Estadístico')

    op = st.selectbox("Elija socio", ["Violencia", "genero", "localidad"])

    '''
    if op == "Violencia":
        fig = px.bar(filex.head(10), x="community", y="Pop2014", color="community", title="Distribución Violencia")
    elif op == "genero":
        fig = px.scatter(filex, x="Pop2014", y="Property_C", size="Property_C", color="community",
                         title="Relación Género")
    else:
        fig = px.bar(filex.head(10), x="community", y="Pop2014", color="community", title="Distribución Localidad")

    st.plotly_chart(fig, use_container_width=True, key="grafico_dinamico")
    '''

def render_analisis(localidades, CAIS):
    """Renderiza la sección de Localidades."""
    st.subheader('Visualización por Localidades')

    # ── Columnas del mapa ─────────────────────────────────────────────────

    n = localidades.explore(
            location=[4.629, -74.105],
            zoom_start=12,
            style_kwds={
                "fillOpacity": 0.3,
                "weight": 2,
                "color": "darkorange",
                "fillColor": "orange"
            },
            name="Localidades"
        )


    mapa_data = st_folium(n, use_container_width=True, height=500, key="mapa_localidades")


    # Capturar localidad seleccionada
    localidad_seleccionada = None

    if mapa_data and mapa_data.get("last_active_drawing"):
        props = mapa_data["last_active_drawing"].get("properties", {})
        localidad_seleccionada = props.get("LocCodigo")  # ← ajusta al nombre de tu columna


    # Mostrar gráficos si hay selección
    if localidad_seleccionada:
        st.subheader(f"📊 Análisis Localidad No: {localidad_seleccionada}")

        # Filtrar CAIS de esa localidad
        cais_filtrados = CAIS[CAIS['CAIIULOCAL'] == localidad_seleccionada]

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
    st.subheader('Análisis Estadístico')

    # ── Columnas de las opciones (independientes del mapa) ────────────────
    col3, col4 = st.columns(2)

    with col3:
        genero = st.selectbox("Selecciona tu género", GENEROS)

    with col4:
        zona = st.selectbox("¿Dónde vas?", ZONAS_LIST)


    hora = st.slider("Hora del día", 0, 23, 14, format="%d:00 h")

    if st.button("Evaluar peligrosidad", use_container_width=True, type="primary"):
        resultado = predecir(zona, genero, hora)

        nivel = resultado["nivel"]
        score = resultado["score"]
        confianza = resultado["confianza"]

        emoji, color, consejo = COLORES[nivel]
        # ── Resultado visual ──────────────────────────────────────────────────
        st.markdown(f"""
            <div style="
                background:{color}22; border:2px solid {color};
                border-radius:12px; padding:20px; text-align:center;
            ">
                <h1 style="color:{color}; margin:0">{emoji} Nivel: {nivel}</h1>
                <h2 style="margin:4px 0">Puntuación de riesgo: {score}/100</h2>
                <p style="color:{color}; margin:0">Confianza del modelo: {confianza}%</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"**📍 Zona:** {zona}  \n**🕐 Hora:** {hora:02d}:00  \n**👤 Género:** {genero}")




def render_final(filex):
    """Renderiza la sección de Inicio con métricas y mapa de comunidad."""
    st.header('Formulación de Proyectos')
    st.title("Proyecto CCB")
    st.success("Carga de datos exitosa")

    st.subheader('Visualización Geoespacial')
    with st.expander("Ver detalles del modelo y mapa", expanded=True):
        col1, col2 = st.columns([1, 3])

        with col1:
            st.write("**Métricas Principales**")
            st.metric("Total Áreas", len(filex))
            st.metric("Población Total", f"{filex['Pop2014'].sum():,}")
            st.write("---")

        with col2:
            # Generar mapa optimizado
            filex_map = filex[['community', 'Pop2014', 'Property_C', 'geometry']]
            m = filex_map.explore(column="Property_C", cmap="magma")
            st_folium(m, use_container_width=True, height=500, key="mapa_inicio")

    st.divider()
    # Sección de selección de gráficos
    st.subheader('Análisis Estadístico')
    op = st.selectbox("Elija socio", ["Violencia", "genero", "localidad"])

    if op == "Violencia":
        fig = px.bar(filex.head(10), x="community", y="Pop2014", color="community", title="Distribución Violencia")
    elif op == "genero":
        fig = px.scatter(filex, x="Pop2014", y="Property_C", size="Property_C", color="community",
                         title="Relación Género")
    else:
        fig = px.bar(filex.head(10), x="community", y="Pop2014", color="community", title="Distribución Localidad")

    st.plotly_chart(fig, use_container_width=True, key="grafico_dinamico")

