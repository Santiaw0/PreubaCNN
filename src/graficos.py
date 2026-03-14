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

from src.preprocesamiento import (
    LABELS_P204, LABELS_LOCALIDAD, LABELS_SEXO,
    DELITOS_MAP_ECN, DEL_COLS_ECN, MEDIDAS_MAP_ECN, MED_COLS_ECN,
    COLS_P204, DELITOS_EMPRESAS,
)

# ── Paleta y layout base ──────────────────────────────────────────────────────
PRIMARY  = "#0D1B2A"
ACCENT1  = "#1B4F72"
ACCENT2  = "#2E86AB"
DANGER   = "#E74C3C"
WARN     = "#F39C12"
SUCCESS  = "#27AE60"
NEUTRAL  = "#95A5A6"
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
    vic["color"] = vic["pct"].apply(lambda p: DANGER if p > tasa else (WARN if p > tasa*.85 else SUCCESS))

    fig = go.Figure(go.Bar(
        x=vic["pct"], y=vic["Sector"], orientation="h",
        marker_color=vic["color"],
        text=vic["pct"].round(1).astype(str)+"%", textposition="outside",
        hovertemplate="<b>%{y}</b><br>Victimización: %{x:.1f}%<extra></extra>",
    ))
    fig.add_vline(x=tasa, line_dash="dash", line_color=DANGER, opacity=.6,
                  annotation_text=f"Promedio {tasa:.1f}%", annotation_position="top right")
    fig.update_layout(**BASE, title="Victimización por sector",
                      xaxis_range=[0, vic["pct"].max()*1.3], showlegend=False, height=280)
    st.plotly_chart(fig, use_container_width=True)


def barras_tamano(df: pd.DataFrame):
    tasa  = df["Victima_bin"].sum() / len(df) * 100
    ORDER = ["Microempresa","Pequeña","Mediana","Grande"]
    vic   = df.groupby("Tamaño")["Victima_bin"].mean().reindex(ORDER).reset_index()
    vic["pct"]   = vic["Victima_bin"] * 100
    vic["color"] = vic["pct"].apply(lambda p: DANGER if p > tasa*1.1 else (WARN if p > tasa*.9 else SUCCESS))

    fig = go.Figure(go.Bar(
        x=vic["Tamaño"], y=vic["pct"],
        marker_color=vic["color"],
        text=vic["pct"].round(1).astype(str)+"%", textposition="outside",
        hovertemplate="<b>%{x}</b><br>Victimización: %{y:.1f}%<extra></extra>",
    ))
    fig.add_hline(y=tasa, line_dash="dash", line_color=DANGER, opacity=.6,
                  annotation_text=f"Promedio {tasa:.1f}%", annotation_position="top right")
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
    totals["texto"]  = totals.apply(lambda r: f"{int(r['N'])}  ({r['pct']}%)", axis=1)
    totals["color"]  = px.colors.sample_colorscale(
        "RdYlGn_r", [i/max(len(totals)-1,1) for i in range(len(totals))]
    )
    fig = go.Figure(go.Bar(
        x=totals["N"], y=totals["Delito"], orientation="h",
        marker_color=totals["color"],
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

    fig = make_subplots(rows=1, cols=2, specs=[[{"type":"pie"},{"type":"bar"}]],
                        subplot_titles=("¿Mejoró o empeoró vs 2023?",
                                        "¿Bogotá es segura para negocios?"))
    fig.add_trace(go.Pie(labels=ORDER_P, values=vals_p,
                         marker_colors=[SUCCESS,NEUTRAL,DANGER], hole=.35,
                         textinfo="label+percent",
                         hovertemplate="<b>%{label}</b><br>%{value} empresas<extra></extra>"),
                  row=1, col=1)
    fig.add_trace(go.Bar(x=vals_s, y=SEG_ORDER, orientation="h",
                         marker_color=[DANGER,"#E67E22",NEUTRAL,ACCENT2,SUCCESS],
                         text=vals_s, textposition="outside",
                         hovertemplate="<b>%{y}</b><br>%{x} empresas<extra></extra>"),
                  row=1, col=2)
    fig.update_layout(**BASE, showlegend=False, height=340)
    fig.update_xaxes(title_text="N° de empresas", row=1, col=2)
    st.plotly_chart(fig, use_container_width=True)


def barras_medidas(df: pd.DataFrame):
    adoption = {label: round(df[col].mean()*100,1)
                for col, label in MEDIDAS_MAP_ECN.items() if col in df.columns}
    ser = pd.Series(adoption).reset_index().rename(columns={"index":"Medida",0:"pct"})
    ser = ser.sort_values("pct")
    ser["color"] = ser["pct"].apply(lambda v: SUCCESS if v>30 else (WARN if v>15 else NEUTRAL))

    fig = go.Figure(go.Bar(
        x=ser["pct"], y=ser["Medida"], orientation="h",
        marker_color=ser["color"],
        text=ser["pct"].astype(str)+"%", textposition="outside",
        hovertemplate="<b>%{y}</b><br>Adopción: %{x:.1f}%<extra></extra>",
    ))
    for umbral, etiqueta, color in [(15,"15% — baja",NEUTRAL),(30,"30% — media",WARN)]:
        fig.add_vline(x=umbral, line_dash="dot", line_color=color, opacity=.5,
                      annotation_text=etiqueta, annotation_position="top")
    fig.update_layout(**BASE, title="Medidas de seguridad adoptadas",
                      xaxis_range=[0, ser["pct"].max()*1.3], showlegend=False, height=320)
    st.plotly_chart(fig, use_container_width=True)


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
# GRÁFICOS EPV — Percepción y Victimización
# ═════════════════════════════════════════════════════════════════════════════

def kpis_epv(df_uniq: pd.DataFrame, ids_den: set):
    N          = len(df_uniq)
    N_vic      = int((df_uniq["P203"]==1).sum())
    tasa_vic   = N_vic/N*100 if N else 0
    vic_ids    = set(df_uniq[df_uniq["P203"]==1]["ID"])
    tasa_den   = len(vic_ids & ids_den)/N_vic*100 if N_vic else 0
    perc_ciudad= df_uniq["P103_1"].mean() if "P103_1" in df_uniq.columns else 0

    col1,col2,col3,col4 = st.columns(4)
    for col,val,label,color,icon in [
        (col1,f"{tasa_vic:.1f}%",       "Tasa de victimización",         DANGER, "🔴"),
        (col2,f"{N_vic:,}",             f"Personas víctimas (de {N:,})",  ACCENT1,"👤"),
        (col3,f"{tasa_den:.1f}%",       "Tasa de denuncia",              WARN,   "📋"),
        (col4,f"{perc_ciudad:.2f} / 5", "Percepción seg. ciudad (prom.)",ACCENT2,"🏙️"),
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


def victimizacion_general(df_uniq: pd.DataFrame):
    counts = df_uniq["P203"].map({1:"Sí fue víctima",2:"No fue víctima"}).value_counts()
    tab    = (df_uniq.groupby("ESTRATO_NOM")["P203"]
              .apply(lambda x: (x==1).mean()*100).reset_index()
              .rename(columns={"P203":"pct"}).sort_values("ESTRATO_NOM"))

    fig = make_subplots(rows=1,cols=2, specs=[[{"type":"pie"},{"type":"bar"}]],
                        subplot_titles=("¿Fue víctima en 2024?","% víctimas por estrato"))
    fig.add_trace(go.Pie(labels=counts.index, values=counts.values,
                         marker_colors=[DANGER,SUCCESS], hole=.38,
                         textinfo="label+percent"), row=1, col=1)
    fig.add_trace(go.Bar(x=tab["ESTRATO_NOM"], y=tab["pct"],
                         marker_color=DANGER, opacity=.85,
                         text=tab["pct"].round(1).astype(str)+"%", textposition="outside",
                         hovertemplate="<b>Estrato %{x}</b><br>%{y:.1f}%<extra></extra>"),
                  row=1, col=2)
    fig.update_layout(**BASE, showlegend=False, height=340)
    fig.update_yaxes(title_text="% víctimas", row=1, col=2)
    st.plotly_chart(fig, use_container_width=True)


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


def denuncia_por_delito(p204_long: pd.DataFrame, p214_long: pd.DataFrame):
    vic  = p204_long.drop_duplicates(["ID","P204"]).groupby("P204")["ID"].nunique()
    den  = p214_long.drop_duplicates(["ID","P214"]).groupby("P214")["ID"].nunique()
    tasa = (den/vic*100).dropna().sort_values()
    tasa.index = tasa.index.map(lambda x: LABELS_P204.get(x,str(x)))
    avg  = tasa.mean()
    colores = [DANGER if v<avg else SUCCESS for v in tasa.values]

    fig = go.Figure(go.Bar(
        x=tasa.values, y=tasa.index, orientation="h",
        marker_color=colores,
        text=tasa.round(1).astype(str)+"%", textposition="outside",
        hovertemplate="<b>%{y}</b><br>Denuncia: %{x:.1f}%<extra></extra>",
    ))
    fig.add_vline(x=avg, line_dash="dash", line_color=NEUTRAL, opacity=.7,
                  annotation_text=f"Promedio {avg:.1f}%", annotation_position="top right")
    fig.update_layout(**BASE, title="Tasa de denuncia por tipo de delito",
                      xaxis_range=[0,tasa.max()*1.3], showlegend=False, height=400)
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
    st.plotly_chart(fig, use_container_width=True)


def genero_victimizacion(df_uniq: pd.DataFrame, p204_long: pd.DataFrame, ids_den: set):
    tasa_gen = (df_uniq.groupby("SEXO_NOM")["P203"]
                .apply(lambda x: (x==1).mean()*100).reset_index()
                .rename(columns={"P203":"tasa"}))
    vic_df   = df_uniq[df_uniq["P203"]==1]
    den_gen  = (vic_df.groupby("SEXO_NOM")
                .apply(lambda x: pd.Series({
                    "victimas": len(x),
                    "denuncias": x["ID"].isin(ids_den).sum()
                }), include_groups=False).reset_index())
    den_gen["tasa_%"] = (den_gen["denuncias"]/den_gen["victimas"]*100).round(1)

    top5 = (p204_long.drop_duplicates(["ID","P204"])["P204"]
            .value_counts().head(5).index) if not p204_long.empty else []
    df_top = (p204_long[p204_long["P204"].isin(top5)]
              .drop_duplicates(["ID","P204"])
              .merge(df_uniq[["ID","SEXO_NOM"]], on="ID")) if len(top5)>0 else pd.DataFrame()
    tab_del = (df_top.groupby(["P204","SEXO_NOM"])["ID"].nunique()
               .unstack(fill_value=0).reset_index()
               .assign(P204_NOM=lambda d: d["P204"].map(LABELS_P204))
               ) if not df_top.empty else pd.DataFrame()

    fig = make_subplots(rows=1,cols=3,
                        subplot_titles=("Victimización por sexo (%)",
                                        "Tasa de denuncia por sexo (%)",
                                        "Top 5 delitos por sexo"))
    for df_g, y_col, col_idx, ytitle in [
        (tasa_gen, "tasa", 1, "% víctimas"),
        (den_gen,  "tasa_%", 2, "% que denunció"),
    ]:
        fig.add_trace(go.Bar(
            x=df_g["SEXO_NOM"], y=df_g[y_col],
            marker_color=[HOMBRE if s=="Hombre" else MUJER for s in df_g["SEXO_NOM"]],
            text=df_g[y_col].round(1).astype(str)+"%", textposition="outside",
            hovertemplate=f"<b>%{{x}}</b><br>{ytitle}: %{{y:.1f}}%<extra></extra>",
        ), row=1, col=col_idx)

    if not tab_del.empty:
        for sexo,color in [("Hombre",HOMBRE),("Mujer",MUJER)]:
            if sexo in tab_del.columns:
                fig.add_trace(go.Bar(
                    name=sexo, x=tab_del[sexo], y=tab_del["P204_NOM"],
                    orientation="h", marker_color=color,
                    hovertemplate=f"<b>%{{y}}</b><br>{sexo}: %{{x:,}}<extra></extra>",
                ), row=1, col=3)

    fig.update_layout(**BASE, barmode="group", showlegend=True,
                      legend=dict(title="Sexo",orientation="h",y=-0.15), height=400)
    st.plotly_chart(fig, use_container_width=True)


def victimizacion_localidad(df_uniq: pd.DataFrame):
    df_u = df_uniq[df_uniq["LOCALIDAD_NOM"].notna()].copy()
    tasa = (df_u.groupby("LOCALIDAD_NOM")["P203"]
            .apply(lambda x: (x==1).mean()*100).sort_values().reset_index()
            .rename(columns={"P203":"tasa"}))
    avg  = tasa["tasa"].mean()
    tasa["color"] = tasa["tasa"].apply(lambda v: DANGER if v>avg else SUCCESS)

    fig = go.Figure(go.Bar(
        x=tasa["tasa"], y=tasa["LOCALIDAD_NOM"], orientation="h",
        marker_color=tasa["color"],
        text=tasa["tasa"].round(1).astype(str)+"%", textposition="outside",
        hovertemplate="<b>%{y}</b><br>Victimización: %{x:.1f}%<extra></extra>",
    ))
    fig.add_vline(x=avg, line_dash="dash", line_color=NEUTRAL, opacity=.7,
                  annotation_text=f"Promedio {avg:.1f}%", annotation_position="top right")
    fig.update_layout(**BASE, title="Tasa de victimización por localidad",
                      xaxis_range=[0,tasa["tasa"].max()*1.3], showlegend=False, height=500)
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
