# src/preprocesamiento.py
"""
preprocesamiento.py
───────────────────
Limpieza y transformación de las encuestas ECN y EPV.
No contiene nada de Streamlit ni de gráficos.
Cada función pública recibe el DataFrame crudo y devuelve el limpio.
"""

import re
import streamlit as st
import pandas as pd
import numpy as np

# ═════════════════════════════════════════════════════════════════════════════
# CONSTANTES COMPARTIDAS
# ═════════════════════════════════════════════════════════════════════════════

LABELS_SEXO = {1: "Hombre", 2: "Mujer"}

LABELS_P204 = {
    1: "Hurto a persona",        2: "Hurto a residencia",
    3: "Lesiones personales",    4: "Hurto de vehículo",
    6: "Violencia intrafamiliar",8: "Robo de bicicleta",
    13: "Vandalismo",            19: "Violencia sexual",
    20: "Delitos cibernéticos",  21: "Secuestro",
    22: "Extorsión",             23: "Hurto a establecimientos",
    24: "Terrorismo",            25: "Trata de personas",
    26: "Violencia contra la mujer", 27: "Desaparición forzada",
    28: "Desplazamiento forzado",29: "Amenazas",
    30: "Abigeato",
}

LABELS_LOCALIDAD = {
    1: "Usaquén",         2: "Chapinero",         3: "Santa Fe",
    4: "San Cristóbal",   5: "Usme",              6: "Tunjuelito",
    7: "Bosa",            8: "Kennedy",            9: "Fontibón",
    10: "Engativá",       11: "Suba",             12: "Barrios Unidos",
    13: "Teusaquillo",    14: "Los Mártires",     15: "Antonio Nariño",
    16: "Puente Aranda",  17: "La Candelaria",    18: "Rafael Uribe Uribe",
    19: "Ciudad Bolívar",
}
LOC_NOMBRE_A_COD = {v: k for k, v in LABELS_LOCALIDAD.items()}

LABELS_ESTRATO = {0:"0", 1:"1", 2:"2", 3:"3", 4:"4", 5:"5", 6:"6"}
LABELS_REDAD   = {1:"18-24", 2:"25-35", 3:"36-45", 4:"46-55", 5:"56-70", 6:"70+"}

COLS_P204 = {
    "P2041":1,  "P2042":2,  "P2043":3,  "P2044":4,
    "P2046":6,  "P2048":8,  "P20413":13,"P20419":19,
    "P20420":20,"P20421":21,"P20422":22,"P20423":23,
    "P20424":24,"P20425":25,"P20426":26,"P20427":27,
    "P20428":28,"P20429":29,"P20430":30,
}
DELITOS_EMPRESAS = {1, 4, 20, 22, 23, 13, 21, 29}

DELITOS_MAP_ECN = {
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
DEL_COLS_ECN = list(DELITOS_MAP_ECN.keys())

MEDIDAS_MAP_ECN = {
    "P61A_1": "Alarmas de seguridad",
    "P61A_3": "Seguridad privada",
    "P61A_4": "Frentes de seguridad",
    "P61A_5": "Cámaras de seguridad",
    "P61A_6": "Ciberseguridad",
    "P61A_7": "App / Herramienta móvil",
    "P61A_9": "Otra medida",
}
MED_COLS_ECN = list(MEDIDAS_MAP_ECN.keys())


# ═════════════════════════════════════════════════════════════════════════════
# ECN — Encuesta Clima de Negocios
# ═════════════════════════════════════════════════════════════════════════════

@st.cache_data(show_spinner=False)
def preparar_ecn(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia el DataFrame crudo de la ECN 2024.
    Devuelve un DataFrame con variables derivadas y etiquetas listas para graficar.
    """
    COLS = [
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
    df = df_raw[[c for c in COLS if c in df_raw.columns]].copy()
    df = df.drop_duplicates(subset="NUMERO", keep="first").reset_index(drop=True)

    # Filtrar solo Bogotá D.C. (REGION=1) — el proyecto trabaja exclusivamente Bogotá
    if "REGION" in df.columns:
        df = df[df["REGION"] == 1].copy().reset_index(drop=True)

    int_cols = ["F4","F5","REGION","P56","P56_1","P57","P58"]
    del_cols = DEL_COLS_ECN
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

    # Etiquetas
    df["Sector"]      = df["F4"].map({1:"Industria", 2:"Comercio", 3:"Servicios"})
    df["Tamaño"]      = df["F5"].map({1:"Microempresa", 2:"Pequeña", 3:"Mediana", 4:"Grande"})
    df["Percepcion"]  = df["P57"].map({1:"Mejoró", 2:"Igual", 3:"Empeoró"})
    df["Seguridad"]   = df["P56_1"].map({1:"Muy inseguro", 2:"Inseguro", 3:"Ni/Ni", 4:"Seguro", 5:"Muy seguro"})

    # Variables derivadas
    df["Victima_bin"]     = (df["P58"] == 1).astype(int)
    med_real              = [c for c in med_cols if c != "P61A_2"]
    df["Num_Delitos"]     = df[del_cols].sum(axis=1)
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


# ═════════════════════════════════════════════════════════════════════════════
# EPV — Encuesta de Percepción y Victimización
# ═════════════════════════════════════════════════════════════════════════════

def _colapsar_multiple(df_full: pd.DataFrame, cols_hijas: list,
                       patron: str, nombre_var: str) -> pd.DataFrame:
    """Convierte columnas binarias de opción múltiple a formato long."""
    sub = df_full[["ID"] + cols_hijas].melt(
        id_vars="ID", value_vars=cols_hijas,
        var_name="_col", value_name="_valor",
    )
    sub = sub[sub["_valor"].notna() & (sub["_valor"] != 0)].copy()
    sub[nombre_var] = sub["_col"].str.extract(patron).astype(int)
    return sub[["ID", nombre_var]]


@st.cache_data(show_spinner=False)
def preparar_epv(df_raw: pd.DataFrame) -> dict:
    """
    Limpia el DataFrame crudo de la EPV 2024.
    Devuelve un dict con:
        - df_uniq    : una fila por encuestado, con etiquetas
        - p204_long  : delitos en formato long
        - p214_long  : denuncias en formato long
        - tasa_loc   : tasa de victimización por código de localidad
        - ids_den    : set de IDs que denunciaron
    """
    df = df_raw.copy()
    rename_map = {
        "P1021": "P102_1", "P1031": "P103_1",
        "P20311": "P203_1_1", "P4011": "P401_1",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # Filtrar solo Bogotá D.C. (código DANE 11001)
    if "MUNICIPIO" in df.columns:
        df = df[df["MUNICIPIO"] == 11001].copy().reset_index(drop=True)

    # df_uniq
    id_vars = ["ID","MUNICIPIO","LOCALIDAD","ESTRATO","SEXO","REDAD",
               "P102","P102_1","P103","P103_1","P203","P203_1_1","P401_1","P417","P421"]
    id_vars = [c for c in id_vars if c in df.columns]
    df_uniq = df[id_vars].drop_duplicates("ID").copy()
    df_uniq["SEXO_NOM"]      = df_uniq["SEXO"].map(LABELS_SEXO)
    df_uniq["LOCALIDAD_NOM"] = df_uniq["LOCALIDAD"].map(LABELS_LOCALIDAD)
    df_uniq["ESTRATO_NOM"]   = df_uniq["ESTRATO"].map(LABELS_ESTRATO)
    df_uniq["REDAD_NOM"]     = df_uniq["REDAD"].map(LABELS_REDAD)

    # Delitos (P204)
    cols_p204 = [c for c in COLS_P204 if c in df.columns]
    if cols_p204:
        sub = df[["ID"] + cols_p204].melt(id_vars="ID", var_name="_col", value_name="_val")
        sub = sub[sub["_val"] == 1].copy()
        sub["P204"] = sub["_col"].map(COLS_P204)
        p204_long = sub[["ID","P204"]].drop_duplicates()
    else:
        p204_long = pd.DataFrame(columns=["ID","P204"])

    # Denuncias (P214)
    cols_p214 = [c for c in df.columns if re.match(r"^P214(\d+)$", c)]
    if cols_p214:
        p214_long = _colapsar_multiple(df, cols_p214, r"^P214(\d+)$", "P214")
    else:
        p214_long = pd.DataFrame(columns=["ID","P214"])

    # Normalizar LOCALIDAD a entero para que coincida con LocCodigo del shapefile
    df_uniq["LOCALIDAD"] = pd.to_numeric(df_uniq["LOCALIDAD"], errors="coerce").astype("Int64")

    # Tasa de victimización por localidad
    tasa_loc = (
        df_uniq.groupby("LOCALIDAD")["P203"]
        .apply(lambda x: (x == 1).mean() * 100)
        .reset_index().rename(columns={"P203": "tasa_vic"})
    )

    return {
        "df_uniq":  df_uniq,
        "p204_long": p204_long,
        "p214_long": p214_long,
        "tasa_loc":  tasa_loc,
        "ids_den":   set(p214_long["ID"].unique()),
    }