import streamlit as st
from modulos.config.conexion import obtener_conexion
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

# ---------------------------
# UTILIDADES
# ---------------------------
def fmt_money(x):
    """Formatear número a moneda con 2 decimales (x puede ser Decimal, float o None)"""
    try:
        val = Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        # formateo con separador de miles
        return f"${val:,.2f}"
    except:
        return "$0.00"

# ---------------------------
# OBTENER REUNIÓN MÁS CERCANA AL FIN DE MES
# ---------------------------
def obtener_reunion_mas_cercana_fin_mes(con, id_grupo, fecha_referencia, mes_offset=0):
    """Encuentra la reunión más cercana al fin de mes basado en la frecuencia de reuniones.
       Retorna un objeto date (o datetime si la fecha en DB es datetime)."""
    cursor = con.cursor()
    # Obtener frecuencia de reuniones del grupo (solo lectura)
    cursor.execute("""
        SELECT frecuencia_reunion 
        FROM Reglamento 
        WHERE ID_Grupo = %s 
        ORDER BY ID_Reglamento DESC 
        LIMIT 1
    """, (id_grupo,))
    resultado = cursor.fetchone()
    frecuencia = resultado[0] if resultado else "Mensual"

    # Calcular fecha objetivo (último día del mes objetivo si mes_offset != 0)
    if mes_offset == 0:
        fecha_objetivo = fecha_referencia
    else:
        year = fecha_referencia.year
        month = fecha_referencia.month + mes_offset
        while month > 12:
            month -= 12
            year += 1
        # último día del mes objetivo
        if month == 12:
            next_month = date(year + 1, 1, 1)
        else:
            next_month = date(year, month + 1, 1)
        fecha_objetivo = next_month - timedelta(days=1)

    # Buscar reunión más cercana a fecha_objetivo (si hay alguna en ese mes)
    cursor.execute("""
        SELECT ID_Reunion, fecha, lugar 
        FROM Reunion 
        WHERE ID_Grupo = %s 
        AND YEAR(fecha) = %s AND MONTH(fecha) = %s
        ORDER BY ABS(DATEDIFF(fecha, %s)) ASC
        LIMIT 1
    """, (id_grupo, fecha_objetivo.year, fecha_objetivo.month, fecha_objetivo))
    reunion = cursor.fetchone()
    cursor.close()

    if reunion:
        return reunion[1]
    return fecha_objetivo

# ---------------------------
# GENERAR CRONOGRAMA (USANDO EXACTAMENTE DATOS REGISTRADOS)
# ---------------------------
def generar_cronograma_pagos(id_prestamo, con, id_grupo):
    """Genera el cronograma de pagos usando EXACTAMENTE los datos registrados del préstamo"""
    cursor = con.cursor()

    cursor.execute("""
        SELECT 
            p.monto,
            p.total_interes,
            p.plazo,
            p.fecha_desembolso,
            p.cuota_mensual,
            p.monto_total_pagar
        FROM Prestamo p
        WHERE p.ID_Prestamo = %s
    """, (id_prestamo,))
    prestamo = cursor.fetchone()
    if not prestamo:
        st.error("❌ No se encontró el préstamo")
        cursor.close()
        return False

    # Desempaquetar estrictamente los valores guardados
    monto, total_interes, plazo, fecha_desembolso, cuota_mensual, monto_total_pagar = prestamo

    # Si alguno de los campos críticos es None, detener (evita recalculos)
    if monto is None or total_interes is None or plazo is None or fecha_desembolso is None:
        st.error("❌ Falta información registrada en el préstamo. Verifica monto, interés, plazo o fecha de desembolso.")
        cursor.close()
        return False

    # Eliminar cronograma existente (recreación total)
    cursor.execute("DELETE FROM CuotaPrestamo WHERE ID_Prestamo = %s", (id_prestamo,))

    # Usar Decimal para evitar errores de redondeo
    saldo_capital = Decimal(str(monto))
    saldo_interes = Decimal(str(total_interes))
    plazo_int = int(plazo)

    # Distribución proporcional basada en los totales guardados:
    # NOTA: aquí NO recalculamos intereses ni cuotas; distribuimos en partes iguales salvo la última que recoge el sobrante
    for i in range(1, plazo_int + 1):
        if i == plazo_int:
            capital_cuota = saldo_capital
            interes_cuota = saldo_interes
        else:
            capital_cuota = (Decimal(str(monto)) / Decimal(str(plazo_int))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            interes_cuota = (Decimal(str(total_interes)) / Decimal(str(plazo_int))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        total_cuota = (capital_cuota + interes_cuota).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # Fecha de pago: usar reuniones (1 mes después = mes_offset = i)
        fecha_pago = obtener_reunion_mas_cercana_fin_mes(con, id_grupo, fecha_desembolso, i)

        cursor.execute("""
            INSERT INTO CuotaPrestamo 
            (ID_Prestamo, numero_cuota, fecha_programada, capital_programado, 
             interes_programado, total_programado, estado, capital_pagado, interes_pagado, total_pagado)
            VALUES (%s, %s, %s, %s, %s, %s, 'pendiente', 0, 0, 0)
        """, (id_prestamo, i, fecha_pago, float(capital_cuota), float(interes_cuota), float(total_cuota)))

        saldo_capital -= capital_cuota
        saldo_interes -= interes_cuota

    con.commit()
    cursor.close()
    st.success(f"✅ Cronograma generado: {plazo_int} pagos mensuales (según datos registrados).")
    return True

# ---------------------------
# APLICAR PAGO (completo/parcial)
# ---------------------------
def aplicar_pago_cuota(id_prestamo, monto_pagado, fecha_pago, tipo_pago, con, numero_cuota=None):
    """Aplica un pago (completo o parcial) a una cuota específica.
       Esta función respeta los campos ya existentes en CuotaPrestamo."""
    cursor = con.cursor()

    if tipo_pago == "completo" and numero_cuota:
        cursor.execute("""
            SELECT ID_Cuota, capital_programado, interes_programado, total_programado,
                   capital_pagado, interes_pagado, total_pagado, estado
            FROM CuotaPrestamo 
            WHERE ID_Prestamo = %s AND numero_cuota = %s
        """, (id_prestamo, numero_cuota))
    else:
        cursor.execute("""
            SELECT ID_Cuota, numero_cuota, capital_programado, interes_programado, total_programado,
                   capital_pagado, interes_pagado, total_pagado, estado, fecha_programada
            FROM CuotaPrestamo 
            WHERE ID_Prestamo = %s AND estado != 'pagado'
            ORDER BY fecha_programada ASC
            LIMIT 1
        """, (id_prestamo,))

    cuota = cursor.fetchone()
    if not cuota:
        cursor.close()
        return False, "No hay cuotas pendientes"

    # (resto de la lógica igual que la tuya, con Decimal)
    if tipo_pago == "completo":
        (id_cuota, capital_prog, interes_prog, total_prog, 
         capital_pag, interes_pag, total_pag, estado) = cuota
        numero_cuota = numero_cuota
        fecha_programada = None
    else:
        (id_cuota, numero_cuota, capital_prog, interes_prog, total_prog, 
         capital_pag, interes_pag, total_pag, estado, fecha_programada) = cuota

    capital_prog = Decimal(str(capital_prog))
    interes_prog = Decimal(str(interes_prog))
    total_prog = Decimal(str(total_prog))
    capital_pag = Decimal(str(capital_pag or 0))
    interes_pag = Decimal(str(interes_pag or 0))
    total_pag = Decimal(str(total_pag or 0))
    monto_pagado = Decimal(str(monto_pagado))

    if tipo_pago == "completo":
        nuevo_capital_pagado = capital_prog
        nuevo_interes_pagado = interes_prog
        nuevo_total_pagado = total_prog
        nuevo_estado = 'pagado'
        monto_sobrante = Decimal('0')
    else:
        interes_faltante = interes_prog - interes_pag
        capital_faltante = capital_prog - capital_pag

        nuevo_interes_pagado = interes_pag
        nuevo_capital_pagado = capital_pag

        if interes_faltante > 0:
            if monto_pagado >= interes_faltante:
                nuevo_interes_pagado = interes_prog
                monto_pagado -= interes_faltante
            else:
                nuevo_interes_pagado = interes_pag + monto_pagado
                monto_pagado = Decimal('0')

        if monto_pagado > 0 and capital_faltante > 0:
            if monto_pagado >= capital_faltante:
                nuevo_capital_pagado = capital_prog
                monto_pagado -= capital_faltante
            else:
                nuevo_capital_pagado = capital_pag + monto_pagado
                monto_pagado = Decimal('0')

        nuevo_total_pagado = nuevo_capital_pagado + nuevo_interes_pagado
        if nuevo_total_pagado >= total_prog:
            nuevo_estado = 'pagado'
        elif nuevo_total_pagado > 0:
            nuevo_estado = 'parcial'
        else:
            nuevo_estado = 'pendiente'

        monto_sobrante = monto_pagado

    cursor.execute("""
        UPDATE CuotaPrestamo 
        SET capital_pagado = %s, interes_pagado = %s, total_pagado = %s, estado = %s
        WHERE ID_Cuota = %s
    """, (float(nuevo_capital_pagado), float(nuevo_interes_pagado), float(nuevo_total_pagado), nuevo_estado, id_cuota))

    # Si quedó sobrante en parcial, crear nueva cuota con el saldo pendiente + sobrante
    if tipo_pago == "parcial" and monto_sobrante > 0:
        cursor.execute("SELECT p.ID_Grupo FROM Prestamo p WHERE p.ID_Prestamo = %s", (id_prestamo,))
        resultado = cursor.fetchone()
        id_grupo = resultado[0] if resultado else None

        cursor.execute("""
            SELECT 
                COALESCE(SUM(capital_programado - COALESCE(capital_pagado, 0)), 0) as capital_pendiente,
                COALESCE(SUM(interes_programado - COALESCE(interes_pagado, 0)), 0) as interes_pendiente
            FROM CuotaPrestamo 
            WHERE ID_Prestamo = %s AND estado != 'pagado'
        """, (id_prestamo,))
        saldos = cursor.fetchone()
        capital_pendiente, interes_pendiente = saldos

        if capital_pendiente > 0 or interes_pendiente > 0:
            cursor.execute("SELECT COALESCE(MAX(numero_cuota), 0) FROM CuotaPrestamo WHERE ID_Prestamo = %s", (id_prestamo,))
            ultimo_numero = cursor.fetchone()[0] or 0
            nuevo_numero = ultimo_numero + 1

            if id_grupo:
                nueva_fecha = obtener_reunion_mas_cercana_fin_mes(con, id_grupo, fecha_pago, 1)
            else:
                nueva_fecha = fecha_pago + timedelta(days=30)

            nuevo_capital = Decimal(str(capital_pendiente)) + monto_sobrante
            nuevo_total = nuevo_capital + Decimal(str(interes_pendiente))

            cursor.execute("""
                INSERT INTO CuotaPrestamo 
                (ID_Prestamo, numero_cuota, fecha_programada, capital_programado, 
                 interes_programado, total_programado, estado, capital_pagado, interes_pagado, total_pagado)
                VALUES (%s, %s, %s, %s, %s, %s, 'pendiente', 0, 0, 0)
            """, (id_prestamo, nuevo_numero, nueva_fecha, float(nuevo_capital), float(interes_pendiente), float(nuevo_total)))

    con.commit()
    cursor.close()
    return True, f"Pago {tipo_pago} aplicado correctamente"

# ---------------------------
# MOSTRAR PAGO PRESTAMO (INTERFAZ) - SOLO LLAMAR DATOS REGISTRADOS
# ---------------------------
def mostrar_pago_prestamo():
    st.header("💵 Sistema de Pagos de Préstamo")

    if 'reunion_actual' not in st.session_state:
        st.warning("⚠️ Primero debes seleccionar una reunión en el módulo de Asistencia.")
        return

    try:
        con = obtener_conexion()
        cursor = con.cursor()

        reunion_info = st.session_state.reunion_actual
        id_reunion = reunion_info['id_reunion']
        id_grupo = reunion_info['id_grupo']
        nombre_reunion = reunion_info.get('nombre_reunion', 'Reunión')

        st.info(f"📅 **Reunión actual:** {nombre_reunion}")

        # Obtener frecuencia (solo lectura)
        cursor.execute("""
            SELECT frecuencia_reunion 
            FROM Reglamento 
            WHERE ID_Grupo = %s 
            ORDER BY ID_Reglamento DESC 
            LIMIT 1
        """, (id_grupo,))
        frecuencia_result = cursor.fetchone()
        frecuencia = frecuencia_result[0] if frecuencia_result else "Mensual"
        st.info(f"🔄 **Frecuencia de reuniones del grupo:** {frecuencia}")

        # Cargar miembros que asistieron
        cursor.execute("""
            SELECT m.ID_Miembro, m.nombre 
            FROM Miembro m
            JOIN Miembroxreunion mr ON m.ID_Miembro = mr.ID_Miembro
            WHERE mr.ID_Reunion = %s AND mr.asistio = 1
            ORDER BY m.nombre
        """, (id_reunion,))
        miembros_presentes = cursor.fetchall()
        if not miembros_presentes:
            st.warning("⚠️ No hay miembros registrados como presentes en esta reunión.")
            return

        ids_miembros_presentes = [m[0] for m in miembros_presentes]

        # Obtener préstamos activos SOLO de miembros presentes (solo traer campos guardados)
        if ids_miembros_presentes:
            placeholders = ','.join(['%s'] * len(ids_miembros_presentes))
            cursor.execute(f"""
                SELECT 
                    p.ID_Prestamo, 
                    p.ID_Miembro, 
                    p.monto,
                    p.total_interes,
                    p.plazo,
                    p.fecha_desembolso,
                    m.nombre, 
                    p.proposito,
                    p.cuota_mensual,
                    p.monto_total_pagar,
                    p.tasa_interes
                FROM Prestamo p
                JOIN Miembro m ON p.ID_Miembro = m.ID_Miembro
                WHERE p.ID_Estado_prestamo != 3
                AND p.ID_Miembro IN ({placeholders})
            """, ids_miembros_presentes)
        else:
            st.info("🎉 No hay miembros presentes.")
            return

        prestamos = cursor.fetchall()
        if not prestamos:
            st.warning("⚠️ No hay préstamos activos para los miembros presentes en esta reunión.")
            return

        prestamos_dict = {
            f"Préstamo {p[0]} - {p[6]} - {fmt_money(p[2])} - {p[4]} meses": p[0]
            for p in prestamos
        }

        prestamo_sel = st.selectbox("Selecciona el préstamo:", list(prestamos_dict.keys()))
        id_prestamo = prestamos_dict[prestamo_sel]
        prestamo_info = [p for p in prestamos if p[0] == id_prestamo][0]

        # ---------- SOLO USAR DATOS REGISTRADOS (no hacer cálculos aquí) ----------
        monto = prestamo_info[2]
        total_interes = prestamo_info[3]
        plazo = prestamo_info[4]
        fecha_desembolso = prestamo_info[5]
        proposito = prestamo_info[7]
        cuota_mensual = prestamo_info[8]
        monto_total_pagar = prestamo_info[9]
        tasa_interes = prestamo_info[10]

        # Mostrar (exactamente los valores guardados)
        st.subheader("📋 RESUMEN DEL PRÉSTAMO")
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Información Básica**")
            st.write(f"• **Fecha desembolso:** {fecha_desembolso}")
            st.write(f"• **Tasa interés (registrada):** {tasa_interes}%")
            st.write(f"• **Plazo (meses):** {plazo}")
            st.write(f"• **Propósito:** {proposito}")
            st.write(f"• **Frecuencia reuniones:** {frecuencia}")

        with col2:
            st.markdown("**Montos (Datos Registrados)**")
            st.write(f"• **Monto préstamo:** {fmt_money(monto)}")
            st.write(f"• **Interés total a pagar (registrado):** {fmt_money(total_interes)}")
            st.write(f"• **Total a pagar (registrado):** {fmt_money(monto_total_pagar)}")
            st.write(f"• **Cuota mensual (registrada):** {fmt_money(cuota_mensual)}")

        st.markdown("---")

        # ¿Tiene cronograma?
        cursor.execute("SELECT COUNT(*) FROM CuotaPrestamo WHERE ID_Prestamo = %s", (id_prestamo,))
        tiene_cronograma = cursor.fetchone()[0] > 0

        if not tiene_cronograma:
            st.info("📅 Este préstamo no tiene cronograma de pagos generado.")
            if st.button("🔄 Generar Plan de Pagos", type="primary"):
                if generar_cronograma_pagos(id_prestamo, con, id_grupo):
                    st.success("✅ Plan de pagos generado correctamente!")
                    st.rerun()
                else:
                    st.error("❌ Error al generar plan de pagos")
            return

        # Mostrar cuotas
        cursor.execute("""
            SELECT numero_cuota, fecha_programada, capital_programado, 
                   interes_programado, total_programado, capital_pagado, 
                   interes_pagado, total_pagado, estado
            FROM CuotaPrestamo
            WHERE ID_Prestamo = %s
            ORDER BY fecha_programada ASC
        """, (id_prestamo,))
        cuotas = cursor.fetchall()

        st.subheader("📅 PLAN DE PAGOS")
        st.markdown("---")
        tabla_data = []
        for cuota in cuotas:
            numero, fecha_prog, capital_prog, interes_prog, total_prog, \
            capital_pag, interes_pag, total_pag, estado = cuota

            capital_pag = capital_pag or 0
            interes_pag = interes_pag or 0
            total_pag = total_pag or 0

            estado_emoji = {'pendiente': '⚪', 'parcial': '🟡', 'pagado': '🟢'}
            if estado == 'pagado':
                capital_mostrar = fmt_money(capital_pag)
                interes_mostrar = fmt_money(interes_pag)
                total_mostrar = fmt_money(total_pag)
            elif estado == 'parcial':
                capital_mostrar = f"{fmt_money(capital_pag)} de {fmt_money(capital_prog)}"
                interes_mostrar = f"{fmt_money(interes_pag)} de {fmt_money(interes_prog)}"
                total_mostrar = f"{fmt_money(total_pag)} de {fmt_money(total_prog)}"
            else:
                capital_mostrar = fmt_money(capital_prog)
                interes_mostrar = fmt_money(interes_prog)
                total_mostrar = fmt_money(total_prog)

            tabla_data.append({
                "Cuota": numero,
                "Fecha": fecha_prog,
                "Estado": f"{estado_emoji.get(estado, '⚪')} {estado.upper()}",
                "Capital": capital_mostrar,
                "Interés": interes_mostrar,
                "Total": total_mostrar
            })

        st.dataframe(tabla_data, use_container_width=True)

        # Totales (mostrar usando campos registrados)
        total_pagado = sum(c[7] or 0 for c in cuotas)  # c[7] es total_pagado
        saldo_pendiente = Decimal(str(monto_total_pagar)) - Decimal(str(total_pagado))

        st.markdown("---")
        st.markdown(f"**TOTAL (registro):** {fmt_money(monto)} (capital) + {fmt_money(total_interes)} (interés) = **{fmt_money(monto_total_pagar)}**")

        if saldo_pendiente <= 0:
            st.success("**SALDO: $0 (COMPLETAMENTE PAGADO)** 🎉")
        else:
            st.warning(f"**SALDO PENDIENTE: {fmt_money(saldo_pendiente)}**")

        # ---------- Formularios de pago (igual a tu lógica) ----------
        st.subheader("💰 REGISTRAR PAGO")
        st.markdown("---")
        col1, col2 = st.columns(2)

        # Pago completo
        with col1:
            st.markdown("### 💵 Pago Completo")
            with st.form("form_pago_completo"):
                cursor.execute("""
                    SELECT numero_cuota, total_programado, total_pagado, fecha_programada
                    FROM CuotaPrestamo 
                    WHERE ID_Prestamo = %s AND estado != 'pagado'
                    ORDER BY numero_cuota
                """, (id_prestamo,))
                cuotas_pendientes = cursor.fetchall()

                if cuotas_pendientes:
                    cuotas_opciones = [f"Cuota {c[0]} - {fmt_money(c[1])} - {c[3]}" for c in cuotas_pendientes]
                    cuota_seleccionada = st.selectbox("Selecciona la cuota a pagar:", cuotas_opciones, key="completo")
                    numero_cuota = int(cuota_seleccionada.split(" ")[1])
                    fecha_pago_completo = st.date_input("Fecha del pago:", value=date.today(), key="fecha_completo")
                    enviar_completo = st.form_submit_button("✅ Pagar Cuota Completa")

                    if enviar_completo:
                        try:
                            cuota_info = [c for c in cuotas_pendientes if c[0] == numero_cuota][0]
                            monto_cuota = cuota_info[1]
                            success, mensaje = aplicar_pago_cuota(id_prestamo, monto_cuota, fecha_pago_completo, "completo", con, numero_cuota)
                            if success:
                                cursor.execute("""
                                    INSERT INTO Pago_prestamo 
                                    (ID_Prestamo, ID_Reunion, fecha_pago, monto_capital, monto_interes, total_cancelado)
                                    VALUES (%s, %s, %s, %s, %s, %s)
                                """, (id_prestamo, id_reunion, fecha_pago_completo, 0, 0, float(monto_cuota)))
                                con.commit()
                                st.success(f"✅ {mensaje}")
                                st.balloons()
                                st.rerun()
                            else:
                                st.error(f"❌ {mensaje}")
                        except Exception as e:
                            con.rollback()
                            st.error(f"❌ Error al procesar el pago completo: {e}")
                else:
                    st.info("🎉 No hay cuotas pendientes para pago completo")

        # Pago parcial
        with col2:
            st.markdown("### 💳 Pago Parcial")
            with st.form("form_pago_parcial"):
                cursor.execute("""
                    SELECT numero_cuota, total_programado, total_pagado, fecha_programada
                    FROM CuotaPrestamo 
                    WHERE ID_Prestamo = %s AND estado != 'pagado'
                    ORDER BY fecha_programada ASC
                    LIMIT 1
                """, (id_prestamo,))
                cuota_actual = cursor.fetchone()

                if cuota_actual:
                    numero_cuota, total_programado, total_pagado, fecha_programada = cuota_actual
                    pendiente_actual = Decimal(str(total_programado)) - Decimal(str(total_pagado or 0))

                    st.write(f"**Próxima cuota:** #{numero_cuota}")
                    st.write(f"**Total pendiente:** {fmt_money(pendiente_actual)}")
                    st.write(f"**Fecha programada:** {fecha_programada}")

                    fecha_pago_parcial = st.date_input("Fecha del pago:", value=date.today(), key="fecha_parcial")
                    monto_parcial = st.number_input(
                        "Monto a pagar:",
                        min_value=0.01,
                        max_value=float(pendiente_actual),
                        value=float(min(pendiente_actual, 100)),
                        step=10.0,
                        format="%.2f"
                    )
                    enviar_parcial = st.form_submit_button("💰 Registrar Pago Parcial")

                    if enviar_parcial:
                        if monto_parcial <= 0:
                            st.warning("⚠️ El monto debe ser mayor a cero.")
                        else:
                            try:
                                success, mensaje = aplicar_pago_cuota(id_prestamo, monto_parcial, fecha_pago_parcial, "parcial", con)
                                if success:
                                    cursor.execute("""
                                        INSERT INTO Pago_prestamo 
                                        (ID_Prestamo, ID_Reunion, fecha_pago, monto_capital, monto_interes, total_cancelado)
                                        VALUES (%s, %s, %s, %s, %s, %s)
                                    """, (id_prestamo, id_reunion, fecha_pago_parcial, 0, 0, float(monto_parcial)))
                                    con.commit()
                                    st.success(f"✅ {mensaje}")
                                    st.rerun()
                                else:
                                    st.error(f"❌ {mensaje}")
                            except Exception as e:
                                con.rollback()
                                st.error(f"❌ Error al procesar el pago parcial: {e}")
                else:
                    st.info("🎉 No hay cuotas pendientes para pago parcial")

    except Exception as e:
        st.error(f"❌ Error general: {e}")
    finally:
        try:
            cursor.close()
        except:
            pass
        try:
            con.close()
        except:
            pass
