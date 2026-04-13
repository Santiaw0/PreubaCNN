# src/components.py

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

from src.loaders import load_ecn, load_epv, load_siedcore, add_markers
from src.preprocesamiento import preparar_ecn, preparar_epv, preparar_siedcore, LABELS_LOCALIDAD, LOC_NOMBRE_A_COD
from src.graficos import (
    # ECN
    kpis_ecn, barras_sector, barras_tamano, barras_delitos_ecn,
    pie_percepcion_ecn, barras_medidas,
    # EPV
    kpis_epv, delitos_empresariales_epv, percepcion_barrio_ciudad,
    # Riesgo local
    detalle_localidad,
    percepcion_ciudad, denuncia_y_satisfaccion, bacano_dashboard, kpis_siedcore,

#SIEDCORE
kpis_siedcore, barras_hechos_siedcore, barras_localidad_siedcore,
       linea_tendencia_siedcore, barras_sexo_siedcore,
      barras_rango_dia_siedcore, barras_rango_vital_siedcore, barras_arma_siedcore,
)

# ═════════════════════════════════════════════════════════════════════════════
# PÁGINA 1 — Servicio de Ayuda
# ═════════════════════════════════════════════════════════════════════════════
def render_servicio_ayuda(localidades, CAIS):
    st.title("Servicio de Ayuda")
    st.subheader("Visualización de CAI's en Bogotá")
    st.markdown("""
    Encuentra los CAIs más cercanos a tu ubicación y accede a líneas de atención 
    de emergencia. Usa el mapa para identificar puntos de apoyo policial en cada 
    localidad de Bogotá.
    """)

    m = localidades.explore(
        location=[4.629, -74.105], zoom_start=11.5,
        style_kwds={"fillOpacity":0.3,"weight":2,
                    "color":"#6B5855","fillColor":"darkgray"},
        name="Localidades",
    )
    for _, row in CAIS.iterrows():
        add_markers(row, m)

    st_folium(m, use_container_width=True, height=500,
              returned_objects=[], key="mapa_ayuda")

    st.divider()
    st.header("🟣 Línea Púrpura")
    st.caption(
        "Servicio de atención gratuito **24 horas**, dirigido a mujeres mayores de 18 años "
        "víctimas de violencia física, verbal o psicológica, o en riesgo de feminicidio."
    )
    col1, col2 = st.columns(2)
    col1.markdown(" ##### 📞 Teléfono \n ## **018000112137**")
    col2.markdown(" ##### 💬 WhatsApp \n ## **300 755 1846**")
    st.markdown("#### 📧 Correo: **lpurpura@sdmujer.gov.co**")

    st.divider()

    st.header("¿Te encuentras en peligro?")

    # 1. Definir la base de datos de guías (puedes expandirla)
    guias = [
        "Hurto",
        "Acoso / Amenazas",
        "Extorsión",
        "Delito Sexual"]

    # 2. Selector de delitos
    opcion = st.selectbox(
        "En que situación te encuentas?",
        list(guias)
    )

    # 3. Mostrar la guía según la selección
    if opcion == "Hurto":
        # Usamos un expander para mantener la interfaz limpia
        st.subheader("Guía de acción en caso de hurto")
        st.markdown("### Pasos a seguir:")

        st.markdown("""
            1.  **Mantén la calma:** Prioriza siempre tu integridad física.
            2.  **Contacta a la autoridad:** Llama de inmediato a la **línea de emergencia 123** para reportar el incidente a la Policía Nacional.
            3.  **Documenta el suceso:** Registra la hora, ubicación exacta y datos de posibles testigos.
            4.  **Denuncia formal:** Dirígete a la **Fiscalía General de la Nación** para presentar la denuncia (verbal o escrita).
            5.  **Seguros:** Contacta a tu aseguradora lo antes posible.
            """)

            # Un aviso para resaltar la importancia del tiempo
        st.warning(
                "⚠️ **Nota importante:** Revisa tu póliza de seguro, ya que suelen tener tiempos límites para presentar reclamaciones. ¡Actúa sin demora!")
    if opcion == "Acoso / Amenazas":
        st.subheader("Guía para Acoso o Amenazas")
        st.markdown("""
        * **Prioriza tu seguridad:** Sal de la zona donde te encuentras si te sientes en riesgo.
        * **Registra evidencia:** Guarda capturas de pantalla, audios o fotos si es digital.
        * **Línea Púrpura (Bogotá):** Llama al **01 8000 112 137** o escribe al **WhatsApp 300 755 1846**.
        * **Denuncia:** Acude a la URI de la Fiscalía más cercana.
        """)
        st.warning("Si estás en peligro inminente, llama al 123.")

    elif opcion == "Extorsión":
        st.subheader("Guía para Extorsión")
        st.markdown("""
        * **¡No pagues!** El pago no garantiza que los delincuentes paren; al contrario, te marca como víctima recurrente.
        * **Cuelga de inmediato:** No entres en diálogo.
        * **Bloquea:** Bloquea el número y no respondas llamadas de desconocidos.
        * **Línea GAULA:** Llama al **165**. Ellos son los expertos en este tipo de delitos.
        * **Recopila:** Guarda números, cuentas bancarias o nombres que hayan utilizado.
        """)

    elif opcion == "Delito Sexual":
        st.subheader("Guía para Delito Sexual")
        st.markdown("""
        * **Busca un lugar seguro:** Busca ayuda con alguien de confianza o en un lugar público.
        * **Atención médica:** Es prioritario ir a una urgencia hospitalaria para atención física y profilaxis.
        * **Línea 155:** Orientación a mujeres víctimas de violencia (funciona 24/7).
        * **No te culpes:** No estás sola/o. La prioridad es tu salud mental y física.
        * **Denuncia:** La denuncia es vital para activar la ruta de protección y justicia.
        """)
        st.caption("Recuerda: Los hospitales tienen la obligación de brindarte atención integral inmediatamente.")

    st.caption("Actuar de forma prudente y organizada es la mejor manera de proteger lo más importante TU VIDA \:green_heart:.")



# ═════════════════════════════════════════════════════════════════════════════
# PÁGINA 2 — Riesgo Local
# ═════════════════════════════════════════════════════════════════════════════
def _mapa_riesgo(localidades, tasa_loc: pd.DataFrame, CAIS) -> folium.Map:
    """Construye el mapa con localidades coloreadas por victimización."""
    import json
    loc_geo = localidades.copy()

    # Buscar columna de código de localidad
    cod_col = next((c for c in loc_geo.columns
                    if c in ["LocCodigo","LOCCOD","COD_LOC","codigo","CODIGO","Codigo"]), None)

    # Merge con tasas
    if cod_col:
        # Normalizar a entero para coincidir con EPV (que usa 1, 2, 3...)
        loc_geo[cod_col] = loc_geo[cod_col].apply(
            lambda x: int(str(x).strip().lstrip("0") or "0") if pd.notna(x) else 0
        )
        tasa_loc["LOCALIDAD"] = tasa_loc["LOCALIDAD"].astype(int)
        loc_geo = loc_geo.merge(tasa_loc, left_on=cod_col, right_on="LOCALIDAD", how="left")
    else:
        loc_geo["tasa_vic"] = 20.0
    loc_geo["tasa_vic"] = loc_geo["tasa_vic"].fillna(0)

    import branca.colormap as cm

    vmin = loc_geo["tasa_vic"].min()
    vmax = loc_geo["tasa_vic"].max()

    colormap = cm.linear.YlOrRd_09.scale(vmin, vmax+7)
    colormap.caption = "Tasa de victimización (%)"

    if cod_col:
        loc_geo["loc_nombre"] = loc_geo[cod_col].apply(
            lambda x: LABELS_LOCALIDAD.get(int(x), str(x)) if pd.notna(x) else "Desconocida"
        )
        loc_geo["loc_cod_int"] = loc_geo[cod_col].apply(
            lambda x: int(x) if pd.notna(x) else 0
        )
    else:
        loc_geo["loc_nombre"] = "Localidad"
        loc_geo["loc_cod_int"] = 0


    m = folium.Map(location=[4.629, -74.105], zoom_start= 11.5, tiles="CartoDB positron")

    # Un solo GeoJson con todas las localidades — permite capturar clics
    def style_fn(feature):
        tasa = feature["properties"].get("tasa_vic", 0) or 0
        return {
            "fillColor": colormap(tasa),
            "color": "#555",
            "weight": 1.2,
            "fillOpacity": 0.65,
        }

    def highlight_fn(feature):
        return {"weight": 3, "color": "#222", "fillOpacity": 0.75}

    geojson_layer = folium.GeoJson(
        loc_geo[["geometry","loc_nombre","loc_cod_int","tasa_vic"]],
        style_function=style_fn,
        highlight_function=highlight_fn,
        tooltip=folium.GeoJsonTooltip(
            fields=["loc_nombre","tasa_vic"],
            aliases=["Localidad:", "Victimización:"],
            localize=True,
            sticky=True,
        ),
        popup=folium.GeoJsonPopup(
            fields=["loc_nombre","loc_cod_int","tasa_vic"],
            aliases=["Localidad","Código","Victimización (%)"],
        ),
        name="Localidades",
    )
    geojson_layer.add_to(m)

    # Marcadores CAIs
    for _, row in CAIS.iterrows():
        add_markers(row, m)

    # Leyenda
    '''
    m.get_root().html.add_child(folium.Element("""
        <div style="position:fixed;bottom:30px;left:30px;z-index:1000;
                    background:white;padding:10px 14px;border-radius:8px;
                    border:1px solid #ccc;font-size:12px;line-height:1.8">
            <b>Tasa de victimización</b><br>
            <span style="color:#27AE60">&#9632;</span> &lt;15% — Bajo<br>
            <span style="color:#F39C12">&#9632;</span> 15–25% — Medio<br>
            <span style="color:#E74C3C">&#9632;</span> &gt;25% — Alto
        </div>"""))
    '''
    colormap.add_to(m)
    return m


def render_riesgo_local(localidades, CAIS):
    st.title("📍 Riesgo Local")

    # ── Cargar SIEDCORE FUERA de los tabs ────────────────────────────────
    df_s = None  # ← inicializar siempre primero
    try:
        df_s = preparar_siedcore(load_siedcore())
    except FileNotFoundError:
        pass

    tab1, tab2 = st.tabs(["👥 Percepción y Victimización", "🚨 SIEDCO"])
    with tab1:
        st.markdown("""
        Explora el nivel de victimización por localidad según la Encuesta de Percepción 
        y Victimización 2024. Haz clic en cualquier localidad para ver los delitos más 
        frecuentes, percepción de inseguridad por género y CAIs disponibles en la zona.
        """)


        datos = preparar_epv(load_epv())
        tasa_loc = datos["tasa_loc"]
        epv_ok   = True

        m         = _mapa_riesgo(localidades, tasa_loc, CAIS)
        mapa_data = st_folium(
            m,
            use_container_width=True,
            height=520,
            key="mapa_riesgo",
            returned_objects=["last_clicked","last_object_clicked_popup"],
        )

        # Capturar localidad desde el popup del GeoJson
        loc_cod, loc_nom = None, None
        if mapa_data:
            # El popup llega como string con el formato del HTML generado
            popup_txt = mapa_data.get("last_object_clicked_popup")
            if popup_txt and isinstance(popup_txt, str):
                import re
                # Buscar el código numérico que aparece después de "Código"
                match = re.search(r"C[oó]digo\s+(\d+)", popup_txt)
                if match:
                    try:
                        loc_cod = int(match.group(1))
                        loc_nom = LABELS_LOCALIDAD.get(loc_cod, "")
                    except (ValueError, TypeError):
                        pass

            # Fallback: point-in-polygon con last_clicked
            if not loc_cod:
                clicked = mapa_data.get("last_clicked")
                if clicked:
                    from shapely.geometry import Point
                    import geopandas as gpd
                    punto    = Point(clicked["lng"], clicked["lat"])
                    loc_4326 = localidades.to_crs("EPSG:4326") if localidades.crs and str(localidades.crs) != "EPSG:4326" else localidades
                    cod_col  = next((c for c in loc_4326.columns
                                     if c in ["LocCodigo","LOCCOD","COD_LOC","codigo","CODIGO","Codigo"]), None)
                    # Buscar la localidad más cercana al punto clickeado
                    distancias = loc_4326.geometry.distance(punto)
                    idx_min    = distancias.idxmin()
                    fila       = loc_4326.loc[idx_min]
                    if cod_col:
                        try:
                            loc_cod = int(str(fila[cod_col]).strip())
                            loc_nom = LABELS_LOCALIDAD.get(loc_cod, str(loc_cod))
                        except (ValueError, TypeError):
                            pass
        st.divider()

        if loc_cod:
            st.session_state["siedcore_loc_cod"] = loc_cod
            st.session_state["siedcore_loc_nom"] = loc_nom

        # Panel de análisis por localidad
        if loc_cod and epv_ok:
            st.subheader(f"📊 Análisis · {loc_nom}")
            detalle_localidad(loc_cod, loc_nom,
                              datos["df_uniq"], datos["p204_long"], CAIS)
        elif loc_cod:
            st.subheader(f"📊 CAIs · {loc_nom}")
            cais_loc = CAIS[CAIS["CAIIULOCAL"].apply(lambda x: int(str(x).lstrip("0") or "0")) == loc_cod]
            st.metric("CAIs en la zona", len(cais_loc))
        else:
            st.caption("No se ha seleccionado ninguna localidad para resumen de análisis")

    with tab2:
        loc_cod_s = st.session_state.get("siedcore_loc_cod")
        loc_nom_s = st.session_state.get("siedcore_loc_nom")

        if df_s is None:
            st.error("No se encontró el archivo SIEDCORE.")
            st.stop()

        st.markdown("""
        Explora los delitos registrados por localidad según la dataset de SIEDCO. 
        """)

        # Mapa coloreado por delitos
        m_s = _mapa_siedcore(localidades, df_s, CAIS)
        mapa_s = st_folium(
            m_s,
            use_container_width=True,
            height=520,
            key="mapa_siedcore",
            returned_objects=["last_clicked", "last_object_clicked_popup"],
        )

        # Capturar localidad del clic — misma lógica que tab1
        import re
        loc_cod_s, loc_nom_s = None, None
        if mapa_s:
            popup_txt = mapa_s.get("last_object_clicked_popup")
            if popup_txt and isinstance(popup_txt, str):
                match = re.search(r"C[oó]digo\s+(\d+)", popup_txt)
                if match:
                    try:
                        loc_cod_s = int(match.group(1))
                        loc_nom_s = LABELS_LOCALIDAD.get(loc_cod_s, "")
                    except (ValueError, TypeError):
                        pass

            if not loc_cod_s:
                clicked = mapa_s.get("last_clicked")
                if clicked:
                    from shapely.geometry import Point
                    import geopandas as gpd
                    punto = Point(clicked["lng"], clicked["lat"])
                    loc_4326 = localidades.to_crs("EPSG:4326") if localidades.crs and str(
                        localidades.crs) != "EPSG:4326" else localidades
                    cod_col = next((c for c in loc_4326.columns
                                    if c in ["LocCodigo", "LOCCOD", "COD_LOC", "codigo", "CODIGO", "Codigo"]), None)
                    distancias = loc_4326.geometry.distance(punto)
                    idx_min = distancias.idxmin()
                    fila = loc_4326.loc[idx_min]
                    if cod_col:
                        try:
                            loc_cod_s = int(str(fila[cod_col]).strip())
                            loc_nom_s = LABELS_LOCALIDAD.get(loc_cod_s, str(loc_cod_s))
                        except (ValueError, TypeError):
                            pass

        st.divider()

        if not loc_cod_s:
            st.caption("Haz clic en una localidad para ver su análisis SIEDCO.")
            st.stop()

        # Filtrar y mostrar gráficos
        df_loc = df_s[df_s["LOCALIDAD"] == loc_nom_s.upper()]

        if df_loc.empty:
            st.warning(f"No hay registros SIEDCO para **{loc_nom_s}**.")
            st.stop()

        st.subheader(f"🚨 SIEDCO · {loc_nom_s}")
        st.caption(f"Todos los años · {int(df_loc['CANTIDAD'].sum()):,} casos registrados")
        st.divider()

        kpis_siedcore(df_loc)
        st.divider()


        col_a, col_b = st.columns(2)
        with col_a:
            barras_hechos_siedcore(df_loc)
        with col_b:
            barras_arma_siedcore(df_loc)
        st.divider()


        barras_sexo_siedcore(df_loc)


# ═════════════════════════════════════════════════════════════════════════════
# PÁGINA 3 — Análisis (tabs ECN + EPV)
# ═════════════════════════════════════════════════════════════════════════════
def render_analisis():
    st.title("Análisis")
    tab1, tab2, tab3 = st.tabs(["🏢 Clima de Negocios", "👥 Percepción y Victimización", "SIEDCO"])

    # ── Tab 1: ECN ────────────────────────────────────────────────────────
    with tab1:
        try:
            df = preparar_ecn(load_ecn())
        except FileNotFoundError:
            st.error("No se encontró el archivo ECN 2024.")
            up = st.file_uploader("Sube el Excel ECN 2024", type=["xlsx"], key="up_ecn")
            if up: df = preparar_ecn(pd.read_excel(up))
            else: st.stop()

        st.markdown("### Seguridad Empresarial · ECN 2024")
        st.markdown("""
        Resultados de la Encuesta de Clima de Negocios 2024 de la CCB. Analiza la 
        victimización empresarial por sector y tamaño, los delitos más frecuentes, 
        las medidas de seguridad adoptadas.
        """)
        st.divider()

        st.markdown("### Indicadores clave")
        kpis_ecn(df)
        st.divider()

        st.markdown("### ¿Quiénes son más afectados?")
        col_a, col_b = st.columns(2)
        with col_a: barras_sector(df)
        with col_b: barras_tamano(df)
        st.divider()

        st.markdown("### Tipos de delito más frecuentes")
        barras_delitos_ecn(df)
        st.divider()

        st.markdown("### Percepción de seguridad")
        pie_percepcion_ecn(df)
        st.divider()

        st.markdown("### Medidas de seguridad adoptadas")
        barras_medidas(df)
        st.divider()


    # ── Tab 2: EPV ────────────────────────────────────────────────────────
    with tab2:
        try:
            df_raw = load_epv()
            datos  = preparar_epv(df_raw)
        except FileNotFoundError:
            st.error("No se encontró el archivo EPV 2024.")
            up2 = st.file_uploader("Sube el Excel EPV 2024", type=["xlsx"], key="up_epv")
            if up2:
                df_raw = pd.read_excel(up2)
                datos  = preparar_epv(df_raw)
            else: st.stop()

        df_u   = datos["df_uniq"]
        st.markdown("### Percepción y Victimización · EPV 2024")
        st.markdown("""
        Resultados de la Encuesta de Percepción y Victimización 2024 de la CCB. 
        Explora cómo perciben la seguridad los bogotanos, qué delitos se reportan más, 
        quiénes denuncian.
        """)
        st.divider()

        st.markdown("### Indicadores clave")
        kpis_epv(df_u, datos["ids_den"])
        percepcion_ciudad(df_u)
        st.divider()


        st.markdown("### Delitos relevantes para el entorno empresarial")
        delitos_empresariales_epv(df_raw)
        st.divider()

        st.markdown("### Percepción de seguridad: barrio y ciudad")
        percepcion_barrio_ciudad(df_u)
        st.divider()

        st.markdown("### Relación con la Policía")
        denuncia_y_satisfaccion(df_u)
        st.divider()

    with tab3:
        try:
            df_s = preparar_siedcore(load_siedcore())
        except FileNotFoundError:
            st.error("No se encontró el archivo SIEDCO.")
            st.stop()

        st.markdown("### Estadísticas Delictivas · SIEDCORE")
        st.markdown("""
           Registros de hechos delictivos en Bogotá D.C. según el sistema SIEDCORE.
           Explora qué delitos ocurren más, en qué localidades, a qué horas y a qué perfiles de víctima.
           """)
        st.divider()

        # Filtros
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            anios = sorted(df_s["ANIO"].unique())
            anio_sel = st.multiselect("Año", anios, default=anios, key="siedcore_anio")
        with col_f2:
            hechos = sorted(df_s["HECHO"].str.title().unique())
            hecho_sel = st.multiselect("Tipo de hecho", hechos, default=[], key="siedcore_hecho")
        with col_f3:
            locs = sorted(df_s["LOCALIDAD"].str.title().unique())
            loc_sel = st.multiselect("Localidad", locs, default=[], key="siedcore_loc")

        # Aplicar filtros
        df_f = df_s[df_s["ANIO"].isin(anio_sel)] if anio_sel else df_s
        if hecho_sel:
            df_f = df_f[df_f["HECHO"].str.title().isin(hecho_sel)]
        if loc_sel:
            df_f = df_f[df_f["LOCALIDAD"].str.title().isin(loc_sel)]

        if df_f.empty:
            st.warning("No hay datos para los filtros seleccionados.")
            st.stop()

        st.markdown("### Indicadores clave")
        kpis_siedcore(df_f)
        st.divider()

        st.markdown("### Tendencia mensual")
        linea_tendencia_siedcore(df_f)
        st.divider()

        st.markdown("### ¿Qué delitos ocurren más?")
        barras_hechos_siedcore(df_f)
        st.divider()

        st.markdown("### ¿Dónde ocurren más?")
        barras_localidad_siedcore(df_f)
        st.divider()

        st.markdown("### Perfil de las víctimas")
        col_a, col_b = st.columns(2)
        with col_a:
            barras_sexo_siedcore(df_f)
        with col_b:
            barras_rango_vital_siedcore(df_f)
        st.divider()

        st.markdown("### ¿Cuándo y cómo?")
        col_c, col_d = st.columns(2)
        with col_c:
            barras_rango_dia_siedcore(df_f)
        with col_d:
            barras_arma_siedcore(df_f)


# ═════════════════════════════════════════════════════════════════════════════
# PÁGINA 4 — BACANO (placeholder)
# ═════════════════════════════════════════════════════════════════════════════


def render_bacano():
    st.title("⭐ ¿Qué es el Índice BACANO?")
    st.markdown("#### El termómetro de la seguridad para tu negocio en Bogotá")

    # Introducción amigable
    st.write("""
    **BACANO** no es solo un nombre llamativo; son las siglas de nuestro **Barómetro Analítico de Comportamiento 
    y Amenazas de Negocios y Operaciones**. 

    Imagina que es como una 'calificación' de seguridad: nos dice qué tan difícil o seguro es tener un negocio 
    en Bogotá dependiendo de su tamaño y el sector al que pertenece.
    """)

    # Explicación visual de los 3 pilares
    st.info("### 🔍 ¿Cómo llegamos a ese número?")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.error("### 50%")
        st.markdown("**Delitos Reales**")
        st.caption("¿Cuántos negocios fueron víctimas de robos o ataques?")

    with col2:
        st.warning("### 30%")
        st.markdown("**Silencio (No denuncia)**")
        st.caption("¿Cuántas empresas se quedaron calladas y no avisaron a la policía?")

    with col3:
        st.success("### 20%")
        st.markdown("**Miedo Percibido**")
        st.caption("¿Sienten los dueños que la calle está peor que el año pasado?")

    st.divider()

    # Interpretación del semáforo
    st.markdown("### 🚦 ¿Cómo leer los resultados?")

    col_a, col_b = st.columns([1, 2])

    with col_a:
        st.metric("Rango", "0.0 a 1.0")

    with col_b:
        st.markdown("""
        * 🟢 **Cerca a 0:** Un entorno tranquilo donde se puede trabajar sin miedo.
        * 🟡 **Entre 0.15 y 0.45:** La realidad actual de la mayoría de negocios en Bogotá.
        * 🔴 **Cerca a 1:** Zona de alerta máxima donde se necesita ayuda urgente de las autoridades.
        """)

    st.divider()

    # Lógica de carga de datos (tu código original)
    try:
        from src.preprocesamiento import preparar_ecn
        # Asumiendo que load_ecn() existe en tu ambiente
        df = preparar_ecn(load_ecn())
        bacano_dashboard(df)
    except Exception:
        st.warning("📊 **Para ver el análisis detallado, necesitamos los datos.**")
        up = st.file_uploader("Sube el archivo Excel de la ECN 2024", type=["xlsx"], key="up_bacano")
        if up:
            import pandas as pd
            from src.preprocesamiento import preparar_ecn
            df_subido = pd.read_excel(up)
            st.success("¡Datos cargados con éxito!")
            bacano_dashboard(preparar_ecn(df_subido))
def render_simulador_bacano():
    st.title("🧮 Simulador de Riesgo BACANO Micro")

    with st.form("form_bacano_completo"):
        # --- Dimensión A ---
        st.subheader("Dimensión A: Exposición (40%)")
        p58 = st.radio("1. ¿Su empresa fue víctima de algún delito en 2024?", ["Sí", "No"])
        n_delitos = st.number_input("2. ¿Cuántos tipos de delito distintos sufrió? (0-9)", 0, 9, 0)
        alto_impacto = st.radio("3. ¿Sufrió extorsión, ciberdelito, acoso o delito sexual?", ["Sí", "No"])

        # --- Dimensión B ---
        st.subheader("Dimensión B: Vulnerabilidad (35%)")
        sin_medidas = st.radio("4. ¿Opera SIN medidas de seguridad reales?", ["Sí", "No"])
        denuncio = st.selectbox("5. Si fue víctima, ¿denunció el delito?", ["No aplicable", "Sí", "No"])
        n_impactos = st.number_input("6. ¿Cuántos tipos de impacto económico sufrió? (0-8)", 0, 8, 0)

        # --- Dimensión C ---
        st.subheader("Dimensión C: Percepción (25%)")
        empeoro = st.radio("7. ¿Percibe que la seguridad de su entorno empeoró?", ["Sí", "No"])
        # IMPORTANTE: Asegúrate de que el slider sea flotante o se convierta después
        escala_seguridad = st.slider("8. ¿Qué tan seguro se siente? (1=Muy inseguro, 5=Muy seguro)", 1, 5, 2)
        se_siente_seguro = st.radio("9. ¿Se siente seguro en su entorno empresarial?", ["Sí", "No"])

        enviado = st.form_submit_button("Calcular Índice de Riesgo")

    if enviado:
        # --- DIMENSIÓN A: EXPOSICIÓN (Peso 40%) ---
        a1 = 1.0 if p58 == "Sí" else 0.0
        a2 = n_delitos / 9.0
        a3 = 1.0 if alto_impacto == "Sí" else 0.0
        dim_a = (0.50 * a1) + (0.30 * a2) + (0.20 * a3)

        # --- DIMENSIÓN B: VULNERABILIDAD (Peso 35%) ---
        b1 = 1.0 if sin_medidas == "Sí" else 0.0
        b2 = 1.0 if (p58 == "Sí" and denuncio == "No") else 0.0
        b3 = n_impactos / 8.0
        dim_b = (0.40 * b1) + (0.40 * b2) + (0.20 * b3)

        # --- DIMENSIÓN C: PERCEPCIÓN (Peso 25%) ---
        # 7. Percepción de seguridad (P57)
        # Si responde "Empeoró" (Sí) -> valor 1
        val_c1 = 1.0 if empeoro == "Sí" else 0.0

        # 8. Escala de seguridad (P103)
        # Inversión de escala: (5 - valor) / 4.0
        # Para el ejemplo (valor 2): (5-2)/4 = 0.75
        val_c2 = (5.0 - float(escala_seguridad)) / 4.0

        # 9. Sentimiento de seguridad (P104)
        # Si responde "Inseguro" (No) -> valor 1
        val_c3 = 1.0 if se_siente_seguro == "No" else 0.0

        # CÁLCULO EXACTO DIMENSIÓN C
        # Pesos: 50% C1, 30% C2, 20% C3
        dim_c = (val_c1 * 0.50) + (val_c2 * 0.30) + (val_c3 * 0.20)

        # --- CÁLCULO FINAL DEL ÍNDICE ---
        # Pesos: 40% A, 35% B, 25% C
        score = (dim_a * 0.40) + (dim_b * 0.35) + (dim_c * 0.25)


        # Renderizado
        st.metric("Índice BACANO Micro", f"{score:.3f}")
        # 1. Definir el nivel y el color basado en el score
        if score > 0.50:
            nivel = "CRÍTICO / ALTO 🔴"
            mensaje = "**Nivel Crítico:** La empresa presenta una alta exposición al delito y una percepción de inseguridad severa. Se recomienda intervención inmediata y revisión de medidas de seguridad."
            color_func = st.error
        elif score > 0.30:
            nivel = "MEDIO-ALTO 🟠"
            mensaje = "**Nivel Medio-Alto:** Existe una vulnerabilidad considerable. Es importante fortalecer la cultura de denuncia y mejorar los sistemas de vigilancia."
            color_func = st.warning
        elif score > 0.15:
            nivel = "MEDIO-BAJO 🟡"
            mensaje = "**Nivel Medio-Bajo:** El entorno es relativamente estable, pero hay factores de percepción o falta de medidas que podrían mejorar."
            color_func = st.warning
        else:
            nivel = "BAJO 🟢"
            mensaje = "**Nivel Bajo:** La empresa se encuentra en un entorno seguro y cuenta con una buena gestión de riesgos. ¡Siga así!"
            color_func = st.success



        # 3. Mostrar la caja con el color correspondiente y la explicación
        color_func(mensaje)

        # 4. Visualización de dimensiones
        st.write("---")
        st.markdown("### Desglose por Dimensiones")
        st.progress(dim_a, text=f"Dimensión A (Exposición): {dim_a:.3f}")
        st.progress(dim_b, text=f"Dimensión B (Vulnerabilidad): {dim_b:.3f}")
        st.progress(dim_c, text=f"Dimensión C (Percepción): {dim_c:.3f}")

        # Opcional: Globos si el riesgo es muy bajo
        if score <= 0.15:
            st.balloons()


"""
components.py
─────────────
Funciones render_* para cada página del menú.
Solo arman la UI: llaman a loaders, preprocesamiento y graficos.
No contiene lógica de limpieza ni funciones de gráficos.
"""
def _mapa_siedcore(localidades, df_s, CAIS) -> folium.Map:
    """Mapa coloreado por cantidad de delitos SIEDCORE por localidad."""
    import branca.colormap as cm

    # Totalizar delitos por localidad
    delitos_loc = (df_s.groupby("LOCALIDAD")["CANTIDAD"].sum()
                     .reset_index()
                     .rename(columns={"CANTIDAD": "total_delitos"}))

    loc_geo = localidades.copy()
    cod_col = next((c for c in loc_geo.columns
                    if c in ["LocCodigo","LOCCOD","COD_LOC","codigo","CODIGO","Codigo"]), None)

    # Agregar nombre normalizado para hacer merge
    loc_geo["loc_nombre"] = loc_geo[cod_col].apply(
        lambda x: LABELS_LOCALIDAD.get(
            int(str(x).strip().lstrip("0") or "0"), ""
        ).upper() if pd.notna(x) else ""
    ) if cod_col else ""

    loc_geo = loc_geo.merge(delitos_loc, left_on="loc_nombre", right_on="LOCALIDAD", how="left")
    loc_geo["total_delitos"] = loc_geo["total_delitos"].fillna(0)

    if cod_col:
        loc_geo["loc_cod_int"] = loc_geo[cod_col].apply(
            lambda x: int(str(x).strip().lstrip("0") or "0") if pd.notna(x) else 0
        )
    else:
        loc_geo["loc_cod_int"] = 0

    vmin = loc_geo["total_delitos"].min()
    vmax = loc_geo["total_delitos"].max()
    colormap = cm.linear.YlOrRd_09.scale(vmin, vmax)
    colormap.caption = "Total delitos registrados"
    # ── Formatear los ticks de la leyenda ────────────────────────────────
    import numpy as np
    tick_vals = [vmin, (vmin + vmax) / 2, vmax]

    colormap = cm.linear.YlOrRd_09.scale(vmin, vmax)
    colormap.caption = "Total delitos registrados"
    colormap.index = tick_vals
    colormap.tick_labels = [f"{int(v):,}".replace(",", ".") for v in tick_vals]
    def style_fn(feature):
        val = feature["properties"].get("total_delitos", 0) or 0
        return {"fillColor": colormap(val), "color": "#555",
                "weight": 1.2, "fillOpacity": 0.7}

    def highlight_fn(feature):
        return {"weight": 3, "color": "#222", "fillOpacity": 0.85}

    m = folium.Map(location=[4.629, -74.105], zoom_start=11.5, tiles="CartoDB positron")

    folium.GeoJson(
        loc_geo[["geometry", "loc_nombre", "loc_cod_int", "total_delitos"]],
        style_function=style_fn,
        highlight_function=highlight_fn,
        tooltip=folium.GeoJsonTooltip(
            fields=["loc_nombre", "total_delitos"],
            aliases=["Localidad:", "Total delitos:"],
            localize=True, sticky=True,
        ),
        popup=folium.GeoJsonPopup(
            fields=["loc_nombre", "loc_cod_int", "total_delitos"],
            aliases=["Localidad", "Código", "Total delitos"],
        ),
        name="Localidades",
    ).add_to(m)

    for _, row in CAIS.iterrows():
        add_markers(row, m)

    # Leyenda manual en HTML
    leyenda_html = f"""
    <div style="
        position: fixed; bottom: 30px; left: 30px; z-index: 1000;
        background: white; padding: 12px 16px; border-radius: 8px;
        border: 1px solid #ccc; font-family: Arial; font-size: 12px;
    ">
        <b>Total delitos registrados</b><br><br>
        <div style="
            background: linear-gradient(to right, #ffffb2, #fecc5c, #fd8d3c, #f03b20, #bd0026);
            width: 180px; height: 16px; border-radius: 3px;
        "></div>
        <div style="display:flex; justify-content:space-between; width:180px; margin-top:4px;">
            <span>{int( round(vmin, 2)):,}</span>
            <span>{ round(int((vmin+vmax)/2), 2):,}</span>
            <span>{int(round(vmax)):,}</span>
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(leyenda_html))

    colormap = cm.linear.YlOrRd_09.scale(vmin, vmax)
    colormap.caption = "Total delitos registrados"


    return m