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
        # Cargar catálogos
        cursor.execute("SELECT ID_Tipo_usuario, tipo_usuario AS Tipo FROM Tipo_de_usuario")
        tipos = cursor.fetchall()
        cursor.execute("SELECT ID_Cargo, tipo_de_cargo AS Cargo FROM Cargo")
        cargos = cursor.fetchall()
    except Exception as e:
        st.error(f"Error al cargar catálogos: {e}")
        cursor.close()
        conexion.close()
        return

    # Crear diccionarios {nombre: id}
    tipo_opciones = {t["Tipo"]: t["ID_Tipo_usuario"] for t in tipos}
    cargo_opciones = {c["Cargo"]: c["ID_Cargo"] for c in cargos}

    # --- Interfaz ---
    st.markdown("""
        <p>Selecciona tu cargo y completa la información para crear tu cuenta.<br>
        El tipo de usuario se asignará automáticamente según tu cargo:</p>
        <ul>
            <li>💜 Administradora / Promotora → <b>Lector</b></li>
            <li>💙 Presidenta / Secretaria → <b>Editor</b></li>
        </ul>
    """, unsafe_allow_html=True)

    # Campo: cargo
    cargo_sel = st.selectbox("Cargo", list(cargo_opciones.keys()))

    # Asignación automática del tipo
    if cargo_sel.lower() in ["administradora", "promotora"]:
        tipo_sel = "Lector"
    elif cargo_sel.lower() in ["presidenta", "secretaria"]:
        tipo_sel = "Editor"
    else:
        tipo_sel = "Lector"  # Por defecto, lector

    # Mostrar tipo bloqueado
    st.text_input("Tipo de usuario asignado", tipo_sel, disabled=True)

    # Campos de usuario y contraseña
    usuario = st.text_input("Nombre de usuario")
    contraseña = st.text_input("Contraseña", type="password")

    # --- Registrar ---
    if st.button("Registrar usuario"):
        if usuario and contraseña:
            try:
                # Buscar los IDs en base de datos
                id_tipo = tipo_opciones.get(tipo_sel)
                id_cargo = cargo_opciones.get(cargo_sel)

                if not id_tipo or not id_cargo:
                    st.error("⚠️ No se encontró el tipo o cargo en la base de datos.")
                    return

                # Encriptar contraseña
                contraseña_hash = hashlib.sha256(contraseña.encode()).hexdigest()

                # Insertar usuario
                cursor.execute("""
                    INSERT INTO Usuario (ID_Tipo_usuario, ID_Cargo, usuario, contraseña)
                    VALUES (%
