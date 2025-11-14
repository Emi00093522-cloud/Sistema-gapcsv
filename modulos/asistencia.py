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

        # Diccionario para mostrar fecha | lugar
        reuniones_dict = {
            r[0]: f"{r[2]} | {r[1]}"   # fecha | lugar
            for r in reuniones
        }

        id_reunion = st.selectbox(
            "Selecciona la reunión",
            options=list(reuniones_dict.keys()),
            format_func=lambda x: reuniones_dict[x]
        )

        # Obtener ID_Grupo de la reunión seleccionada
        id_grupo = None
        for r in reuniones:
            if r[0] == id_reunion:
                id_grupo = r[3]
                break

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

        # 3. Cargar asistencia previa (usa el nombre real de la tabla y columna)
        cursor.execute("""
            SELECT ID_Miembro, asistio
            FROM Miembroxreunion
            WHERE ID_Reunion = %s
        """, (id_reunion,))
        asistencia_previa = dict(cursor.fetchall())  # {(id_miembro, asistio), ...} -> dict

        st.subheader("👥 Lista de asistencia")

        # Formulario con checkboxes
        checkboxes = {}
        with st.form("form_asistencia"):
            for id_miembro, nombre in miembros:
                asistio = asistencia_previa.get(id_miembro, 0)
                checkboxes[id_miembro] = st.checkbox(
                    label=nombre,
                    value=True if asistio == 1 else False
                )

            guardar = st.form_submit_button("💾 Guardar asistencia")

        # Guardar: insertar o actualizar según exista el registro
        if guardar:
            try:
                for id_miembro, checked in checkboxes.items():
                    valor = 1 if checked else 0

                    # ¿Existe ya un registro para este miembro + reunión?
                    cursor.execute("""
                        SELECT ID_MiembroxReunion
                        FROM Miembroxreunion
                        WHERE ID_Miembro = %s AND ID_Reunion = %s
                        LIMIT 1
                    """, (id_miembro, id_reunion))
                    fila = cursor.fetchone()

                    if fila:
                        # UPDATE
                        cursor.execute("""
                            UPDATE Miembroxreunion
                            SET asistio = %s, fecha_registro = CURRENT_TIMESTAMP
                            WHERE ID_Miembro = %s AND ID_Reunion = %s
                        """, (valor, id_miembro, id_reunion))
                    else:
                        # INSERT
                        cursor.execute("""
                            INSERT INTO Miembroxreunion (ID_Miembro, ID_Reunion, asistio, fecha_registro)
                            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                        """, (id_miembro, id_reunion, valor))

                con.commit()

                # Contar presentes y actualizar Reunion.total_presentes
                cursor.execute("""
                    SELECT COUNT(*) FROM Miembroxreunion
                    WHERE ID_Reunion = %s AND asistio = 1
                """, (id_reunion,))
                total_presentes = cursor.fetchone()[0] or 0

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
