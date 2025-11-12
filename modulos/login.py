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

        # ✅ Ajustado al nombre real de tu columna: Tipo_usuario
        query = """
            SELECT 
                u.ID_Usuario,
                u.Usuario,
                t.Tipo_usuario AS tipo_usuario
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


def obtener_cargos_por_tipo_usuario(tipo_usuario):
    """Obtiene los cargos disponibles según el tipo de usuario."""
    if tipo_usuario == "LECTOR":
        return ["ADMINISTRADOR", "PROMOTORA", "TESORERA", "SOCIA"]
    elif tipo_usuario == "EDITOR":
        return ["PRESIDENTE", "SECRETARIA"]
    else:
        return []


def login():
    """Interfaz del login."""
    st.title("Inicio de sesión 👩‍💼")

    usuario = st.text_input("Usuario", key="usuario_input")
    contrasena = st.text_input("Contraseña", type="password", key="contrasena_input")
    
    # Selector de tipo de usuario
    tipo_usuario = st.selectbox(
        "Tipo de usuario",
        ["LECTOR", "EDITOR"],
        key="tipo_usuario_select"
    )
    
    # Obtener cargos según el tipo de usuario seleccionado
    cargos_disponibles = obtener_cargos_por_tipo_usuario(tipo_usuario)
    
    # Selector de cargo que se actualiza según el tipo de usuario seleccionado
    cargo = st.selectbox(
        "Cargo",
        cargos_disponibles,
        key="cargo_select"
    )

    if st.button("Iniciar sesión"):
        # Primero verificamos el usuario en la base de datos
        datos_usuario = verificar_usuario(usuario, contrasena)

        if datos_usuario:
            # Verificamos que el tipo de usuario seleccionado coincida con el de la BD
            tipo_usuario_bd = datos_usuario["tipo_usuario"]
            
            if tipo_usuario != tipo_usuario_bd:
                st.error(f"❌ Error: El tipo de usuario no coincide. Su usuario es de tipo: {tipo_usuario_bd}")
                return
            
            # Verificamos que el cargo seleccionado sea válido para el tipo de usuario
            cargos_permitidos = obtener_cargos_por_tipo_usuario(tipo_usuario_bd)
            if cargo not in cargos_permitidos:
                st.error(f"❌ Error: Cargo no válido para el tipo de usuario {tipo_usuario_bd}")
                return
            
            st.session_state["sesion_iniciada"] = True
            st.session_state["usuario"] = datos_usuario["Usuario"]
            st.session_state["tipo_usuario"] = datos_usuario["tipo_usuario"]
            st.session_state["cargo"] = cargo

            st.success(f"Bienvenido, {datos_usuario['Usuario']} 👋 (Tipo: {datos_usuario['tipo_usuario']}, Cargo: {cargo})")
            st.rerun()
        else:
            st.error("❌ Usuario o contraseña incorrectos.")


# Versión alternativa si quieres que el tipo de usuario se determine automáticamente desde la BD
def login_automatico():
    """Interfaz del login donde el tipo de usuario se determina automáticamente desde la BD."""
    st.title("Inicio de sesión 👩‍💼")

    usuario = st.text_input("Usuario", key="usuario_input")
    contrasena = st.text_input("Contraseña", type="password", key="contrasena_input")

    if st.button("Iniciar sesión"):
        datos_usuario = verificar_usuario(usuario, contrasena)

        if datos_usuario:
            tipo_usuario_bd = datos_usuario["tipo_usuario"]
            cargos_disponibles = obtener_cargos_por_tipo_usuario(tipo_usuario_bd)
            
            # Si solo hay un cargo disponible, lo seleccionamos automáticamente
            if len(cargos_disponibles) == 1:
                cargo_seleccionado = cargos_disponibles[0]
            else:
                # Mostramos selector de cargo basado en el tipo de usuario de la BD
                cargo_seleccionado = st.selectbox(
                    "Seleccione su cargo",
                    cargos_disponibles,
                    key="cargo_auto_select"
                )
            
            st.session_state["sesion_iniciada"] = True
            st.session_state["usuario"] = datos_usuario["Usuario"]
            st.session_state["tipo_usuario"] = tipo_usuario_bd
            st.session_state["cargo"] = cargo_seleccionado

            st.success(f"Bienvenido, {datos_usuario['Usuario']} 👋 (Tipo: {tipo_usuario_bd}, Cargo: {cargo_seleccionado})")
            st.rerun()
        else:
            st.error("❌ Usuario o contraseña incorrectos.")


# Función adicional para usar en otras partes de tu aplicación
def obtener_cargo_actual():
    """Retorna el cargo actual del usuario logueado."""
    return st.session_state.get("cargo", "")


def obtener_tipo_usuario_actual():
    """Retorna el tipo de usuario actual."""
    return st.session_state.get("tipo_usuario", "")

# Para usar en tu app, llama a una de las dos funciones:
# login()  # Si quieres que el usuario seleccione tipo de usuario
# login_automatico()  # Si quieres que el tipo de usuario se determine desde la BD
