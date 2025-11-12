import mysql.connector
import streamlit as st

def obtener_conexion():
    try:
        conexion = mysql.connector.connect(
            host="bxdoosqjcoa8senn4bzt-mysql.services.clever-cloud.com",        # Ejemplo: "bxd...clever-cloud.com"
            user="uew98fb7s6o8aam5",     # Ejemplo: "uabcxyz"
            password="E9LAVdpxhYFonyDcjRl0",
            database="bxdoosqjcoa8senn4bzt"  # Ejemplo: "bxd...4bzt"
        )
        return conexion
    except mysql.connector.Error as e:
        st.error(f"Error al conectar a la base de datos: {e}")
        return None
