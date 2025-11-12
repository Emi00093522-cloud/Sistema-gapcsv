import streamlit as st
import hashlib
from modulos.config.conexion import obtener_conexion

def registrar_usuario():
    st.title("Registro de nuevo usuario 👩‍💼")

    conexion = obtener_conexion()
    if not conexion:
        st.error("No se pudo establecer la conexión con la base de datos.")
        return

    cursor = conexion.cursor(dictionary=True)

    try:
        # Cargar catálogos de tipo y cargo
        cursor.execute("SELECT ID_Tipo_usuario, tipo_usuario AS Tipo FROM Tipo_de_usuario")
        tipos = cursor.fetchall()
        cursor.execute("SELECT ID_Cargo, tipo_de_cargo AS Cargo FROM Cargo")
        cargos = cursor.fetchall()
    except Exception as e:
        st.error(f"Error al cargar catálogos: {e}")
        cursor.close()
        conexion.close()
        return

    # Crear diccionarios para los select
    tipo_opciones = {t["Tipo"]: t["ID_Tipo_usuario"] for t in tipos}
    cargo_opciones = {c["Cargo"]: c["ID_Cargo"] for c in cargos}

    # --- FORMULARIO ---
    usuario = st.text_input("Nombre de usuario")
    contraseña = st.text_input("Contraseña", type="password")
    tipo_sel = st.selectbox("Tipo de usuario", list(tipo_opciones.keys()))

    # ✅ Filtrar cargos según tipo seleccionado
    if tipo_sel.lower() in ["administradora", "promotora"]:
        st.info("Los usuarios Administradora y Promotora solo pueden registrarse con cargo 'Lector'.")
        cargos_filtrados = {k: v for k, v in cargo_opciones.items() if k.lower() == "lector"}
    else:
        cargos_filtrados = cargo_opciones  # Por si en el futuro agregas otros tipos de usuario

    cargo_sel = st.selectbox("Cargo", list(cargos_filtrados.keys()))

    if st.button("Registrar usuario"):
        if usuario and contraseña:
            # Encriptar la contraseña
            contraseña_hash = hashlib.sha256(contraseña.encode()).hexdigest()

            # Insertar usuario
            try:
                cursor.execute("""
                    INSERT INTO Usuario (ID_Tipo_usuario, ID_Cargo, usuario, contraseña)
                    VALUES (%s, %s, %s, %s)
                """, (tipo_opciones[tipo_sel], cargos_filtrados[cargo_sel], usuario, contraseña_hash))
                conexion.commit()
                st.success(f"✅ Usuario '{usuario}' registrado exitosamente como {tipo_sel} (Cargo: {cargo_sel})")
            except Exception as e:
                st.error(f"❌ Error al registrar usuario: {e}")
        else:
            st.warning("Por favor completa todos los campos antes de continuar.")

    cursor.close()
    conexion.close()

