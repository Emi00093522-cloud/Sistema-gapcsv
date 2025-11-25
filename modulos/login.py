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

        # Consulta: obtenemos usuario, tipo y cargo
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
        dui = st.text_input(
            "DUI*", 
            placeholder="00000000-0",
            help="Formato: 8 dígitos, guión, 1 dígito"
        )
        
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
                
            # Validar formato del DUI
            if not validar_formato_dui(dui):
                st.error("❌ Formato de DUI inválido. Use: 00000000-0")
                return
                
            con = obtener_conexion()
            if not con:
                st.error("⚠️ No se pudo conectar a la base de datos.")
                return
                
            try:
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
                
                cursor_actualizar = con.cursor()
                nueva_contrasena_hash = hashlib.sha256(nueva_contrasena.encode()).hexdigest()
                
                cursor_actualizar.execute(
                    "UPDATE Usuario SET Contraseña = %s WHERE Usuario = %s AND DUI = %s",
                    (nueva_contrasena_hash, usuario, dui)
                )
                con.commit()
                
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
    patron = r'^\d{8}-\d{1}$'
    return bool(re.match(patron, dui))


def obtener_id_promotora_por_usuario(id_usuario):
    """
    Obtiene el ID de la Promotora asociada al usuario.
    
    Estrategias de búsqueda:
    1. Por ID_Usuario (si existe relación directa en la tabla Promotora)
    2. Por DUI (si la tabla Promotora tiene campo DUI)
    3. Por nombre del usuario coincidente con nombre de promotora (flexible)
    
    Retorna None si no es promotora o no se encuentra.
    """
    con = obtener_conexion()
    if not con:
        return None
    
    try:
        cursor = con.cursor(dictionary=True)
        
        # Obtener información del usuario
        cursor.execute("""
            SELECT ID_Usuario, Usuario, DUI 
            FROM Usuario 
            WHERE ID_Usuario = %s
        """, (id_usuario,))
        
        usuario_info = cursor.fetchone()
        if not usuario_info:
            return None
        
        nombre_usuario = usuario_info["Usuario"].strip()
        dui = usuario_info.get("DUI", "").strip()
        
        # ESTRATEGIA 1: Buscar por ID_Usuario (si existe el campo en Promotora)
        try:
            cursor.execute("""
                SELECT ID_Promotora FROM Promotora WHERE ID_Usuario = %s
            """, (id_usuario,))
            
            promotora_info = cursor.fetchone()
            if promotora_info:
                return promotora_info["ID_Promotora"]
        except:
            pass  # La columna ID_Usuario no existe en Promotora
        
        # ESTRATEGIA 2: Buscar por DUI (si existe el campo en Promotora)
        if dui:
            try:
                cursor.execute("""
                    SELECT ID_Promotora FROM Promotora WHERE DUI = %s
                """, (dui,))
                
                promotora_info = cursor.fetchone()
                if promotora_info:
                    return promotora_info["ID_Promotora"]
            except:
                pass  # La columna DUI no existe en Promotora
        
        # ESTRATEGIA 3: Buscar por coincidencia de nombre (MUY FLEXIBLE)
        cursor.execute("""
            SELECT ID_Promotora, nombre 
            FROM Promotora
        """)
        
        promotoras = cursor.fetchall()
        
        # Normalizar nombre de usuario para comparación
        nombre_usuario_lower = nombre_usuario.lower().strip()
        nombre_usuario_sin_espacios = nombre_usuario_lower.replace(" ", "")
        nombre_usuario_sin_numeros = ''.join(c for c in nombre_usuario_lower if not c.isdigit())
        
        for promotora in promotoras:
            nombre_promotora = promotora["nombre"].strip()
            nombre_promotora_lower = nombre_promotora.lower().strip()
            nombre_promotora_sin_espacios = nombre_promotora_lower.replace(" ", "")
            nombre_promotora_sin_numeros = ''.join(c for c in nombre_promotora_lower if not c.isdigit())
            
            # Múltiples formas de coincidencia:
            # 1. Coincidencia exacta
            if nombre_usuario_lower == nombre_promotora_lower:
                return promotora["ID_Promotora"]
            
            # 2. Uno contiene al otro
            if nombre_usuario_lower in nombre_promotora_lower or nombre_promotora_lower in nombre_usuario_lower:
                return promotora["ID_Promotora"]
            
            # 3. Sin espacios
            if nombre_usuario_sin_espacios == nombre_promotora_sin_espacios:
                return promotora["ID_Promotora"]
            
            # 4. Sin números (ej: "Promotora1" coincide con "Promotora")
            if len(nombre_usuario_sin_numeros) > 2 and len(nombre_promotora_sin_numeros) > 2:
                if nombre_usuario_sin_numeros in nombre_promotora_sin_numeros or nombre_promotora_sin_numeros in nombre_usuario_sin_numeros:
                    return promotora["ID_Promotora"]
            
            # 5. Primeras palabras coinciden
            palabras_usuario = nombre_usuario_lower.split()
            palabras_promotora = nombre_promotora_lower.split()
            if palabras_usuario and palabras_promotora:
                if palabras_usuario[0] == palabras_promotora[0] and len(palabras_usuario[0]) > 3:
                    return promotora["ID_Promotora"]
        
        # Si no se encontró, retornar None
        return None
        
    except Exception as e:
        # No mostrar error aquí, se manejará en el módulo que llama
        return None
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if con:
            con.close()


def login():
    """Interfaz del login."""
    st.title("Inicio de sesión 👩‍💼")
    
    # Botón volver al menú principal
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
                # Guardar datos básicos en sesión
                st.session_state["sesion_iniciada"] = True
                st.session_state["usuario"] = datos_usuario["Usuario"]
                st.session_state["tipo_usuario"] = datos_usuario["tipo_usuario"]
                st.session_state["cargo_de_usuario"] = datos_usuario["cargo"]
                st.session_state["id_usuario"] = datos_usuario["ID_Usuario"]

                # 👉 Obtener el grupo asociado a este usuario
                id_grupo = obtener_id_grupo_por_usuario(datos_usuario["ID_Usuario"])
                st.session_state["id_grupo"] = id_grupo

                # 👉 Si es PROMOTORA, obtener su ID_Promotora
                if datos_usuario["cargo"].upper() == "PROMOTORA" or datos_usuario["tipo_usuario"].lower() == "promotora":
                    id_promotora = obtener_id_promotora_por_usuario(datos_usuario["ID_Usuario"])
                    st.session_state["id_promotora"] = id_promotora

                # Obtener permisos
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
