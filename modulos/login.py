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
        return result

    except Exception as e:
        st.error(f"❌ Error al verificar usuario: {e}")
        return None
    finally:
        con.close()

def restablecer_contrasena():
    """Interfaz para restablecer contraseña"""
    st.subheader("🔐 Restablecer Contraseña")
    
    with st.form("form_restablecer"):
        usuario = st.text_input("Ingresa tu nombre de usuario")
        nueva_contrasena = st.text_input("Nueva contraseña", type="password")
        confirmar_contrasena = st.text_input("Confirmar nueva contraseña", type="password")
        
        if st.form_submit_button("Restablecer Contraseña"):
            if not usuario or not nueva_contrasena or not confirmar_contrasena:
                st.error("❌ Todos los campos son obligatorios.")
                return
                
            if nueva_contrasena != confirmar_contrasena:
                st.error("❌ Las contraseñas no coinciden.")
                return
                
            # Verificar que el usuario existe
            con = obtener_conexion()
            if not con:
                st.error("⚠️ No se pudo conectar a la base de datos.")
                return
                
            try:
                cursor = con.cursor(dictionary=True)
                
                # Verificar si el usuario existe
                cursor.execute("SELECT ID_Usuario FROM Usuario WHERE Usuario = %s", (usuario,))
                usuario_existe = cursor.fetchone()
                
                if not usuario_existe:
                    st.error("❌ El usuario no existe en el sistema.")
                    return
                
                # Actualizar la contraseña
                nueva_contrasena_hash = hashlib.sha256(nueva_contrasena.encode()).hexdigest()
                
                cursor.execute(
                    "UPDATE Usuario SET Contraseña = %s WHERE Usuario = %s",
                    (nueva_contrasena_hash, usuario)
                )
                con.commit()
                
                st.success("✅ Contraseña restablecida exitosamente. Ya puedes iniciar sesión.")
                st.session_state["mostrar_restablecer"] = False
                
            except Exception as e:
                st.error(f"❌ Error al restablecer contraseña: {e}")
            finally:
                con.close()

def login():
    """Interfaz del login."""
    st.title("Inicio de sesión 👩‍💼")
    
    # Mostrar opción de restablecer contraseña si se solicita
    if st.session_state.get("mostrar_restablecer", False):
        restablecer_contrasena()
        
        if st.button("⬅️ Volver al login"):
            st.session_state["mostrar_restablecer"] = False
            st.rerun()
        return

    usuario = st.text_input("Usuario", key="usuario_input")
    contrasena = st.text_input("Contraseña", type="password", key="contrasena_input")

    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Iniciar sesión", use_container_width=True):
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
    
    with col2:
        if st.button("¿Olvidaste tu contraseña?", use_container_width=True):
            st.session_state["mostrar_restablecer"] = True
            st.rerun()
