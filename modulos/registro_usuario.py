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

    # Convertir resultados en diccionarios
    tipo_opciones = {t["Tipo"]: t["ID_Tipo_usuario"] for t in tipos}
    cargo_opciones = {c["Cargo"]: c["ID_Cargo"] for c in cargos}

    # --- Interfaz ---
    st.markdown("""
        <p>Selecciona tu cargo y completa la información para crear tu cuenta. 
        Solo los usuarios con roles de <b>Administradora</b> o <b>Promotora</b> pueden registrarse, 
        y ambos se registran como <b>Lectores</b>.</p>
    """, unsafe_allow_html=True)

    # 🔸 Seleccionar cargo
    cargo_sel = st.selectbox("Cargo", ["Administradora", "Promotora"])

    # 🔒 Tipo de usuario fijo: lector
    tipo_sel = "Lector"
    st.text_input("Tipo de usuario", tipo_sel, disabled=True)

    usuario = st.text_input("Nombre de usuario")
    contraseña = st.text_input("Contraseña", type="password")

    if st.button("Registrar usuario"):
        if usuario and contraseña and cargo_sel:
            try:
                # Buscar los IDs correctos
                id_tipo = tipo_opciones.get(tipo_sel)
                id_cargo = cargo_opciones.get(cargo_sel)

                if not id_tipo or not id_cargo:
                    st.error("No se pudo encontrar el tipo o cargo correspondiente en la base de datos.")
                    return

                # Encriptar la contraseña
                contraseña_hash = hashlib.sha256(contraseña.encode()).hexdigest()

                # Insertar en la base de datos
                cursor.execute("""
                    INSERT INTO Usuario (ID_Tipo_usuario, ID_Cargo, usuario, contraseña)
                    VALUES (%s, %s, %s, %s)
                """, (id_tipo, id_cargo, usuario, contraseña_hash))
                conexion.commit()
                st.success(f"✅ Usuario '{usuario}' registrado correctamente como {cargo_sel} (Lector).")

            except Exception as e:
                st.error(f"❌ Error al registrar usuario: {e}")
        else:
            st.warning("Por favor completa todos los campos.")

    cursor.close()
    conexion.close()
