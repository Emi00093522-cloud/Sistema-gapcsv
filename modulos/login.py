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

        # 🔥 CONSULTA FINAL — Ahora incluye el cargo
        query = """
            SELECT 
                u.ID_Usuario,
                u.Usuario,
                t.Tipo_usuario AS tipo_usuario,
                c.tipo_de_cargo AS cargo
            FROM Usuario u
            INNER JOIN Tipo_de_usuario t ON u.ID_Tipo_usuario = t.ID_Tipo_usuario
            INNER JOIN Cargo c ON u.ID_Cargo = c.ID_Cargo
            WHERE u.Usuario = %s AND u.Contraseña = %s
        """

        cursor.execute(query, (usuario, contrasena_hash))
        result = cursor.fetchone()
        
        # 🔥 FILTRAR SOLO LOS CARGOS PERMITIDOS
        if result and result["cargo"] in ["promotora", "administrador", "secretaria"]:
            return result
        else:
            st.error("❌ Usuario no autorizado para acceder al sistema.")
            return None

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
        if not usuario or not contrasena:
            st.error("❌ Por favor, complete todos los campos.")
            return
            
        datos_usuario = verificar_usuario(usuario, contrasena)

        if datos_usuario:
            # 🔥 GUARDAMOS TODO EN SESIÓN
            st.session_state["sesion_iniciada"] = True
            st.session_state["usuario"] = datos_usuario["Usuario"]
            st.session_state["tipo_usuario"] = datos_usuario["tipo_usuario"]
            st.session_state["cargo_de_usuario"] = datos_usuario["cargo"]

            st.success(
                f"Bienvenido, {datos_usuario['Usuario']} 👋 "
                f"(Cargo: {datos_usuario['cargo']})"
            )

            st.rerun()
        else:
            st.error("❌ Usuario o contraseña incorrectos.")
