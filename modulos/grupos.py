import streamlit as st
from modulos.config.conexion import obtener_conexion

def mostrar_grupo():
    st.header("👥 Registrar Grupo")

    try:
        con = obtener_conexion()
        cursor = con.cursor()

        # Formulario para registrar el grupo
        with st.form("form_grupo"):
            col1, col2 = st.columns(2)
            
            with col1:
                nombre = st.text_input("Nombre del Grupo*")
                fecha_inicio = st.date_input("Fecha de Inicio*")
                duracion_ciclo = st.number_input("Duración del Ciclo (días)*", min_value=1, step=1)
            
            with col2:
                periodicidad_reuniones = st.selectbox(
                    "Periodicidad de Reuniones*",
                    ["Semanal", "Quincenal", "Mensual"]
                )
                tasa_interes = st.number_input("Tasa de Interés (%)*", min_value=0.0, step=0.1, format="%.2f")
                id_promotora = st.number_input("ID Promotora*", min_value=1, step=1)
            
            reglas = st.text_area("Reglas del Grupo")
            id_distrito = st.number_input("ID Distrito", min_value=1, step=1)
            id_estado = st.number_input("ID Estado", min_value=1, step=1, value=1)

            enviar = st.form_submit_button("✅ Registrar Grupo")

            if enviar:
                # Validaciones
                if nombre.strip() == "":
                    st.warning("⚠ El nombre del grupo es obligatorio.")
                else:
                    try:
                        cursor.execute(
                            """INSERT INTO Grupo 
                            (nombre, fecha_inicio, duracion_ciclo, periodicidad_reuniones, 
                             tasa_interes, ID_Promotora, reglas, ID_Distrito, ID_Estado) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                            (nombre, fecha_inicio, duracion_ciclo, periodicidad_reuniones,
                             tasa_interes, id_promotora, reglas if reglas.strip() != "" else None, 
                             id_distrito, id_estado)
                        )
                        con.commit()
                        st.success(f"✅ Grupo '{nombre}' registrado correctamente!")
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
