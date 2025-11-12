import streamlit as st
from modulos.config.conexion import obtener_conexion

def mostrar_grupo():
    st.header("👥 Registrar Grupo")

    try:
        con = obtener_conexion()
        cursor = con.cursor()

        # Obtener lista de promotoras
        cursor.execute("""
            SELECT u.ID_Usuario, u.Usuario 
            FROM Usuario u 
            INNER JOIN Cargo c ON u.ID_Cargo = c.ID_Cargo 
            WHERE c.tipo_de_cargo = 'PROMOTORA'
        """)
        promotoras = cursor.fetchall()

        # Formulario para registrar el grupo
        with st.form("form_grupo"):
            col1, col2 = st.columns(2)
            
            with col1:
                nombre = st.text_input("Nombre del Grupo*")
                fecha_inicio = st.date_input("Fecha de Inicio*")
                
                # Menú desplegable para duración del ciclo
                duracion_ciclo = st.selectbox(
                    "Duración del Ciclo*",
                    ["6 meses", "1 año"]
                )
            
            with col2:
                periodicidad_reuniones = st.selectbox(
                    "Periodicidad de Reuniones*",
                    ["Semanal", "Quincenal", "Mensual"]
                )
                tasa_interes = st.number_input("Tasa de Interés (%)*", min_value=0.0, step=0.1, format="%.2f")
                
                # Menú desplegable para promotoras
                if promotoras:
                    promotora_opciones = {f"{p[1]} (ID: {p[0]})": p[0] for p in promotoras}
                    promotora_seleccionada = st.selectbox(
                        "Promotora*",
                        list(promotora_opciones.keys())
                    )
                    id_promotora = promotora_opciones[promotora_seleccionada]
                else:
                    st.warning("No hay promotoras registradas")
                    id_promotora = None
            
            reglas = st.text_area("Reglas del Grupo")
            
            # Menú desplegable para distritos
            distritos = [f"DISTRITO {i}" for i in range(1, 8)]
            distrito_seleccionado = st.selectbox("Distrito*", distritos)
            id_distrito = distritos.index(distrito_seleccionado) + 1
            
            id_estado = st.number_input("ID Estado", min_value=1, step=1, value=1)

            enviar = st.form_submit_button("✅ Registrar Grupo")

            if enviar:
                # Validaciones
                if nombre.strip() == "":
                    st.warning("⚠ El nombre del grupo es obligatorio.")
                elif not id_promotora:
                    st.warning("⚠ Debe seleccionar una promotora válida.")
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
