# modulos/reuniones.py
import streamlit as st
from datetime import datetime, time
from modulos.config.conexion import obtener_conexion

def mostrar_reuniones():
    """
    Módulo para registrar y gestionar reuniones por grupo.
    Acceso: SOLO usuarios con cargo 'SECRETARIA' (case-insensitive).
    Tabla esperada (según tu imagen): Reunion(ID_Reunion, ID_Grupo, fecha, ID_Estado_reunion, lugar, total_presentes, Hora)
    """

    st.header("📅 Registro de Reuniones por Grupo")

    # --- Permiso: solo SECRETARIA puede editar/crear ---
    cargo = (st.session_state.get("cargo_usuario", "") or "").strip().upper()
    if cargo != "SECRETARIA":
        st.warning("🔒 Acceso restringido: Solo la SECRETARIA puede ver y editar las reuniones.")
        return

    # --- Conexión a BD ---
    try:
        con = obtener_conexion()
        if not con:
            st.error("❌ No se pudo conectar a la base de datos.")
            return
        # Intentamos obtener cursor con dictionary=True; si falla usamos cursor normal.
        try:
            cursor = con.cursor(dictionary=True)
            dict_cursor = True
        except TypeError:
            cursor = con.cursor()
            dict_cursor = False
    except Exception as e:
        st.error(f"❌ Error al conectar a la base de datos: {e}")
        return

    try:
        # --- Cargar grupos ---
        try:
            cursor.execute("SELECT ID_Grupo, nombre FROM Grupo ORDER BY ID_Grupo")
            grupos = cursor.fetchall() or []
            # normalizar a lista de dicts si cursor no da dicts
            if not dict_cursor:
                grupos = [{"ID_Grupo": g[0], "nombre": g[1]} for g in grupos]
        except Exception:
            grupos = []

        if not grupos:
            st.info("No hay grupos registrados. Crea primero los grupos en el módulo correspondiente.")
            return

        mapa_grupos = { f"{g['ID_Grupo']} - {g.get('nombre','Grupo')}": g['ID_Grupo'] for g in grupos }
        grupo_label = st.selectbox("Selecciona grupo", options=list(mapa_grupos.keys()))
        id_grupo = int(mapa_grupos[grupo_label])
        st.write("---")

        # --- Cargar reuniones del grupo ---
        cursor.execute("""
            SELECT ID_Reunion, ID_Grupo, fecha, ID_Estado_reunion, lugar, total_presentes, Hora
            FROM Reunion
            WHERE ID_Grupo = %s
            ORDER BY fecha DESC, Hora DESC
        """, (id_grupo,))
        reuniones = cursor.fetchall() or []
        if not dict_cursor:
            # convertir a dicts
            reuniones = [
                {"ID_Reunion": r[0], "ID_Grupo": r[1], "fecha": r[2], "ID_Estado_reunion": r[3],
                 "lugar": r[4], "total_presentes": r[5], "Hora": r[6]} for r in reuniones
            ]

        # --- Selección reunión existente o nueva ---
        opciones = ["➕ Nueva reunión"]
        mapa_reuniones = {opciones[0]: None}
        for r in reuniones:
            fecha_txt = r["fecha"].strftime("%Y-%m-%d") if r.get("fecha") else "sin_fecha"
            hora_txt = r["Hora"].strftime("%H:%M") if isinstance(r.get("Hora"), (time,)) else (str(r.get("Hora")) if r.get("Hora") else "")
            label = f"{r['ID_Reunion']} • {fecha_txt} {hora_txt} — { (r.get('lugar') or '')[:30] }"
            opciones.append(label)
            mapa_reuniones[label] = r["ID_Reunion"]

        sel_label = st.selectbox("Selecciona reunión para editar o crea una nueva", opciones)
        id_reunion = mapa_reuniones[sel_label]

        # valores por defecto
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

        st.info("Rellena los campos y presiona **Guardar**. Puedes eliminar la reunión seleccionada si lo deseas.")

        # --- Formulario ---
        with st.form("form_reunion"):
            col1, col2 = st.columns(2)
            with col1:
                fecha = st.date_input("Fecha *", value=fecha_def)
            with col2:
                hora = st.time_input("Hora *", value=hora_def)

            lugar = st.text_input("Lugar (opcional)", max_chars=100, value=lugar_def)
            total_presentes = st.text_area("Total presentes (opcional): nombres o número", value=asistentes_def, height=80)

            estados = {1: "Programada", 2: "Realizada", 3: "Cancelada"}
            estado = st.selectbox("Estado", options=list(estados.keys()),
                                  format_func=lambda k: estados[k],
                                  index=list(estados.keys()).index(estado_def) if estado_def in estados else 0)

            guardar = st.form_submit_button("✅ Guardar")
            eliminar = st.form_submit_button("🗑️ Eliminar reunión") if id_reunion else False
            nuevo = st.form_submit_button("➕ Nuevo (limpiar)")

            if nuevo:
                st.experimental_rerun()

            if eliminar:
                if not id_reunion:
                    st.warning("No hay reunión seleccionada para eliminar.")
                else:
                    try:
                        cursor.execute("DELETE FROM Reunion WHERE ID_Reunion = %s", (int(id_reunion),))
                        con.commit()
                        st.success("🗑️ Reunión eliminada correctamente.")
                        st.experimental_rerun()
                    except Exception as e:
                        con.rollback()
                        st.error(f"❌ Error al eliminar la reunión: {e}")

            if guardar:
                # validaciones básicas
                if fecha is None:
                    st.warning("⚠️ Selecciona una fecha.")
                elif hora is None:
                    st.warning("⚠️ Selecciona una hora.")
                else:
                    try:
                        hora_str = hora.strftime("%H:%M:%S") if hasattr(hora, "strftime") else str(hora)

                        if id_reunion:
                            sql_up = """
                                UPDATE Reunion
                                SET fecha=%s, Hora=%s, lugar=%s, total_presentes=%s, ID_Estado_reunion=%s
                                WHERE ID_Reunion=%s
                            """
                            params = (fecha, hora_str, lugar.strip() if lugar else None,
                                      total_presentes.strip() if total_presentes else None,
                                      int(estado), int(id_reunion))
                            cursor.execute(sql_up, params)
                        else:
                            sql_ins = """
                                INSERT INTO Reunion
                                (ID_Grupo, fecha, Hora, lugar, total_presentes, ID_Estado_reunion)
                                VALUES (%s,%s,%s,%s,%s,%s)
                            """
                            params = (int(id_grupo), fecha, hora_str,
                                      lugar.strip() if lugar else None,
                                      total_presentes.strip() if total_presentes else None,
                                      int(estado))
                            cursor.execute(sql_ins, params)

                        con.commit()
                        st.success("✅ Reunión guardada correctamente.")
                        st.experimental_rerun()

                    except Exception as e:
                        con.rollback()
                        st.error(f"❌ Error al guardar la reunión: {e}")

        st.write("---")
        # --- Resumen de reuniones ---
        st.subheader("Reuniones registradas (resumen)")
        if not reuniones:
            st.info("No hay reuniones registradas para este grupo.")
        else:
            import pandas as pd
            rows = []
            for r in reuniones:
                rows.append({
                    "ID_Reunion": r["ID_Reunion"],
                    "Fecha": r["fecha"].strftime("%Y-%m-%d") if r.get("fecha") else "",
                    "Hora": r["Hora"].strftime("%H:%M:%S") if hasattr(r.get("Hora"), "strftime") else (str(r.get("Hora")) if r.get("Hora") else ""),
                    "Lugar": r.get("lugar") or "",
                    "Estado": estados.get(r.get("ID_Estado_reunion"), r.get("ID_Estado_reunion")),
                    "Total_presentes": r.get("total_presentes") or ""
                })
            df = pd.DataFrame(rows)
            st.dataframe(df.sort_values(by=["Fecha","Hora"], ascending=[False, False]))

    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            con.close()
        except Exception:
            pass
