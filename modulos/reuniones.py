import streamlit as st
from datetime import datetime
from modulos.config.conexion import obtener_conexion
import pandas as pd

# ==========================================================
#   FUNCIONES INTERNAS
# ==========================================================

def _get_cargo_detectado():
    return st.session_state.get("cargo_de_usuario", "").strip().upper()

def _tiene_rol_secretaria():
    return _get_cargo_detectado() == "SECRETARIA"

# ==========================================================
#   MÓDULO PRINCIPAL
# ==========================================================

def mostrar_reuniones():

    # Títulos
    st.header("📅 Registro de Reuniones")
    st.subheader("📌 Registro de Reuniones por Distrito y Grupo")

    if not _tiene_rol_secretaria():
        st.warning("🔒 Acceso restringido: Solo la SECRETARIA puede ver y editar las reuniones.")
        return

    # Conexión
    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
    except Exception as e:
        st.error(f"❌ Error de conexión: {e}")
        return

    # ======================================================
    # 1. SELECCIONAR DISTRITO
    # ======================================================
    try:
        cursor.execute("SELECT ID_Distrito, nombre FROM Distrito ORDER BY nombre")
        distritos = cursor.fetchall()
    except Exception:
        distritos = []

    if not distritos:
        st.error("⚠️ No existen Distritos registrados.")
        cursor.close()
        con.close()
        return

    mapa_distritos = {f"{d['ID_Distrito']} - {d['nombre']}": d['ID_Distrito'] for d in distritos}
    distrito_label = st.selectbox("Seleccione Distrito", options=list(mapa_distritos.keys()))
    id_distrito = mapa_distritos[distrito_label]

    st.write("")

    # ======================================================
    # 2. SELECCIONAR GRUPO SEGÚN DISTRITO
    # ======================================================
    cursor.execute(
        "SELECT ID_Grupo, nombre FROM Grupo WHERE ID_Distrito = %s ORDER BY nombre",
        (id_distrito,)
    )
    grupos = cursor.fetchall()

    if not grupos:
        st.warning("⚠️ Este distrito no tiene grupos registrados.")
        cursor.close()
        con.close()
        return

    mapa_grupos = {f"{g['ID_Grupo']} - {g['nombre']}": g['ID_Grupo'] for g in grupos}
    grupo_label = st.selectbox("Seleccione Grupo", list(mapa_grupos.keys()))
    id_grupo = mapa_grupos[grupo_label]

    st.write("---")

    # ======================================================
    # 3. CARGAR REUNIONES DEL GRUPO
    # ======================================================
    cursor.execute("""
        SELECT ID_Reunion, fecha, Hora, lugar, total_presentes, ID_Estado_reunion
        FROM Reunion
        WHERE ID_Grupo = %s
        ORDER BY fecha DESC, Hora DESC
    """, (id_grupo,))
    reuniones = cursor.fetchall()

    st.subheader("📄 Reuniones registradas")

    if not reuniones:
        st.info("No hay reuniones registradas para este grupo.")
    else:
        filas = []
        for r in reuniones:
            # Manejo seguro de fecha y hora (pueden venir como string o datetime)
            fecha_val = r.get("fecha")
            if hasattr(fecha_val, "strftime"):
                fecha_str = fecha_val.strftime("%Y-%m-%d")
            else:
                fecha_str = str(fecha_val) if fecha_val is not None else ""

            hora_val = r.get("Hora")
            hora_str = ""
            if hora_val:
                # si es time/datetime usa strftime, si es string conviértelo tal cual
                if hasattr(hora_val, "strftime"):
                    hora_str = hora_val.strftime("%H:%M")
                else:
                    hora_str = str(hora_val)

            filas.append({
                "ID": r["ID_Reunion"],
                "Fecha": fecha_str,
                "Hora": hora_str,
                "Lugar": r.get("lugar") or "",
                "Estado": r.get("ID_Estado_reunion"),
                "Presentes": r.get("total_presentes") or 0
            })
        st.dataframe(pd.DataFrame(filas), use_container_width=True)

    st.write("---")

    # ======================================================
    # 4. FORMULARIO: CREAR O EDITAR
    # ======================================================
    st.subheader("✏️ Crear o Editar Reunión (solo SECRETARIA)")

    opciones = ["➕ Nueva reunión"]
    mapa_reuniones = {"➕ Nueva reunión": None}

    for r in reuniones:
        # muestra fecha y hora de forma legible en la lista
        fecha_val = r.get("fecha")
        if hasattr(fecha_val, "strftime"):
            fecha_str = fecha_val.strftime("%Y-%m-%d")
        else:
            fecha_str = str(fecha_val) if fecha_val is not None else ""

        hora_val = r.get("Hora")
        hora_str = ""
        if hora_val:
            if hasattr(hora_val, "strftime"):
                hora_str = hora_val.strftime("%H:%M")
            else:
                hora_str = str(hora_val)

        etiqueta = f"{r['ID_Reunion']} — {fecha_str} {hora_str}"
        opciones.append(etiqueta)
        mapa_reuniones[etiqueta] = r["ID_Reunion"]

    seleccion = st.selectbox("Seleccione una reunión", opciones)
    id_reunion = mapa_reuniones[seleccion]

    # Valores por defecto para el form de creación/edición
    if id_reunion is None:
        fecha_def = datetime.now().date()
        hora_def = datetime.now().time().replace(second=0, microsecond=0)
        lugar_def = ""
        pres_def = ""
        estado_def = 1
    else:
        fila = next((x for x in reuniones if x["ID_Reunion"] == id_reunion), {})
        fecha_def = fila.get("fecha") or datetime.now().date()
        hora_def = fila.get("Hora") or datetime.now().time().replace(second=0, microsecond=0)
        lugar_def = fila.get("lugar", "")
        pres_def = fila.get("total_presentes", "")
        estado_def = fila.get("ID_Estado_reunion", 1)

    with st.form("form_reuniones"):
        col1, col2 = st.columns(2)
        with col1:
            fecha = st.date_input("Fecha", fecha_def)
        with col2:
            hora = st.time_input("Hora", hora_def)

        lugar = st.text_input("Lugar", lugar_def)
        total_presentes = st.text_area("Presentes", pres_def)

        estados = {"Programada": 1, "Realizada": 2, "Cancelada": 3}
        estado_texto_actual = [k for k, v in estados.items() if v == estado_def][0]

        estado_texto = st.selectbox(
            "Estado de la reunión",
            list(estados.keys()),
            index=list(estados.keys()).index(estado_texto_actual)
        )
        estado = estados[estado_texto]

        guardar = st.form_submit_button("💾 Guardar")
        eliminar = st.form_submit_button("🗑️ Eliminar") if id_reunion else False
        nuevo = st.form_submit_button("➕ Nuevo")

    # ------------------------------------------------------
    # GUARDAR / INSERT / UPDATE
    # ------------------------------------------------------
    if guardar:
        try:
            # hora a string hh:mm:ss
            if hasattr(hora, "strftime"):
                hora_str_full = hora.strftime("%H:%M:%S")
            else:
                hora_str_full = str(hora)

            if id_reunion:
                cursor.execute("""
                    UPDATE Reunion
                    SET fecha=%s, Hora=%s, lugar=%s, total_presentes=%s, ID_Estado_reunion=%s
                    WHERE ID_Reunion=%s
                """, (fecha, hora_str_full, lugar, total_presentes, int(estado), id_reunion))
            else:
                cursor.execute("""
                    INSERT INTO Reunion (ID_Grupo, fecha, Hora, lugar, total_presentes, ID_Estado_reunion)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (id_grupo, fecha, hora_str_full, lugar, total_presentes, int(estado)))

            con.commit()
            st.success("✅ Reunión guardada correctamente.")
            st.rerun()

        except Exception as e:
            con.rollback()
            st.error(f"❌ Error al guardar: {e}")

    # ------------------------------------------------------
    # ELIMINAR
    # ------------------------------------------------------
    if eliminar and id_reunion:
        try:
            cursor.execute("DELETE FROM Reunion WHERE ID_Reunion=%s", (id_reunion,))
            con.commit()
            st.success("🗑️ Reunión eliminada.")
            st.rerun()
        except Exception as e:
            con.rollback()
            st.error(f"❌ Error al eliminar: {e}")

    # ------------------------------------------------------
    # 5. REGISTRO DE ASISTENCIA (solo si hay una reunión seleccionada)
    # ------------------------------------------------------
    if id_reunion:
        st.write("---")
        st.subheader("🧍‍♂️🧍‍♀️ Registro de Asistencia")

        # 5.1 obtener miembros del grupo
        cursor.execute("""
            SELECT ID_Miembro, nombre, apellido
            FROM Miembro
            WHERE ID_Grupo = %s
            ORDER BY nombre, apellido
        """, (id_grupo,))
        miembros = cursor.fetchall()

        if not miembros:
            st.info("No hay miembros registrados en este grupo.")
        else:
            # 5.2 obtener asistencia previa para la reunión
            cursor.execute("""
                SELECT ID_Miembro, asistencia
                FROM MiembroXReunion
                WHERE ID_Reunion = %s
            """, (id_reunion,))
            asistencia_previa_rows = cursor.fetchall()
            asistencia_previa = {r["ID_Miembro"]: r["asistencia"] for r in asistencia_previa_rows}

            st.write("Marque asistencia y luego presione '💾 Guardar asistencia'")

            # Generar checkboxes con keys estables para que no se pierdan con reruns
            asistentes_dict = {}
            cols = st.columns([3,1])  # layout: lista y luego un pequeño espacio
            # Mostramos un checkbox por miembro
            for m in miembros:
                mid = m["ID_Miembro"]
                label = f"{m.get('nombre','')} {m.get('apellido','')}".strip()
                key = f"asist_{id_reunion}_{mid}"
                default_val = bool(asistencia_previa.get(mid, 0))
                asistentes_dict[mid] = st.checkbox(label, value=default_val, key=key)

            # Botón para guardar asistencia
            if st.button("💾 Guardar asistencia"):
                try:
                    # Insert / update por cada miembro
                    for mid, checked in asistentes_dict.items():
                        asistencia_val = 1 if checked else 0
                        cursor.execute("""
                            INSERT INTO MiembroXReunion (ID_Miembro, ID_Reunion, asistencia, Fecha_registro)
                            VALUES (%s, %s, %s, NOW())
                            ON DUPLICATE KEY UPDATE
                                asistencia = VALUES(asistencia),
                                Fecha_registro = VALUES(Fecha_registro)
                        """, (mid, id_reunion, asistencia_val))

                    # Calcular nuevo total_presentes
                    cursor.execute("""
                        SELECT COUNT(*) AS total
                        FROM MiembroXReunion
                        WHERE ID_Reunion = %s AND asistencia = 1
                    """, (id_reunion,))
                    total_row = cursor.fetchone()
                    total = int(total_row["total"]) if total_row and "total" in total_row else 0

                    # Actualizar Reunion.total_presentes
                    cursor.execute("""
                        UPDATE Reunion SET total_presentes = %s WHERE ID_Reunion = %s
                    """, (total, id_reunion))

                    con.commit()
                    st.success(f"✅ Asistencia guardada. Total presentes: {total}")
                    st.rerun()

                except Exception as e:
                    con.rollback()
                    st.error(f"❌ Error al guardar asistencia: {e}")

    # Cerrar conexión
    cursor.close()
    con.close()

  

