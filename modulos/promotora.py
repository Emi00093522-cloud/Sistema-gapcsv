import streamlit as st
from modulos.config.conexion import obtener_conexion

def mostrar_promotora():
    st.header("👩‍💼 Registrar Promotora")

    # Estado para controlar el mensaje de éxito
    if 'promotora_registrada' not in st.session_state:
        st.session_state.promotora_registrada = False
    if 'id_promotora_creada' not in st.session_state:
        st.session_state.id_promotora_creada = None
    if 'nombre_promotora_creada' not in st.session_state:
        st.session_state.nombre_promotora_creada = ""

    # Mostrar mensaje de éxito si ya se registró
    if st.session_state.promotora_registrada:
        st.success("🎉 ¡Promotora registrada con éxito!")
        st.info(f"**ID de la promotora:** {st.session_state.id_promotora_creada}")
        st.info(f"**Nombre:** {st.session_state.nombre_promotora_creada}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🆕 Registrar otra promotora"):
                st.session_state.promotora_registrada = False
                st.session_state.id_promotora_creada = None
                st.session_state.nombre_promotora_creada = ""
                st.rerun()
        with col2:
            if st.button("🏠 Volver al menú"):
                st.session_state.promotora_registrada = False
                st.success("Redirigiendo al menú principal...")
        return

    try:
        con = obtener_conexion()
        cursor = con.cursor()

        # Obtener opciones para el estado
        cursor.execute("SELECT ID_Estado, nombre FROM Estado")
        estados = cursor.fetchall()

        # Formulario para registrar la promotora
        with st.form("form_promotora"):
            st.subheader("Datos de la Promotora")
            
            # Campo obligatorio: nombre
            nombre = st.text_input("Nombre completo *", 
                                 placeholder="Ingrese el nombre completo de la promotora",
                                 max_chars=100)
            
            # Campo opcional: teléfono
            telefono = st.text_input("Teléfono (opcional)", 
                                   placeholder="Ingrese número de teléfono",
                                   max_chars=20)
            
            # Llave foránea: ID_Estado (obligatorio)
            if estados:
                estado_options = {f"{estado[1]} (ID: {estado[0]})": estado[0] for estado in estados}
                estado_seleccionado = st.selectbox("Estado *", 
                                                 options=list(estado_options.keys()))
                ID_Estado = estado_options[estado_seleccionado]
            else:
                st.error("No hay estados disponibles en la base de datos")
                ID_Estado = None
            
            enviar = st.form_submit_button("✅ Guardar Promotora")

            if enviar:
                if nombre.strip() == "":
                    st.warning("⚠ Debes ingresar el nombre de la promotora.")
                elif ID_Estado is None:
                    st.warning("⚠ Debes seleccionar un estado.")
                else:
                    try:
                        # Convertir teléfono a NULL si está vacío
                        telefono_val = telefono.strip() if telefono.strip() != "" else None
                        
                        # INSERT con los nombres REALES de las columnas
                        cursor.execute(
                            """INSERT INTO Promotora 
                            (nombre, telefono, ID_Estado) 
                            VALUES (%s, %s, %s)""",
                            (nombre.strip(), telefono_val, ID_Estado)
                        )
                        
                        con.commit()
                        
                        # Obtener el ID de la promotora recién insertada
                        cursor.execute("SELECT LAST_INSERT_ID()")
                        id_promotora = cursor.fetchone()[0]
                        
                        # Guardar en session_state para mostrar mensaje de éxito
                        st.session_state.promotora_registrada = True
                        st.session_state.id_promotora_creada = id_promotora
                        st.session_state.nombre_promotora_creada = nombre.strip()
                        
                        st.rerun()
                        
                    except Exception as e:
                        con.rollback()
                        st.error(f"❌ Error al registrar la promotora: {e}")

    except Exception as e:
        st.error(f"❌ Error de conexión: {e}")

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'con' in locals():
            con.close()
