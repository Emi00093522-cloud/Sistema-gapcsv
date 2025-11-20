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
            ORDER BY fecha DESC
        """)
        reuniones = cursor.fetchall()

        if not reuniones:
            st.warning("⚠ No hay reuniones registradas.")
            return

        # Diccionario para mostrar fecha | lugar
        reuniones_dict = {r[0]: f"{str(r[2])} | {r[1]}" for r in reuniones}

        id_reunion = st.selectbox(
            "Selecciona la reunión",
            options=list(reuniones_dict.keys()),
            format_func=lambda x: reuniones_dict[x]
        )

        # Obtener ID_Grupo de la reunión seleccionada
        id_grupo = next((r[3] for r in reuniones if r[0] == id_reunion), None)

        if id_grupo is None:
            st.error("No se pudo obtener el grupo asociado a la reunión seleccionada.")
            return

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

        # 3. Cargar asistencia previa y justificación (si existe)
        cursor.execute("""
            SELECT ID_Miembro, asistio, IFNULL(justificacion, '')
            FROM Miembroxreunion
            WHERE ID_Reunion = %s
        """, (id_reunion,))
        asistencia_previa_rows = cursor.fetchall()
        # convertir a dict: id -> (asistio, justificacion)
        asistencia_previa = {row[0]: (row[1], row[2]) for row in asistencia_previa_rows}

        st.subheader("👥 Lista de asistencia")

        # Mostrar encabezado tipo tabla (estético)
        col_name, col_asistio, col_just = st.columns([3, 1, 3])
        with col_name:
            st.markdown("**Miembro**")
        with col_asistio:
            st.markdown("**Asistió**")
        with col_just:
            st.markdown("**Justificación (si NO)**")

        # Formulario con controles por fila
        controles = {}  # id_miembro -> { 'asistio': 'SI'/'NO', 'justificacion': str }
        with st.form("form_asistencia"):
            for id_miembro, nombre in miembros:
                prev = asistencia_previa.get(id_miembro, (0, ""))  # (asistio, justificacion)
                prev_asistio = "SI" if prev[0] == 1 else "NO"
                prev_just = prev[1] or ""

                # Una fila con 3 columnas: nombre | select SI/NO | text_input justificacion
                c1, c2, c3 = st.columns([3,1,3])
                with c1:
                    st.write(nombre)

                with c2:
                    key_radio = f"asist_{id_reunion}_{id_miembro}"
                    # usamos selectbox para mantener compatibilidad con reruns
                    asist_selection = st.selectbox(
                        label="",
                        options=["SI", "NO"],
                        index=0 if prev_asistio == "SI" else 1,
                        key=key_radio,
                        help="Seleccione SI si asistió, NO si no asistió"
                    )
                with c3:
                    key_just = f"just_{id_reunion}_{id_miembro}"
                    # Si prev selection es NO, habilitamos el texto; si SI, lo dejamos deshabilitado
                    # Para inicializar el valor usamos prev_just
                    # disabled param evita edición cuando asistió
                    justificacion = st.text_input(
                        label="",
                        value=prev_just,
                        key=key_just,
                        disabled=(asist_selection == "SI"),
                        placeholder="Escriba la justificación si NO asistió"
                    )

                controles[id_miembro] = {
                    "asistio": 1 if asist_selection == "SI" else 0,
                    "justificacion": justificacion.strip()
                }

            guardar = st.form_submit_button("💾 Guardar asistencia")

        # Guardar: insertar o actualizar según exista el registro
        if guardar:
            try:
                for id_miembro, data in controles.items():
                    valor = data["asistio"]
                    just = data["justificacion"] if data["justificacion"] != "" else None

                    # Verificar si existe ya registro para este miembro + reunión
                    cursor.execute("""
                        SELECT ID_MiembroxReunion
                        FROM Miembroxreunion
                        WHERE ID_Miembro = %s AND ID_Reunion = %s
                        LIMIT 1
                    """, (id_miembro, id_reunion))
                    fila = cursor.fetchone()

                    if fila:
                        # UPDATE (incluye justificacion)
                        cursor.execute("""
                            UPDATE Miembroxreunion
                            SET asistio = %s,
                                justificacion = %s,
                                fecha_registro = CURRENT_TIMESTAMP
                            WHERE ID_Miembro = %s AND ID_Reunion = %s
                        """, (valor, just, id_miembro, id_reunion))
                    else:
                        # INSERT
                        cursor.execute("""
                            INSERT INTO Miembroxreunion (ID_Miembro, ID_Reunion, asistio, justificacion, fecha_registro)
                            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                        """, (id_miembro, id_reunion, valor, just))

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
