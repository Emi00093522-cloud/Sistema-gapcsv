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
    cargo_opciones = {c["Cargo"].capitalize(): c["ID_Cargo"] for c in cargos}

    # --- FORMULARIO ---
    usuario = st.text_input("Nombre de usuario")
    contraseña = st.text_input("Contraseña", type="password")
    cargo_sel = st.selectbox("Cargo", list(cargo_opciones.keys()))

    # 🔒 Asignar tipo automáticamente según el cargo seleccionado
    if cargo_sel.lower() in ["administradora"]:
        tipo_sel = "Lector"
    elif cargo_sel.lower() in ["presidenta", "presidente", "secretaria", "secretario", "promotora", "promotor"]:
        tipo_sel = "Editor"
    else:
        tipo_sel = "Lector"  # Por defecto, lector para cualquier otro cargo

    # Mostrar tipo de usuario asignado (solo lectura)
    st.text_input("Tipo de usuario asignado", tipo_sel, disabled=True)

    # --- BOTONES ---
    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Registrar usuario"):
            if usuario and contraseña:
                try:
                    id_tipo = tipo_opciones.get(tipo_sel.capitalize())
                    id_cargo = cargo_opciones.get(cargo_sel.capitalize())

                    if not id_tipo or not id_cargo:
                        st.error("⚠️ No se encontró el tipo o cargo en la base de datos.")
                        return

                    # Encriptar contraseña
                    contraseña_hash = hashlib.sha256(contraseña.encode()).hexdigest()

                    # Insertar usuario
                    cursor.execute("""
                        INSERT INTO Usuario (ID_Tipo_usuario, ID_Cargo, usuario, contraseña)
                        VALUES (%s, %s, %s, %s)
                    """, (id_tipo, id_cargo, usuario, contraseña_hash))
                    conexion.commit()

                    st.success(f"✅ Usuario '{usuario}' registrado correctamente como {cargo_sel} ({tipo_sel}).")

                except Exception as e:
                    st.error(f"❌ Error al registrar usuario: {e}")
            else:
                st.warning("Por favor completa todos los campos antes de continuar.")

    with col2:
        # 👇 BOTÓN PARA VOLVER A LA PÁGINA PRINCIPAL
        if st.button("⬅️volver al inicio"):
            st.session_state["pagina_actual"] = "inicio"
            st.rerun()

    cursor.close()
    conexion.close()
