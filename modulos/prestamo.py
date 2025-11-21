import streamlit as st
from modulos.config.conexion import obtener_conexion
from datetime import datetime

def mostrar_prestamo():
    st.header("💰 Registrar Préstamo")

    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)

        # ======================================================
        # 1. CARGAR REUNIONES DISPONIBLES
        # ======================================================
        cursor.execute("""
            SELECT r.ID_Reunion, r.fecha, r.lugar, g.ID_Grupo, g.nombre as grupo_nombre
            FROM Reunion r
            JOIN Grupo g ON r.ID_Grupo = g.ID_Grupo
            ORDER BY r.fecha DESC, g.nombre
        """)
        reuniones = cursor.fetchall()

        if not reuniones:
            st.warning("⚠️ No hay reuniones registradas en el sistema.")
            return

        # Crear opciones para el selectbox de reuniones
        reunion_options = {}
        for reunion in reuniones:
            fecha_str = reunion['fecha'].strftime("%Y-%m-%d") if hasattr(reunion['fecha'], 'strftime') else str(reunion['fecha'])
            label = f"Reunión {reunion['ID_Reunion']} - {fecha_str} - {reunion['grupo_nombre']}"
            if reunion['lugar']:
                label += f" - {reunion['lugar']}"
            reunion_options[label] = {
                'id_reunion': reunion['ID_Reunion'],
                'id_grupo': reunion['ID_Grupo'],
                'grupo_nombre': reunion['grupo_nombre']
            }

        # Seleccionar reunión
        reunion_seleccionada_label = st.selectbox(
            "Selecciona una reunión *",
            options=list(reunion_options.keys())
        )
        
        reunion_info = reunion_options[reunion_seleccionada_label]
        id_reunion = reunion_info['id_reunion']
        id_grupo = reunion_info['id_grupo']
        grupo_nombre = reunion_info['grupo_nombre']

        # Mostrar información de la reunión seleccionada
        st.success(f"📅 Reunión seleccionada: {reunion_seleccionada_label}")
        
        # ======================================================
        # 2. CARGAR MIEMBROS DEL GRUPO DE LA REUNIÓN SELECCIONADA
        # ======================================================
        cursor.execute("""
            SELECT ID_Miembro, nombre, apellido 
            FROM Miembro 
            WHERE ID_Grupo = %s AND ID_Estado = 1
            ORDER BY nombre, apellido
        """, (id_grupo,))
        miembros = cursor.fetchall()

        if not miembros:
            st.warning(f"⚠️ No hay miembros activos en el grupo '{grupo_nombre}'.")
            return

        st.info(f"👥 Grupo: {grupo_nombre} - {len(miembros)} miembros activos")

        # ======================================================
        # 3. CARGAR ESTADOS DE PRÉSTAMO
        # ======================================================
        cursor.execute("SELECT ID_Estado_prestamo, estado_prestamo FROM Estado_prestamo")
        estados_prestamo = cursor.fetchall()

        # ======================================================
        # 4. FORMULARIO DE PRÉSTAMO
        # ======================================================
        with st.form("form_prestamo"):
            st.subheader("Datos del Préstamo")

            # Miembro - Solo miembros del grupo de la reunión seleccionada
            if miembros:
                miembro_options = {f"{m['nombre']} {m.get('apellido', '')} (ID: {m['ID_Miembro']})": m['ID_Miembro'] for m in miembros}
                miembro_seleccionado = st.selectbox("Miembro *", list(miembro_options.keys()))
                ID_Miembro = miembro_options[miembro_seleccionado]
            else:
                st.error("❌ No hay miembros disponibles en este grupo")
                ID_Miembro = None

            # Fecha
            fecha_desembolso = st.date_input("Fecha de desembolso *", value=datetime.now().date())

            # Monto
            monto = st.number_input("Monto del préstamo ($) *",
                                    min_value=0.01,
                                    value=1000.00,
                                    step=100.00,
                                    format="%.2f")

            # Tasa de interés MENSUAL
            tasa_mensual = st.number_input("Tasa de interés MENSUAL (%) *",
                                           min_value=0.00,
                                           max_value=100.00,
                                           value=5.00,
                                           step=0.10,
                                           format="%.2f")

            # Estado préstamo
            if estados_prestamo:
                estado_options = {e["estado_prestamo"]: e["ID_Estado_prestamo"] for e in estados_prestamo}
                estado_seleccionado = st.selectbox("Estado del préstamo *", list(estado_options.keys()))
                ID_Estado_prestamo = estado_options[estado_seleccionado]
            else:
                st.error("❌ No hay estados de préstamo disponibles")
                ID_Estado_prestamo = None

            # Plazo
            plazo = st.number_input("Plazo (meses) *", min_value=1, max_value=120, value=6, step=1)

            # Propósito
            proposito = st.text_area("Propósito del préstamo (opcional)",
                                     placeholder="Ej: Compra de materiales, gastos médicos…",
                                     max_chars=200,
                                     height=80)

            # ================================
            # CÁLCULOS DE INTERÉS MENSUAL SIMPLE
            # ================================
            if monto > 0 and plazo > 0:
                # Convertir tasa mensual a decimal
                tasa_decimal = tasa_mensual / 100

                # Interés de un mes
                interes_mensual = monto * tasa_decimal

                # Interés total
                interes_total = interes_mensual * plazo

                # Total a pagar
                monto_total = monto + interes_total

                # Cuota fija mensual simple
                cuota_mensual = monto_total / plazo

                st.info("📊 **Resumen del préstamo:**")
                st.write(f"- Tasa mensual: **{tasa_mensual:.2f}%**")
                st.write(f"- Interés mensual: **${interes_mensual:,.2f}**")
                st.write(f"- Interés total a pagar: **${interes_total:,.2f}**")
                st.write(f"- Monto total a pagar: **${monto_total:,.2f}**")
                st.write(f"- 💵 **Cuota mensual: ${cuota_mensual:,.2f}**")

            enviar = st.form_submit_button("✅ Registrar Préstamo")

            if enviar:
                errores = []

                if ID_Miembro is None:
                    errores.append("⚠ Debes seleccionar un miembro.")
                if monto <= 0:
                    errores.append("⚠ El monto debe ser mayor a 0.")
                if tasa_mensual < 0:
                    errores.append("⚠ La tasa mensual no puede ser negativa.")
                if plazo <= 0:
                    errores.append("⚠ El plazo debe ser mayor a 0.")
                if ID_Estado_prestamo is None:
                    errores.append("⚠ Debes seleccionar un estado del préstamo.")

                if errores:
                    for e in errores:
                        st.warning(e)
                else:
                    try:
                        proposito_val = proposito.strip() if proposito.strip() else None

                        # ✅ GUARDAR CON LA REUNIÓN SELECCIONADA
                        cursor.execute("""
                            INSERT INTO Prestamo
                            (ID_Miembro, ID_Reunion, fecha_desembolso, monto, total_interes,
                             ID_Estado_prestamo, plazo, proposito)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (ID_Miembro, id_reunion, fecha_desembolso, monto, tasa_mensual,
                              ID_Estado_prestamo, plazo, proposito_val))

                        con.commit()

                        st.success("✅ Préstamo registrado correctamente!")
                        st.success(f"📅 Vinculado a la reunión: {reunion_seleccionada_label}")
                        st.success(f"- Interés total: ${interes_total:,.2f}")
                        st.success(f"- Cuota mensual: ${cuota_mensual:,.2f}")

                        if st.button("🆕 Registrar otro préstamo"):
                            st.rerun()

                    except Exception as e:
                        con.rollback()
                        st.error(f"❌ Error al registrar el préstamo: {e}")

    except Exception as e:
        st.error(f"❌ Error general: {e}")

    finally:
        if "cursor" in locals():
            cursor.close()
        if "con" in locals():
            con.close()
