import streamlit as st
from modulos.registro_usuario import registrar_usuario
from modulos.login import login
from modulos.ahorros import mostrar_ahorros  # Puedes reemplazar luego por tus dashboards reales

# ⚙️ Configuración de la app
st.set_page_config(page_title="Sistema GAPCSV", page_icon="🧁", layout="centered")

# 🎨 --- ESTILOS VISUALES ---
st.markdown(
    """
    <style>
    /* Fuente Poppins */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');

    html, body, [class*="st-"] {
        font-family: 'Poppins', sans-serif;
    }

    /* Fondo general lavanda degradado */
    .stApp {
        background: linear-gradient(135deg, #E6E6FA 0%, #F8E1F4 100%) !important;
        color: #4A4A4A;
    }

    /* Quitar recuadro gris */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: transparent !important;
        box-shadow: none !important;
        padding: 0 !important;
    }

    /* Estilo del contenedor principal */
    .fondo {
        background: rgba(255, 255, 255, 0.4);
        padding: 50px;
        border-radius: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        text-align: center;
        backdrop-filter: blur(10px);
    }

    /* Títulos */
    .titulo {
        color: #5E3C77;
        font-size: 38px;
        font-weight: 700;
        margin-bottom: 10px;
    }
    .subtitulo {
        color: #7A4D96;
        font-size: 22px;
        font-weight: 600;
        margin-bottom: 25px;
    }

    /* Texto descriptivo */
    .texto {
        color: #4A4A4A;
        font-size: 18px;
        margin-bottom: 30px;
    }

    /* Botones personalizados */
    button[kind="primary"] {
        background-color: #7A4D96 !important;
        color: white !important;
        border-radius: 12px !important;
        font-size: 18px !important;
        font-weight: 600 !important;
        border: none !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.15);
        transition: all 0.2s ease-in-out;
    }
    b
