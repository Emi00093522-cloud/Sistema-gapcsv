import streamlit as st
import hashlib
from modulos.config.conexion import obtener_conexion

def verificar_usuario(usuario, contrasena):
    """Verifica usuario y contraseña en la base de datos."""
    con = obtener_conexion()
    if not con:
        st.error("⚠️ No se pudo conectar a la base de datos.")
        return None

    try:
        cursor = con.cursor(dictionary=True)

        # Encriptar la contraseña para compararla con la guardada
        contrasena_hash = hashlib.sha256(contrasena.encode()).hexdigest()

        # Ajusta nombres de columnas según tu tabla real
        query = """
            SELECT 
                u.ID_Usuario,
                u.Usuario,
                t.Tipo AS tipo_usuario
            FROM Usuario u
            INNER JOIN Tipo_de_usuario t ON u.ID_Tipo_usuario = t.ID_Tipo_usuario
            WHERE u.Usuario = %s AND u.Contraseña = %s
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
    """Interfaz del login."""
    st.title("Inicio de sesión 👩‍💼")

    usuario = st.text_input("Usuario", key="usuario_input")
    contrasena = st.text_input("Contraseña", type="password", key="contrasena_input")

    if st.button("Iniciar sesión"):
        datos_usuario = verificar_usuario(usuario, contrasena)

        if datos_usuario:
            st.session_state["sesion_iniciada"] = True
            st.session_state["usuario"] = datos_usuario["Usuario"]
            st.session_state["tipo_usuario"] = datos_usuario["tipo_usuario"]

            st.success(f"Bienvenido, {datos_usuario['Usuario']} 👋 (Tipo: {datos_usuario['tipo_usuario']})")
            st.rerun()
        else:
            st.error("❌ Usuario o contraseña incorrectos.")
