
import streamlit as st
from modulos.registro_usuario import registrar_usuario
from modulos.ahorros import mostrar_ahorros
from modulos.login import login

# Configuración básica de la app
st.set_page_config(page_title="Sistema GAPCSV", page_icon="🧁", layout="centered")

# Inicialización del estado de sesión
if "sesion_iniciada" not in st.session_state:
    st.session_state["sesion_iniciada"] = False
if "pagina_actual" not in st.session_state:
    st.session_state["pagina_actual"] = "login"

# --- Control de navegación lateral ---
st.sidebar.title("📋 Menú principal")

# Si la sesión ya está iniciada, mostrar opciones del sistema
if st.session_state["sesion_iniciada"]:
    usuario = st.session_state.get("usuario", "Usuario")
    tipo = st.session_state.get("tipo_usuario", "Desconocido")

    st.sidebar.write(f"👤 **{usuario}** ({tipo})")

    opcion = st.sidebar.selectbox(
        "Ir a:",
        ["Dashboard", "Registrar usuario", "Cerrar sesión"],
        index=["Dashboard", "Registrar usuario", "Cerrar sesi]()
