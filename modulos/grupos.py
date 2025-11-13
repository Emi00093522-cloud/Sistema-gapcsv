import streamlit as st
from modulos.config.conexion import obtener_conexion
from datetime import datetime

def mostrar_grupos():
    st.header("👥 Registrar Grupo")

    # Estado para controlar el mensaje de éxito
    if 'grupo_registrado' not in st.session_state:
        st.session_state.grupo_registrado = False

    if st.session_state.grupo_registrado:
        st.success("🎉 ¡Grupo registrado con éxito!")
        
        if st.button("🆕 Registrar otro grupo"):
            st.session_state.grupo_registrado = False
            st.rerun()
        
        st.info("💡 **Para seguir navegando, selecciona una opción en el menú de la izquierda**")
        return

    try:
        con = obtener_conexion()
        cursor = con.cursor()

        # Obtener datos para los menús desplegables
        # 1. Obtener distritos registrados
        cursor.execute("SELECT ID_Distrito, nombre FROM Distrito")
        distritos = cursor.fetchall()
        
        # 2. Obtener promotoras registradas
        cursor.execute("SELECT ID_Promotora, nombre FROM Promotora")
        promotoras = cursor.fetchall()

        # Formulario para registrar el grupo
        with st.form("form_grupo"):
            st.subheader("Datos del Grupo")
            
            # Campo 2: nombre (varchar(100), obligatorio)
            nombre = st.text_input("Nombre del grupo *", 
                                 placeholder="Ingrese el nombre del grupo",
                                 max_chars=100)
            
            # Campo 3: ID_Distrito (opcional) - Menú desplegable con distritos
            if distritos:
                distrito_options = {f"Sin distrito": None}
                distrito_options.update({f"{distrito[1]} (ID: {distrito[0]})": distrito[0] for distrito in distritos})
                distrito_seleccionado = st.selectbox("Distrito (opcional)", 
                                                   options=list(distrito_options.keys()),
                                                   index=0)
                ID_Distrito = distrito_options[distrito_seleccionado]
            else:
                ID_Distrito = None
                st.info("No hay distritos disponibles")
            
            # Campo 4: fecha_inicio (date, obligatorio)
            fecha_inicio = st.date_input("Fecha de inicio *",
                                       value=datetime.now().date(),
                                       min_value=datetime.now().date())
            
            # Campo 5: duracion_ciclo (int, obligatorio) - 6 o 12 meses
            duracion_ciclo = st.selectbox("Duración del ciclo *",
                                        options=[6, 12],
                                        format_func=lambda x: f"{x} meses")
            
            # Campo 6: periodicidad_reuniones (varchar(20), obligatorio)
            st.write("**Periodicidad de reuniones ***")
            col1, col2 = st.columns(2)
            
            with col1:
                tipo_periodicidad = st.selectbox("Tipo de periodicidad",
                                               options=["Días", "Semanas", "Meses"])
            
            with col2:
                if tipo_periodicidad == "Días":
                    valor_periodicidad = st.selectbox("Días",
                                                    options=list(range(1, 32)))
                    periodicidad_reuniones = f"{valor_periodicidad} días"
                elif tipo_periodicidad == "Semanas":
                    valor_periodicidad = st.selectbox("Semanas",
                                                    options=list(range(1, 5)))
                    periodicidad_reuniones = f"{valor_periodicidad} semanas"
                else:  # Meses
                    valor_periodicidad = st.selectbox("Meses",
                                                    options=list(range(1, 13)))
                    periodicidad_reuniones = f"{valor_periodicidad} meses"
            
            # Campo 7: tasa_interes (decimal(5,2), obligatorio)
            tasa_interes = st.number_input("Tasa de interés (%) *",
                                         min_value=0.0,
                                         max_value=100.0,
                                         value=5.0,
                                         step=0.5,
                                         format="%.2f")
            
            # Campo 8: ID_Promotora (int, obligatorio) - Menú desplegable con promotoras
            if promotoras:
                promotora_options = {f"{promotora[1]} (ID: {promotora[0]})": promotora[0] for promotora in promotoras}
                promotora_seleccionada = st.selectbox("Promotora *", 
                                                    options=list(promotora_options.keys()))
                ID_Promotora = promotora_options[promotora_seleccionada]
            else:
                st.error("No hay promotoras disponibles en la base de datos")
                ID_Promotora = None
            
            # Campo 9: ID_Estado (int, opcional) - 1=Activo, 2=Inactivo
            ID_Estado = st.selectbox("Estado",
                                   options=[1, 2],
                                   format_func=lambda x: "Activo" if x == 1 else "Inactivo",
                                   index=0)
            
            enviar = st.form_submit_button("✅ Guardar Grupo")

            if enviar:
                if nombre.strip() == "":
                    st.warning("⚠ Debes ingresar el nombre del grupo.")
                elif ID_Promotora is None:
                    st.warning("⚠ Debes seleccionar una promotora.")
                else:
                    try:
                        # Convertir valores opcionales a NULL si están vacíos
                        ID_Distrito_val = ID_Distrito
                        ID_Estado_val = ID_Estado
                        
                        # INSERT en la tabla Grupo
                        cursor.execute(
                            """INSERT INTO Grupo 
                            (nombre, ID_Distrito, fecha_inicio, duracion_ciclo, 
                             periodicidad_reuniones, tasa_interes, ID_Promotora, ID_Estado) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                            (nombre.strip(), ID_Distrito_val, fecha_inicio, duracion_ciclo,
                             periodicidad_reuniones, tasa_interes, ID_Promotora, ID_Estado_val)
                        )
                        
                        con.commit()
                        
                        # Obtener el ID del grupo recién insertado
                        cursor.execute("SELECT LAST_INSERT_ID()")
                        id_grupo = cursor.fetchone()[0]
                        
                        # Guardar en session_state para mostrar mensaje de éxito
                        st.session_state.grupo_registrado = True
                        st.session_state.id_grupo_creado = id_grupo
                        st.session_state.nombre_grupo_creado = nombre.strip()
                        
                        st.rerun()
                        
                    except Exception as e:
                        con.rollback()
                        st.error(f"❌ Error al registrar el grupo: {e}")

    except Exception as e:
        st.error(f"❌ Error de conexión: {e}")

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'con' in locals():
            con.close()
