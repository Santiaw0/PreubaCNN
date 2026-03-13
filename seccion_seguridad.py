"""
seccion_seguridad.py
────────────────────
Sección de Seguridad Empresarial para la plataforma CCB.
Todos los gráficos son interactivos con Plotly.

Requiere: streamlit, pandas, numpy, plotly, openpyxl
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────────────────────
# PALETA CORPORATIVA CCB
# ─────────────────────────────────────────────────────────────────────────────
PRIMARY  = "#0D1B2A"
ACCENT1  = "#1B4F72"
ACCENT2  = "#2E86AB"
DANGER   = "#E74C3C"
WARN     = "#F39C12"
SUCCESS  = "#27AE60"
NEUTRAL  = "#95A5A6"

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="white",
    font=dict(family="Arial", color=PRIMARY),
    margin=dict(l=20, r=20, t=50, b=20),
    hoverlabel=dict(bgcolor="white", font_size=13),
)


# ─────────────────────────────────────────────────────────────────────────────
# PREPROCESAMIENTO
# ─────────────────────────────────────────────────────────────────────────────
def _preparar_datos(df_raw: pd.DataFrame) -> pd.DataFrame:
    COLS_INTERES = [
        "NUMERO", "F4", "F5", "REGION",
        "P56", "P56_1", "P57", "P58",
        "P59_A","P59_B","P59_C","P59_D","P59_E",
        "P59_F","P59_G","P59_H","P59_I",
        "P60", "P61",
        "P61A_1","P61A_2","P61A_3","P61A_4",
        "P61A_5","P61A_6","P61A_7","P61A_9",
        "P61B_1","P61B_2","P61B_3","P61B_4",
        "P61B_5","P61B_6","P61B_7","P61B_8",
    ]
    df = df_raw[[c for c in COLS_INTERES if c in df_raw.columns]].copy()
    df = df.drop_duplicates(subset="NUMERO", keep="first").reset_index(drop=True)

    int_cols = ["F4","F5","REGION","P56","P56_1","P57","P58"]
    del_cols = ["P59_A","P59_B","P59_C","P59_D","P59_E","P59_F","P59_G","P59_H","P59_I"]
    med_cols = ["P61A_1","P61A_2","P61A_3","P61A_4","P61A_5","P61A_6","P61A_7","P61A_9"]
    imp_cols = ["P61B_1","P61B_2","P61B_3","P61B_4","P61B_5","P61B_6","P61B_7","P61B_8"]

    for c in int_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("Int64")
    for c in [c for c in df.columns if c not in int_cols + ["NUMERO"]]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    if "P56_1" in df.columns:
        df["P56_1"] = df["P56_1"].replace(92, pd.NA)

    mask_no_vic = df["P58"] == 2
    for c in del_cols + ["P60","P61"]:
        if c in df.columns:
            df.loc[mask_no_vic, c] = df.loc[mask_no_vic, c].fillna(0)
    for c in del_cols:
        if c in df.columns:
            df[c] = df[c].apply(lambda x: 1 if x == 1 else 0)

    p61b_sin = df[imp_cols].isna().all(axis=1)
    for c in med_cols:
        if c in df.columns:
            df[c] = df[c].notna().astype(int)
    for c in imp_cols:
        if c in df.columns:
            df.loc[~p61b_sin, c] = df.loc[~p61b_sin, c].notna().astype(float)

    df["Sector"]      = df["F4"].map({1:"Industria", 2:"Comercio", 3:"Servicios"})
    df["Tamaño"]      = df["F5"].map({1:"Microempresa", 2:"Pequeña", 3:"Mediana", 4:"Grande"})
    df["Percepcion"]  = df["P57"].map({1:"Mejoró", 2:"Igual", 3:"Empeoró"})
    df["Seguridad"]   = df["P56_1"].map({1:"Muy inseguro", 2:"Inseguro", 3:"Ni/Ni", 4:"Seguro", 5:"Muy seguro"})

    df["Victima_bin"]     = (df["P58"] == 1).astype(int)
    df["Num_Delitos"]     = df[del_cols].sum(axis=1)
    med_real              = [c for c in med_cols if c != "P61A_2"]
    df["Num_Medidas"]     = df[med_real].sum(axis=1)
    df["Sin_Medidas"]     = df["P61A_2"].astype(int)
    df["Percep_Negativa"] = (df["P57"] == 3).astype(int)
    df["Denuncio_bin"]    = ((df["P58"] == 1) & (df["P60"] == 1)).astype(int)
    df["IRE"] = (
        0.5 * df["Victima_bin"] +
        0.3 * ((df["P58"] == 1) & (df["P60"] != 1)).astype(int) +
        0.2 * df["Percep_Negativa"]
    )
    return df


# ─────────────────────────────────────────────────────────────────────────────
# ETIQUETAS
# ─────────────────────────────────────────────────────────────────────────────
DELITOS_MAP = {
    "P59_A": "Hurto al establecimiento",
    "P59_B": "Hurto a empleados/dueño",
    "P59_C": "Extorsión",
    "P59_D": "Vandalismo",
    "P59_E": "Delitos informáticos",
    "P59_F": "Acoso / Amenazas",
    "P59_G": "Estafa / Fraude",
    "P59_H": "Delitos sexuales",
    "P59_I": "Otro delito",
}
DEL_COLS = list(DELITOS_MAP.keys())

MEDIDAS_MAP = {
    "P61A_1": "Alarmas de seguridad",
    "P61A_3": "Seguridad privada",
    "P61A_4": "Frentes de seguridad",
    "P61A_5": "Cámaras de seguridad",
    "P61A_6": "Ciberseguridad",
    "P61A_7": "App / Herramienta móvil",
    "P61A_9": "Otra medida",
}
MED_COLS_REAL = list(MEDIDAS_MAP.keys())


# ─────────────────────────────────────────────────────────────────────────────
# GRÁFICO 1 — KPIs ejecutivos
# ─────────────────────────────────────────────────────────────────────────────
def _graf_kpis(df: pd.DataFrame):
    N        = len(df)
    N_vic    = int(df["Victima_bin"].sum())
    tasa     = N_vic / N * 100
    vic_df   = df[df["Victima_bin"] == 1]
    tasa_den = (vic_df["P60"] == 1).sum() / len(vic_df) * 100 if len(vic_df) else 0

    col1, col2, col3, col4 = st.columns(4)
    for col, val, label, color, icon in [
        (col1, f"{tasa:.1f}%",         "Tasa de victimización",       DANGER,  "🔴"),
        (col2, f"{N_vic:,}",           f"Empresas víctimas (de {N:,})", ACCENT1, "🏢"),
        (col3, f"{tasa_den:.1f}%",     "Tasa de denuncia",            WARN,    "📋"),
        (col4, f"{100-tasa_den:.1f}%", "Sub-reporte (no denuncia)",   NEUTRAL, "🔕"),
    ]:
        with col:
            st.markdown(
                f"""
                <div style="background:{color};border-radius:10px;padding:18px 12px;
                            text-align:center;color:white;min-height:100px">
                  <div style="font-size:28px;font-weight:700">{icon} {val}</div>
                  <div style="font-size:12px;opacity:.9;margin-top:6px">{label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ─────────────────────────────────────────────────────────────────────────────
# GRÁFICO 2 — Victimización por sector
# ─────────────────────────────────────────────────────────────────────────────
def _graf_sector(df: pd.DataFrame):
    N    = len(df)
    tasa = df["Victima_bin"].sum() / N * 100

    vic = (
        df.groupby("Sector")["Victima_bin"]
        .mean().reset_index()
        .rename(columns={"Victima_bin": "pct"})
    )
    vic["pct"]   *= 100
    vic["color"]  = vic["pct"].apply(lambda p: DANGER if p > tasa else (WARN if p > tasa * 0.85 else SUCCESS))
    vic["texto"]  = vic["pct"].apply(lambda p: f"{p:.1f}%")

    fig = go.Figure(go.Bar(
        x=vic["pct"], y=vic["Sector"], orientation="h",
        marker_color=vic["color"],
        text=vic["texto"], textposition="outside",
        hovertemplate="<b>%{y}</b><br>Victimización: %{x:.1f}%<extra></extra>",
    ))
    fig.add_vline(x=tasa, line_dash="dash", line_color=DANGER, opacity=0.6,
                  annotation_text=f"Promedio {tasa:.1f}%", annotation_position="top right")
    fig.update_layout(**PLOTLY_LAYOUT,
        title="Victimización por sector económico",
        xaxis_title="Tasa de victimización (%)",
        xaxis_range=[0, vic["pct"].max() * 1.3],
        showlegend=False, height=280)
    st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# GRÁFICO 3 — Victimización por tamaño
# ─────────────────────────────────────────────────────────────────────────────
def _graf_tamano(df: pd.DataFrame):
    N    = len(df)
    tasa = df["Victima_bin"].sum() / N * 100

    ORDER = ["Microempresa", "Pequeña", "Mediana", "Grande"]
    vic = (
        df.groupby("Tamaño")["Victima_bin"]
        .mean().reindex(ORDER).reset_index()
        .rename(columns={"Victima_bin": "pct"})
    )
    vic["pct"]   *= 100
    vic["color"]  = vic["pct"].apply(lambda p: DANGER if p > tasa * 1.1 else (WARN if p > tasa * 0.9 else SUCCESS))
    vic["texto"]  = vic["pct"].apply(lambda p: f"{p:.1f}%")

    fig = go.Figure(go.Bar(
        x=vic["Tamaño"], y=vic["pct"],
        marker_color=vic["color"],
        text=vic["texto"], textposition="outside",
        hovertemplate="<b>%{x}</b><br>Victimización: %{y:.1f}%<extra></extra>",
    ))
    fig.add_hline(y=tasa, line_dash="dash", line_color=DANGER, opacity=0.6,
                  annotation_text=f"Promedio {tasa:.1f}%", annotation_position="top right")
    fig.update_layout(**PLOTLY_LAYOUT,
        title="Victimización por tamaño de empresa",
        yaxis_title="Tasa de victimización (%)",
        yaxis_range=[0, vic["pct"].max() * 1.3],
        showlegend=False, height=280)
    st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# GRÁFICO 4 — Ranking de delitos
# ─────────────────────────────────────────────────────────────────────────────
def _graf_delitos(df: pd.DataFrame):
    vic_df = df[df["Victima_bin"] == 1]
    N_vic  = len(vic_df)
    cols   = [c for c in DEL_COLS if c in df.columns]

    totals = (
        vic_df[cols].sum().rename(DELITOS_MAP)
        .reset_index().rename(columns={"index": "Delito", 0: "N"})
        .sort_values("N")
    )
    totals["pct"]   = (totals["N"] / N_vic * 100).round(1)
    totals["texto"] = totals.apply(lambda r: f"{int(r['N'])}  ({r['pct']}%)", axis=1)
    totals["color"] = px.colors.sample_colorscale(
        "RdYlGn_r", [i / max(len(totals) - 1, 1) for i in range(len(totals))]
    )

    fig = go.Figure(go.Bar(
        x=totals["N"], y=totals["Delito"], orientation="h",
        marker_color=totals["color"],
        text=totals["texto"], textposition="outside",
        hovertemplate="<b>%{y}</b><br>Empresas afectadas: %{x}<extra></extra>",
    ))
    fig.update_layout(**PLOTLY_LAYOUT,
        title="Delitos más frecuentes en empresas víctimas",
        xaxis_title="N° de empresas afectadas",
        xaxis_range=[0, totals["N"].max() * 1.35],
        showlegend=False, height=380)
    st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# GRÁFICO 5 — Percepción de seguridad (pie + barras)
# ─────────────────────────────────────────────────────────────────────────────
def _graf_percepcion(df: pd.DataFrame):
    ORDER_P  = ["Mejoró", "Igual", "Empeoró"]
    counts_p = df["Percepcion"].value_counts()
    vals_p   = [counts_p.get(k, 0) for k in ORDER_P]

    SEG_ORDER  = ["Muy inseguro", "Inseguro", "Ni/Ni", "Seguro", "Muy seguro"]
    counts_s   = df["Seguridad"].value_counts()
    vals_s     = [counts_s.get(k, 0) for k in SEG_ORDER]
    colors_seg = [DANGER, "#E67E22", NEUTRAL, ACCENT2, SUCCESS]

    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "pie"}, {"type": "bar"}]],
        subplot_titles=("¿Mejoró o empeoró vs 2023?", "¿Bogotá es segura para negocios?"),
    )
    fig.add_trace(go.Pie(
        labels=ORDER_P, values=vals_p,
        marker_colors=[SUCCESS, NEUTRAL, DANGER],
        hole=0.35, textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>%{value} empresas (%{percent})<extra></extra>",
    ), row=1, col=1)
    fig.add_trace(go.Bar(
        x=vals_s, y=SEG_ORDER, orientation="h",
        marker_color=colors_seg,
        text=vals_s, textposition="outside",
        hovertemplate="<b>%{y}</b><br>%{x} empresas<extra></extra>",
    ), row=1, col=2)
    fig.update_layout(**PLOTLY_LAYOUT, showlegend=False, height=340)
    fig.update_xaxes(title_text="N° de empresas", row=1, col=2)
    st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# GRÁFICO 6 — Adopción de medidas de prevención
# ─────────────────────────────────────────────────────────────────────────────
def _graf_medidas(df: pd.DataFrame):
    adoption = {
        label: round(df[col].mean() * 100, 1)
        for col, label in MEDIDAS_MAP.items() if col in df.columns
    }
    ser = (
        pd.Series(adoption).reset_index()
        .rename(columns={"index": "Medida", 0: "pct"})
        .sort_values("pct")
    )
    ser["color"] = ser["pct"].apply(lambda v: SUCCESS if v > 30 else (WARN if v > 15 else NEUTRAL))
    ser["texto"] = ser["pct"].apply(lambda v: f"{v:.1f}%")

    fig = go.Figure(go.Bar(
        x=ser["pct"], y=ser["Medida"], orientation="h",
        marker_color=ser["color"],
        text=ser["texto"], textposition="outside",
        hovertemplate="<b>%{y}</b><br>Adopción: %{x:.1f}%<extra></extra>",
    ))
    for umbral, etiqueta, color in [(15, "15% — baja", NEUTRAL), (30, "30% — media", WARN)]:
        fig.add_vline(x=umbral, line_dash="dot", line_color=color, opacity=0.5,
                      annotation_text=etiqueta, annotation_position="top")
    fig.update_layout(**PLOTLY_LAYOUT,
        title="¿Qué medidas de seguridad usan las empresas?",
        xaxis_title="% de empresas que adoptaron la medida",
        xaxis_range=[0, ser["pct"].max() * 1.3],
        showlegend=False, height=340)
    st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# GRÁFICO 7 — Heatmap IRE
# ─────────────────────────────────────────────────────────────────────────────
def _graf_ire(df: pd.DataFrame):
    ire_rows = []
    for sector in ["Industria", "Comercio", "Servicios"]:
        for tam in ["Microempresa", "Pequeña", "Mediana", "Grande"]:
            sub = df[(df["Sector"] == sector) & (df["Tamaño"] == tam)]
            if len(sub) < 5:
                continue
            tv  = sub["Victima_bin"].mean()
            td  = (sub[sub["Victima_bin"] == 1]["P60"] == 1).mean() if sub["Victima_bin"].sum() > 0 else 0
            tp  = (sub["P57"] == 3).mean()
            ire = 0.5 * tv + 0.3 * (1 - td) + 0.2 * tp
            ire_rows.append({
                "Sector": sector, "Tamaño": tam, "IRE": round(ire, 3),
                "N": len(sub),
                "Victimización": f"{tv*100:.1f}%",
                "Denuncia": f"{td*100:.1f}%",
                "Percep. neg.": f"{tp*100:.1f}%",
            })

    ire_df  = pd.DataFrame(ire_rows)
    ORDER_T = [c for c in ["Microempresa","Pequeña","Mediana","Grande"] if c in ire_df["Tamaño"].values]
    ORDER_S = [s for s in ["Industria","Comercio","Servicios"]          if s in ire_df["Sector"].values]

    pivot   = ire_df.pivot(index="Sector", columns="Tamaño", values="IRE").reindex(index=ORDER_S, columns=ORDER_T)

    # Tooltip enriquecido por celda
    custom = []
    for sector in ORDER_S:
        row = []
        for tam in ORDER_T:
            sub_row = ire_df[(ire_df["Sector"] == sector) & (ire_df["Tamaño"] == tam)]
            if sub_row.empty:
                row.append("Sin datos suficientes")
            else:
                r = sub_row.iloc[0]
                row.append(
                    f"<b>{sector} / {tam}</b><br>"
                    f"IRE: {r['IRE']}<br>"
                    f"N empresas: {int(r['N'])}<br>"
                    f"Victimización: {r['Victimización']}<br>"
                    f"Tasa denuncia: {r['Denuncia']}<br>"
                    f"Percepción neg.: {r['Percep. neg.']}"
                )
        custom.append(row)

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=ORDER_T, y=ORDER_S,
        colorscale=[[0, "#1A5276"], [0.5, "#F39C12"], [1, "#C0392B"]],
        zmin=0.25, zmax=0.70,
        text=pivot.values.round(3),
        texttemplate="%{text}",
        textfont={"size": 14, "color": "white"},
        customdata=custom,
        hovertemplate="%{customdata}<extra></extra>",
        colorbar=dict(
            title="IRE",
            tickvals=[0.25, 0.40, 0.55, 0.70],
            ticktext=["0.25 (bajo)", "0.40", "0.55", "0.70 (alto)"],
        ),
    ))
    fig.update_layout(**PLOTLY_LAYOUT,
        title="Índice de Riesgo Empresarial (IRE) por sector y tamaño",
        xaxis_title="Tamaño de empresa",
        yaxis_title="Sector",
        height=300)
    st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# FUNCIÓN PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────
def render_seccion_seguridad(df_raw: pd.DataFrame):
    """
    Renderiza la sección completa de Seguridad Empresarial en Streamlit.

    Uso
    ───
        from seccion_seguridad import render_seccion_seguridad
        render_seccion_seguridad(pd.read_excel("ruta/archivo.xlsx"))
    """
    with st.spinner("Procesando datos de seguridad…"):
        df = _preparar_datos(df_raw)

    N     = len(df)
    N_vic = int(df["Victima_bin"].sum())
    tasa  = N_vic / N * 100

    st.markdown("## 🛡️ Seguridad Empresarial · ECN 2024")
    st.markdown(
        f"Resultados basados en **{N:,} empresas** encuestadas por la "
        f"Cámara de Comercio de Bogotá. "
        f"**{N_vic:,}** reportaron al menos un delito en 2024 "
        f"(**{tasa:.1f}%** de la muestra)."
    )
    st.divider()

    st.markdown("### 📊 Indicadores clave")
    _graf_kpis(df)
    st.caption("El **sub-reporte** mide la proporción de víctimas que NO radicaron denuncia.")
    st.divider()

    st.markdown("### 🏭 ¿Quiénes son más afectados?")
    col_a, col_b = st.columns(2)
    with col_a:
        _graf_sector(df)
    with col_b:
        _graf_tamano(df)
    st.caption("🔴 Rojo = supera el promedio · 🟡 Amarillo = cercano · 🟢 Verde = por debajo.")
    st.divider()

    st.markdown("### 🔎 Tipos de delito más frecuentes")
    _graf_delitos(df)
    st.caption("Una empresa puede haber sufrido más de un tipo de delito.")
    st.divider()

    st.markdown("### 💬 Percepción de seguridad")
    _graf_percepcion(df)
    st.caption("Izquierda: tendencia vs año anterior. Derecha: valoración del entorno actual.")
    st.divider()

    st.markdown("### 🔐 Medidas de seguridad adoptadas")
    _graf_medidas(df)
    st.caption("Pregunta de respuesta múltiple — los porcentajes no suman 100%.")
    st.divider()

    st.markdown("### ⚠️ Índice de Riesgo Empresarial (IRE)")
    st.info(
        "El **IRE** combina: victimización (50%), sub-reporte (30%) y percepción negativa (20%). "
        "Pasa el cursor sobre cada celda para ver el detalle completo.",
        icon="ℹ️",
    )
    _graf_ire(df)
    st.caption("🔴 Rojo = mayor riesgo · 🔵 Azul = menor riesgo relativo.")

    st.success(
        f"✅ Análisis completado · {N:,} empresas · {N_vic:,} víctimas ({tasa:.1f}%)",
        icon="✅",
    )