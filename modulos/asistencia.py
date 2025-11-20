import streamlit as st
from modulos.config.conexion import obtener_conexion

def mostrar_asistencia():
    st.header("📝 Control de asistencia por reunión")

    try:
        con = obtener_conexion()
        cursor = con.cursor()

        # 1. Obtener reuniones
        cursor.execute("""
            SELECT ID_Reunion, lugar, fecha, ID_Grupo
            FROM Reunion
        """)
        reuniones = cursor.fetchall()

        if not reuniones:
            st.warning("⚠ No hay reuniones registradas.")
            return

        reuniones_dict = {
            r[0]: f"{r[2]} | {r[1]}"
            for r in reuniones
        }

        id_reunion = st.selectbox(
            "Selecciona la reunión",
            options=list(reuniones_dict.keys()),
            format_func=lambda x: reuniones_dict[x]
        )

        # Identificar grupo
        id_grupo = None
        for r in reuniones:
            if r[0] == id_reunion:
                id_grupo = r[3]
                break

        # 2. Obtener miembros
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

        # 3. Obtener asistencia previa
        cursor.execute("""
            SELECT ID_Miembro, asistio, justificacion
            FROM Miembroxreunion
            WHERE ID_Reunion = %s
        """, (id_reunion,))
        asistencia_previa = {
            row[0]: {"asistio": row[1], "justificacion": row[2]}
            for row in cursor.fetchall()
        }

        st.subheader("👥 Lista de asistencia")

        if "asistencia_data" not in st.session_state:
            st.session_state.asistencia_data = {
                m[0]: {
                    "asistio": asistencia_previa.get(m[0], {}).get("asistio", 1),
                    "justificacion": asistencia_previa.get(m[0], {}).get("justificacion", "")
                }
                for m in miembros
            }

        # ------- TABLA DINÁMICA -------
        for id_m, nombre in miembros:
            st.write(f"### {nombre}")

            col1, col2 = st.columns([1, 3])

            # Checkbox de asistencia
            with col1:
                asistio = st.checkbox(
                    "Asistió",
                    value=True if st.session_state.asistencia_data[id_m]["asistio"] == 1 else False,
                    key=f"chk_{id_m}"
                )

            # Si NO asistió → mostrar campo de justificación
            with col2:
                if not asistio:
                    just = st.text_input(
                        "Justificación",
                        value=st.session_state.asistencia_data[id_m]["justificacion"],
                        key=f"just_{id_m}"
                    )
                else:
                    just = ""

            # Actualizar estado
            st.session_state.asistencia_data[id_m]["asistio"] = 1 if asistio else 0
            st.session_state.asistencia_data[id_m]["justificacion"] = just

            st.markdown("---")

        # ------- GUARDAR -------
        if st.button("💾 Guardar asistencia"):
            try:
                for id_m, datos in st.session_state.asistencia_data.items():
                    asistio = datos["asistio"]
                    justificacion = datos["justificacion"]

                    # Verificar si existe registro
                    cursor.execute("""
                        SELECT ID_MiembroxReunion
                        FROM Miembroxreunion
                        WHERE ID_Miembro = %s AND ID_Reunion = %s
                    """, (id_m, id_reunion))
                    fila = cursor.fetchone()

                    if fila:
                        cursor.execute("""
                            UPDATE Miembroxreunion
                            SET asistio = %s,
                                justificacion = %s,
                                fecha_registro = CURRENT_TIMESTAMP
                            WHERE ID_Miembro = %s AND ID_Reunion = %s
                        """, (asistio, justificacion, id_m, id_reunion))

                    else:
                        cursor.execute("""
                            INSERT INTO Miembroxreunion
                            (ID_Miembro, ID_Reunion, asistio, justificacion, fecha_registro)
                            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                        """, (id_m, id_reunion, asistio, justificacion))

                con.commit()

                # Actualizar total de presentes
                cursor.execute("""
                    SELECT COUNT(*) FROM Miembroxreunion
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
                st.error(f"❌ Error al guardar: {e}")

    except Exception as e:
        st.error(f"❌ Error: {e}")

    finally:
        if "cursor" in locals(): cursor.close()
        if "con" in locals(): con.close()
