import streamlit as st
from modulos.registro_usuario import registrar_usuario

st.set_page_config(page_title="Sistema GAPCSV", page_icon="🧁", layout="centered")

menu = st.sidebar.selectbox("Menú", ["Registrar usuario", "Login"])

if menu == "Registrar usuario":
    registrar_usuario()
elif menu == "Login":
    st.write("Aquí irá tu formulario de login")
