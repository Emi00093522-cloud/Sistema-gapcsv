import streamlit as st
from modulos.config.conexion import obtener_conexion
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

def obtener_reunion_mas_cercana_fin_mes(con, id_grupo, fecha_referencia, mes_offset=0):
    cursor = con.cursor()
    cursor.execute("""
        SELECT frecuencia_reunion
        FROM Reglamento
        WHERE ID_Grupo = %s
        ORDER BY ID_Reglamento DESC
        LIMIT 1
    """, (id_grupo,))
    row = cursor.fetchone()
    frecuencia = row[0] if row else "Mensual"

    if mes_offset == 0:
        fecha_objetivo = fecha_referencia
    else:
        year = fecha_referencia.year
        month = fecha_referencia.month + mes_offset
        while month > 12:
            month -= 12
            year += 1
        if month == 12:
            next_month = date(year + 1, 1, 1)
        else:
            next_month = date(year, month + 1, 1)
        fecha_objetivo = next_month - timedelta(days=1)

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


def generar_cronograma_pagos(id_prestamo, con):
    """
    Genera cronograma USANDO EXCLUSIVAMENTE los campos guardados en Prestamo:
    - monto
    - total_interes (EN MONEDA $ O NULL)
    - monto_total_pagar (EN $)
    - cuota_mensual (EN $) opcional
    - plazo
    - fecha_desembolso
    """
    cursor = con.cursor(dictionary=True)
    cursor.execute("""
        SELECT ID_Prestamo, ID_Miembro, monto, total_interes, monto_total_pagar,
               cuota_mensual, plazo, fecha_desembolso
        FROM Prestamo
        WHERE ID_Prestamo = %s
    """, (id_prestamo,))
    p = cursor.fetchone()
    if not p:
        cursor.close()
        return False

    monto = p.get('monto')
    total_interes = p.get('total_interes') or 0
    monto_total_pagar = p.get('monto_total_pagar')
    cuota_mensual_reg = p.get('cuota_mensual')   # puede ser None
    plazo = p.get('plazo')
    fecha_desembolso = p.get('fecha_desembolso')

    if monto is None or monto_total_pagar is None or plazo is None or fecha_desembolso is None:
        st.error("❌ Faltan campos obligatorios en Prestamo: monto / monto_total_pagar / plazo / fecha_desembolso.")
        cursor.close()
        return False

    # Borrar cronograma anterior
    cursor.execute("DELETE FROM CuotaPrestamo WHERE ID_Prestamo = %s", (id_prestamo,))

    # Preparar Decimals
    monto_d = Decimal(str(monto)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    monto_total_d = Decimal(str(monto_total_pagar)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    total_interes_d = Decimal(str(total_interes)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    plazo_i = int(plazo)

    # Determinar total por cuota (si existe cuota_mensual registrada, la usamos)
    if cuota_mensual_reg is not None:
        cuota_d = Decimal(str(cuota_mensual_reg)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    else:
        cuota_d = (monto_total_d / plazo_i).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Determinar interés por cuota (si total_interes fue guardado en $)
    interes_por_cuota = (total_interes_d / plazo_i).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if total_interes_d > 0 else Decimal("0.00")

    saldo_capital = monto_d
    saldo_interes = total_interes_d
    fecha_primer_pago = fecha_desembolso + timedelta(days=30)

    for i in range(1, plazo_i + 1):
        if i == plazo_i:
            # última cuota toma saldos restantes
            interes_cuota = saldo_interes
            if cuota_mensual_reg is not None:
                total_cuota = cuota_d
                capital_cuota = (total_cuota - interes_cuota).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            else:
                total_cuota = (saldo_capital + saldo_interes).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                capital_cuota = saldo_capital
        else:
            interes_cuota = interes_por_cuota
            total_cuota = cuota_d
            capital_cuota = (total_cuota - interes_cuota).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        fecha_pago = fecha_primer_pago + timedelta(days=30*(i-1))

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
    return True


def aplicar_pago_cuota(id_prestamo, monto_pagado, fecha_pago, tipo_pago, con, numero_cuota=None):
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
        return False, "No hay cuotas pendientes"

    if tipo_pago == "completo":
        (id_cuota, capital_prog, interes_prog, total_prog,
         capital_pag, interes_pag, total_pag, estado) = cuota
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

    if tipo_pago == "parcial" and monto_sobrante > 0:
        cursor.execute("""
            SELECT COALESCE(SUM(capital_programado - COALESCE(capital_pagado,0)),0) as capital_pendiente,
                   COALESCE(SUM(interes_programado - COALESCE(interes_pagado,0)),0) as interes_pendiente
            FROM CuotaPrestamo WHERE ID_Prestamo = %s
        """, (id_prestamo,))
        saldos = cursor.fetchone()
        capital_pendiente, interes_pendiente = saldos
        if capital_pendiente > 0 or interes_pendiente > 0:
            nueva_fecha = fecha_pago + timedelta(days=30)
            cursor.execute("SELECT COALESCE(MAX(numero_cuota),0) FROM CuotaPrestamo WHERE ID_Prestamo = %s", (id_prestamo,))
            ultimo = cursor.fetchone()[0] or 0
            nuevo_num = ultimo + 1
            cursor.execute("""
                INSERT INTO CuotaPrestamo
                (ID_Prestamo, numero_cuota, fecha_programada, capital_programado,
                 interes_programado, total_programado, estado, capital_pagado, interes_pagado, total_pagado)
                VALUES (%s, %s, %s, %s, %s, %s, 'pendiente', %s, %s, %s)
            """, (id_prestamo, nuevo_num, nueva_fecha, float(capital_pendiente), float(interes_pendiente),
                  float(capital_pendiente + interes_pendiente), float(monto_sobrante), 0, float(monto_sobrante)))

    con.commit()
    cursor.close()
    return True, f"Pago {tipo_pago} aplicado correctamente"


def mostrar_pago_prestamo():
    st.header("💵 Sistema de Pagos de Préstamo")
    if 'reunion_actual' not in st.session_state:
        st.warning("⚠️ Primero debes seleccionar una reunión en el módulo de Asistencia.")
        return

    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        reunion_info = st.session_state.reunion_actual
        id_reunion = reunion_info['id_reunion']
        id_grupo = reunion_info.get('id_grupo')
        nombre_reunion = reunion_info.get('nombre_reunion', 'Reunión')
        st.info(f"📅 **Reunión actual:** {nombre_reunion}")

        cursor.execute("""
            SELECT m.ID_Miembro, m.nombre
            FROM Miembro m
            JOIN Miembroxreunion mr ON m.ID_Miembro = mr.ID_Miembro
            WHERE mr.ID_Reunion = %s AND mr.asistio = 1
            ORDER BY m.nombre
        """, (id_reunion,))
        miembros = cursor.fetchall()
        if not miembros:
            st.warning("⚠️ No hay miembros registrados como presentes en esta reunión.")
            cursor.close()
            return

        ids = [m['ID_Miembro'] for m in miembros]
        placeholders = ','.join(['%s'] * len(ids))
        cursor.execute(f"""
            SELECT p.ID_Prestamo, p.ID_Miembro, p.monto, p.total_interes, p.monto_total_pagar,
                   p.cuota_mensual, p.plazo, p.fecha_desembolso, m.nombre as miembro_nombre, p.proposito, p.tasa_interes
            FROM Prestamo p
            JOIN Miembro m ON p.ID_Miembro = m.ID_Miembro
            WHERE p.ID_Estado_prestamo != 3
              AND p.ID_Miembro IN ({placeholders})
        """, ids)
        prestamos = cursor.fetchall()
        if not prestamos:
            st.warning("⚠️ No hay préstamos activos para los miembros presentes en esta reunión.")
            cursor.close()
            return

        prestamos_dict = {
            f"Préstamo {p['ID_Prestamo']} - {p['miembro_nombre']} - ${p['monto']:,.2f} - {p['plazo']} meses": p['ID_Prestamo']
            for p in prestamos
        }
        sel = st.selectbox("Selecciona el préstamo:", list(prestamos_dict.keys()))
        id_prestamo = prestamos_dict[sel]
        prestamo = next(p for p in prestamos if p['ID_Prestamo'] == id_prestamo)

        # === MOSTRAR SOLO LOS CAMPOS REGISTRADOS (SIN NINGÚN CÁLCULO) ===
        monto = prestamo.get('monto')
        total_interes = prestamo.get('total_interes')         # INTERÉS TOTAL GUARDADO (EN $ o 0)
        monto_total_pagar = prestamo.get('monto_total_pagar')
        cuota_mensual = prestamo.get('cuota_mensual')         # puede ser None (si no se guardó)
        plazo = prestamo.get('plazo')
        fecha_desembolso = prestamo.get('fecha_desembolso')
        proposito = prestamo.get('proposito')
        tasa_interes = prestamo.get('tasa_interes')

        st.subheader("📋 RESUMEN DEL PRÉSTAMO")
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Información Básica**")
            st.write(f"• **Fecha inicio:** {fecha_desembolso}")
            st.write(f"• **Tasa interés (registrada):** {tasa_interes if tasa_interes is not None else 'N/A'}")
            st.write(f"• **Plazo:** {plazo} meses")
            st.write(f"• **Propósito:** {proposito}")
        with c2:
            st.markdown("**Montos (registrados en Prestamo)**")
            st.write(f"• **Monto préstamo:** ${monto:,.2f}")
            st.write(f"• **Interés total (registrado):** ${total_interes:,.2f}")
            st.write(f"• **Total a pagar (registrado):** ${monto_total_pagar:,.2f}")
            if cuota_mensual is not None:
                st.write(f"• **Cuota mensual (registrada):** ${cuota_mensual:,.2f}")
            else:
                st.write("• **Cuota mensual (registrada):** (no existe columna o no fue guardada)")

        st.markdown("---")

        # Si no hay cronograma, ofrecer generarlo (usando los valores guardados)
        cursor.execute("SELECT COUNT(*) as c FROM CuotaPrestamo WHERE ID_Prestamo = %s", (id_prestamo,))
        tiene = cursor.fetchone().get('c', 0) > 0
        if not tiene:
            st.info("📅 Este préstamo no tiene cronograma de pagos generado.")
            if st.button("🔄 Generar Plan de Pagos", type="primary"):
                if generar_cronograma_pagos(id_prestamo, con):
                    st.success("✅ Plan de pagos generado correctamente!")
                    st.rerun()
                else:
                    st.error("❌ Error al generar plan de pagos")
            cursor.close()
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
        tabla = []
        for c in cuotas:
            numero = c['numero_cuota']
            fecha_p = c['fecha_programada']
            cap_prog = c['capital_programado']
            int_prog = c['interes_programado']
            tot_prog = c['total_programado']
            cap_pag = c['capital_pagado'] or 0
            int_pag = c['interes_pagado'] or 0
            tot_pag = c['total_pagado'] or 0
            estado = c['estado']

            if estado == 'pagado':
                cap_m = f"${cap_pag:,.2f}"
                int_m = f"${int_pag:,.2f}"
                tot_m = f"${tot_pag:,.2f}"
            elif estado == 'parcial':
                cap_m = f"${cap_pag:,.2f} de ${cap_prog:,.2f}"
                int_m = f"${int_pag:,.2f} de ${int_prog:,.2f}"
                tot_m = f"${tot_pag:,.2f} de ${tot_prog:,.2f}"
            else:
                cap_m = f"${cap_prog:,.2f}"
                int_m = f"${int_prog:,.2f}"
                tot_m = f"${tot_prog:,.2f}"

            tabla.append({
                "Cuota": numero,
                "Fecha": fecha_p,
                "Estado": estado.upper(),
                "Capital": cap_m,
                "Interés": int_m,
                "Total": tot_m
            })

        st.dataframe(tabla, use_container_width=True)

        # Totales
        total_pagado = sum(c['total_pagado'] or 0 for c in cuotas)
        saldo = Decimal(str(monto_total_pagar)) - Decimal(str(total_pagado or 0))
        st.markdown("---")
        st.markdown(f"**TOTAL (registro):** ${monto:,.2f} (capital) + ${total_interes:,.2f} (interés) = **${monto_total_pagar:,.2f}**")
        if saldo <= 0:
            st.success("**SALDO: $0 (COMPLETAMENTE PAGADO)** 🎉")
        else:
            st.warning(f"**SALDO PENDIENTE: ${saldo:,.2f}**")

        cursor.close()

    except Exception as e:
        st.error(f"❌ Error general: {e}")
    finally:
        try: cursor.close()
        except: pass
        try: con.close()
        except: pass
