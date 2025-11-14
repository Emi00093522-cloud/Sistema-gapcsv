import streamlit as st
import pandas as pd
from datetime import datetime, time
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

    # ------------------------------------------------------
    # CONEXIÓN
    # ------------------------------------------------------
    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
    except Exception as e:
        st.error(f"❌ Error de conexión: {e}")
        return

    # ------------------------------------------------------
    # SELECCIONAR DISTRITO
    # ------------------------------------------------------
    cursor.execute("SELECT ID_Distrito, nombre FROM Distrito ORDER BY nombre")
    distritos = cursor.fetchall()

    if not distritos:
        st.error("⚠️ No existen Distritos registrados.")
        return

    mapa_distritos = {f"{d['ID_Distrito']} - {d['nombre']}": d['ID_Distrito'] for d in distritos}

    distrito_label = st.selectbox("Seleccione Distrito", options=list(mapa_distritos.keys()))
    id_distrito = mapa_distritos[distrito_label]

    st.write("")

    # ------------------------------------------------------
    # SELECCIONAR GRUPO
    # ------------------------------------------------------
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

    # ------------------------------------------------------
    # CARGAR REUNIONES
    # ------------------------------------------------------
    cursor.execute("""
        SELECT ID_Reunion, fecha, Hora, lugar, total_presentes, ID_Estado_reunion
        FROM Reunion
        WHERE ID_Grupo = %s
        ORDER BY fecha DESC, Hora DESC
    """, (id_grupo,))

    reuniones = cursor.fetchall()

    st.subheader("📄 Reuniones registradas")

    if reuniones:
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
    else:
        st.info("No hay reuniones registradas para este grupo.")

    st.write("---")

    # ------------------------------------------------------
    # SELECCIÓN DE REUNIÓN
    # ------------------------------------------------------
    st.subheader("✏️ Crear o Editar Reunión")

    opciones = ["➕ Nueva reunión"]
    mapa_reu = {"➕ Nueva reunión": None}

    for r in reuniones:
        label = f"{r['ID_Reunion']} — {r['fecha']} {r['Hora']}"
        opciones.append(label)
        mapa_reu[label] = r["ID_Reunion"]

    seleccion = st.selectbox("Seleccione una reunión", opciones)
    id_reunion = mapa_reu[seleccion]

    # ------------------------------------------------------
    # CARGAR DATOS DE REUNIÓN
    # ------------------------------------------------------
    if id_reunion is None:
        fecha_def = datetime.now().date()
        hora_def = time(18, 0)
        lugar_def = ""
        presentes_def = ""
        estado_def = 1
    else:
        fila = next((x for x in reuniones if x["ID_Reunion"] == id_reunion), {})

        fecha_def = fila.get("fecha", datetime.now().date())
        hora_raw = fila.get("Hora")

        # --- CORRECCIÓN DEFINITIVA DEL TIME_INPUT ---
        if isinstance(hora_raw, time):
            hora_def = hora_raw
        elif isinstance(hora_raw, str):
            try:
                hora_def = datetime.strptime(hora_raw, "%H:%M:%S").time()
            except:
                hora_def = time(18, 0)
        elif isinstance(hora_raw, datetime):
            hora_def = hora_raw.time()
        else:
            hora_def = time(18, 0)
        # --------------------------------------------

        lugar_def = fila.get("lugar", "")
        presentes_def = fila.get("total_presentes", "")
        estado_def = fila.get("ID_Estado_reunion", 1)

    # ------------------------------------------------------
    # FORMULARIO
    # ------------------------------------------------------
    with st.form("form_reunion"):

        col1, col2 = st.columns(2)
        with col1:
            fecha = st.date_input("Fecha", fecha_def)
        with col2:
            hora = st.time_input("Hora", hora_def)

        lugar = st.text_input("Lugar", lugar_def)
        presentes = st.text_area("Presentes", presentes_def)

        estados = {
            "Programada": 1,
            "Realizada": 2,
            "Cancelada": 3
        }

        estado_texto_actual = [k for k, v in estados.items() if v == estado_def][0]

        estado_texto = st.selectbox(
            "Estado",
            list(estados.keys()),
            index=list(estados.keys()).index(estado_texto_actual)
        )

        estado = estados[estado_texto]

        btn_guardar = st.form_submit_button("💾 Guardar")
        btn_eliminar = st.form_submit_button("🗑️ Eliminar") if id_reunion else False

    # ------------------------------------------------------
    # GUARDAR
    # ------------------------------------------------------
    if btn_guardar:
        try:
            hora_str = hora.strftime("%H:%M:%S")

            if id_reunion:
                cursor.execute("""
                    UPDATE Reunion
                    SET fecha=%s, Hora=%s, lugar=%s, total_presentes=%s, ID_Estado_reunion=%s
                    WHERE ID_Reunion=%s
                """, (fecha, hora_str, lugar, presentes, estado, id_reunion))
            else:
                cursor.execute("""
                    INSERT INTO Reunion (ID_Grupo, fecha, Hora, lugar, total_presentes, ID_Estado_reunion)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (id_grupo, fecha, hora_str, lugar, presentes, estado))

            con.commit()
            st.success("✅ Reunión guardada correctamente.")
            st.rerun()

        except Exception as e:
            con.rollback()
            st.error(f"❌ Error al guardar: {e}")

    # ------------------------------------------------------
    # ELIMINAR
    # ------------------------------------------------------
    if btn_eliminar and id_reunion:
        try:
            cursor.execute("DELETE FROM Reunion WHERE ID_Reunion=%s", (id_reunion,))
            con.commit()
            st.success("🗑️ Reunión eliminada.")
            st.rerun()
        except Exception as e:
            con.rollback()
            st.error(f"❌ Error al eliminar: {e}")

    cursor.close()
    con.close()
