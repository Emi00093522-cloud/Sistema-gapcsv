# modulos/reglamentos.py
import streamlit as st
from modulos.config.conexion import obtener_conexion

def mostrar_reglamentos():
    st.header("📜 Reglamentos por Grupo")

    # Intento de obtener conexión y cursores
    try:
        con = obtener_conexion()
        if not con:
            st.error("⚠️ No se pudo conectar a la base de datos.")
            return
        cursor = con.cursor(dictionary=True)  # dictionary=True si usas mysql-connector / pymysql
    except Exception as e:
        st.error(f"❌ Error al conectar: {e}")
        return

    try:
        # --- Obtener lista de grupos para el select ---
        grupos = []
        try:
            cursor.execute("SELECT ID_Grupo, nombre_grupo FROM Grupos")
            grupos = cursor.fetchall()
        except Exception:
            # Si no existe la tabla Grupos o hay error, dejamos la lista vacía
            grupos = []

        # Convertir a opciones para st.selectbox
        opciones_grupos = {}
        if grupos:
            for g in grupos:
                # si rows son dicts (dictionary=True)
                if isinstance(g, dict):
                    opciones_grupos[f"{g['ID_Grupo']} - {g.get('nombre_grupo','Grupo')}"] = g['ID_Grupo']
                else:
                    # si viene como tupla (ID, nombre)
                    opciones_grupos[f"{g[0]} - {g[1] if len(g)>1 else 'Grupo'}"] = g[0]

        st.subheader("➕ Registrar / Actualizar reglamento")
        with st.form("form_reglamento", clear_on_submit=False):
            # Selección de grupo (si hay)
            if opciones_grupos:
                llave = st.selectbox("Selecciona el grupo", options=list(opciones_grupos.keys()))
                id_grupo = opciones_grupos[llave]
            else:
                st.info("No se encontró la tabla 'Grupos' o no hay grupos. Ingresa el ID de grupo manualmente.")
                id_grupo = st.number_input("ID_Grupo", min_value=1, step=1)

            nombre_regla = st.text_input("Nombre de la regla", max_chars=100)
            descripcion = st.text_area("Descripción (opcional)")
            monto_multa = st.text_input("Monto multa (ej. 10.50) - opcional", value="")
            tipo_sancion = st.text_input("Tipo de sanción (opcional)", max_chars=50)

            # Estado (por ejemplo 1 = activo, 0 = inactivo)
            estado_opciones = {"Activo": 1, "Inactivo": 0}
            estado_label = st.selectbox("Estado", options=list(estado_opciones.keys()))
            id_estado = estado_opciones[estado_label]

            enviar = st.form_submit_button("✅ Guardar reglamento")

            if enviar:
                # Validaciones
                if not nombre_regla.strip():
                    st.warning("⚠️ Debes ingresar el nombre de la regla.")
                elif not id_grupo:
                    st.warning("⚠️ Debes indicar el grupo al que pertenece el reglamento.")
                else:
                    # Validar y convertir monto_multa si fue proporcionado
                    monto_val = None
                    if monto_multa.strip() != "":
                        try:
                            # Asegurarse formato decimal con punto
                            monto_val = float(monto_multa.replace(",", "."))
                        except ValueError:
                            st.warning("⚠️ El monto de multa no tiene un formato válido. Usa números (ej. 12.50).")
                            monto_val = "INVALIDO"

                    if monto_val == "INVALIDO":
                        pass
                    else:
                        try:
                            # Insert (usar nombres de columnas exactamente como en tu tabla)
                            sql = """
                                INSERT INTO Reglamentos
                                (ID_Grupo, nombre_regla, descripcion, monto_multa, tipo_sanción, ID_Estado)
                                VALUES (%s, %s, %s, %s, %s, %s)
                            """
                            params = (
                                int(id_grupo),
                                nombre_regla.strip(),
                                descripcion.strip() if descripcion else None,
                                monto_val if monto_val is not None else None,
                                tipo_sancion.strip() if tipo_sancion else None,
                                int(id_estado)
                            )
                            cursor.execute(sql, params)
                            con.commit()

                            # Obtener id insertado si el conector lo provee
                            inserted_id = getattr(cursor, "lastrowid", None)
                            st.success(f"✅ Reglamento guardado correctamente. ID: {inserted_id if inserted_id else ''}")
                            # Opcional: limpiar formulario
                            st.experimental_rerun()
                        except Exception as e:
                            con.rollback()
                            st.error(f"❌ Error al guardar el reglamento: {e}")

        # --- Mostrar reglamentos existentes (opcional filtrado por grupo) ---
        st.subheader("📋 Reglamentos existentes")
        filt_group = None
        if opciones_grupos:
            # select para filtrar
            sel = st.selectbox("Filtrar por grupo (mostrar todos si eliges 'Todos')",
                               options=["Todos"] + list(opciones_grupos.keys()))
            if sel != "Todos":
                filt_group = opciones_grupos[sel]

        # Construir consulta para mostrar
        try:
            if filt_group:
                cursor.execute("""SELECT r.ID_Reglamento, r.ID_Grupo, r.nombre_regla, r.descripcion,
                                         r.monto_multa, r.`tipo_sanción`, r.ID_Estado
                                  FROM Reglamentos r
                                  WHERE r.ID_Grupo = %s
                                  ORDER BY r.ID_Reglamento DESC
                               """, (filt_group,))
            else:
                cursor.execute("""SELECT r.ID_Reglamento, r.ID_Grupo, r.nombre_regla, r.descripcion,
                                         r.monto_multa, r.`tipo_sanción`, r.ID_Estado
                                  FROM Reglamentos r
                                  ORDER BY r.ID_Reglamento DESC
                               """)
            filas = cursor.fetchall()

            if not filas:
                st.info("No hay reglamentos registrados aún.")
            else:
                # Mostrar de forma simple; puedes usar st.dataframe si lo prefieres
                import pandas as pd
                # convertir filas a DataFrame (considerar que cursor devuelve dicts o tuplas)
                if isinstance(filas[0], dict):
                    df = pd.DataFrame(filas)
                else:
                    df = pd.DataFrame(filas, columns=["ID_Reglamento","ID_Grupo","nombre_regla",
                                                      "descripcion","monto_multa","tipo_sanción","ID_Estado"])
                st.dataframe(df)

        except Exception as e:
            st.error(f"❌ Error al recuperar reglamentos: {e}")

    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            con.close()
        except Exception:
            pass
