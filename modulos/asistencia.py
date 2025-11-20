import streamlit as st
from modulos.config.conexion import obtener_conexion


def mostrar_asistencia():
    st.header("📝 Control de asistencia por reunión")

    try:
        con = obtener_conexion()
        cursor = con.cursor()

        # Reuniones
        cursor.execute("""
            SELECT ID_Reunion, lugar, fecha, ID_Grupo
            FROM Reunion
        """)
        reuniones = cursor.fetchall()

        if not reuniones:
            st.warning("⚠ No hay reuniones registradas.")
            return

        reuniones_dict = {r[0]: f"{r[2]} | {r[1]}" for r in reuniones}

        id_reunion = st.selectbox(
            "Selecciona la reunión",
            options=list(reuniones_dict.keys()),
            format_func=lambda x: reuniones_dict[x]
        )

        id_grupo = next(r[3] for r in reuniones if r[0] == id_reunion)

        # Miembros
        cursor.execute("""
            SELECT ID_Miembro, nombre
            FROM Miembro
            WHERE ID_Grupo = %s
            ORDER BY nombre
        """, (id_grupo,))
        miembros = cursor.fetchall()

        if not miembros:
            st.warning("⚠ No hay miembros para este grupo.")
            return

        # Asistencia previa
        cursor.execute("""
            SELECT ID_Miembro, asistio, justificacion
            FROM Miembroxreunion
            WHERE ID_Reunion = %s
        """, (id_reunion,))
        prev = cursor.fetchall()

        asistencia_previa = {
            fila[0]: {"asistio": fila[1], "justificacion": fila[2]}
            for fila in prev
        }

        st.subheader("📋 Lista de asistencia")

        with st.form("form_asistencia"):
            asistencia_data = {}

            for id_miembro, nombre in miembros:

                asistio_prev = asistencia_previa.get(id_miembro, {}).get("asistio", 1)
                just_prev = asistencia_previa.get(id_miembro, {}).get("justificacion", "")

                col1, col2, col3 = st.columns([2, 1.2, 2])

                with col1:
                    st.write(nombre)

                # ---------- SELECTBOX ----------
                key_asistio = f"asistio_{id_miembro}"
                with col2:
                    asistio = st.selectbox(
                        f"Asistió_{id_miembro}",          # Label ÚNICO
                        ["SI", "NO"],
                        index=(0 if asistio_prev == 1 else 1),
                        key=key_asistio
                    )

                # ---------- JUSTIFICACIÓN SOLO SI ES "NO" ----------
                key_just = f"just_{id_miembro}"
                with col3:
                    if st.session_state.get(key_asistio) == "NO":
                        justificacion = st.text_input(
                            f"Justificacion_{id_miembro}",  # Label ÚNICO
                            value=just_prev,
                            key=key_just
                        )
                    else:
                        justificacion = ""

                asistencia_data[id_miembro] = {
                    "asistio": 1 if asistio == "SI" else 0,
                    "justificacion": justificacion
                }

            guardar = st.form_submit_button("💾 Guardar asistencia")

        if guardar:
            try:
                for id_miembro, datos in asistencia_data.items():
                    asistio = datos["asistio"]
                    justificacion = datos["justificacion"]

                    # Verificar si existe
                    cursor.execute("""
                        SELECT ID_MiembroxReunion
                        FROM Miembroxreunion
                        WHERE ID_Miembro = %s AND ID_Reunion = %s
                    """, (id_miembro, id_reunion))
                    existe = cursor.fetchone()

                    if existe:
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

                st.success("✔ Asistencia guardada correctamente.")

            except Exception as e:
                con.rollback()
                st.error(f"❌ Error al guardar: {e}")

    except Exception as e:
        st.error(f"❌ Error: {e}")

    finally:
        try:
            cursor.close()
            con.close()
        except:
            pass
