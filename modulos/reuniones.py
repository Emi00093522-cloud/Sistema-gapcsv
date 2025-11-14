import streamlit as st
from datetime import datetime
from modulos.config.conexion import obtener_conexion


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

    st.header("📅 Registro de Reuniones")
    st.subheader("📌 Registro de Reuniones por Distrito y Grupo")

    if not _tiene_rol_secretaria():
        st.warning("🔒 Acceso restringido: Solo la SECRETARIA puede ver y editar las reuniones.")
        return

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

    import pandas as pd

    if not reuniones:
        st.info("No hay reuniones registradas para este grupo.")
    else:
        filas = []
        for r in reuniones:
            filas.append({
                "ID": r["ID_Reunion"],
                "Fecha": r["fecha"].strftime("%Y-%m-%d") if r["fecha"] else "",
                "Hora": r["Hora"].strftime("%H:%M") if r["Hora"] else "",
                "Lugar": r["lugar"] or "",
                "Estado": r["ID_Estado_reunion"],
                "Presentes": r["total_presentes"] or ""
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
        etiqueta = f"{r['ID_Reunion']} — {r['fecha']} {r['Hora']}"
        opciones.append(etiqueta)
        mapa_reuniones[etiqueta] = r["ID_Reunion"]

    seleccion = st.selectbox("Seleccione una reunión", opciones)
    id_reunion = mapa_reuniones[seleccion]

    # Valores por defecto
    if id_reunion is None:
        fecha_def = datetime.now().date()
        hora_def = datetime.now().time().replace(second=0, microsecond=0)
        lugar_def = ""
        pres_def = ""
        estado_def = 1
    else:
        fila = next((x for x in reuniones if x["ID_Reunion"] == id_reunion), {})
        fecha_def = fila.get("fecha")
        hora_def = fila.get("Hora")
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

        # ESTADOS CON TEXTO REAL
        estados = {
            "Programada": 1,
            "Realizada": 2,
            "Cancelada": 3
        }

        # Convertir valor numérico → texto
        estado_texto_actual = [k for k, v in estados.items() if v == estado_def][0]

        estado_texto = st.selectbox(
            "Estado de la reunión",
            list(estados.keys()),
            index=list(estados.keys()).index(estado_texto_actual)
        )

        estado = estados[estado_texto]  # devuelve 1,2,3

        guardar = st.form_submit_button("💾 Guardar")
        eliminar = st.form_submit_button("🗑️ Eliminar") if id_reunion else False
        nuevo = st.form_submit_button("➕ Nuevo")

    # ------------------------------------------------------
    # GUARDAR
    # ------------------------------------------------------
    if guardar:
        try:
            hora_str = hora.strftime("%H:%M:%S")
            if id_reunion:
                # UPDATE
                cursor.execute("""
                    UPDATE Reunion
                    SET fecha=%s, Hora=%s, lugar=%s, total_presentes=%s, ID_Estado_reunion=%s
                    WHERE ID_Reunion=%s
                """, (fecha, hora_str, lugar, total_presentes, int(estado), id_reunion))
            else:
                # INSERT
                cursor.execute("""
                    INSERT INTO Reunion (ID_Grupo, fecha, Hora, lugar, total_presentes, ID_Estado_reunion)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (id_grupo, fecha, hora_str, lugar, total_presentes, int(estado)))

            con.commit()
            st.success("✅ Reunión guardada correctamente.")
            st.experimental_rerun()

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
            st.experimental_rerun()
        except Exception as e:
            con.rollback()
            st.error(f"❌ Error al eliminar: {e}")

    cursor.close()
    con.close()
