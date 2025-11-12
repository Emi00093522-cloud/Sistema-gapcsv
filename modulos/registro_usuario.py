import streamlit as st
import hashlib
from modulos.config.conexion import obtener_conexion

def registrar_usuario():
    st.title("Registro de nuevo usuario 👩‍💼")

    conexion = obtener_conexion()
    if not conexion:
        return

    cursor = conexion.cursor(dictionary=True)

    # Cargar catálogos
    cursor.execute("SELECT ID_Tipo_usuario, Tipo FROM Tipo_de_usuario")
    tipos = cursor.fetchall()
    cursor.execute("SELECT ID_Cargo, Cargo FROM Cargo")
    cargos = cursor.fetchall()

    # Crear listas para los select
    tipo_opciones = {t["Tipo"]: t["ID_Tipo_usuario"] for t in tipos}
    cargo_opciones = {c["Cargo"]: c["ID_Cargo"] for c in cargos}

    # Formulario
    usuario = st.text_input("Nombre de usuario")
    contraseña = st.text_input("Contraseña", type="password")
    tipo_sel = st.selectbox("Tipo de usuario", list(tipo_opciones.keys()))
    cargo_sel = st.selectbox("Cargo", list(cargo_opciones.keys()))

    if st.button("Registrar usuario"):
        if usuario and contraseña:
            # Encriptar contraseña
            contraseña_hash = hashlib.sha256(contraseña.encode()).hexdigest()

            # Insertar en la BD
            try:
                cursor.execute("""
                    INSERT INTO Usuario (ID_Tipo_usuario, ID_Cargo, usuario, contraseña)
                    VALUES (%s, %s, %s, %s)
                """, (tipo_opciones[tipo_sel], cargo_opciones[cargo_sel], usuario, contraseña_hash))
                conexion.commit()
                st.success("✅ Usuario registrado exitosamente")
            except Exception as e:
                st.error(f"❌ Error al registrar usuario: {e}")
        else:
            st.warning("Por favor completa todos los campos")

    cursor.close()
    conexion.close()
