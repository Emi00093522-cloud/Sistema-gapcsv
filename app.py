# app.py
import os
import sys
import streamlit as st

# --- 🔧 Solución al error de importación ---
# Agregamos la ruta actual al PATH de Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- 🔹 Imports de los módulos ---
from modulos.ahorros import mostrar_ahorros
from modulos.login import login

# --- 🔹 Ejecución de la aplicación ---
def main():
    st.set_page_config(page_title="Sistema GAPCSV", layout="wide")
    st.title("Sistema de Gestión GAPCSV")
    
    # Llamamos las funciones de los módulos
    mostrar_ahorros()
    login()

if __name__ == "__main__":
    main()

