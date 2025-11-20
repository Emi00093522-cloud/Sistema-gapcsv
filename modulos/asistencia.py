import streamlit as st
from modulos.config.conexion import obtener_conexion


def mostrar_asistencia():
    st.header("📝 Control de asistencia por reunión")

    try:
        con = obtener_conexion()
        cursor = con.cursor()

        # 1. Cargar reuniones (lugar + fecha)
        cursor.execute("""
            SELECT ID_Reunion, lugar, fecha, ID_Grupo
            FROM Reunion
        """)
        reuniones = cursor.fetchall()

        if not reuniones:
            st.warning("⚠ No hay reuniones registradas.")
            return

        # Diccionario: mostrar fecha | lugar
        reuniones_dict = {
            r[0]: f"{r[2]} | {r[1]}"
            for r in reuniones
        }

        id_reunion = st.selectbox(
            "Selecciona la reunión",
            options=list(reuniones_dict.keys()),
            format_func=lambda x: reuniones_dict[x]
        )

        # Obtener ID_Grupo
        id_grupo = next(r[3] for r in reuniones if r[0] == id_reunion)

        # 2. Cargar miembros del grupo
        cursor.execute("""
            SELECT ID_Miembro, nombre
            FROM Miembro
            WHERE ID_Grupo = %s
            ORDER BY nombre
        """, (id_grupo,))
        miembros = cursor.fetchall()

        if not miembros:
            st.warning("⚠ No hay miembros en este grupo.")
            return

        # 3. Cargar asistencia previa
        cursor.execute("""
            SELECT ID_Miembro, asistio, justificacion
            FROM Miembroxreunion
            WHERE ID_Reunion = %s
        """, (id_reunion,))
        asistencia_previa_raw = cursor.fetchall()
        asistencia_previa = {
            fila[0]: {"asistio": fila[1], "justificacion": fila[2]}
            for fila in asistencia_previa_raw
        }

        st.subheader("📋 Tabla de asistencia")

        # ---------------- FORMULARIO ----------------
        with st.form("form_asistencia"):

            asistencia_data = {}

            for id_miembro, nombre in miembros:

                asistio_prev = asistencia_previa.get(id_miembro, {}).get("asistio", 0)
                just_prev = asistencia_previa.get(id_miembro, {}).get("justificacion", "")

                col1, col2, col3 = st.columns([2, 1.2, 2])

                with col1:
                    st.write(nombre)

                # Selector SI/NO
                key_asistio = f"asistio_{id_miembro}"
                with col2:
                    asistio_value = st.selectbox(
                        "Asistió",
                        ["SI", "NO"],
                        index=(0 if asistio_prev == 1 else 1),
                        key=key_asistio
                    )

                # Justificación SOLO si la persona NO asistió
                justificacion = ""
                key_just = f"just_{id_miembro}"

                with col3:
                    if st.session_state.get(key_asistio) == "NO":
                        justificacion = st.text_input(
                            "Justificación",
                            value=just_prev,
                            key=key_just
                        )

                asistencia_data[id_miembro] = {
                    "asistio": 1 if asistio_value == "SI" else 0,
                    "justificacion": justificacion
                }

            guardar = st.form_submit_button("💾 Guardar asistencia")

        # ---------------- GUARDADO ----------------
        if guardar:
            try:
                for id_miembro, datos in asistencia_data.items():
                    asistio = datos["asistio"]
                    justificacion = datos["justificacion"]

                    # ¿Existe registro previo?
                    cursor.execute("""
                        SELECT ID_MiembroxReunion
                        FROM Miembroxreunion
                        WHERE ID_Miembro = %s AND ID_Reunion = %s
                    """, (id_miembro, id_reunion))
                    fila = cursor.fetchone()

                    if fila:
                        cursor.execute("""
                            UPDATE Miembroxreunion
                            SET asistio = %s,
                                justificacion = %s,
                                fecha_registro = CURRENT_TIMESTAMP
                            WHERE ID_Miembro = %s AND ID_Reunion = %s
                        """, (asistio, justificacion, id_miembro, id_reunion))

                    else:
                        cursor.execute("""
                            INSERT INTO Miembroxreunion
                            (ID_Miembro, ID_Reunion, asistio, justificacion, fecha_registro)
                            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                        """, (id_miembro, id_reunion, asistio, justificacion))

                con.commit()

                # ---- Actualizar total de presentes ----
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM Miembroxreunion
                    WHERE ID_Reunion = %s AND asistio = 1
                """, (id_reunion,))
                total_presentes = cursor.fetchone()[0]

                cursor.execute("""
                    UPDATE Reunion
                    SET total_presentes = %s
                    WHERE ID_Reunion = %s
                """, (total_presentes, id_reunion))
                con.commit()

                st.success("✅ Asistencia guardada correctamente.")

            except Exception as e:
                con.rollback()
                st.error(f"❌ Error al guardar asistencia: {e}")

    except Exception as e:
        st.error(f"❌ Error: {e}")

    finally:
        try:
            cursor.close()
            con.close()
        except:
            pass
