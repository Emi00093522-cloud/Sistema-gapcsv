import streamlit as st
from modulos.config.conexion import obtener_conexion

def mostrar_promotora():
    st.header("👩‍💼 Registrar Promotora")

    try:
        con = obtener_conexion()
        cursor = con.cursor()

        # Formulario para registrar la promotora
        with st.form("form_promotora"):
            st.subheader("Datos de la Promotora")
            
            # Campo 2: nombre (varchar(100), obligatorio)
            nombre = st.text_input("Nombre completo *", 
                                 placeholder="Ingrese el nombre completo de la promotora",
                                 max_chars=100)
            
            # Campo 3: (int, opcional) - Asumo que es algo como ID_Distrito o similar
            id_distrito = st.number_input("ID de Distrito (opcional)", 
                                        min_value=0, 
                                        step=1,
                                        value=0)
            
            # Campo 4: (varchar(100), opcional) - Asumo que es dirección o email
            direccion_email = st.text_input("Dirección o Email (opcional)", 
                                          placeholder="Ingrese dirección o email",
                                          max_chars=100)
            
            # Campo 5: (varchar(20), opcional) - Asumo que es teléfono
            telefono = st.text_input("Teléfono (opcional)", 
                                   placeholder="Ingrese número de teléfono",
                                   max_chars=20)
            
            # Campo 6: (int, opcional, default 1) - Asumo que es estado o activo
            estado = st.selectbox("Estado", 
                                options=[1, 0], 
                                format_func=lambda x: "Activo" if x == 1 else "Inactivo",
                                index=0)
            
            # Campo 7: (int, obligatorio) - Asumo que es algún ID de referencia
            id_referencia = st.number_input("ID de Referencia *", 
                                          min_value=1, 
                                          step=1)
            
            enviar = st.form_submit_button("✅ Guardar Promotora")

            if enviar:
                if nombre.strip() == "":
                    st.warning("⚠ Debes ingresar el nombre de la promotora.")
                elif id_referencia <= 0:
                    st.warning("⚠ Debes ingresar un ID de referencia válido.")
                else:
                    try:
                        # Convertir valores opcionales a NULL si están vacíos
                        id_distrito_val = id_distrito if id_distrito > 0 else None
                        direccion_val = direccion_email.strip() if direccion_email.strip() != "" else None
                        telefono_val = telefono.strip() if telefono.strip() != "" else None
                        
                        cursor.execute(
                            """INSERT INTO Promotora 
                            (nombre, campo3, campo4, campo5, campo6, campo7) 
                            VALUES (%s, %s, %s, %s, %s, %s)""",
                            (nombre.strip(), id_distrito_val, direccion_val, telefono_val, estado, id_referencia)
                        )
                        con.commit()
                        
                        # Obtener el ID de la promotora recién insertada
                        cursor.execute("SELECT LAST_INSERT_ID()")
                        id_promotora = cursor.fetchone()[0]
                        
                        st.success(f"✅ Promotora registrada correctamente!")
                        st.info(f"**ID de la promotora:** {id_promotora}")
                        st.info(f"**Nombre:** {nombre.strip()}")
                        
                        # Botones de acción después del registro
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("🆕 Registrar otra promotora"):
                                st.rerun()
                        with col2:
                            if st.button("🏠 Volver al menú principal"):
                                st.success("Redirigiendo al menú principal...")
                        
                    except Exception as e:
                        con.rollback()
                        st.error(f"❌ Error al registrar la promotora: {e}")

    except Exception as e:
        st.error(f"❌ Error general: {e}")

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'con' in locals():
            con.close()
