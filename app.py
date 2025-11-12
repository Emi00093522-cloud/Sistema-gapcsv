import streamlit as st
from modulos.registro_usuario import registrar_usuario
from modulos.ahorros import mostrar_ahorros  # Importamos la función mostrar_venta del módulo venta
from modulos.login import login
mostrar_ahorros()
login()
# Llamamos a la función mostrar_venta para mostrar el mensaje en la app
mostrar_ahorros()

st.set_page_config(page_title="Sistema GAPCSV", page_icon="🧁", layout="centered")

menu = st.sidebar.selectbox("Menú", ["Registrar usuario", "Login"])

if menu == "Registrar usuario":
    registrar_usuario()
elif menu == "Login":
    st.write("Aquí irá tu formulario de login")
