import streamlit as st
import pandas as pd
import time

@st.cache_resource
def load_trained_model():
    """
    Aquí cargarías tu modelo real: model = joblib.load('modelo.pkl')
    Por ahora, simulamos que el modelo está cargado.
    """
    time.sleep(1) # Simula tiempo de carga
    return "Modelo_Mockup_v1"

def predict_impact(model, features):
    """
    Simula una predicción basada en los inputs del usuario.
    """
    # Aquí iría model.predict(features)
    score = (features['poblacion'] * 0.5) + (features['area'] * 0.2)
    return round(score, 2)