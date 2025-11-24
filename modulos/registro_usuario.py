import streamlit as st
import hashlib
from modulos.config.conexion import obtener_conexion

def registrar_usuario():
    st.title("Registro de nuevo usuario 👩‍💼")

    conexion = obtener_conexion()
    if not conexion:
        st.error("❌ No se pudo establecer la conexión con la base de datos.")
        return

    cursor = conexion.cursor(dictionary=True)

    try:
        # Cargar catálogos desde la base de datos
        cursor.execute("SELECT ID_Tipo_usuario, tipo_usuario AS Tipo FROM Tipo_de_usuario")
        tipos = cursor.fetchall()
        cursor.execute("SELECT ID_Cargo, tipo_de_cargo AS Cargo FROM Cargo")
        cargos = cursor.fetchall()
    except Exception as e:
        st.error(f"⚠️ Error al cargar catálogos: {e}")
        cursor.close()
        conexion.close()
        return

    # Crear diccionarios {nombre: id}
    tipo_opciones = {t["Tipo"].capitalize(): t["ID_Tipo_usuario"] for t in tipos}
    
    # 🔥 FILTRAR SOLO LOS CARGOS PERMITIDOS
    cargos_permitidos = ["Promotora", "Administrador", "Secretaria"]
    cargo_opciones_filtrados = {}
    
    for cargo in cargos:
        cargo_nombre = cargo["Cargo"].capitalize()
        if cargo_nombre in cargos_permitidos:
            cargo_opciones_filtrados[f"{cargo_nombre} ({'editor' if cargo_nombre in ['Promotora', 'Secretaria'] else 'editor'})"] = cargo["ID_Cargo"]

    # --- FORMULARIO ---
    usuario = st.text_input("Nombre de usuario")
    contraseña = st.text_input("Contraseña", type="password")
    
    # 🔥 CAMPO DUI OBLIGATORIO
    dui = st.text_input("DUI (Documento Único de Identidad)*", 
                       placeholder="00000000-0",
                       max_chars=10,
                       help="Formato: 8 dígitos, guión, 1 dígito")
    
    # 🔥 MOSTRAR SOLO CARGOS FILTRADOS
    if cargo_opciones_filtrados:
        cargo_sel_display = st.selectbox("Cargo", list(cargo_opciones_filtrados.keys()))
        # Obtener el nombre real del cargo (sin el paréntesis)
        cargo_sel = cargo_sel_display.split(" (")[0]
        id_cargo = cargo_opciones_filtrados[cargo_sel_display]
    else:
        st.error("No se encontraron cargos permitidos para registrar")
        cursor.close()
        conexion.close()
        return

    # 🔒 CORRECCIÓN: Asignar tipo EDITOR para todos los cargos
    tipo_sel = "Editor"  # Todos los cargos serán editores

    # Mostrar tipo de usuario asignado (solo lectura)
    st.text_input("Tipo de usuario asignado", tipo_sel, disabled=True)

    # --- BOTONES ---
    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Registrar usuario"):
            # 🔥 VALIDAR CAMPOS OBLIGATORIOS
            if not usuario or not contraseña or not dui:
                st.error("❌ Todos los campos marcados con * son obligatorios.")
                return
                
            # 🔥 VALIDAR FORMATO DEL DUI
            if not validar_formato_dui(dui):
                st.error("❌ Formato de DUI inválido. Use: 00000000-0")
                return
                
            try:
                id_tipo = tipo_opciones.get(tipo_sel.capitalize())

                if not id_tipo:
                    st.error("⚠️ No se encontró el tipo de usuario en la base de datos.")
                    return

                # 🔥 VERIFICAR SI EL DUI YA EXISTE
                cursor.execute("SELECT ID_Usuario FROM Usuario WHERE DUI = %s", (dui,))
                dui_existente = cursor.fetchone()
                
                if dui_existente:
                    st.error("❌ Este DUI ya está registrado en el sistema.")
                    return

                # Encriptar contraseña
                contraseña_hash = hashlib.sha256(contraseña.encode()).hexdigest()

                # 🔥 INSERTAR USUARIO CON DUI
                cursor.execute("""
                    INSERT INTO Usuario (ID_Tipo_usuario, ID_Cargo, usuario, contraseña, DUI)
                    VALUES (%s, %s, %s, %s, %s)
                """, (id_tipo, id_cargo, usuario, contraseña_hash, dui))
                conexion.commit()

                st.success(f"✅ Usuario '{usuario}' registrado correctamente como {cargo_sel} ({tipo_sel}).")

            except Exception as e:
                st.error(f"❌ Error al registrar usuario: {e}")

    with col2:
        # 👇 BOTÓN PARA VOLVER A LA PÁGINA PRINCIPAL
        if st.button("⬅️volver al inicio"):
            st.session_state["pagina_actual"] = "inicio"
            st.rerun()

    cursor.close()
    conexion.close()

def validar_formato_dui(dui):
    """Valida el formato del DUI salvadoreño"""
    import re
    # Formato: 8 dígitos, guión, 1 dígito
    patron = r'^\d{8}-\d{1}$'
    return bool(re.match(patron, dui))
