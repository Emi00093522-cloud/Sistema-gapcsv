import streamlit as st
from modulos.config.conexion import obtener_conexion

def mostrar_asistencia():
    st.header("📝 Control de asistencia por reunión")

    try:
        con = obtener_conexion()
        cursor = con.cursor()

        # 1. Cargar reuniones
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

        # Obtener ID_Grupo asociado
        id_grupo = next((r[3] for r in reuniones if r[0] == id_reunion), None)

        # 2. Cargar miembros
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

        # 3. Cargar asistencia previa (incluye justificación)
        cursor.execute("""
            SELECT ID_Miembro, asistio, justificacion
            FROM Miembroxreunion
            WHERE ID_Reunion = %s
        """, (id_reunion,))
        asistencia_previa = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}

        st.subheader("👥 Lista de asistencia")

        checkboxes = {}
        justificaciones = {}

        with st.form("form_asistencia"):
            st.write("### Tabla de asistencia")

            for id_miembro, nombre in miembros:
                asistio_prev, just_prev = asistencia_previa.get(id_miembro, (0, ""))

                col1, col2, col3 = st.columns([2, 1, 3])

                # Nombre
                col1.write(nombre)

                # SI / NO
                asistio = col2.selectbox(
                    "Asistió",
                    ["SI", "NO"],
                    index=0 if asistio_prev == 1 else 1,
                    key=f"asistio_{id_miembro}"
                )

                # Justificación solo si NO asistió
                justificacion = ""
                if asistio == "NO":
                    justificacion = col3.text_input(
                        "Justificación",
                        value=just_prev or "",
                        key=f"just_{id_miembro}"
                    )
                else:
                    col3.write("—")

                checkboxes[id_miembro] = 1 if asistio == "SI" else 0
                justificaciones[id_miembro] = justificacion

            guardar = st.form_submit_button("💾 Guardar asistencia")

        if guardar:
            try:
                for id_miembro in checkboxes.keys():
                    asistio_val = checkboxes[id_miembro]
                    just_val = justificaciones[id_miembro] if asistio_val == 0 else ""

                    # ¿Existe ya?
                    cursor.execute("""
                        SELECT ID_MiembroxReunion
                        FROM Miembroxreunion
                        WHERE ID_Miembro = %s AND ID_Reunion = %s
                        LIMIT 1
                    """, (id_miembro, id_reunion))
                    existe = cursor.fetchone()

                    if existe:
                        cursor.execute("""
                            UPDATE Miembroxreunion
                            SET asistio = %s, justificacion = %s, fecha_registro = CURRENT_TIMESTAMP
                            WHERE ID_Miembro = %s AND ID_Reunion = %s
                        """, (asistio_val, just_val, id_miembro, id_reunion))
                    else:
                        cursor.execute("""
                            INSERT INTO Miembroxreunion (ID_Miembro, ID_Reunion, asistio, justificacion, fecha_registro)
                            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                        """, (id_miembro, id_reunion, asistio_val, just_val))

                con.commit()

                # Contar presentes
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

                st.success(f"✅ Asistencia guardada. Presentes: {total_presentes}")

            except Exception as e:
                con.rollback()
                st.error(f"❌ Error al guardar asistencia: {e}")

    except Exception as e:
        st.error(f"❌ Error: {e}")

    finally:
        if "cursor" in locals():
            cursor.close()
        if "con" in locals():
            con.close()
