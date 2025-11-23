import streamlit as st
from modulos.config.conexion import obtener_conexion
from datetime import datetime

from modulos.consultas_db import obtener_prestamos
from modulos.permisos import verificar_permisos

def mostrar_prestamos():
    # Necesitas crear esta función en consultas_db.py
    prestamos = obtener_prestamos()  # ✅ Filtrado automático
    # ... tu código actual




#def mostrar_prestamo():
    st.header("💰 Registrar Préstamo")

    # Verificar si hay una reunión seleccionada
    if 'reunion_actual' not in st.session_state:
        st.warning("⚠️ Primero debes seleccionar una reunión en el módulo de Asistencia.")
        return

    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)

        # Obtener la reunión del session_state
        reunion_info = st.session_state.reunion_actual
        id_reunion = reunion_info['id_reunion']
        id_grupo = reunion_info['id_grupo']
        nombre_reunion = reunion_info['nombre_reunion']

        # Mostrar información de la reunión actual
        st.info(f"📅 **Reunión actual:** {nombre_reunion}")

        # Cargar SOLO miembros que asistieron a esta reunión (marcaron SI)
        cursor.execute("""
            SELECT m.ID_Miembro, m.nombre 
            FROM Miembro m
            JOIN Miembroxreunion mr ON m.ID_Miembro = mr.ID_Miembro
            WHERE mr.ID_Reunion = %s AND mr.asistio = 1
            ORDER BY m.nombre
        """, (id_reunion,))
        
        miembros_presentes = cursor.fetchall()

        if not miembros_presentes:
            st.warning(f"⚠️ No hay miembros registrados como presentes en esta reunión.")
            st.info("Por favor, registra la asistencia primero en el módulo correspondiente.")
            return

        # Cargar estados de préstamo
        cursor.execute("SELECT ID_Estado_prestamo, estado_prestamo FROM Estado_prestamo")
        estados_prestamo = cursor.fetchall()

        with st.form("form_prestamo"):
            st.subheader("Datos del Préstamo")

            # Miembro (solo los presentes)
            if miembros_presentes:
                miembro_options = {f"{m['nombre']} (ID: {m['ID_Miembro']})": m['ID_Miembro'] for m in miembros_presentes}
                miembro_seleccionado = st.selectbox("Miembro *", list(miembro_options.keys()))
                ID_Miembro = miembro_options[miembro_seleccionado]
            else:
                st.error("❌ No hay miembros disponibles")
                ID_Miembro = None

            # Fecha
            fecha_desembolso = st.date_input("Fecha de desembolso *", value=datetime.now().date())

            # Monto
            monto = st.number_input("Monto del préstamo ($) *",
                                    min_value=0.01,
                                    value=1000.00,
                                    step=100.00,
                                    format="%.2f")

            # Tasa de interés MENSUAL (real)
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

                # Interés total (EN DÓLARES) - CORREGIDO
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

                        # CORRECCIÓN: Guardar el INTERÉS TOTAL EN DÓLARES, no la tasa
                        cursor.execute("""
                            INSERT INTO Prestamo
                            (ID_Miembro, fecha_desembolso, monto, total_interes,
                             ID_Estado_prestamo, plazo, proposito, monto_total_pagar, cuota_mensual)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (ID_Miembro, fecha_desembolso, monto, interes_total,  # ← Aquí va el interés total en $
                              ID_Estado_prestamo, plazo, proposito_val, monto_total, cuota_mensual))

                        con.commit()

                        st.success("✅ Préstamo registrado correctamente!")
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
