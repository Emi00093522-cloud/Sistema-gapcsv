# modulos/reglamentos.py
import streamlit as st
from modulos.config.conexion import obtener_conexion

def mostrar_reglamentos():
    """
    UI para registrar/editar reglamentos por grupo.
    - Carga grupos desde la tabla Grupos.
    - Permite crear/editar reglas por renglón (nombre, descripción).
    - Para cada renglón: Multa (Sí/No) y Monto (USD) con decimales.
    - Si Multa == No, el monto se muestra como guion y se guarda NULL en la BD.
    - Botones: GUARDAR CAMBIOS, Registrar otro reglamento, Editar, Mensajes de confirmación.
    """

    st.header("📜 Reglamentos por Grupo")

    # 0) Permiso UI: solo SECRETARIA / PRESIDENTE pueden editar
    cargo = (st.session_state.get("cargo_usuario", "") or "").strip().upper()
    if cargo not in ("SECRETARIA", "PRESIDENTE"):
        st.warning("🔒 Solo usuarios con cargo 'SECRETARIA' o 'PRESIDENTE' pueden gestionar reglamentos.")
        return

    # 1) Conexión a la BD
    try:
        con = obtener_conexion()
        if not con:
            st.error("❌ No fue posible conectar a la base de datos.")
            return
        cursor = con.cursor(dictionary=True)
    except Exception as e:
        st.error(f"❌ Error al conectar a la BD: {e}")
        return

    try:
        # 2) Cargar grupos
        try:
            cursor.execute("SELECT ID_Grupo, nombre_grupo FROM Grupos ORDER BY ID_Grupo")
            grupos = cursor.fetchall() or []
        except Exception:
            grupos = []

        if not grupos:
            st.info("No se encontraron grupos. Crea primero los grupos en el módulo correspondiente.")
            return

        opciones_grupos = [f"{g['ID_Grupo']} - {g.get('nombre_grupo','Grupo')}" for g in grupos]
        mapa_grupos = {opciones_grupos[i]: grupos[i]['ID_Grupo'] for i in range(len(grupos))}

        sel_label = st.selectbox("REGLAMENTO de grupo: selecciona un grupo", opciones_grupos, key="sel_grupo_regl")
        id_grupo = int(mapa_grupos[sel_label])
        st.write("---")

        # 3) Cargar reglamentos existentes del grupo
        cursor.execute("""
            SELECT ID_Reglamento, nombre_regla, descripcion, monto_multa, `tipo_sanción`, ID_Estado
            FROM Reglamentos
            WHERE ID_Grupo = %s
            ORDER BY ID_Reglamento
        """, (id_grupo,))
        regs = cursor.fetchall() or []

        # Mantener nuevos temporalmente en session_state para poder agregar varios antes de guardar
        if "reglamentos_nuevos_temp" not in st.session_state:
            st.session_state["reglamentos_nuevos_temp"] = []

        st.subheader("Editar / Crear reglas")
        st.write("Modifica los renglones y presiona **GUARDAR CAMBIOS**. Usa **Registrar otro reglamento** para agregar renglones vacíos.")

        # Construir una lista de renglones editables (existentes + temporales)
        rows = []

        # Renglones existentes
        for r in regs:
            rows.append({
                "ID_Reglamento": r['ID_Reglamento'],
                "nombre_regla": r.get('nombre_regla') or "",
                "descripcion": r.get('descripcion') or "",
                "tiene_multa": "Sí" if (r.get('tipo_sanción') or "").lower() == "sí" else "No",
                "monto_multa": float(r['monto_multa']) if r.get('monto_multa') is not None else None,
                "ID_Estado": r.get('ID_Estado') or 1
            })

        # Renglones nuevos temporales (agregados por el usuario)
        for t in st.session_state["reglamentos_nuevos_temp"]:
            rows.append({
                "ID_Reglamento": None,
                "nombre_regla": t.get("nombre_regla",""),
                "descripcion": t.get("descripcion",""),
                "tiene_multa": t.get("tiene_multa","No"),
                "monto_multa": t.get("monto_multa", None),
                "ID_Estado": 1
            })

        # Formulario que contiene todos los renglones
        with st.form("form_reglamentos_grid"):
            editable_rows = []
            for idx, row in enumerate(rows):
                # Encabezado del renglón
                header = f"Reglón {idx+1}" + (f" — ID {row['ID_Reglamento']}" if row["ID_Reglamento"] else " — Nuevo")
                st.markdown(f"**{header}**")
                c1, c2, c3, c4 = st.columns([4,3,1.2,1.2])

                # Nombre regla
                key_nombre = f"nombre_{idx}_{row['ID_Reglamento'] or 'new'}"
                nombre = c1.text_input("Regla", value=row["nombre_regla"], key=key_nombre)

                # Descripción
                key_desc = f"desc_{idx}_{row['ID_Reglamento'] or 'new'}"
                descripcion = c2.text_input("Descripción (opcional)", value=row["descripcion"], key=key_desc)

                # Multa Sí/No
                key_multa = f"multa_{idx}_{row['ID_Reglamento'] or 'new'}"
                multa = c3.selectbox("Multa", options=["No","Sí"], index=0 if row["tiene_multa"]!="Sí" else 1, key=key_multa)

                # Monto - se habilita solo si multa == Sí
                key_monto = f"monto_{idx}_{row['ID_Reglamento'] or 'new'}"
                if multa == "Sí":
                    monto = c4.number_input("Monto (USD)", min_value=0.0, step=0.01, format="%.2f",
                                            value=float(row["monto_multa"]) if row["monto_multa"] is not None else 0.00,
                                            key=key_monto)
                else:
                    c4.write("—")  # guion automático
                    monto = None

                editable_rows.append({
                    "ID_Reglamento": row["ID_Reglamento"],
                    "ID_Grupo": id_grupo,
                    "nombre_regla": nombre.strip(),
                    "descripcion": descripcion.strip() if descripcion else None,
                    "tiene_multa": multa,
                    "monto_multa": monto,
                    "ID_Estado": row.get("ID_Estado",1)
                })
                st.markdown("---")

            # Botones abajo del formulario
            btn_guardar = st.form_submit_button("✅ GUARDAR CAMBIOS")
            btn_agregar = st.form_submit_button("➕ Registrar otro reglamento")
            btn_cancel = st.form_submit_button("✖ Cancelar")

            # Acciones botones
            if btn_agregar:
                # añadir renglón temporal en session_state
                st.session_state["reglamentos_nuevos_temp"].append({
                    "nombre_regla": "",
                    "descripcion": "",
                    "tiene_multa": "No",
                    "monto_multa": None
                })
                st.experimental_rerun()

            if btn_cancel:
                st.session_state["reglamentos_nuevos_temp"] = []
                st.info("Acción cancelada. No se realizaron cambios.")
                st.experimental_rerun()

            if btn_guardar:
                errores = []
                exitos = 0
                for erow in editable_rows:
                    # ignorar si no tiene nombre
                    if not erow["nombre_regla"]:
                        continue

                    # validar monto si tiene multa
                    if erow["tiene_multa"] == "Sí":
                        if erow["monto_multa"] is None:
                            errores.append(f"Regla '{erow['nombre_regla']}' requiere un monto válido.")
                            continue
                        try:
                            monto_val = round(float(erow["monto_multa"]), 2)
                        except Exception:
                            errores.append(f"Monto inválido en regla '{erow['nombre_regla']}'.")
                            continue
                    else:
                        monto_val = None

                    try:
                        if erow["ID_Reglamento"]:
                            # UPDATE
                            sql_up = """
                                UPDATE Reglamentos
                                SET nombre_regla=%s, descripcion=%s, monto_multa=%s, `tipo_sanción`=%s, ID_Estado=%s
                                WHERE ID_Reglamento=%s
                            """
                            params = (
                                erow["nombre_regla"],
                                erow["descripcion"],
                                monto_val,
                                "Sí" if erow["tiene_multa"]=="Sí" else "No",
                                int(erow.get("ID_Estado",1)),
                                int(erow["ID_Reglamento"])
                            )
                            cursor.execute(sql_up, params)
                        else:
                            # INSERT
                            sql_ins = """
                                INSERT INTO Reglamentos
                                (ID_Grupo, nombre_regla, descripcion, monto_multa, `tipo_sanción`, ID_Estado)
                                VALUES (%s,%s,%s,%s,%s,%s)
                            """
                            params = (
                                int(erow["ID_Grupo"]),
                                erow["nombre_regla"],
                                erow["descripcion"],
                                monto_val,
                                "Sí" if erow["tiene_multa"]=="Sí" else "No",
                                int(erow.get("ID_Estado",1))
                            )
                            cursor.execute(sql_ins, params)
                        exitos += 1
                    except Exception as e:
                        errores.append(f"Error guardando '{erow['nombre_regla']}': {e}")

                # commit / rollback
                if errores:
                    con.rollback()
                    st.error("❌ Ocurrieron errores al guardar:")
                    for e in errores:
                        st.write("- " + e)
                else:
                    con.commit()
                    if exitos > 0:
                        st.success("✅ Cambios guardados exitosamente.")
                    else:
                        st.info("No se detectaron renglones válidos para guardar.")
                    # limpiar temporales
                    st.session_state["reglamentos_nuevos_temp"] = []
                    st.experimental_rerun()

        # sección inferior: botones extras y guía
        col_a, col_b, col_c = st.columns([1,1,2])
        with col_a:
            if st.button("✏️ Editar un reglamento existente"):
                st.info("Selecciona un reglamento en la lista arriba y edítalo, luego presiona GUARDAR CAMBIOS.")
        with col_b:
            if st.button("➕ Registrar otro reglamento (vacío)"):
                st.session_state["reglamentos_nuevos_temp"].append({
                    "nombre_regla": "",
                    "descripcion": "",
                    "tiene_multa": "No",
                    "monto_multa": None
                })
                st.experimental_rerun()
        with col_c:
            st.info("Para seguir navegando usa el menú de la izquierda. ✅")

        # Mostrar resumen rápido de reglamentos del grupo
        st.write("---")
        st.subheader("Resumen actual de reglas")
        if not regs:
            st.info("No hay reglamentos guardados para este grupo aún.")
        else:
            for r in regs:
                monto_text = f"${float(r['monto_multa']):.2f}" if r.get('monto_multa') is not None else "—"
                tipo = r.get('tipo_sanción') or "No"
                st.markdown(f"- **{r['ID_Reglamento']}** • {r['nombre_regla']} — Multa: **{tipo}** — Monto: **{monto_text}**")

    finally:
        try: cursor.close()
        except: pass
        try: con.close()
        except: pass
