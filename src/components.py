# src/components.py
"""
components.py
─────────────
Funciones render_* para cada página del menú.
Solo arman la UI: llaman a loaders, preprocesamiento y graficos.
No contiene lógica de limpieza ni funciones de gráficos.
"""

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

from src.loaders import load_ecn, load_epv, add_markers
from src.preprocesamiento import preparar_ecn, preparar_epv, LABELS_LOCALIDAD, LOC_NOMBRE_A_COD
from src.graficos import (
    # ECN
    kpis_ecn, barras_sector, barras_tamano, barras_delitos_ecn,
    pie_percepcion_ecn, barras_medidas, heatmap_ire,
    # EPV
    kpis_epv, victimizacion_general, delitos_empresariales_epv,
    denuncia_por_delito, percepcion_barrio_ciudad,
    genero_victimizacion, victimizacion_localidad,
    # Riesgo local
    detalle_localidad,
)

# ═════════════════════════════════════════════════════════════════════════════
# PÁGINA 1 — Servicio de Ayuda
# ═════════════════════════════════════════════════════════════════════════════
def render_servicio_ayuda(localidades, CAIS):
    st.title("🛡️ Servicio de Ayuda")
    st.subheader("Visualización de CAIs en Bogotá")

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
    col1.metric("📞 Teléfono",  "018000112137")
    col2.metric("💬 WhatsApp",  "300 755 1846")
    st.metric("📧 Correo", "lpurpura@sdmujer.gov.co")


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
    m.get_root().html.add_child(folium.Element("""
        <div style="position:fixed;bottom:30px;left:30px;z-index:1000;
                    background:white;padding:10px 14px;border-radius:8px;
                    border:1px solid #ccc;font-size:12px;line-height:1.8">
            <b>Tasa de victimización</b><br>
            <span style="color:#27AE60">&#9632;</span> &lt;15% — Bajo<br>
            <span style="color:#F39C12">&#9632;</span> 15–25% — Medio<br>
            <span style="color:#E74C3C">&#9632;</span> &gt;25% — Alto
        </div>"""))
    colormap.add_to(m)
    return m
def render_riesgo_local(localidades, CAIS):
    st.title("📍 Riesgo Local")

    # Cargar y procesar EPV
    try:
        datos = preparar_epv(load_epv())
        tasa_loc = datos["tasa_loc"]
        epv_ok   = True
    except FileNotFoundError:
        st.warning("⚠️ No se encontró Base2024.xlsx — mapa sin colores de riesgo.")
        tasa_loc = pd.DataFrame(columns=["LOCALIDAD","tasa_vic"])
        datos    = {"df_uniq": pd.DataFrame(), "p204_long": pd.DataFrame()}
        epv_ok   = False

    # Mapa
    st.caption("🟢 <15%  🟡 15–25%  🔴 >25% de victimización · Haz clic en una localidad.")
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
        st.info("👆 Haz clic en una localidad para ver el análisis de riesgo.")

    # Evaluador de peligrosidad

# ═════════════════════════════════════════════════════════════════════════════
# PÁGINA 3 — Análisis (tabs ECN + EPV)
# ═════════════════════════════════════════════════════════════════════════════
def render_analisis():
    st.title("📊 Análisis")
    tab1, tab2 = st.tabs(["🏢 Clima de Negocios", "👥 Percepción y Victimización"])

    # ── Tab 1: ECN ────────────────────────────────────────────────────────
    with tab1:
        try:
            df = preparar_ecn(load_ecn())
        except FileNotFoundError:
            st.error("No se encontró el archivo ECN 2024.")
            up = st.file_uploader("Sube el Excel ECN 2024", type=["xlsx"], key="up_ecn")
            if up: df = preparar_ecn(pd.read_excel(up))
            else: st.stop()

        N, N_vic = len(df), int(df["Victima_bin"].sum())
        st.markdown("### 🛡️ Seguridad Empresarial · ECN 2024")
        st.markdown(f"**{N:,} empresas** encuestadas · **{N_vic:,}** víctimas "
                    f"(**{N_vic/N*100:.1f}%**)")
        st.divider()

        st.markdown("### 📊 Indicadores clave")
        kpis_ecn(df)
        st.divider()

        st.markdown("### 🏭 ¿Quiénes son más afectados?")
        col_a, col_b = st.columns(2)
        with col_a: barras_sector(df)
        with col_b: barras_tamano(df)
        st.divider()

        st.markdown("### 🔎 Tipos de delito más frecuentes")
        barras_delitos_ecn(df)
        st.divider()

        st.markdown("### 💬 Percepción de seguridad")
        pie_percepcion_ecn(df)
        st.divider()

        st.markdown("### 🔐 Medidas de seguridad adoptadas")
        barras_medidas(df)
        st.divider()

        st.markdown("### ⚠️ Índice de Riesgo Empresarial (IRE)")
        st.info("**IRE** = victimización (50%) + sub-reporte (30%) + percepción negativa (20%). "
                "Pasa el cursor sobre cada celda para ver el detalle.", icon="ℹ️")
        heatmap_ire(df)
        st.success(f"✅ {N:,} empresas · {N_vic:,} víctimas ({N_vic/N*100:.1f}%)", icon="✅")

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
        N, N_vic = len(df_u), int((df_u["P203"]==1).sum())

        st.markdown("### 👥 Percepción y Victimización · EPV 2024")
        st.markdown(f"**{N:,} personas** encuestadas · **{N_vic:,}** víctimas "
                    f"(**{N_vic/N*100:.1f}%**)")
        st.divider()

        st.markdown("### 📊 Indicadores clave")
        kpis_epv(df_u, datos["ids_den"])
        st.divider()

        st.markdown("### 🔴 Victimización general")
        victimizacion_general(df_u)
        st.divider()

        st.markdown("### 🏢 Delitos relevantes para el entorno empresarial")
        delitos_empresariales_epv(df_raw)
        st.divider()

        st.markdown("### 📋 Tasa de denuncia por delito")
        denuncia_por_delito(datos["p204_long"], datos["p214_long"])
        st.divider()

        st.markdown("### 💬 Percepción de seguridad: barrio y ciudad")
        percepcion_barrio_ciudad(df_u)
        st.divider()

        st.markdown("### ⚧ Enfoque de género")
        genero_victimizacion(df_u, datos["p204_long"], datos["ids_den"])
        st.divider()

        st.markdown("### 🗺️ Victimización por localidad")
        victimizacion_localidad(df_u)
        st.success(f"✅ {N:,} encuestados · {N_vic:,} víctimas ({N_vic/N*100:.1f}%)", icon="✅")


# ═════════════════════════════════════════════════════════════════════════════
# PÁGINA 4 — BACANO (placeholder)
# ═════════════════════════════════════════════════════════════════════════════
def render_bacano():
    st.title("⭐ BACANO")
    st.subheader("Barómetro Analítico de Comportamiento y Amenazas de Negocios & Operaciones")
    st.info("Sección en construcción.")