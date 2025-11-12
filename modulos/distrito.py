import streamlit as st
from modulos.config.conexion import obtener_conexion

def mostrar_distrito():
    st.header("🏛️ Registrar Distrito")
    st.success("👋 ¡Hola, promotor!")
    
    # Variable para controlar el estado de éxito
    if 'distrito_creado' not in st.session_state:
        st.session_state.distrito_creado = False
    if 'id_distrito_creado' not in st.session_state:
        st.session_state.id_distrito_creado = None
    if 'nombre_distrito_creado' not in st.session_state:
        st.session_state.nombre_distrito_creado = ""

    # Si ya se creó un distrito, mostrar mensaje de éxito
    if st.session_state.distrito_creado:
        st.success("🎉 ¡Distrito creado con éxito!")
        st.info(f"**ID del distrito:** {st.session_state.id_distrito_creado}")
        st.info(f"**Nombre del distrito:** {st.session_state.nombre_distrito_creado}")
        
        # Botón para regresar a la pantalla de inicio
        if st.button("🏠 Regresar a Inicio"):
            st.session_state.distrito_creado = False
            st.session_state.id_distrito_creado = None
            st.session_state.nombre_distrito_creado = ""
            st.rerun()
        return

    try:
        con = obtener_conexion()
        cursor = con.cursor()

        # Formulario para registrar el distrito
        with st.form("form_distrito"):
            nombre = st.text_input("Nombre del distrito", 
                                 placeholder="Ingrese el nombre completo del distrito")
            codigo = st.text_input("Código del distrito (opcional)", 
                                 placeholder="Ingrese el código (máx. 10 caracteres)",
                                 max_chars=10)
            enviar = st.form_submit_button("💾 Guardar distrito")

            if enviar:
                if nombre.strip() == "":
                    st.warning("⚠ Debes ingresar el nombre del distrito.")
                else:
                    try:
                        # Si el código está vacío, lo convertimos a None (NULL en la BD)
                        codigo_valor = codigo.strip() if codigo.strip() != "" else None
                        
                        # Insertar en la tabla usando la estructura de tu foto
                        cursor.execute(
                            "INSERT INTO Distritos (nombre, codigo) VALUES (%s, %s)",
                            (nombre.strip(), codigo_valor)
                        )
                        con.commit()
                        
                        # Obtener el ID del distrito recién insertado
                        cursor.execute("SELECT LAST_INSERT_ID()")
                        id_distrito = cursor.fetchone()[0]
                        
                        # Guardar en session_state para mostrar en el mensaje de éxito
                        st.session_state.distrito_creado = True
                        st.session_state.id_distrito_creado = id_distrito
                        st.session_state.nombre_distrito_creado = nombre.strip()
                        
                        st.rerun()
                        
                    except Exception as e:
                        con.rollback()
                        st.error(f"❌ Error al registrar el distrito: {e}")

    except Exception as e:
        st.error(f"❌ Error de conexión: {e}")

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'con' in locals():
            con.close()

# Función para mostrar distritos existentes (opcional)
def mostrar_distritos_existentes():
    try:
        con = obtener_conexion()
        cursor = con.cursor()
        
        cursor.execute("SELECT ID_Distrito, nombre, codigo FROM Distritos ORDER BY ID_Distrito DESC LIMIT 5")
        distritos = cursor.fetchall()
        
        if distritos:
            st.subheader("📋 Distritos recientes")
            for distrito in distritos:
                id_dist, nombre, codigo = distrito
                codigo_display = codigo if codigo else "Sin código"
                st.write(f"**ID {id_dist}:** {nombre} - {codigo_display}")
                
    except Exception as e:
        st.error(f"Error al cargar distritos: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'con' in locals():
            con.close()

# Función principal
def gestionar_distritos():
    mostrar_distrito()
    
    # Solo mostrar distritos existentes si no estamos en estado de éxito
    if not st.session_state.distrito_creado:
        st.divider()
        mostrar_distritos_existentes()
