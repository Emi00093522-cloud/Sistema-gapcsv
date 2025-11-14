import streamlit as st
from modulos.config.conexion import obtener_conexion
import pandas as pd
import io

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

        # 3. Cargar asistencia previa
        cursor.execute("""
            SELECT ID_Miembro, asistio
            FROM Miembroxreunion
            WHERE ID_Reunion = %s
        """, (id_reunion,))
        asistencia_previa = dict(cursor.fetchall())

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

        # Guardar cambios
        if guardar:
            try:
                for id_miembro, checked in checkboxes.items():
                    valor = 1 if checked else 0

                    # Verificar si existe registro
                    cursor.execute("""
                        SELECT ID_MiembroxReunion
                        FROM Miembroxreunion
                        WHERE ID_Miembro = %s AND ID_Reunion = %s
                        LIMIT 1
                    """, (id_miembro, id_reunion))
                    fila = cursor.fetchone()

                    if fila:
                        cursor.execute("""
                            UPDATE Miembroxreunion
                            SET asistio = %s, fecha_registro = CURRENT_TIMESTAMP
                            WHERE ID_Miembro = %s AND ID_Reunion = %s
                        """, (valor, id_miembro, id_reunion))
                    else:
                        cursor.execute("""
                            INSERT INTO Miembroxreunion (ID_Miembro, ID_Reunion, asistio, fecha_registro)
                            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                        """, (id_miembro, id_reunion, valor))

                con.commit()

                # Contar presentes
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

        # -----------  MOSTRAR LISTA DE PRESENTES + DESCARGAR EXCEL  ----------

        st.subheader("🟢 Miembros presentes")

        cursor.execute("""
            SELECT M.nombre
            FROM Miembroxreunion MR
            INNER JOIN Miembro M ON MR.ID_Miembro = M.ID_Miembro
            WHERE MR.ID_Reunion = %s AND MR.asistio = 1
            ORDER BY M.nombre
        """, (id_reunion,))
        presentes = cursor.fetchall()

        if presentes:
            nombres_presentes = [p[0] for p in presentes]

            for nombre in nombres_presentes:
                st.write(f"- {nombre}")

            # Crear DataFrame
            df_export = pd.DataFrame({
                "Nombre": nombres_presentes
            })

            # Convertir a Excel en memoria
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
                df_export.to_excel(writer, index=False, sheet_name="Asistencia")

            # Botón de descarga
            st.download_button(
                label="📥 Descargar lista en Excel",
                data=excel_buffer.getvalue(),
                file_name=f"Asistencia_Reunion_{id_reunion}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        else:
            st.info("Nadie asistió a esta reunión.")

    except Exception as e:
        st.error(f"❌ Error: {e}")

    finally:
        if "cursor" in locals(): cursor.close()
        if "con" in locals(): con.close()
