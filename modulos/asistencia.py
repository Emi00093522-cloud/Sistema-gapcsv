import streamlit as st
from modulos.config.conexion import obtener_conexion

def mostrar_asistencia():
    st.header("📝 Control de asistencia por reunión")

    try:
        con = obtener_conexion()
        cursor = con.cursor()

        # 1. Cargar todas las reuniones
        cursor.execute("SELECT ID_Reunion, lugar, fecha, ID_Grupo FROM Reunion")
        reuniones = cursor.fetchall()

        if not reuniones:
            st.warning("⚠ No hay reuniones registradas.")
            return

        # Mostrar bonito en el selectbox
        reuniones_dict = {
            r[0]: f"{r[1]} - {r[2]}"   # lugar - fecha
            for r in reuniones
        }

        id_reunion = st.selectbox(
            "Selecciona la reunión",
            options=list(reuniones_dict.keys()),
            format_func=lambda x: reuniones_dict[x]
        )

        # Buscar el ID_Grupo de esa reunión
        id_grupo = None
        for r in reuniones:
            if r[0] == id_reunion:
                id_grupo = r[3]
                break

        # 2. Cargar miembros del grupo seleccionado
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

        checkboxes = {}
        with st.form("form_asistencia"):
            for id_miembro, nombre in miembros:
                asistio = asistencia_previa.get(id_miembro, 0)
                checkboxes[id_miembro] = st.checkbox(
                    label=nombre,
                    value=True if asistio == 1 else False
                )

            guardar = st.form_submit_button("💾 Guardar asistencia")

        if guardar:
            # Guardar asistencia
            for id_miembro, asistio in checkboxes.items():
                cursor.execute("""
                    REPLACE INTO MiembroxReunion 
                    (ID_MiembroxReunion, ID_Miembro, ID_Reunion, Asistio)
                    VALUES (
                        (SELECT ID_MiembroxReunion FROM MiembroxReunion 
                         WHERE ID_Miembro = %s AND ID_Reunion = %s),
                        %s, %s, %s
                    )
                """, (id_miembro, id_reunion, id_miembro, id_reunion, 1 if asistio else 0))

            con.commit()

            # Contar presentes
            cursor.execute("""
                SELECT COUNT(*) 
                FROM MiembroxReunion
                WHERE ID_Reunion = %s AND Asistio = 1
            """, (id_reunion,))
            total_presentes = cursor.fetchone()[0]

            st.success(f"✅ Asistencia guardada. Presentes: {total_presentes}")

    except Exception as e:
        st.error(f"❌ Error: {e}")

    finally:
        if "cursor" in locals(): cursor.close()
        if "con" in locals(): con.close()
