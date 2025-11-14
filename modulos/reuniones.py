import streamlit as st
from datetime import datetime, time
from modulos.config.conexion import obtener_conexion

def _get_cargo_detectado():
    posibles = ["cargo_de_usuario", "cargo_usuario", "cargo", "tipo_usuario"]
    for k in posibles:
        if k in st.session_state and st.session_state[k]:
            return str(st.session_state[k]).strip()
    return ""

def _tiene_rol(cargo_str, rol_buscar):
    if not cargo_str:
        return False
    return rol_buscar.lower() in cargo_str.lower()

def mostrar_reuniones():
    st.header("📅 Registro de Reuniones por Grupo")

    cargo_detectado = _get_cargo_detectado()
    es_secretaria = _tiene_rol(cargo_detectado, "secretaria")

    # Conexión
    try:
        con = obtener_conexion()
        if not con:
            st.error("❌ No se pudo conectar a la base de datos.")
            return
        try:
            cursor = con.cursor(dictionary=True)
            dict_cursor = True
        except Exception:
            cursor = con.cursor()
            dict_cursor = False
    except Exception as e:
        st.error(f"❌ Error al conectar a la base de datos: {e}")
        return

    try:
        # ---------------------------------------------------------
        # 🔹 PRIMERO: SELECCIONAR DISTRITO
        # ---------------------------------------------------------
        try:
            cursor.execute("SELECT ID_Distrito, nombre FROM Distrito ORDER BY nombre")
            distritos = cursor.fetchall() or []
            if not dict_cursor:
                distritos = [{"ID_Distrito": d[0], "nombre": d[1]} for d in distritos]
        except Exception:
            distritos = []

        if not distritos:
            st.info("No hay distritos registrados. Registre uno primero.")
            return

        mapa_distritos = {
            f"{d['ID_Distrito']} - {d.get('nombre','Distrito')}": d['ID_Distrito']
            for d in distritos
        }

        distrito_label = st.selectbox("Selecciona distrito", options=list(mapa_distritos.keys()))
        id_distrito = int(mapa_distritos[distrito_label])

        st.write("")

        # ---------------------------------------------------------
        # 🔹 SEGUNDO: Seleccionar solo grupos del distrito elegido
        # ---------------------------------------------------------
        try:
            cursor.execute("""
                SELECT ID_Grupo, nombre 
                FROM Grupo 
                WHERE ID_Distrito = %s
                ORDER BY nombre
            """, (id_distrito,))
            grupos = cursor.fetchall() or []
            if not dict_cursor:
                grupos = [{"ID_Grupo": g[0], "nombre": g[1]} for g in grupos]
        except Exception:
            grupos = []

        if not grupos:
            st.info("No hay grupos registrados en este distrito.")
            return

        mapa_grupos = {
            f"{g['ID_Grupo']} - {g.get('nombre','Grupo')}": g['ID_Grupo']
            for g in grupos
        }

        grupo_label = st.selectbox("Selecciona grupo", options=list(mapa_grupos.keys()))
        id_grupo = int(mapa_grupos[grupo_label])

        # ---------------------------------------------------------
        # 🔹 CARGAR REUNIONES DEL GRUPO
        # ---------------------------------------------------------
        cursor.execute("""
            SELECT ID_Reunion, ID_Grupo, fecha, Hora, ID_Estado_reunion, lugar, total_presentes
            FROM Reunion
            WHERE ID_Grupo = %s
            ORDER BY fecha DESC, Hora DESC
        """, (id_grupo,))
        reuniones = cursor.fetchall() or []
        if not dict_cursor:
            reuniones = [
                {"ID_Reunion": r[0], "ID_Grupo": r[1], "fecha": r[2], "Hora": r[3],
                 "ID_Estado_reunion": r[4], "lugar": r[5], "total_presentes": r[6]} for r in reuniones
            ]

        # ---------------------------------------------------------
        # Mostrar tabla
        # ---------------------------------------------------------
        st.subheader("Reuniones registradas")
        if not reuniones:
            st.info("No hay reuniones registradas para este grupo.")
        else:
            import pandas as pd
            filas = []
            for r in reuniones:
                filas.append({
                    "ID": r.get("ID_Reunion"),
                    "Fecha": r.get("fecha").strftime("%Y-%m-%d") if r.get("fecha") else "",
                    "Hora": r.get("Hora").strftime("%H:%M:%S")
                            if hasattr(r.get("Hora"), "strftime")
                            else (str(r.get("Hora")) if r.get("Hora") else ""),
                    "Lugar": r.get("lugar") or "",
                    "Estado": r.get("ID_Estado_reunion") or "",
                    "Total_presentes": r.get("total_presentes") or ""
                })
            df = pd.DataFrame(filas)
            st.dataframe(df.sort_values(by=["Fecha", "Hora"], ascending=[False, False]), use_container_width=True)

        st.write("---")

        # ---------------------------------------------------------
        # SI NO ES SECRETARIA → vista solo lectura
        # ---------------------------------------------------------
        if not es_secretaria:
            if cargo_detectado:
                st.info(f"🔒 Vista de solo lectura. Cargo: **{cargo_detectado}**")
            else:
                st.info("🔒 Vista de solo lectura. Solo la SECRETARIA puede modificar reuniones.")
            return

        # ---------------------------------------------------------
        # FORMULARIO (solo secretaria)
        # ---------------------------------------------------------
        st.subheader("Crear / Editar reunión (solo SECRETARIA)")

        opciones = ["➕ Nueva reunión"]
        mapa_reuniones = {opciones[0]: None}
        for r in reuniones:
            fecha_txt = r["fecha"].strftime("%Y-%m-%d") if r.get("fecha") else "sin_fecha"
            hora_txt = (
                r["Hora"].strftime("%H:%M")
                if hasattr(r.get("Hora"), "strftime")
                else (str(r.get("Hora")) if r.get("Hora") else "")
            )
            label = f"{r['ID_Reunion']} • {fecha_txt} {hora_txt} — {(r.get('lugar') or '')[:30]}"
            opciones.append(label)
            mapa_reuniones[label] = r["ID_Reunion"]

        sel_label = st.selectbox("Selecciona reunión para editar o crear una nueva", opciones)
        id_reunion = mapa_reuniones[sel_label]

        # Valores por defecto
        if id_reunion is None:
            fecha_def = datetime.now().date()
            hora_def = datetime.now().time().replace(second=0, microsecond=0)
            lugar_def = ""
            asistentes_def = ""
            estado_def = 1
        else:
            fila = next((x for x in reuniones if x["ID_Reunion"] == id_reunion), {})
            fecha_def = fila.get("fecha") or datetime.now().date()
            hora_def = fila.get("Hora") or datetime.now().time().replace(second=0, microsecond=0)
            lugar_def = fila.get("lugar") or ""
            asistentes_def = fila.get("total_presentes") or ""
            estado_def = fila.get("ID_Estado_reunion") or 1

        with st.form("form_reunion"):
            col1, col2 = st.columns(2)

            with col1:
                fecha = st.date_input("Fecha *", value=fecha_def)
            with col2:
                hora = st.time_input("Hora *", value=hora_def)

            lugar = st.text_input("Lugar (opcional)", max_chars=100, value=lugar_def)
            total_presentes = st.text_area("Total presentes (opcional)", value=asistentes_def, height=80)

            estados = {1: "Programada", 2: "Realizada", 3: "Cancelada"}
            estado = st.selectbox(
                "Estado",
                options=list(estados.keys()),
                format_func=lambda k: estados[k],
                index=list(estados.keys()).index(estado_def) if estado_def in estados else 0
            )

            btn_guardar = st.form_submit_button("✅ Guardar")
            btn_eliminar = st.form_submit_button("🗑️ Eliminar") if id_reunion else False
            btn_nuevo = st.form_submit_button("➕ Nuevo")

            if btn_nuevo:
                st.experimental_rerun()

            if btn_eliminar:
                try:
                    cursor.execute("DELETE FROM Reunion WHERE ID_Reunion = %s", (int(id_reunion),))
                    con.commit()
                    st.success("🗑️ Reunión eliminada.")
                    st.experimental_rerun()
                except Exception as e:
                    con.rollback()
                    st.error(f"❌ Error al eliminar: {e}")

            if btn_guardar:
                try:
                    hora_str = hora.strftime("%H:%M:%S")

                    if id_reunion:
                        cursor.execute("""
                            UPDATE Reunion
                            SET fecha=%s, Hora=%s, lugar=%s, total_presentes=%s, ID_Estado_reunion=%s
                            WHERE ID_Reunion=%s
                        """, (fecha, hora_str, lugar or None, total_presentes or None, int(estado), int(id_reunion)))
                    else:
                        cursor.execute("""
                            INSERT INTO Reunion
                            (ID_Grupo, fecha, Hora, lugar, total_presentes, ID_Estado_reunion)
                            VALUES (%s,%s,%s,%s,%s,%s)
                        """, (id_grupo, fecha, hora_str, lugar or None, total_presentes or None, int(estado)))

                    con.commit()
                    st.success("✅ Reunión guardada.")
                    st.experimental_rerun()

                except Exception as e:
                    con.rollback()
                    st.error(f"❌ Error al guardar: {e}")

    except Exception as e:
        st.error(f"❌ Error inesperado: {e}")

    finally:
        try:
            cursor.close()
        except:
            pass
        try:
            con.close()
        except:
            pass
