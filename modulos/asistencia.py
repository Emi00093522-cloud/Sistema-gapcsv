import streamlit as st
from modulos.config.conexion import obtener_conexion

def mostrar_asistencia():
    st.header("📋 Control de asistencia")

    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)

        # Seleccionar reunión
        st.subheader("Seleccione la reunión")
        id_reunion = st.number_input("ID de reunión", min_value=1, step=1)

        cargar = st.button("📄 Cargar lista de asistencia")

        if cargar:
            try:
                cursor.execute("""
                    SELECT m.id_miembro, m.nombre, mr.asistencia
                    FROM miembro m
                    INNER JOIN miembro_por_reunion mr ON mr.id_miembro = m.id_miembro
                    WHERE mr.id_reunion = %s
                """, (id_reunion,))
                lista = cursor.fetchall()

                if not lista:
                    st.warning("⚠️ No se encontraron miembros registrados para esta reunión.")
                else:
                    st.session_state["lista_asistencia"] = lista

            except Exception as e:
                st.error(f"❌ Error al cargar la lista: {e}")

        # Si ya hay una lista cargada, mostrar los miembros
        if "lista_asistencia" in st.session_state:

            st.subheader("Marcar asistencia")

            # Formulario para guardar asistencia
            with st.form("form_asistencia"):
                nuevos_valores = []

                for miembro in st.session_state["lista_asistencia"]:
                    presente = st.checkbox(
                        miembro["nombre"],
                        value=bool(miembro["asistencia"]),
                        key=f"asistencia_{miembro['id_miembro']}"
                    )

                    nuevos_valores.append({
                        "id_miembro": miembro["id_miembro"],
                        "asistencia": 1 if presente else 0
                    })

                guardar = st.form_submit_button("💾 Guardar asistencia")

                if guardar:
                    try:
                        for item in nuevos_valores:
                            cursor.execute("""
                                UPDATE miembro_por_reunion
                                SET asistencia = %s, hora_asistencia = NOW()
                                WHERE id_reunion = %s AND id_miembro = %s
                            """, (item["asistencia"], id_reunion, item["id_miembro"]))

                        con.commit()

                        # Obtener total de presentes
                        cursor.execute("""
                            SELECT COUNT(*) AS total
                            FROM miembro_por_reunion
                            WHERE id_reunion = %s AND asistencia = 1
                        """, (id_reunion,))
                        total = cursor.fetchone()["total"]

                        st.success(f"✅ Asistencia guardada correctamente. Total de presentes: {total}")
                        st.rerun()

                    except Exception as e:
                        con.rollback()
                        st.error(f"❌ Error al guardar asistencia: {e}")

    except Exception as e:
        st.error(f"❌ Error general: {e}")

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'con' in locals():
            con.close()
