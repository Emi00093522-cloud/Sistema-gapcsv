# app.py
import streamlit as st
from modulos.ahorro import mostrar_ahorro  # Importamos la función mostrar_venta del módulo venta
from modulos.login import login
# Llamamos a la función mostrar_venta para mostrar el mensaje en la app
mostrar_ahorro()
login()

