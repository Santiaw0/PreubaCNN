# src/graficos.py
"""
graficos.py
───────────
Todas las funciones que generan gráficos Plotly.
Cada función recibe datos limpios y devuelve una figura o la renderiza
directamente con st.plotly_chart().
No contiene lógica de limpieza ni imports de Streamlit de navegación.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from streamlit import success

from src.preprocesamiento import (
    LABELS_P204, LABELS_LOCALIDAD, LABELS_SEXO,
    DELITOS_MAP_ECN, DEL_COLS_ECN, MEDIDAS_MAP_ECN, MED_COLS_ECN,
    COLS_P204, DELITOS_EMPRESAS,
)

# ── Paleta y layout base ──────────────────────────────────────────────────────

PRIMARY  = '#0D1B2A'
ACCENT1  = '#1B4F72'
ACCENT2  = '#2E86AB'
ACCENT3  = '#56B4D3'
DANGER   = '#E74C3C'
WARN     = '#F39C12'
SUCCESS  = '#27AE60'
NEUTRAL  = '#95A5A6'
LIGHT_BG = '#F0F4F8'
GOLD     = '#F1C40F'

HOMBRE   = "#9CACD5"
MUJER    = "#CA2A93"

BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="white",
    font=dict(family="Arial", color=PRIMARY),
    margin=dict(l=20, r=20, t=50, b=20),
    hoverlabel=dict(bgcolor="white", font_size=13),
)


# ═════════════════════════════════════════════════════════════════════════════
# GRÁFICOS ECN — Clima de Negocios
# ═════════════════════════════════════════════════════════════════════════════

def kpis_ecn(df: pd.DataFrame):
    """4 tarjetas KPI: victimización, víctimas, denuncia, sub-reporte."""
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
                f"""<div style="background:{color};border-radius:10px;padding:18px 12px;
                               text-align:center;color:white;min-height:100px">
                      <div style="font-size:26px;font-weight:700">{icon} {val}</div>
                      <div style="font-size:12px;opacity:.9;margin-top:6px">{label}</div>
                    </div>""",
                unsafe_allow_html=True,
            )


def barras_sector(df: pd.DataFrame):
    tasa = df["Victima_bin"].sum() / len(df) * 100
    vic  = df.groupby("Sector")["Victima_bin"].mean().reset_index()
    vic["pct"]   = vic["Victima_bin"] * 100
    vic = df.groupby("Sector")["Victima_bin"].mean().reset_index()
    vic["pct"] = vic["Victima_bin"] * 100

    vic = vic.sort_values("pct", ascending=True)
    fig = go.Figure(go.Bar(
        x=vic["pct"],
        y=vic["Sector"],
        orientation="h",
        marker=dict(
            color=vic["pct"],
            colorscale="RdYlGn_r",
            showscale= False
        ),
        text=vic["pct"].round(1).astype(str)+"%", textposition="outside",
        hovertemplate="<b>%{y}</b><br>Victimización: %{x:.1f}%<extra></extra>",
    ))
    fig.update_layout(**BASE, title="Victimización por sector",
                      xaxis_range=[0, vic["pct"].max()*1.3], showlegend=False, height=280)
    st.plotly_chart(fig, use_container_width=True)


def barras_tamano(df: pd.DataFrame):
    tasa  = df["Victima_bin"].sum() / len(df) * 100
    ORDER = ["Microempresa","Pequeña","Mediana","Grande"]
    vic   = df.groupby("Tamaño")["Victima_bin"].mean().reindex(ORDER).reset_index()
    vic["pct"]   = vic["Victima_bin"] * 100
    vic["color"] = vic["pct"].apply(
        lambda p: "#E74C3C" if p > tasa * 1.1 else ("#F39C12" if p > tasa * .9 else "#27AE60")
    )
    colores = {
        "Microempresa": ACCENT1,
        "Pequeña": NEUTRAL,
        "Mediana": WARN,
        "Grande": DANGER
    }

    fig = go.Figure(go.Bar(
        x=vic["Tamaño"],
        y=vic["pct"],
        marker_color=vic["Tamaño"].map(colores),
        text=vic["pct"].round(1).astype(str) + "%",
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Victimización: %{y:.1f}%<extra></extra>",
    ))
    fig.update_layout(**BASE, title="Victimización por tamaño",
                      yaxis_range=[0, vic["pct"].max()*1.3], showlegend=False, height=280)
    st.plotly_chart(fig, use_container_width=True)


def barras_delitos_ecn(df: pd.DataFrame):
    vic_df = df[df["Victima_bin"] == 1]
    N_vic  = len(vic_df)
    cols   = [c for c in DEL_COLS_ECN if c in df.columns]
    totals = vic_df[cols].sum().rename(DELITOS_MAP_ECN).reset_index()
    totals.columns = ["Delito","N"]
    totals = totals.sort_values("N")
    totals["pct"]    = (totals["N"] / N_vic * 100).round(1)
    totals["texto"] = totals["pct"].astype(str) + "%"
    colores = px.colors.sample_colorscale(
        "RdYlGn_r", [i/max(len(totals)-1,1) for i in range(len(totals))]
    )
    fig = go.Figure(go.Bar(
        x=totals["N"], y=totals["Delito"], orientation="h",
        marker_color=colores,
        text=totals["texto"], textposition="outside",
        hovertemplate="<b>%{y}</b><br>Empresas: %{x}<extra></extra>",
    ))
    fig.update_layout(**BASE, title="Delitos más frecuentes (empresas víctimas)",
                      xaxis_range=[0, totals["N"].max()*1.35], showlegend=False, height=380)
    st.plotly_chart(fig, use_container_width=True)


def pie_percepcion_ecn(df: pd.DataFrame):

    ORDER_P  = ["Mejoró","Igual","Empeoró"]
    counts_p = df["Percepcion"].value_counts()
    vals_p   = [counts_p.get(k,0) for k in ORDER_P]

    SEG_ORDER  = ["Muy inseguro","Inseguro","Ni/Ni","Seguro","Muy seguro"]
    counts_s   = df["Seguridad"].value_counts()
    vals_s     = [counts_s.get(k,0) for k in SEG_ORDER]

    # dataframe para ordenar barras
    seg_df = pd.DataFrame({
        "seg": SEG_ORDER,
        "vals": vals_s
    })

    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type":"pie"},{"type":"bar"}]],
        subplot_titles=(
            "¿Mejoró o empeoró vs 2023?",
            "¿Bogotá es segura para negocios?"
        )
    )

    # PIE
    fig.add_trace(
        go.Pie(
            labels=ORDER_P,
            values=vals_p,
            hole=.4,
            marker_colors=[
                SUCCESS,  # mejoró (verde)
                NEUTRAL,  # igual (gris)
                DANGER   # empeoró (rojo)
            ],
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>%{value} empresas<extra></extra>"
        ),
        row=1, col=1
    )

    # BARRAS ORDENADAS
    fig.add_trace(
        go.Bar(
            x=seg_df["seg"],
            y=seg_df["vals"],
            marker_color=["#C0392B",
                          "#E67E22",
                          NEUTRAL,
                          "#7DCEA0",
                          "#27AE60"],
            text=seg_df["vals"],
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>%{x} empresas<extra></extra>"
        ),
        row=1, col=2
    )

    fig.update_layout(**BASE, showlegend=False, height=340)
    fig.update_xaxes(title_text="Percepción", row=1, col=2)

    st.plotly_chart(fig, use_container_width=True)

def barras_medidas(df: pd.DataFrame):
    adoption = {label: round(df[col].mean()*100,1)
                for col, label in MEDIDAS_MAP_ECN.items() if col in df.columns}
    ser = pd.Series(adoption).reset_index().rename(columns={"index":"Medida",0:"pct"})
    ser = ser.sort_values("pct")
    colores = px.colors.sample_colorscale(
        "RdYlGn_r", [i / max(len(ser) - 1, 1) for i in range(len(ser))]
    )

    fig = go.Figure(go.Bar(
        x=ser["pct"], y=ser["Medida"], orientation="h",
        marker_color=colores,
        text=ser["pct"].astype(str)+"%", textposition="outside",
        hovertemplate="<b>%{y}</b><br>Adopción: %{x:.1f}%<extra></extra>",
    ))

    fig.update_layout(**BASE, title="Medidas de seguridad adoptadas",
                      xaxis_range=[0, ser["pct"].max()*1.3], showlegend=False, height=320)
    st.plotly_chart(fig, use_container_width=True)


# ═════════════════════════════════════════════════════════════════════════════
# GRÁFICOS EPV — Percepción y Victimización
# ═════════════════════════════════════════════════════════════════════════════

def kpis_epv(df_uniq: pd.DataFrame, ids_den: set):
    N          = len(df_uniq)
    N_vic      = int((df_uniq["P203"]==1).sum())
    tasa_vic   = N_vic/N*100 if N else 0
    vic_ids    = set(df_uniq[df_uniq["P203"]==1]["ID"])
    perc_ciudad= df_uniq["P103_1"].mean() if "P103_1" in df_uniq.columns else 0

    col1,col2,col3 = st.columns(3)
    for col,val,label,color,icon in [
        (col1,f"{tasa_vic:.1f}%",       "Tasa de victimización",         DANGER, "🔴"),
        (col2,f"{N_vic:,}",             f"Personas víctimas (de {N:,})",  ACCENT1,"👤"),
        (col3,f"{perc_ciudad:.2f} / 5", "Percepción seg. ciudad (prom.)",ACCENT2,"🏙️"),
    ]:
        with col:
            st.markdown(
                f"""<div style="background:{color};border-radius:10px;padding:18px 12px;
                               text-align:center;color:white;min-height:100px">
                      <div style="font-size:26px;font-weight:700">{icon} {val}</div>
                      <div style="font-size:12px;opacity:.9;margin-top:6px">{label}</div>
                    </div>""",
                unsafe_allow_html=True,
            )

def delitos_empresariales_epv(df_raw: pd.DataFrame):
    df_bog = df_raw[df_raw["MUNICIPIO"]==11001].copy() if "MUNICIPIO" in df_raw.columns else df_raw.copy()
    cols_p = {col:val for col,val in COLS_P204.items() if col in df_bog.columns}
    resultado = {LABELS_P204[cod]: int((df_bog[col]==1).sum())
                 for col,cod in cols_p.items()
                 if (df_bog[col]==1).sum()>0 and cod in DELITOS_EMPRESAS}
    if not resultado:
        st.info("No se encontraron datos de delitos empresariales."); return

    ser   = pd.Series(resultado).sort_values()
    n_vic = int((df_bog["P203"]==1).sum()) if "P203" in df_bog.columns else 1
    pct   = (ser/n_vic*100).round(1)
    texto = [f"{int(v)}  ({p}%)" for v,p in zip(ser.values,pct.values)]
    colores = px.colors.sample_colorscale("RdYlGn_r",[i/max(len(ser)-1,1) for i in range(len(ser))])

    fig = go.Figure(go.Bar(
        x=ser.values, y=ser.index, orientation="h",
        marker_color=colores, text=texto, textposition="outside",
        hovertemplate="<b>%{y}</b><br>%{x:,} víctimas<extra></extra>",
    ))
    fig.update_layout(**BASE, title="Delitos relevantes para el entorno empresarial (Bogotá)",
                      xaxis_range=[0,ser.max()*1.35], showlegend=False, height=340)
    st.plotly_chart(fig, use_container_width=True)


def percepcion_barrio_ciudad(df_uniq: pd.DataFrame):
    colores_esc = [DANGER,"#E67E22",NEUTRAL,ACCENT2,SUCCESS]
    fig = make_subplots(rows=1,cols=2,
                        subplot_titles=("Percepción seguridad del barrio (1-5)",
                                        "Percepción seguridad de Bogotá (1-5)"))
    for col_var,col_idx in [("P102_1",1),("P103_1",2)]:
        if col_var not in df_uniq.columns: continue
        counts = df_uniq[col_var].value_counts().sort_index()
        total  = counts.sum()
        fig.add_trace(go.Bar(
            x=[str(int(k)) for k in counts.index], y=counts.values,
            marker_color=colores_esc[:len(counts)],
            text=[f"{v/total*100:.1f}%" for v in counts.values], textposition="outside",
            hovertemplate="<b>Nivel %{x}</b><br>%{y:,} encuestados<extra></extra>",
        ), row=1, col=col_idx)
    fig.update_layout(**BASE, showlegend=False, height=330)
    fig.update_xaxes(title_text="1=Muy inseguro → 5=Muy seguro")
    fig.update_xaxes(range=[0, 5.5], row=1, col=1)
    fig.update_xaxes(range=[0, 5.5], row=1, col=2)

    st.plotly_chart(fig, use_container_width=True)


def denuncia_y_satisfaccion(df_uniq: pd.DataFrame):
    colores_esc = [DANGER, "#E67E22", NEUTRAL, ACCENT2, SUCCESS]

    # ── Datos ─────────────────────────────────────────────────────────────
    # Pie: ¿acudió a la policía?
    counts_p417 = df_uniq["P417"].map({1: "Sí acudió", 2: "No acudió"}).value_counts()

    # Barras: satisfacción — solo quienes acudieron (P417==1)
    sat = (df_uniq[df_uniq["P417"] == 1]["P421"]
           .dropna().value_counts().sort_index())

    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "pie"}, {"type": "bar"}]],
        subplot_titles=(
            "¿Acudió a la Policía en 2024?",
            "Satisfacción con la atención policial\n(solo quienes acudieron)",
        ),
    )

    fig.add_trace(go.Pie(
        labels=counts_p417.index, values=counts_p417.values,
        marker_colors=[ACCENT2, NEUTRAL],
        hole=0.38, textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>%{value:,} personas (%{percent})<extra></extra>",
    ), row=1, col=1)

    total_sat = sat.sum()
    fig.add_trace(go.Bar(
        x=sat.index.astype(str), y=sat.values,
        marker_color=colores_esc[:len(sat)],
        text=[f"{v/total_sat*100:.1f}%" for v in sat.values],
        textposition="outside",
        hovertemplate="<b>Nivel %{x}</b><br>%{y:,} personas<extra></extra>",
    ), row=1, col=2)

    fig.update_layout(**BASE, showlegend=False, height=360)
    fig.update_xaxes(title_text="1=Pésimo → 5=Excelente",
                     range=[0, 5.8], row=1, col=2)
    fig.update_yaxes(title_text="N° personas", row=1, col=2)
    st.plotly_chart(fig, use_container_width=True)


# ═════════════════════════════════════════════════════════════════════════════
# GRÁFICOS RIESGO LOCAL — análisis por localidad seleccionada en el mapa
# ═════════════════════════════════════════════════════════════════════════════

def detalle_localidad(loc_cod: int, loc_nom: str,
                      df_uniq: pd.DataFrame, p204_long: pd.DataFrame, CAIS):
    """4 gráficas para la localidad clickeada en el mapa."""
    df_loc = df_uniq[df_uniq["LOCALIDAD"] == loc_cod].copy()
    if df_loc.empty:
        st.warning(f"No hay datos EPV para {loc_nom}."); return

    N_loc = len(df_loc)
    N_vic = int((df_loc["P203"]==1).sum())
    tasa  = N_vic/N_loc*100 if N_loc else 0

    # KPIs rápidos
    c1,c2,c3 = st.columns(3)
    c1.metric("Encuestados", f"{N_loc:,}")
    c2.metric("Víctimas", f"{N_vic:,}  ({tasa:.1f}%)")
    if "P103_1" in df_loc.columns:
        c3.metric("Percepción seg. ciudad", f"{df_loc['P103_1'].mean():.2f} / 5")

    st.markdown("---")
    col_a, col_b = st.columns(2)

    # ── Top delitos ───────────────────────────────────────────────────────
    with col_a:
        ids_loc = set(df_loc["ID"])
        del_loc = p204_long[p204_long["ID"].isin(ids_loc)].drop_duplicates(["ID","P204"])
        if not del_loc.empty:
            conteo  = (del_loc.groupby("P204")["ID"].nunique()
                       .rename(LABELS_P204).sort_values(ascending=True).tail(8))
            colores = px.colors.sample_colorscale("RdYlGn_r",[i/max(len(conteo)-1,1) for i in range(len(conteo))])
            fig = go.Figure(go.Bar(
                x=conteo.values, y=conteo.index, orientation="h",
                marker_color=colores, text=conteo.values, textposition="outside",
                hovertemplate="<b>%{y}</b><br>%{x} víctimas<extra></extra>",
            ))
            fig.update_layout(**BASE, title=dict(
                    text=f"Delitos Más Recurrentes · {loc_nom}"
                         "<br><span style='color:gray;font-size:12px'>Frecuencia</span>"
                ),
                              showlegend=False, height=320)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin datos de delitos para esta localidad.")

    # ── Percepción por género ─────────────────────────────────────────────
    with col_b:
        if "P103_1" in df_loc.columns:
            pg = (df_loc.groupby("SEXO_NOM")["P103_1"]
                  .agg(["mean","count"]).reset_index()
                  .rename(columns={"mean":"prom","count":"n"}))
            fig2 = go.Figure(go.Bar(
                x=pg["SEXO_NOM"], y=pg["prom"],
                marker_color=[HOMBRE if s=="Hombre" else MUJER for s in pg["SEXO_NOM"]],
                text=pg["prom"].round(2), textposition="outside",
                customdata=pg["n"],
                hovertemplate="<b>%{x}</b><br>Percepción: %{y:.2f}/5<br>N: %{customdata}<extra></extra>",
            ))
            fig2.update_layout(
                **BASE,
                title=dict(
                    text=f"Percepción seg. por género · {loc_nom}"
                         "<br><span style='color:gray;font-size:12px'>Promedio Precepción de 1 a 5</span>"
                ),
                yaxis_range=[0, 5.5],
                showlegend=False,
                height=320
            )
            st.plotly_chart(fig2, use_container_width=True)

    col_c, col_d = st.columns(2)

    # ── Victimización por género ──────────────────────────────────────────
    with col_c:
        tg = (df_loc.groupby("SEXO_NOM")["P203"]
              .apply(lambda x: (x==1).mean()*100).reset_index()
              .rename(columns={"P203":"tasa"}))
        fig3 = go.Figure(go.Bar(
            x=tg["SEXO_NOM"], y=tg["tasa"],
            marker_color=[HOMBRE if s=="Hombre" else MUJER for s in tg["SEXO_NOM"]],
            text=tg["tasa"].round(1).astype(str)+"%", textposition="outside",
            hovertemplate="<b>%{x}</b><br>Victimización: %{y:.1f}%<extra></extra>",
        ))
        fig3.update_layout(**BASE, title=dict(
                    text=f"Victimización por Genero · {loc_nom}"
                         "<br><span style='color:gray;font-size:12px'>Porcentaje(%)</span>"
                ),
                yaxis_range=[0,tg["tasa"].max()*1.35], showlegend=False, height=300)
        st.plotly_chart(fig3, use_container_width=True)

    # ── CAIs de la localidad ──────────────────────────────────────────────
    with col_d:
        cais_loc = CAIS[CAIS["CAIIULOCAL"].apply(lambda x: int(str(x).lstrip("0") or "0")) == loc_cod]
        st.metric("CAIs en la localidad", len(cais_loc))



def percepcion_ciudad(df_uniq: pd.DataFrame):
    labels_p103 = {1: "Seguro", 2: "Inseguro"}

    counts = (
        df_uniq["P103"]
        .map(labels_p103)
        .value_counts()
    )

    fig = go.Figure(go.Pie(
        labels=counts.index,
        values=counts.values,
        marker_colors=[SUCCESS, DANGER],
        hole=0.38,
        textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>%{value:,} encuestados (%{percent})<extra></extra>",
    ))

    fig.update_layout(**BASE,
        title="Percepción de seguridad de Bogotá",
        showlegend=True,
        height=340,
    )
    st.plotly_chart(fig, use_container_width=True)




########################################
##  BACANO
########################################

def heatmap_ire(df: pd.DataFrame):
    rows = []
    for sector in ["Industria","Comercio","Servicios"]:
        for tam in ["Microempresa","Pequeña","Mediana","Grande"]:
            sub = df[(df["Sector"]==sector) & (df["Tamaño"]==tam)]
            if len(sub) < 5: continue
            tv  = sub["Victima_bin"].mean()
            td  = (sub[sub["Victima_bin"]==1]["P60"]==1).mean() if sub["Victima_bin"].sum()>0 else 0
            tp  = (sub["P57"]==3).mean()
            ire = 0.5*tv + 0.3*(1-td) + 0.2*tp
            rows.append({"Sector":sector,"Tamaño":tam,"IRE":round(ire,3),
                         "N":len(sub),"Victimización":f"{tv*100:.1f}%",
                         "Denuncia":f"{td*100:.1f}%","Percep.neg.":f"{tp*100:.1f}%"})

    ire_df  = pd.DataFrame(rows)
    ORDER_T = [c for c in ["Microempresa","Pequeña","Mediana","Grande"] if c in ire_df["Tamaño"].values]
    ORDER_S = [s for s in ["Industria","Comercio","Servicios"]          if s in ire_df["Sector"].values]
    pivot   = ire_df.pivot(index="Sector", columns="Tamaño", values="IRE").reindex(index=ORDER_S, columns=ORDER_T)

    custom = []
    for sector in ORDER_S:
        row = []
        for tam in ORDER_T:
            r = ire_df[(ire_df["Sector"]==sector)&(ire_df["Tamaño"]==tam)]
            row.append("Sin datos" if r.empty else
                       f"<b>{sector}/{tam}</b><br>IRE:{r.iloc[0]['IRE']}<br>"
                       f"N:{int(r.iloc[0]['N'])}<br>Vic:{r.iloc[0]['Victimización']}<br>"
                       f"Den:{r.iloc[0]['Denuncia']}<br>Perc.neg:{r.iloc[0]['Percep.neg.']}")
        custom.append(row)

    fig = go.Figure(go.Heatmap(
        z=pivot.values, x=ORDER_T, y=ORDER_S,
        colorscale=[[0,"#1A5276"],[.5,"#F39C12"],[1,"#C0392B"]],
        zmin=.25, zmax=.70,
        text=pivot.values.round(3), texttemplate="%{text}",
        textfont={"size":14,"color":"white"},
        customdata=custom,
        hovertemplate="%{customdata}<extra></extra>",
        colorbar=dict(title="IRE", tickvals=[.25,.40,.55,.70],
                      ticktext=["0.25 (bajo)","0.40","0.55","0.70 (alto)"]),
    ))
    fig.update_layout(**BASE, title="Índice de Riesgo Empresarial (IRE)",
                      xaxis_title="Tamaño", yaxis_title="Sector", height=300)
    st.plotly_chart(fig, use_container_width=True)


# ═════════════════════════════════════════════════════════════════════════════
# BACANO — Barómetro Analítico de Comportamiento y Amenazas de Negocios
# Paleta "Bogotá Noir" — dark mode
# ═════════════════════════════════════════════════════════════════════════════

# Paleta Bogotá Noir
_BG_DARK = "#0A0E1A"
_BG_PANEL = "#111827"
_BG_CARD = "#1A2332"
_RED_HOT = "#FF2D55"
_ORANGE_W = "#FF6B35"
_GOLD_N = "#FFD700"
_TEAL_N = "#00C9B1"
_BLUE_SOFT = "#4FC3F7"
_WHITE_N = "#F0F4FF"
_GREY_MID = "#4A5568"
_GREY_PALE = "#A0AEC0"


def _calcular_bacano(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula el índice BACANO por perfil Sector × Tamaño. Solo Bogotá D.C. (REGION=1)."""
    import numpy as np
    rows = []
    for sector in ["Industria", "Comercio", "Servicios"]:
        for tam in ["Microempresa", "Pequeña", "Mediana", "Grande"]:
            sub = df[(df["Sector"] == sector) & (df["Tamaño"] == tam)]
            if len(sub) < 5:
                continue
            tv = sub["Victima_bin"].mean()
            td = (sub[sub["Victima_bin"] == 1]["P60"] == 1).mean() if sub["Victima_bin"].sum() > 0 else 0
            tp = (sub["P57"] == 3).mean()
            bac = 0.5 * tv + 0.3 * (1 - td) + 0.2 * tp
            rows.append({
                "Sector": sector, "Tamaño": tam,
                "BACANO": round(bac, 4), "N": len(sub),
                "TV": tv * 100, "TD": td * 100, "TPN": tp * 100,
                "comp_vic": 0.5 * tv,
                "comp_den": 0.3 * (1 - td),
                "comp_perc": 0.2 * tp,
            })
    return pd.DataFrame(rows)


def bacano_dashboard(df: pd.DataFrame):
    """
    Sección BACANO completa: heatmap de perfiles + simulador de política pública.
    Paleta dark mode "Bogotá Noir".
    """
    import numpy as np
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    bacano_df = _calcular_bacano(df)
    if bacano_df.empty:
        st.warning("No hay suficientes datos para calcular el BACANO.")
        return

    N = len(df)
    N_vic = int(df["Victima_bin"].sum())
    tv_m = df["Victima_bin"].mean()
    tpn_m = df["Percep_Negativa"].mean()
    vic_df = df[df["Victima_bin"] == 1]
    tasa_den = (vic_df["P60"] == 1).sum() / len(vic_df) * 100 if len(vic_df) else 0

    # ── Encabezado ────────────────────────────────────────────────────────
    st.markdown("#### Barómetro Analítico de Comportamiento y Amenazas de Negocios y Operaciones")
    st.caption("BACANO = 0.5 × Victimización + 0.3 × (1 – Denuncia) + 0.2 × Percepción negativa")

    # ── KPIs rápidos ──────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    DANGER = "#E74C3C"
    SUCCESS = "#27AE60"
    WARN = "#F39C12"
    ACCENT1 = "#1B4F72"
    for col, val, label, color, icon in [
        (c1, f"{tv_m * 100:.1f}%", "Victimización promedio", DANGER, "🔴"),
        (c2, f"{tasa_den:.1f}%", "Tasa de denuncia", WARN, "📋"),
        (c3, f"{tpn_m * 100:.1f}%", "Percepción negativa", ACCENT1, "💬"),
        (c4, f"{bacano_df['BACANO'].mean():.3f}", "BACANO promedio", SUCCESS, "📊"),
    ]:
        with col:
            st.markdown(
                f"""<div style="background:{color};border-radius:10px;padding:18px 12px;
                               text-align:center;color:white;min-height:100px">
                      <div style="font-size:26px;font-weight:700">{icon} {val}</div>
                      <div style="font-size:12px;opacity:.9;margin-top:6px">{label}</div>
                    </div>""",
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    col_a, col_b = st.columns([1.1, 1])

    # ── Panel A — Heatmap BACANO por Sector × Tamaño ─────────────────────
    with col_a:
        ORDER_S = ["Industria", "Comercio", "Servicios"]
        ORDER_T = ["Microempresa", "Pequeña", "Mediana", "Grande"]

        pivot = (bacano_df.pivot(index="Sector", columns="Tamaño", values="BACANO")
                 .reindex(index=ORDER_S, columns=ORDER_T))
        pivot_n = (bacano_df.pivot(index="Sector", columns="Tamaño", values="N")
                   .reindex(index=ORDER_S, columns=ORDER_T))

        z = pivot.values.tolist()
        text = []
        for i, sec in enumerate(ORDER_S):
            row_txt = []
            for j, tam in enumerate(ORDER_T):
                val = pivot.iloc[i, j] if not np.isnan(pivot.iloc[i, j]) else None
                n = int(pivot_n.iloc[i, j]) if val and not np.isnan(pivot_n.iloc[i, j]) else 0
                row_txt.append(f"{val:.3f}<br><span style='font-size:10px'>n={n}</span>" if val else "n/a")
            text.append(row_txt)

        # Tooltip enriquecido
        custom = []
        for sec in ORDER_S:
            row_c = []
            for tam in ORDER_T:
                r = bacano_df[(bacano_df["Sector"] == sec) & (bacano_df["Tamaño"] == tam)]
                if r.empty:
                    row_c.append("Sin datos")
                else:
                    r = r.iloc[0]
                    row_c.append(
                        f"<b>{sec} / {tam}</b><br>"
                        f"BACANO: {r['BACANO']}<br>"
                        f"N empresas: {int(r['N'])}<br>"
                        f"Victimización: {r['TV']:.1f}%<br>"
                        f"Denuncia: {r['TD']:.1f}%<br>"
                        f"Percep. neg.: {r['TPN']:.1f}%"
                    )
            custom.append(row_c)

        fig_hm = go.Figure(go.Heatmap(
            z=pivot.values,
            x=ORDER_T, y=ORDER_S,
            colorscale=[
                [0.0, "#EAF7EE"],
                [0.25, "#A8D5B5"],
                [0.5, "#4CAF72"],
                [0.75, "#1E7A45"],
                [1.0, "#0D3B22"],
            ],
            zmin=0.1, zmax=0.6,
            text=pivot.values.round(3),
            texttemplate="<b>%{text}</b>",
            textfont={"size": 16, "color": "white"},
            customdata=custom,
            hovertemplate="%{customdata}<extra></extra>",
            colorbar=dict(
                title=dict(text="BACANO", font=dict(color=_GREY_PALE)),
                tickvals=[0.1, 0.25, 0.4, 0.55],
                ticktext=["0.10 (bajo)", "0.25", "0.40", "0.55 (alto)"],
                tickfont=dict(color=_GREY_PALE),
            ),
        ))
        fig_hm.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="white",
            font=dict(color="#0D1B2A", family="Arial"),
            title=dict(text="BACANO por perfil empresarial", font=dict(color="#0D1B2A", size=14)),
            xaxis=dict(tickfont=dict(color="#0D1B2A", size=11)),
            yaxis=dict(tickfont=dict(color="#0D1B2A", size=11)),
            margin=dict(l=20, r=20, t=50, b=20),
            height=320,
        )
        st.plotly_chart(fig_hm, use_container_width=True)

    # ── Panel B — Simulador de política pública ───────────────────────────
    with col_b:
        td_range = np.linspace(tasa_den / 100, 0.95, 200)
        bac_range = np.array([
            tv_m * 0.5 + tv_m * (1 - td) * 0.3 + tpn_m * 0.2
            for td in td_range
        ])

        bac_actual = bac_range[0]
        td_80 = 0.80
        bac_80 = tv_m * 0.5 + tv_m * (1 - td_80) * 0.3 + tpn_m * 0.2
        delta = bac_actual - bac_80

        fig_sim = go.Figure()

        # Área rellena
        fig_sim.add_trace(go.Scatter(
            x=td_range * 100, y=bac_range,
            fill="tozeroy", fillcolor="rgba(21,101,192,0.15)",
            line=dict(color=_BLUE_SOFT, width=2.5),
            name="BACANO simulado",
            hovertemplate="TD: %{x:.1f}%<br>BACANO: %{y:.4f}<extra></extra>",
        ))

        # Punto actual
        fig_sim.add_trace(go.Scatter(
            x=[tasa_den], y=[bac_actual],
            mode="markers+text",
            marker=dict(size=14, color=_RED_HOT, line=dict(color=_BG_DARK, width=2)),
            text=[f"HOY {tasa_den:.1f}%"],
            textposition="top right",
            textfont=dict(color=_RED_HOT, size=10),
            name="Situación actual",
            hovertemplate=f"TD actual: {tasa_den:.1f}%<br>BACANO: {bac_actual:.4f}<extra></extra>",
        ))

        # Punto meta 80%
        fig_sim.add_trace(go.Scatter(
            x=[80], y=[bac_80],
            mode="markers+text",
            marker=dict(size=14, color=_TEAL_N, line=dict(color=_BG_DARK, width=2)),
            text=["META 80%"],
            textposition="top right",
            textfont=dict(color=_TEAL_N, size=10),
            name="Meta denuncia 80%",
            hovertemplate=f"TD meta: 80%<br>BACANO: {bac_80:.4f}<extra></extra>",
        ))

        # Líneas guía
        fig_sim.add_vline(x=tasa_den, line_dash="dot", line_color=_RED_HOT, opacity=0.4)
        fig_sim.add_vline(x=80, line_dash="dot", line_color=_TEAL_N, opacity=0.4)

        y_min = max(0, bac_range.min() * 0.92)
        y_max = bac_range.max() * 1.08
        fig_sim.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="white",
            font=dict(color="#0D1B2A", family="Arial"),
            title=dict(
                text=f"Simulador: elevar denuncia al 80% reduce BACANO en −{delta:.4f} pts",
                font=dict(color="#0D1B2A", size=13),
            ),
            xaxis=dict(title="Tasa de denuncia hipotética (%)",
                       gridcolor="#CCCCCC", gridwidth=0.5),
            yaxis=dict(title="BACANO promedio resultante",
                       gridcolor="#CCCCCC", gridwidth=0.5,
                       range=[y_min, y_max]),
            legend=dict(bgcolor="white", bordercolor="#CCCCCC", borderwidth=1),
            margin=dict(l=20, r=20, t=55, b=40),
            height=320,
        )
        st.plotly_chart(fig_sim, use_container_width=True)

    # ── Insight final ─────────────────────────────────────────────────────
    top1 = bacano_df.nlargest(1, "BACANO").iloc[0]
    st.info(
        f"⚠️ **Perfil de mayor riesgo:** {top1['Sector']} / {top1['Tamaño']} — "
        f"BACANO = **{top1['BACANO']}** (n = {int(top1['N'])} empresas).  \n"
        f"Elevar la tasa de denuncia al 80% reduciría el BACANO en **−{delta:.4f} puntos**, "
        f"más que eliminar toda la percepción negativa.",
        icon="⚠️",
    )