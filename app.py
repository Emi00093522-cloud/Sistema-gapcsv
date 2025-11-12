import streamlit as st
from modulos.registro_usuario import registrar_usuario
from modulos.login import login
from modulos.ahorros import mostrar_ahorros

# Configuración básica de la página
st.set_page_config(page_title="Sistema GAPCSV", page_icon="🧁", layout="centered")

# Título general del sistema
st.title("🧁 Sistema de Gestión GAPCSV")

# Menú lateral
menu = st.sidebar.selectbox(
    "Menú principal",
    ["Iniciar sesión", "Registrar usuario", "Ver ahorros"]
)

# Control de navegación
if menu == "Iniciar sesión":
    login()

elif menu == "Registrar usuario":
    registrar_usuario()

elif menu == "Ver ahorros":
    # Solo mostrar si hay sesión activa
    if "usuario" in st.session_state:
        st.success(f"Bienvenido/a {st.session_state['usuario']} 👋")
        mostrar_ahorros()
    else:
        st.warning("Debes iniciar sesión primero para ver los ahorros.")

