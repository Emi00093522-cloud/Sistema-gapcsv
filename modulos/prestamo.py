import streamlit as st
from modulos.config.conexion import obtener_conexion
from datetime import datetime

def mostrar_prestamo():
    st.header("💰 Registrar Préstamo")

    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)

        # Cargar datos
        cursor.execute("SELECT ID_Miembro, nombre FROM Miembro WHERE ID_Estado = 1")
        miembros = cursor.fetchall()

        cursor.execute("SELECT ID_Estado_prestamo, estado_prestamo FROM Estado_prestamo")
        estados_prestamo = cursor.fetchall()

        # Formulario
        with st.form("form_prestamo"):
            st.subheader("Datos del Préstamo")

            # Miembro
            if miembros:
                miembro_options = {f"{m['nombre']} (ID: {m['ID_Miembro']})": m['ID_Miembro'] for m in miembros}
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

            # Interés %
            total_interes = st.number_input("Tasa de interés ANUAL (%) *",
                                            min_value=0.00,
                                            max_value=100.00,
                                            value=10.00,
                                            step=0.5,
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
            plazo = st.number_input("Plazo (meses) *", min_value=1, max_value=120, value=12, step=1)

            # Propósito
            proposito = st.text_area("Propósito del préstamo (opcional)",
                                     placeholder="Ej: Compra de materiales, gastos médicos…",
                                     max_chars=200,
                                     height=80)

            # ================================
            # 🔵 CÁLCULOS CORRECTOS (SISTEMA FRANCÉS)
            # ================================
            if monto > 0 and plazo > 0:

                # Convertir tasa anual a tasa mensual en decimal
                tasa_mensual = (total_interes / 100) / 12  

                if tasa_mensual > 0:
                    # Fórmula real de cuota fija
                    cuota_mensual = (monto * tasa_mensual) / (1 - (1 + tasa_mensual) ** (-plazo))
                else:
                    cuota_mensual = monto / plazo  # Caso especial sin interés

                interes_total = (cuota_mensual * plazo) - monto
                monto_total = monto + interes_total

                # Mostrar resultado
                st.info("📊 **Resumen del préstamo:**")
                st.write(f"- Tasa mensual: **{tasa_mensual * 100:.4f}%**")
                st.write(f"- Interés total a pagar: **${interes_total:,.2f}**")
                st.write(f"- Monto total a pagar: **${monto_total:,.2f}**")
                st.write(f"- 💵 **Cuota mensual real: ${cuota_mensual:,.2f}**")

            enviar = st.form_submit_button("✅ Registrar Préstamo")

            if enviar:

                errores = []

                if ID_Miembro is None:
                    errores.append("⚠ Debes seleccionar un miembro.")

                if monto <= 0:
                    errores.append("⚠ El monto debe ser mayor a 0.")

                if total_interes < 0:
                    errores.append("⚠ La tasa de interés no puede ser negativa.")

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

                        cursor.execute("""
                            INSERT INTO Prestamo
                            (ID_Miembro, fecha_desembolso, monto, total_interes,
                             ID_Estado_prestamo, plazo, proposito)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (ID_Miembro, fecha_desembolso, monto, total_interes,
                              ID_Estado_prestamo, plazo, proposito_val))

                        con.commit()

                        st.success("✅ Préstamo registrado correctamente!")
                        st.success(f"- Monto: ${monto:,.2f}")
                        st.success(f"- Tasa anual: {total_interes}%")
                        st.success(f"- Plazo: {plazo} meses")
                        st.success(f"- Interés total: ${interes_total:,.2f}")
                        st.success(f"- Monto total: ${monto_total:,.2f}")
                        st.success(f"- 💵 **Cuota mensual: ${cuota_mensual:,.2f}**")

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
