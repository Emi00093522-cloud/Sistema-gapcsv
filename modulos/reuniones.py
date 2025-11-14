import datetime
import streamlit as st
from conexion import obtener_conexion

def mostrar_reuniones():

    st.title("📆 Gestión de Reuniones")

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    # =======================
    # MOSTRAR FORMULARIO
    # =======================
    with st.form("form_reunion"):
        st.subheader("Registrar / Editar reunión")

        fecha = st.date_input("Fecha")

        # CORRECCIÓN: convertir strings a objetos time válidos
        hora_def = None
        if "hora_edit" in st.session_state:
            try:
                hora_def = datetime.time.fromisoformat(st.session_state["hora_edit"])
            except:
                hora_def = None

        hora = st.time_input("Hora", hora_def)

        lugar = st.text_input("Lugar")
        estado = st.selectbox("Estado", ["Programada", "Realizada", "Cancelada"])

        # CORRECCIÓN IMPORTANTE: agregar botón de submit
        guardar = st.form_submit_button("💾 Guardar reunión")

    # ============================
    # PROCESAR FORMULARIO
    # ============================
    if guardar:
        cursor.execute("""
            INSERT INTO Reunion (fecha, hora, lugar, ID_Estado_reunion)
            VALUES (%s, %s, %s, %s)
        """, (fecha, hora, lugar, 1))  # 1 = Programada
        conexion.commit()
        st.success("Reunión guardada correctamente.")
        st.rerun()

    # =======================
    # LISTADO DE REUNIONES
    # =======================
    cursor.execute("SELECT * FROM Reunion ORDER BY fecha DESC")
    reuniones = cursor.fetchall()

    st.subheader("Listado de reuniones")

    for r in reuniones:
        with st.expander(f"Reunión #{r['ID_Reunion']} - {r['fecha']}"):
            st.write(f"**Lugar:** {r['lugar']}")
            st.write(f"**Hora:** {str(r['hora'])}")
            st.write(f"**Estado:** {r['ID_Estado_reunion']}")
            st.write(f"**Presentes:** {r['total_presentes']}")

            # BOTÓN PARA TOMAR ASISTENCIA
            if st.button(f"Tomar asistencia reunión {r['ID_Reunion']}"):
                st.session_state["reunion_seleccionada"] = r["ID_Reunion"]
                st.rerun()

    # ==========================================
    # MÓDULO PARA TOMAR ASISTENCIA (MiembroXReunion)
    # ==========================================
    if "reunion_seleccionada" in st.session_state:

        id_reunion = st.session_state["reunion_seleccionada"]

        st.header(f"👥 Tomar asistencia — Reunión {id_reunion}")

        # 1. Obtener miembros del grupo de esta reunión
        cursor.execute("""
            SELECT M.ID_Miembro, M.nombre
            FROM Miembro M
            INNER JOIN Grupo G ON G.ID_Grupo = M.ID_Grupo
            INNER JOIN Reunion R ON R.ID_Grupo = G.ID_Grupo
            WHERE R.ID_Reunion = %s
        """, (id_reunion,))
        miembros = cursor.fetchall()

        # 2. Crear registro si no existe
        for m in miembros:
            cursor.execute("""
                INSERT IGNORE INTO MiembroXReunion(ID_Miembro, ID_Reunion, presente)
                VALUES (%s, %s, 0)
            """, (m["ID_Miembro"], id_reunion))
        conexion.commit()

        # 3. Mostrar lista de asistencia
        st.subheader("Marcar presentes:")

        with st.form("asistencia_form"):
            checks = {}
            for m in miembros:
                checks[m["ID_Miembro"]] = st.checkbox(m["nombre"])

            save_asistencia = st.form_submit_button("💾 Guardar asistencia")

        if save_asistencia:
            for m in miembros:
                cursor.execute("""
                    UPDATE MiembroXReunion SET presente=%s 
                    WHERE ID_Miembro=%s AND ID_Reunion=%s
                """, (1 if checks[m["ID_Miembro"]] else 0,
                      m["ID_Miembro"], id_reunion))

            # actualizar total presentes
            cursor.execute("""
                UPDATE Reunion 
                SET total_presentes = (
                    SELECT COUNT(*) 
                    FROM MiembroXReunion 
                    WHERE ID_Reunion=%s AND presente=1
                )
                WHERE ID_Reunion=%s
            """, (id_reunion, id_reunion))
            conexion.commit()

            st.success("Asistencia actualizada.")
            st.rerun()
