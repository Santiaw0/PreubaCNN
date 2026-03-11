# ── Listas que también importa app_peligrosidad.py ───────────────────────────

import pickle
import os
import numpy as np

# ── Listas que también importa app_peligrosidad.py ───────────────────────────
ZONAS_LIST = [
    "Centro Histórico",
    "Zona Rosa",
    "Chapinero",
    "Usaquén",
    "Ciudad Bolívar",
    "Suba",
]

GENEROS = [
    "Hombre",
    "Mujer",
    "No binario / Prefiero no decir",
]

NIVELES = {0: "Bajo", 1: "Medio", 2: "Alto", 3: "Crítico"}

# ── Colores y consejos por nivel ─────────────────────────────────────────────
COLORES = {
    "Bajo":    ("🟢", "#2ecc71", "Puedes moverte con relativa tranquilidad. Mantén precauciones básicas."),
    "Medio":   ("🟡", "#f39c12", "Ten cuidado con tus pertenencias y evita zonas aisladas de noche."),
    "Alto":    ("🔴", "#e74c3c", "Se recomienda no ir solo/a. Comparte tu ubicación y evita la noche."),
    "Crítico": ("🚨", "#8e1a0e", "Zona de alto riesgo. Si no es indispensable, evita ir."),
}

# ── Cache del modelo (se carga una sola vez) ──────────────────────────────────
_modelo = None

def cargar_modelo():
    global _modelo
    if _modelo is None:
        # Busca el .pkl relativo al archivo predictor.py
        ruta = os.path.join(os.path.dirname(__file__), "..", "src", "modeloprueba.pkl")
        ruta = os.path.abspath(ruta)
        with open(ruta, "rb") as f:
            _modelo = pickle.load(f)
    return _modelo

def predecir(zona: str, genero: str, hora: int) -> dict:
    modelo = cargar_modelo()

    zona_enc   = ZONAS_LIST.index(zona)   if zona   in ZONAS_LIST else 0
    genero_enc = GENEROS.index(genero)    if genero in GENEROS    else 0

    X = np.array([[zona_enc, genero_enc, hora]])

    nivel_idx      = modelo.predict(X)[0]
    probabilidades = modelo.predict_proba(X)[0]
    confianza      = round(float(max(probabilidades)) * 100, 1)
    score          = min(100, int(nivel_idx * 30 + confianza * 0.4))

    return {
        "nivel":     NIVELES[nivel_idx],
        "confianza": confianza,
        "score":     score,
    }


'''
ZONAS_LIST = [
    "Usaquén",
    "Chapinero",
    "Santa Fe",
    "San Cristóbal",
    "Usme",
    "Tunjuelito",
    "Bosa",
    "Kennedy",
    "Fontibón",
    "Engativá",
    "Suba",
    "Barrios Unidos",
    "Teusaquillo",
    "La Candelaria",
    "Los Mártires",
    "Antonio Nariño",
    "Puente Aranda",
    "Rafael Uribe Uribe",
    "San Benito",
    "Sumapaz"

]
'''