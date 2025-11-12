import streamlit as st
from modulos.config.conexion import obtener_conexion

def mostrar_distrito():
    st.header("🏛️ Registrar Distrito")
    st.success("👋 ¡Hola, promotor!")
    
    # Variable para controlar el estado de éxito
    if 'distrito_creado' not in st.session_state:
        st.session_state.distrito_creado = False

    # Si ya se creó un distrito, mostrar mensaje de éxito con opciones
    if st.session_state.distrito_creado:
        st.success("✅ Distrito almacenado con éxito!")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🆕 Crear nuevo distrito"):
                st.session_state.distrito_creado = False
                st.rerun()
        with col2:
            if st.button("🏠 Volver al menú principal"):
                # Aquí puedes redirigir a tu menú principal
                st.success("Redirigiendo al menú principal...")
                # st.experimental_rerun() o tu función de navegación
        return

    try:
        con = obtener_conexion()
        cursor = con.cursor()

        # Formulario simple para registrar el distrito
        with st.form("form_distrito"):
            st.subheader("Nuevo Distrito")
            
            nombre = st.text_input(
                "Nombre del distrito *",
                placeholder="Ingrese el nombre del distrito"
            )
            
            codigo = st.text_input(
                "Código del distrito (numérico, opcional)",
                placeholder="Solo números, máximo 10 dígitos",
                max_chars=10
            )
            
            enviar = st.form_submit_button("💾 Guardar distrito")

            if enviar:
                if nombre.strip() == "":
                    st.warning("⚠ Debes ingresar el nombre del distrito.")
                else:
                    # Validar que el código sea numérico si se ingresó
                    if codigo.strip() != "":
                        if not codigo.strip().isdigit():
                            st.error("❌ El código debe contener solo números.")
                        else:
                            guardar_distrito(nombre.strip(), codigo.strip(), cursor, con)
                    else:
                        guardar_distrito(nombre.strip(), None, cursor, con)

    except Exception as e:
        st.error(f"❌ Error de conexión: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'con' in locals():
            con.close()

def guardar_distrito(nombre, codigo, cursor, con):
    """Función para guardar el distrito en la base de datos"""
    try:
        cursor.execute(
            "INSERT INTO Distritos (nombre, codigo) VALUES (%s, %s)",
            (nombre, codigo)
        )
        con.commit()
        
        # Obtener el ID del distrito recién insertado
        cursor.execute("SELECT LAST_INSERT_ID()")
        id_distrito = cursor.fetchone()[0]
        
        st.session_state.distrito_creado = True
        st.session_state.ultimo_id = id_distrito
        st.session_state.ultimo_nombre = nombre
        st.rerun()
        
    except Exception as e:
        con.rollback()
        st.error(f"❌ Error al registrar el distrito: {e}")

# Función principal
def gestionar_distritos():
    mostrar_distrito()
