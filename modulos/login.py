import streamlit as st
import hashlib
from modulos.config.conexion import obtener_conexion
from modulos.grupos import obtener_id_grupo_por_usuario

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
        st.write("**Ingresa tus datos para verificar identidad:**")
        
        usuario = st.text_input("Nombre de usuario*")
        dui = st.text_input("DUI*", 
                           placeholder="00000000-0",
                           help="Formato: 8 dígitos, guión, 1 dígito")
        
        st.markdown("---")
        st.write("**Ingresa tu nueva contraseña:**")
        
        nueva_contrasena = st.text_input("Nueva contraseña*", type="password")
        confirmar_contrasena = st.text_input("Confirmar nueva contraseña*", type="password")
        
        submitted = st.form_submit_button("🔄 Restablecer Contraseña")
        
        if submitted:
            if not usuario or not dui or not nueva_contrasena or not confirmar_contrasena:
                st.error("❌ Todos los campos marcados con * son obligatorios.")
                return
                
            if nueva_contrasena != confirmar_contrasena:
                st.error("❌ Las contraseñas no coinciden.")
                return
                
            # 🔥 VALIDAR FORMATO DEL DUI
            if not validar_formato_dui(dui):
                st.error("❌ Formato de DUI inválido. Use: 00000000-0")
                return
                
            # Verificar que el usuario existe y el DUI coincide
            con = obtener_conexion()
            if not con:
                st.error("⚠️ No se pudo conectar a la base de datos.")
                return
                
            try:
                # 🔥 VERIFICAR SI EL USUARIO Y DUI COINCIDEN
                cursor_verificar = con.cursor(dictionary=True)
                
                cursor_verificar.execute(
                    "SELECT ID_Usuario, Usuario FROM Usuario WHERE Usuario = %s AND DUI = %s", 
                    (usuario, dui)
                )
                usuario_valido = cursor_verificar.fetchone()
                cursor_verificar.close()
                
                if not usuario_valido:
                    st.error("❌ El usuario y DUI no coinciden o no existen en el sistema.")
                    con.close()
                    return
                
                # 🔥 Usar un NUEVO cursor para la actualización
                cursor_actualizar = con.cursor()
                nueva_contrasena_hash = hashlib.sha256(nueva_contrasena.encode()).hexdigest()
                
                cursor_actualizar.execute(
                    "UPDATE Usuario SET Contraseña = %s WHERE Usuario = %s AND DUI = %s",
                    (nueva_contrasena_hash, usuario, dui)
                )
                con.commit()
                
                # 🔥 VERIFICAR SI SE ACTUALIZÓ CORRECTAMENTE
                if cursor_actualizar.rowcount > 0:
                    st.success("✅ Contraseña restablecida exitosamente. Ya puedes iniciar sesión.")
                    st.session_state["mostrar_restablecer"] = False
                else:
                    st.error("❌ No se pudo actualizar la contraseña. Verifica tus datos.")
                
                cursor_actualizar.close()
                
            except Exception as e:
                st.error(f"❌ Error al restablecer contraseña: {e}")
            finally:
                con.close()

def validar_formato_dui(dui):
    """Valida el formato del DUI salvadoreño"""
    import re
    # Formato: 8 dígitos, guión, 1 dígito
    patron = r'^\d{8}-\d{1}$'
    return bool(re.match(patron, dui))

def login():
    """Interfaz del login."""
    st.title("Inicio de sesión 👩‍💼")
    
    # 🔥 BOTÓN VOLVER AL MENÚ PRINCIPAL
    if st.button("🏠 Volver al menú principal"):
        st.session_state["pagina_actual"] = "inicio"
        st.rerun()
    
    st.markdown("---")
    
    # Mostrar opción de restablecer contraseña si se solicita
    if st.session_state.get("mostrar_restablecer", False):
        restablecer_contrasena()
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Volver al login", use_container_width=True):
                st.session_state["mostrar_restablecer"] = False
                st.rerun()
        with col2:
            if st.button("🏠 Volver al menú principal", use_container_width=True):
                st.session_state["pagina_actual"] = "inicio"
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
                # 🔥 GUARDAMOS TODO EN SESIÓN + PERMISOS (LO NUEVO)
                st.session_state["sesion_iniciada"] = True
                st.session_state["usuario"] = datos_usuario["Usuario"]
                st.session_state["tipo_usuario"] = datos_usuario["tipo_usuario"]
                st.session_state["cargo_de_usuario"] = datos_usuario["cargo"]
                st.session_state["id_usuario"] = datos_usuario["ID_Usuario"]
                id_grupo = obtener_id_grupo_por_usuario(datos_usuario["ID_Usuario"])
                st.session_state["id_grupo"] = id_grupo
                from modulos.permisos import obtener_permisos_usuario
                permisos = obtener_permisos_usuario(
                    datos_usuario["ID_Usuario"],
                    datos_usuario["tipo_usuario"],
                    datos_usuario["cargo"]
                )
                st.session_state["permisos_usuario"] = permisos
                st.success(
                    f"Bienvenido, {datos_usuario['Usuario']} 👋 "
                    f"(Cargo: {datos_usuario['cargo']})"
                )    

                st.rerun()
                
                # 🔥 OBTENER Y GUARDAR PERMISOS (LO NUEVO)
                from modulos.permisos import obtener_permisos_usuario
                permisos = obtener_permisos_usuario(
                    datos_usuario["ID_Usuario"],
                    datos_usuario["tipo_usuario"],
                    datos_usuario["cargo"]
                )
                st.session_state["permisos_usuario"] = permisos

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
