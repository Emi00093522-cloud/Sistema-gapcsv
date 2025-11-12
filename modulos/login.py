import streamlit as st
import hashlib
from modulos.config.conexion import obtener_conexion


def verificar_usuario(usuario, contrasena):
    """
    Verifica si el usuario y la contraseña son válidos en la base de datos.
    Las contraseñas se comparan en su versión encriptada (SHA-256).
    """
    con = obtener_conexion()
    if not con:
        st.error("⚠️ No se pudo conectar a la base de datos.")
        return None

    try:
        cursor = con.cursor(dictionary=True)

        # Encriptar la contraseña ingresada
        contrasena_hash = hashlib.sha256(contrasena.encode()).hexdigest()

        # Consulta de validación
        query = """
            SELECT u.usuario, t.Tipo_usuario
            FROM Usuario u
            JOIN Tipo_usuario t ON u.ID_Tipo_usuario = t.ID_Tipo_usuario
            WHERE u.usuario = %s AND u.contraseña = %s
        """
        cursor.execute(query, (usuario, contrasena_hash))
        result = cursor.fetchone()
        return result
    except Exception as e:
        st.error(f"❌ Error al verificar usuario: {e}")
        return None
    finally:
        con.close()


def login():
    """
    Interfaz de inicio de sesión con control de estado y redirección automática.
    """
    st.title("🔐 Inicio de sesión")

    # Mostrar mensaje si la conexión previa fue exi
