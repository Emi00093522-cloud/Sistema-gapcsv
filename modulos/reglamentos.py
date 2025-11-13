# modulos/reglamentos.py
import streamlit as st
from modulos.config.conexion import obtener_conexion
import decimal

def mostrar_reglamentos():
    st.header("📜 Reglamentos por Grupo")

    # --- Conexión ---
    try:
        con = obtener_conexion()
        if not con:
            st.error("⚠️ No se pudo conectar a la base de datos.")
            return
        cursor = con.cursor(dictionary=True)  # si tu conector no soporta dictionary=True, quita y adapta
    except Exception as e:
        st.error(f"❌ Error al conectar: {e}")
        return

    try:
        # --- Cargar grupos para el selectbox ---
        grupos = []
        try:
            cursor.execute("SELECT ID_Grupo, nombre_grupo FROM Grupos ORDER BY ID_Grupo")
            grupos = cursor.fetchall()
        except Exception:
            grupos = []

        opciones = []
        mapa_grupos = {}
        for g in grupos:
            if isinstance(g, dict):
                label = f"{g['ID_Grupo']} - {g.get('nombre_grupo', 'Grupo')}"
                mapa_grupos[label] = g['ID_Grupo']
            else:
                label = f"{g[0]} - {g[1] if len(g) > 1 else 'Grupo'}"
                mapa_grupos[label] = g[0]
            opciones.append(label)

        if not opciones:
            st.warning("No se encontraron grupos en la base de datos. Puedes crear grupos desde el módulo correspondiente.")
            # permitir ingresar ID manual por si desean hacerlo
            id_grupo_manual = st.number_input("ID_Grupo (ingresa manualmente)", min_value=1, step=1)
            selected_label = None
            id_grupo = int(id_grupo_manual)
        else:
            selected_label = st.selectbox("REGLAMENTO de grupo: selecciona un grupo", opciones)
            id_grupo = int(mapa_grupos[selected_label])

        st.write("---")

        # --- Obtener reglamentos existentes del grupo seleccionado ---
        cursor.execute("""
            SELECT ID_Reglamento, ID_Grupo, nombre_regla, descripcion, monto_multa, `tipo_sanción`, ID_Estado
            FROM Reglamentos
            WHERE ID_Grupo = %s
            ORDER BY ID_Reglamento
        """, (id_grupo,))
        filas = cursor.fetchall() or []

        # Estado para manejar nuevos renglones
        if "reglamentos_nuevos" not in st.session_state:
            st.session_state["reglamentos_nuevos"] = []  # lista de dicts temporales para nuevos renglones

        st.subheader("Editar reglas (modifica los renglones y presiona GUARDAR CAMBIOS)")
        with st.form("form_reglamentos"):
            filas_editables = []

            # Mostrar reglamentos ya guardados (edición)
            for i, row in enumerate(filas):
                # row puede venir como dict o tupla
                if isinstance(row, dict):
                    id_reg = row.get("ID_Reglamento")
                    nombre = row.get("nombre_regla") or ""
                    descripcion = row.get("descripcion") or ""
                    monto = row.get("monto_multa")
                    tipo_sancion = row.get("tipo_sanción") or "No"
                    id_estado = row.get("ID_Estado") or 1
                else:
                    # si tu cursor devuelve tuplas, ajusta índices
                    id_reg = row[0]
                    nombre = row[2] or ""
                    descripcion = row[3] or ""
                    monto = row[4]
                    tipo_sancion = row[5] or "No"
                    id_estado = row[6] if len(row) > 6 else 1

                st.markdown(f"**Reglón {i+1} — ID {id_reg}**")
                cols = st.columns([4, 3, 2, 2])  # nombre, descripcion, multa, monto
                nombre_input = cols[0].text_input(f"Nombre regla {id_reg}", value=nombre, key=f"nombre_{id_reg}")
                descripcion_input = cols[1].text_input(f"Descripción {id_reg}", value=descripcion, key=f"desc_{id_reg}")
                multa_select = cols[2].selectbox(f"Multa {id_reg}", options=["No", "Sí"], index=0 if tipo_sancion.lower()!="sí" else 1, key=f"multa_{id_reg}")
                # monto: si multa == No mostramos '-' (disabled), sino número editable
                if multa_select == "Sí":
                    # mostrar number_input con 2 decimales, USD
                    monto_val = cols[3].number_input(f"Monto multa (USD) {id_reg}", min_value=0.0, step=0.01, format="%.2f",
                                                     value=float(monto) if monto is not None else 0.00, key=f"monto_{id_reg}")
                else:
                    # mostramos campo deshabilitado visualmente como texto y guardamos monto_val = None
                    cols[3].write("—")  # guion automático
                    monto_val = None

                filas_editables.append({
                    "ID_Reglamento": id_reg,
                    "ID_Grupo": id_grupo,
                    "nombre_regla": nombre_input,
                    "descripcion": descripcion_input,
                    "tiene_multa": multa_select,
                    "monto_multa": monto_val,
                    "ID_Estado": id_estado
                })
                st.markdown("---")

            # Mostrar renglones nuevos (si el usuario añadió previamente)
            for idx, temp in enumerate(st.session_state["reglamentos_nuevos"]):
                st.markdown(f"**Nuevo reglón {idx+1} (temporal)**")
                cols = st.columns([4, 3, 2, 2])
                nombre_input = cols[0].text_input(f"Nombre nuevo {idx}", value=temp.get("nombre_regla",""), key=f"nuevo_nombre_{idx}")
                descripcion_input = cols[1].text_input(f"Descripción nuevo {idx}", value=temp.get("descripcion",""), key=f"nuevo_desc_{idx}")
                multa_select = cols[2].selectbox(f"Multa nuevo {idx}", options=["No","Sí"], index=0 if temp.get("tiene_multa","No")!="Sí" else 1, key=f"nuevo_multa_{idx}")
                if multa_select == "Sí":
                    monto_val = cols[3].number_input(f"Monto nuevo (USD) {idx}", min_value=0.0, step=0.01, format="%.2f", value=float(temp.get("monto_multa") or 0.0), key=f"nuevo_monto_{idx}")
                else:
                    cols[3].write("—")
                    monto_val = None

                filas_editables.append({
                    "ID_Reglamento": None,  # indicador de nuevo
                    "ID_Grupo": id_grupo,
                    "nombre_regla": nombre_input,
                    "descripcion": descripcion_input,
                    "tiene_multa": multa_select,
                    "monto_multa": monto_val,
                    "ID_Estado": 1
                })
                st.markdown("---")

            # Botones del form
            guardar = st.form_submit_button("✅ GUARDAR CAMBIOS")
            agregar_otro = st.form_submit_button("➕ Registrar otro reglamento")
            cancelar = st.form_submit_button("✖ Cancelar / Volver")

            if guardar:
                # Validaciones básicas y guardado
                guardados = 0
                errores = []
                for fr in filas_editables:
                    nombre = (fr["nombre_regla"] or "").strip()
                    if not nombre:
                        # ignorar renglones vacíos
                        continue

                    tiene_multa = fr["tiene_multa"]
                    monto = fr["monto_multa"]
                    if tiene_multa == "Sí":
                        # monto obligatorio (>= 0)
                        if monto is None:
                            errores.append(f"La regla '{nombre}' requiere un monto de multa válido.")
                            continue
                        # Normalizar a decimal con 2 decimales
                        try:
                            monto_dec = round(float(monto), 2)
                        except Exception:
                            errores.append(f"Monto inválido para la regla '{nombre}'.")
                            continue
                    else:
                        monto_dec = None  # guardamos NULL

                    try:
                        if fr["ID_Reglamento"]:
                            # UPDATE
                            sql_up = """
                                UPDATE Reglamentos
                                SET nombre_regla = %s,
                                    descripcion = %s,
                                    monto_multa = %s,
                                    `tipo_sanción` = %s,
                                    ID_Estado = %s
                                WHERE ID_Reglamento = %s
                            """
                            params = (
                                nombre,
                                fr["descripcion"] if fr["descripcion"] else None,
                                monto_dec,
                                "Sí" if tiene_multa == "Sí" else "No",
                                int(fr.get("ID_Estado", 1)),
                                int(fr["ID_Reglamento"])
                            )
                            cursor.execute(sql_up, params)
                        else:
                            # INSERT
                            sql_ins = """
                                INSERT INTO Reglamentos
                                (ID_Grupo, nombre_regla, descripcion, monto_multa, `tipo_sanción`, ID_Estado)
                                VALUES (%s, %s, %s, %s, %s, %s)
                            """
                            params = (
                                int(fr["ID_Grupo"]),
                                nombre,
                                fr["descripcion"] if fr["descripcion"] else None,
                                monto_dec,
                                "Sí" if tiene_multa == "Sí" else "No",
                                int(fr.get("ID_Estado", 1))
                            )
                            cursor.execute(sql_ins, params)
                        guardados += 1
                    except Exception as e:
                        errores.append(f"Error guardando '{nombre}': {e}")

                # commit o rollback
                if errores:
                    con.rollback()
                    st.error("❌ Ocurrieron errores al guardar:")
                    for er in errores:
                        st.write("- " + er)
                else:
                    con.commit()
                    if guardados > 0:
                        st.success("✅ Cambios guardados exitosamente.")
                    else:
                        st.info("No se detectaron cambios para guardar.")

                    # limpiar nuevos temporales
                    st.session_state["reglamentos_nuevos"] = []

                    # Mostrar opciones debajo
                    st.write("")
                    col1, col2, col3 = st.columns([1,1,2])
                    with col1:
                        if st.button("➕ Registrar otro reglamento"):
                            # añadimos un nuevo renglón temporal
                            st.session_state["reglamentos_nuevos"].append({
                                "nombre_regla": "",
                                "descripcion": "",
                                "tiene_multa": "No",
                                "monto_multa": None
                            })
                            st.experimental_rerun()
                    with col2:
                        if st.button("✏️ Editar un reglamento"):
                            st.info("Para editar, modifica los campos arriba y presiona GUARDAR CAMBIOS.")
                    with col3:
                        st.info("Para seguir navegando usa el menú izquierdo. ✅")

            if agregar_otro:
                # añadir fila temporal para nuevo reglamento
                st.session_state["reglamentos_nuevos"].append({
                    "nombre_regla": "",
                    "descripcion": "",
                    "tiene_multa": "No",
                    "monto_multa": None
                })
                st.experimental_rerun()

            if cancelar:
                st.info("Acción cancelada.")
                st.session_state["reglamentos_nuevos"] = []
                st.experimental_rerun()

    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            con.close()
        except Exception:
            pass
