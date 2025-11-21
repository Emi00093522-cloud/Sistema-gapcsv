import streamlit as st
from modulos.config.conexion import obtener_conexion
from datetime import datetime

def mostrar_prestamo(id_reunion=None, id_grupo=None, reunion_info=None, grupo_info=None):
    """
    Versión modificada que puede recibir parámetros del contexto de reuniones
    """
    
    # Si viene del contexto de reuniones, mostramos información heredada
    if id_reunion and id_grupo:
        st.header(f"💰 Préstamos - Reunión {reunion_info}")
        st.success(f"📅 Reunión actual: {reunion_info}")
        st.info(f"👥 Grupo: {grupo_info}")
    else:
        st.header("💰 Registrar Préstamo")
        # Modo standalone (como antes)

    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)

        # CARGAR DATOS DEPENDIENDO DEL CONTEXTO
        if id_reunion and id_grupo:
            # ✅ MODO CONTEXTO REUNIÓN: Solo miembros del grupo de esta reunión
            cursor.execute("""
                SELECT ID_Miembro, nombre, apellido 
                FROM Miembro 
                WHERE ID_Grupo = %s AND ID_Estado = 1
                ORDER BY nombre, apellido
            """, (id_grupo,))
            miembros = cursor.fetchall()
            
            if not miembros:
                st.warning("⚠️ No hay miembros activos en este grupo.")
                return
                
        else:
            # 🔄 MODO STANDALONE: Todos los miembros (comportamiento original)
            cursor.execute("SELECT ID_Miembro, nombre FROM Miembro WHERE ID_Estado = 1")
            miembros = cursor.fetchall()

        cursor.execute("SELECT ID_Estado_prestamo, estado_prestamo FROM Estado_prestamo")
        estados_prestamo = cursor.fetchall()

        with st.form("form_prestamo"):
            st.subheader("Datos del Préstamo")

            # MIEMBRO - Diferente según el contexto
            if miembros:
                if id_reunion and id_grupo:
                    # En contexto reunión: mostrar nombre completo
                    miembro_options = {f"{m['nombre']} {m.get('apellido', '')}".strip(): m['ID_Miembro'] for m in miembros}
                else:
                    # Modo standalone: formato original
                    miembro_options = {f"{m['nombre']} (ID: {m['ID_Miembro']})": m['ID_Miembro'] for m in miembros}
                
                miembro_seleccionado = st.selectbox("Miembro *", list(miembro_options.keys()))
                ID_Miembro = miembro_options[miembro_seleccionado]
            else:
                st.error("❌ No hay miembros disponibles")
                ID_Miembro = None

            # FECHA
            fecha_desembolso = st.date_input("Fecha de desembolso *", value=datetime.now().date())

            # MONTO
            monto = st.number_input("Monto del préstamo ($) *",
                                    min_value=0.01,
                                    value=1000.00,
                                    step=100.00,
                                    format="%.2f")

            # TASA DE INTERÉS MENSUAL
            tasa_mensual = st.number_input("Tasa de interés MENSUAL (%) *",
                                           min_value=0.00,
                                           max_value=100.00,
                                           value=5.00,
                                           step=0.10,
                                           format="%.2f")

            # ESTADO PRÉSTAMO
            if estados_prestamo:
                estado_options = {e["estado_prestamo"]: e["ID_Estado_prestamo"] for e in estados_prestamo}
                estado_seleccionado = st.selectbox("Estado del préstamo *", list(estado_options.keys()))
                ID_Estado_prestamo = estado_options[estado_seleccionado]
            else:
                st.error("❌ No hay estados de préstamo disponibles")
                ID_Estado_prestamo = None

            # PLAZO
            plazo = st.number_input("Plazo (meses) *", min_value=1, max_value=120, value=6, step=1)

            # PROPÓSITO
            proposito = st.text_area("Propósito del préstamo (opcional)",
                                     placeholder="Ej: Compra de materiales, gastos médicos…",
                                     max_chars=200,
                                     height=80)

            # ================================
            # 🔵 CÁLCULOS DE INTERÉS MENSUAL SIMPLE
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

                        # ✅ GUARDAR TAMBIÉN LA REUNIÓN SI VIENE DEL CONTEXTO
                        if id_reunion:
                            cursor.execute("""
                                INSERT INTO Prestamo
                                (ID_Miembro, ID_Reunion, fecha_desembolso, monto, total_interes,
                                 ID_Estado_prestamo, plazo, proposito)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """, (ID_Miembro, id_reunion, fecha_desembolso, monto, tasa_mensual,
                                  ID_Estado_prestamo, plazo, proposito_val))
                        else:
                            cursor.execute("""
                                INSERT INTO Prestamo
                                (ID_Miembro, fecha_desembolso, monto, total_interes,
                                 ID_Estado_prestamo, plazo, proposito)
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """, (ID_Miembro, fecha_desembolso, monto, tasa_mensual,
                                  ID_Estado_prestamo, plazo, proposito_val))

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
