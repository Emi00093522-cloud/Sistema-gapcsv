import streamlit as st
from modulos.config.conexion import obtener_conexion

def mostrar_asistencia():
    st.header("📝 Control de asistencia por reunión")

    try:
        con = obtener_conexion()
        cursor = con.cursor()

        # 1. Cargar reuniones correctas (sin Tema)
        cursor.execute("""
            SELECT ID_Reunion, lugar, fecha, ID_Grupo
            FROM Reunion
        """)
        reuniones = cursor.fetchall()

        if not reuniones:
            st.warning("⚠ No hay reuniones registradas.")
            return

        # Diccionario bonito para el selectbox
        reuniones_dict = {
            r[0]: f"{r[2]} | {r[1]}"   # fecha | lugar
            for r in reuniones
        }

        id_reunion = st.selectbox(
            "Selecciona la reunión",
            options=list(reuniones_dict.keys()),
            format_func=lambda x: reuniones_dict[x]
        )

        # Buscar el grupo al que pertenece la reunión
        for r in reuniones:
            if r[0] == id_reunion:
                id_grupo = r[3]
                break

        # 2. Cargar miembros del grupo
        cursor.execute("""
            SELECT ID_Miembro, Nombre
            FROM Miembro
            WHERE ID_Grupo = %s
        """, (id_grupo,))
        miembros = cursor.fetchall()

        if not miembros:
            st.warning("⚠ No hay miembros en este grupo.")
            return

        # 3. Cargar asistencia previa
        cursor.execute("""
            SELECT ID_Miembro, Asistio
            FROM MiembroxReunion
            WHERE ID_Reunion = %s
        """, (id_reunion,))
        asistencia_previa = dict(cursor.fetchall())

        st.subheader("👥 Lista de asistencia")

        # Formulario
        checkboxes = {}
        with st.form("form_asistencia"):
            for id_miembro, nombre in miembros:
                asistio = asistencia_previa.get(id_miembro, 0)
                checkboxes[id_miembro] = st.checkbox(
                    label=nombre,
                    value=True if asistio == 1 else False
                )

            guardar = st.form_submit_button("💾 Guardar asistencia")

        # 4. Guardar asistencia
        if guardar:
            for id_miembro, asistio in checkboxes.items():
                cursor.execute("""
                    INSERT INTO MiembroxReunion (ID_Miembro, ID_Reunion, Asistio)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE Asistio = VALUES(Asistio)
                """, (id_miembro, id_reunion, 1 if asistio else 0))

            con.commit()

            # Contar presentes
            cursor.execute("""
                SELECT COUNT(*)
                FROM MiembroxReunion
                WHERE ID_Reunion = %s AND Asistio = 1
            """, (id_reunion,))
            total_presentes = cursor.fetchone()[0]

            st.success(f"✅ Asistencia guardada correctamente. Presentes: {total_presentes}")

    except Exception as e:
        st.error(f"❌ Error: {e}")

    finally:
        if "cursor" in locals():
            cursor.close()
        if "con" in locals():
            con.close()
