import streamlit as st
from modulos.config.conexion import obtener_conexion
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

def obtener_prestamos_grupo():
    """
    Función para el módulo de cierre de ciclo
    Retorna todos los pagos de préstamos del grupo actual para consolidar en el cierre
    """
    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        # Obtener el ID del grupo actual desde session_state
        if 'reunion_actual' not in st.session_state:
            st.error("No hay reunión activa seleccionada")
            return []
        
        id_grupo = st.session_state.reunion_actual['id_grupo']
        
        # Consulta para obtener todos los pagos de préstamos del grupo
        cursor.execute("""
            SELECT 
                pp.ID_PagoPrestamo,
                pp.ID_Prestamo,
                pp.ID_Reunion,
                pp.fecha_pago,
                pp.monto_capital,
                pp.monto_interes,
                pp.total_cancelado,
                p.ID_Miembro,
                m.nombre as nombre_miembro,
                prest.monto as monto_prestamo,
                prest.proposito
            FROM Pago_prestamo pp
            JOIN Prestamo prest ON pp.ID_Prestamo = prest.ID_Prestamo
            JOIN Miembro m ON prest.ID_Miembro = m.ID_Miembro
            WHERE m.ID_Grupo = %s
            ORDER BY pp.fecha_pago
        """, (id_grupo,))
        
        prestamos_data = cursor.fetchall()
        
        # Convertir a lista de diccionarios
        resultado = []
        for pago in prestamos_data:
            resultado.append({
                'id_pago_prestamo': pago['ID_PagoPrestamo'],
                'id_prestamo': pago['ID_Prestamo'],
                'id_reunion': pago['ID_Reunion'],
                'fecha_pago': pago['fecha_pago'],
                'monto_capital': float(pago['monto_capital'] or 0),
                'monto_interes': float(pago['monto_interes'] or 0),
                'total_cancelado': float(pago['total_cancelado'] or 0),
                'id_miembro': pago['ID_Miembro'],
                'nombre_miembro': pago['nombre_miembro'],
                'monto_prestamo': float(pago['monto_prestamo'] or 0),
                'proposito': pago['proposito']
            })
        
        return resultado
        
    except Exception as e:
        st.error(f"❌ Error en obtener_prestamos_grupo: {e}")
        return []
    
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'con' in locals():
            con.close()

def obtener_total_prestamos_ciclo():
    """
    Retorna la suma total de todos los pagos de préstamos del grupo
    Incluye tanto capital como intereses pagados
    """
    try:
        prestamos_data = obtener_prestamos_grupo()
        
        if not prestamos_data:
            return 0.00
        
        # Sumar todos los totales cancelados (capital + intereses)
        total_prestamos = sum(item['total_cancelado'] for item in prestamos_data)
        return total_prestamos
        
    except Exception as e:
        st.error(f"❌ Error calculando total de préstamos: {e}")
        return 0.00

def obtener_frecuencia_reunion(con, id_grupo):
    """Obtiene la frecuencia de reunión del grupo desde Reglamento"""
    cursor = con.cursor()
    cursor.execute("""
        SELECT frecuencia_reunion
        FROM Reglamento
        WHERE ID_Grupo = %s
        ORDER BY ID_Reglamento DESC
        LIMIT 1
    """, (id_grupo,))
    row = cursor.fetchone()
    cursor.close()
    return row[0] if row else "Mensual"

def obtener_fecha_reunion_por_mes(con, id_grupo, año, mes):
    """
    Retorna la fecha de reunión más cercana al fin de mes para un mes específico
    según la frecuencia de reuniones del grupo
    """
    cursor = con.cursor()
    
    # Obtener frecuencia de reunión
    frecuencia = obtener_frecuencia_reunion(con, id_grupo)
    
    # Calcular fecha objetivo (fin de mes)
    if mes == 12:
        fecha_fin_mes = date(año + 1, 1, 1) - timedelta(days=1)
    else:
        fecha_fin_mes = date(año, mes + 1, 1) - timedelta(days=1)
    
    # Buscar reuniones en el mes y año específicos
    cursor.execute("""
        SELECT fecha
        FROM Reunion
        WHERE ID_Grupo = %s AND YEAR(fecha) = %s AND MONTH(fecha) = %s
        ORDER BY fecha DESC
    """, (id_grupo, año, mes))
    
    reuniones = cursor.fetchall()
    cursor.close()
    
    if reuniones:
        # Si hay reuniones, tomar la más cercana al fin de mes
        fechas_reuniones = [r[0] for r in reuniones]
        fecha_cercana = min(fechas_reuniones, key=lambda x: abs((x - fecha_fin_mes).days))
        return fecha_cercana
    else:
        # Si no hay reuniones registradas, calcular según frecuencia
        if frecuencia == "Semanal":
            # Cuarta semana del mes
            primer_dia = date(año, mes, 1)
            # Encontrar el primer lunes del mes
            dias_hasta_lunes = (0 - primer_dia.weekday()) % 7
            primera_semana = primer_dia + timedelta(days=dias_hasta_lunes)
            # Cuarta semana (21 días después de la primera semana)
            return primera_semana + timedelta(days=21)
        elif frecuencia == "Quincenal":
            # Mitad del mes (día 15)
            return date(año, mes, 15)
        else:  # Mensual
            # Fin de mes
            return fecha_fin_mes

def generar_cronograma_pagos(id_prestamo, con, id_grupo=None):
    """
    Genera cronograma usando solo valores guardados en Prestamo
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
    cuota_mensual_reg = p.get('cuota_mensual')
    plazo = p.get('plazo')
    fecha_desembolso = p.get('fecha_desembolso')

    if monto_total_pagar is None or plazo is None or fecha_desembolso is None:
        st.error("❌ No se puede generar cronograma: faltan campos guardados en Prestamo")
        cursor.close()
        return False

    # Eliminar cronograma anterior del préstamo
    cursor.execute("DELETE FROM CuotaPrestamo WHERE ID_Prestamo = %s", (id_prestamo,))

    # Preparar Decimals
    monto_d = Decimal(str(monto)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    monto_total_d = Decimal(str(monto_total_pagar)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    total_interes_d = Decimal(str(total_interes)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    plazo_i = int(plazo)

    # Calcular interés mensual (CORREGIDO)
    interes_mensual = total_interes_d / plazo_i

    # Determinar total por cuota:
    if cuota_mensual_reg is not None:
        cuota_d = Decimal(str(cuota_mensual_reg)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    else:
        cuota_d = (monto_total_d / plazo_i).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    saldo_capital = monto_d

    # Generar cuotas
    for i in range(1, plazo_i + 1):
        # Calcular mes de la cuota
        año_cuota = fecha_desembolso.year
        mes_cuota = fecha_desembolso.month + i - 1
        
        # Ajustar año si el mes excede 12
        while mes_cuota > 12:
            mes_cuota -= 12
            año_cuota += 1

        # Determinar fecha de pago según frecuencia de reuniones
        if id_grupo is not None:
            fecha_pago = obtener_fecha_reunion_por_mes(con, id_grupo, año_cuota, mes_cuota)
        else:
            # Si no hay grupo, calcular aproximadamente 30 días por mes
            fecha_pago = fecha_desembolso + timedelta(days=30 * (i - 1))

        # Calcular montos de la cuota (CORREGIDO)
        if i == plazo_i:  # Última cuota
            capital_cuota = saldo_capital
            interes_cuota = interes_mensual
        else:
            capital_cuota = (cuota_d - interes_mensual).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            interes_cuota = interes_mensual

        total_cuota = (capital_cuota + interes_cuota).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        cursor.execute("""
            INSERT INTO CuotaPrestamo
            (ID_Prestamo, numero_cuota, fecha_programada, capital_programado,
             interes_programado, total_programado, estado, capital_pagado, interes_pagado, total_pagado)
            VALUES (%s, %s, %s, %s, %s, %s, 'pendiente', 0, 0, 0)
        """, (
            id_prestamo, i, fecha_pago,
            float(capital_cuota), float(interes_cuota), float(total_cuota)
        ))

        saldo_capital -= capital_cuota

    con.commit()
    cursor.close()
    return True

def recalcular_cronograma_despues_pago_parcial(id_prestamo, con, id_grupo=None):
    """
    Recalcula el cronograma CORRECTAMENTE después de un pago parcial
    """
    cursor = con.cursor(dictionary=True)
    
    # Obtener datos del préstamo
    cursor.execute("""
        SELECT monto, total_interes, monto_total_pagar, plazo, fecha_desembolso
        FROM Prestamo WHERE ID_Prestamo = %s
    """, (id_prestamo,))
    prestamo = cursor.fetchone()
    
    if not prestamo:
        cursor.close()
        return False
    
    monto_original = Decimal(str(prestamo['monto']))
    total_interes_original = Decimal(str(prestamo['total_interes']))
    plazo_total = int(prestamo['plazo'])
    
    # Calcular interés MENSUAL (CORREGIDO)
    interes_mensual = total_interes_original / plazo_total
    
    # Obtener TODAS las cuotas para calcular lo PAGADO
    cursor.execute("""
        SELECT numero_cuota, capital_programado, interes_programado, total_programado,
               capital_pagado, interes_pagado, total_pagado, estado, fecha_programada
        FROM CuotaPrestamo
        WHERE ID_Prestamo = %s
        ORDER BY numero_cuota
    """, (id_prestamo,))
    
    todas_cuotas = cursor.fetchall()
    
    # Calcular totales PAGADOS
    total_capital_pagado = Decimal('0')
    total_interes_pagado = Decimal('0')
    
    for cuota in todas_cuotas:
        total_capital_pagado += Decimal(str(cuota['capital_pagado'] or 0))
        total_interes_pagado += Decimal(str(cuota['interes_pagado'] or 0))
    
    # Calcular NUEVA DEUDA (CORREGIDO)
    deuda_actual = monto_original - total_capital_pagado
    interes_total_pagado = total_interes_pagado
    
    st.info(f"💰 Nueva deuda calculada: Capital: ${deuda_actual:,.2f}")
    
    # Obtener cuotas PENDIENTES
    cuotas_pendientes = [c for c in todas_cuotas if c['estado'] != 'pagado']
    cuotas_restantes = len(cuotas_pendientes)
    
    if cuotas_restantes == 0:
        cursor.close()
        return True
    
    # Recalcular NUEVA CUOTA MENSUAL (CORREGIDO)
    # El interés mensual sigue siendo el mismo, solo redistribuimos el capital
    nuevo_capital_mensual = (deuda_actual / cuotas_restantes).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    
    # Redistribuir en las cuotas pendientes
    capital_acumulado = Decimal('0')
    
    for i, cuota in enumerate(cuotas_pendientes):
        if i == len(cuotas_pendientes) - 1:  # Última cuota
            capital_cuota = deuda_actual - capital_acumulado
        else:
            capital_cuota = nuevo_capital_mensual
        
        interes_cuota = interes_mensual
        total_cuota = (capital_cuota + interes_cuota).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        
        # Actualizar SOLO los montos PROGRAMADOS
        cursor.execute("""
            UPDATE CuotaPrestamo 
            SET capital_programado = %s, interes_programado = %s, total_programado = %s
            WHERE ID_Cuota = %s
        """, (float(capital_cuota), float(interes_cuota), float(total_cuota), cuota['ID_Cuota']))
        
        capital_acumulado += capital_cuota
    
    con.commit()
    cursor.close()
    return True

def aplicar_pago_cuota(id_prestamo, monto_pagado, fecha_pago, tipo_pago, con, id_grupo=None, numero_cuota=None):
    """
    Aplica pago completo o parcial y recalcula el cronograma si es parcial
    """
    cursor = con.cursor(dictionary=True)

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
                   COALESCE(capital_pagado,0) AS capital_pagado, COALESCE(interes_pagado,0) AS interes_pagado,
                   COALESCE(total_pagado,0) AS total_pagado, estado
            FROM CuotaPrestamo
            WHERE ID_Prestamo = %s AND estado != 'pagado'
            ORDER BY numero_cuota ASC
            LIMIT 1
        """, (id_prestamo,))

    cuota = cursor.fetchone()
    if not cuota:
        cursor.close()
        return False, "No hay cuotas pendientes"

    id_cuota = cuota['ID_Cuota']
    capital_prog = Decimal(str(cuota['capital_programado']))
    interes_prog = Decimal(str(cuota['interes_programado']))
    total_prog = Decimal(str(cuota['total_programado']))
    capital_pag = Decimal(str(cuota.get('capital_pagado', 0)))
    interes_pag = Decimal(str(cuota.get('interes_pagado', 0)))
    monto_pagado_d = Decimal(str(monto_pagado))

    if tipo_pago == "completo":
        # Pago completo - marcar como pagado
        nuevo_capital_pagado = capital_prog
        nuevo_interes_pagado = interes_prog
        nuevo_total_pagado = total_prog
        nuevo_estado = 'pagado'
        
        cursor.execute("""
            UPDATE CuotaPrestamo
            SET capital_pagado = %s, interes_pagado = %s, total_pagado = %s, estado = %s
            WHERE ID_Cuota = %s
        """, (float(nuevo_capital_pagado), float(nuevo_interes_pagado), float(nuevo_total_pagado), nuevo_estado, id_cuota))
        
    else:
        # Pago parcial
        interes_faltante = interes_prog - interes_pag
        capital_faltante = capital_prog - capital_pag
        total_faltante = interes_faltante + capital_faltante

        # Validar que el pago no exceda lo faltante
        if monto_pagado_d > total_faltante:
            monto_pagado_d = total_faltante
            st.warning(f"⚠️ El monto excede lo pendiente. Se ajustó a ${monto_pagado_d:,.2f}")

        nuevo_interes_pagado = interes_pag
        nuevo_capital_pagado = capital_pag

        # Aplicar a interés primero (regla financiera estándar)
        if monto_pagado_d > 0 and interes_faltante > 0:
            if monto_pagado_d >= interes_faltante:
                nuevo_interes_pagado = interes_prog
                monto_pagado_d -= interes_faltante
            else:
                nuevo_interes_pagado = interes_pag + monto_pagado_d
                monto_pagado_d = Decimal('0')

        # Aplicar el resto a capital
        if monto_pagado_d > 0 and capital_faltante > 0:
            if monto_pagado_d >= capital_faltante:
                nuevo_capital_pagado = capital_prog
                monto_pagado_d -= capital_faltante
            else:
                nuevo_capital_pagado = capital_pag + monto_pagado_d
                monto_pagado_d = Decimal('0')

        nuevo_total_pagado = (nuevo_capital_pagado + nuevo_interes_pagado).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        
        # Determinar estado
        if abs(nuevo_total_pagado - total_prog) < Decimal('0.01'):  # Considerar pagado si es casi igual
            nuevo_estado = 'pagado'
        elif nuevo_total_pagado > 0:
            nuevo_estado = 'parcial'
        else:
            nuevo_estado = 'pendiente'

        # Actualizar la cuota
        cursor.execute("""
            UPDATE CuotaPrestamo
            SET capital_pagado = %s, interes_pagado = %s, total_pagado = %s, estado = %s
            WHERE ID_Cuota = %s
        """, (float(nuevo_capital_pagado), float(nuevo_interes_pagado), float(nuevo_total_pagado), nuevo_estado, id_cuota))

        # Recalcular cronograma SIEMPRE después de un pago parcial
        if tipo_pago == "parcial":
            success = recalcular_cronograma_despues_pago_parcial(id_prestamo, con, id_grupo)
            if not success:
                st.error("❌ Error al recalcular el cronograma después del pago parcial")

    con.commit()
    cursor.close()
    return True, "Pago aplicado correctamente"

def mostrar_pago_prestamo():
    """
    Muestra resumen del préstamo usando SOLO LOS VALORES GUARDADOS EN LA TABLA Prestamo.
    """
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

        st.info(f"📅 Reunión actual: {nombre_reunion}")

        # Obtener miembros presentes
        cursor.execute("""
            SELECT m.ID_Miembro, m.nombre
            FROM Miembro m
            JOIN Miembroxreunion mr ON m.ID_Miembro = mr.ID_Miembro
            WHERE mr.ID_Reunion = %s AND mr.asistio = 1
            ORDER BY m.nombre
        """, (id_reunion,))
        miembros = cursor.fetchall()
        if not miembros:
            st.warning("⚠️ No hay miembros marcados como presentes en esta reunión.")
            cursor.close()
            return

        ids = [m['ID_Miembro'] for m in miembros]
        placeholders = ','.join(['%s'] * len(ids))

        # Leer préstamos solo de miembros presentes
        cursor.execute(f"""
            SELECT p.ID_Prestamo, p.ID_Miembro, p.monto, p.total_interes, p.monto_total_pagar,
               p.cuota_mensual, p.plazo, p.fecha_desembolso, m.nombre as miembro_nombre, p.proposito
            FROM Prestamo p
            JOIN Miembro m ON p.ID_Miembro = m.ID_Miembro
            WHERE p.ID_Estado_prestamo != 3
              AND p.ID_Miembro IN ({placeholders})
        """, ids)
        prestamos = cursor.fetchall()
        if not prestamos:
            st.warning("⚠️ No hay préstamos activos para los miembros presentes.")
            cursor.close()
            return

        # Selector de préstamo
        prestamos_dict = {
            f"Préstamo {p['ID_Prestamo']} - {p['miembro_nombre']} - ${p['monto']:,.2f} - {p['plazo']} meses": p['ID_Prestamo']
            for p in prestamos
        }
        sel = st.selectbox("Selecciona el préstamo:", list(prestamos_dict.keys()))
        id_prestamo = prestamos_dict[sel]
        prestamo = next(p for p in prestamos if p['ID_Prestamo'] == id_prestamo)

        # Mostrar información del préstamo
        monto = prestamo.get('monto')
        total_interes = prestamo.get('total_interes')
        monto_total_pagar = prestamo.get('monto_total_pagar')
        cuota_mensual = prestamo.get('cuota_mensual')
        plazo = prestamo.get('plazo')
        fecha_desembolso = prestamo.get('fecha_desembolso')
        proposito = prestamo.get('proposito')

        st.subheader("📋 RESUMEN DEL PRÉSTAMO")
        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Información básica**")
            st.write(f"• Fecha desembolso: {fecha_desembolso}")
            st.write(f"• Plazo: {plazo} meses")
            st.write(f"• Propósito: {proposito}")
        with c2:
            st.markdown("**Montos (registrados en Prestamo)**")
            st.write(f"• Monto préstamo: ${monto:,.2f}")
            st.write(f"• Interés total (registrado): ${total_interes:,.2f}")
            if monto_total_pagar is not None:
                st.write(f"• Total a pagar (registrado): ${monto_total_pagar:,.2f}")
            else:
                st.warning("⚠️ En Prestamo no hay 'monto_total_pagar' guardado.")
            if cuota_mensual is not None:
                st.write(f"• Cuota mensual (registrada): ${cuota_mensual:,.2f}")
            else:
                st.info("• Cuota mensual (registrada): (no existe o no fue guardada)")

        st.markdown("---")

        # Mostrar frecuencia del reglamento
        if id_grupo is not None:
            frecuencia = obtener_frecuencia_reunion(con, id_grupo)
            st.info(f"🔄 Frecuencia de reuniones del grupo: {frecuencia}")
        else:
            st.info("🔄 Frecuencia de reuniones: (no disponible, grupo no especificado)")

        # Verificar cronograma
        cursor.execute("SELECT COUNT(*) AS c FROM CuotaPrestamo WHERE ID_Prestamo = %s", (id_prestamo,))
        tiene = cursor.fetchone().get('c', 0) > 0
        if not tiene:
            st.info("📅 Este préstamo no tiene cronograma generado.")
            if st.button("🔄 Generar Plan de Pagos"):
                ok = generar_cronograma_pagos(id_prestamo, con, id_grupo)
                if ok:
                    st.success("✅ Cronograma generado usando los valores guardados en Prestamo.")
                    st.rerun()
                else:
                    st.error("❌ No se pudo generar el cronograma.")
            cursor.close()
            return

        # Mostrar cuotas ORDENADAS por número de cuota
        cursor.execute("""
            SELECT numero_cuota, fecha_programada, capital_programado, interes_programado, total_programado,
                   COALESCE(capital_pagado,0) AS capital_pagado, COALESCE(interes_pagado,0) AS interes_pagado,
                   COALESCE(total_pagado,0) AS total_pagado, estado
            FROM CuotaPrestamo
            WHERE ID_Prestamo = %s
            ORDER BY numero_cuota ASC
        """, (id_prestamo,))
        cuotas = cursor.fetchall()

        st.subheader("📅 Plan de pagos")
        st.markdown("---")
        tabla = []
        for c in cuotas:
            numero = c['numero_cuota']
            fecha_p = c['fecha_programada']
            cap_prog = c['capital_programado']
            int_prog = c['interes_programado']
            tot_prog = c['total_programado']
            cap_pag = c['capital_pagado']
            int_pag = c['interes_pagado']
            tot_pag = c['total_pagado']
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

        # Totales y saldo pendiente
        total_pagado = sum(c['total_pagado'] or 0 for c in cuotas)
        if monto_total_pagar is not None:
            saldo = Decimal(str(monto_total_pagar)) - Decimal(str(total_pagado or 0))
            st.markdown("---")
            st.markdown(f"**TOTAL (registro):** ${monto:,.2f} (capital) + ${total_interes:,.2f} (interés) = **${monto_total_pagar:,.2f}**")
            st.markdown(f"**TOTAL PAGADO:** ${total_pagado:,.2f}")
            if saldo <= 0:
                st.success("**SALDO: $0 (COMPLETAMENTE PAGADO)** 🎉")
            else:
                st.warning(f"**SALDO PENDIENTE: ${saldo:,.2f}**")
        else:
            st.info("Saldo: no disponible (monto_total_pagar no registrado en Prestamo).")

        # --- Formularios de pago (completo / parcial)
        st.markdown("---")
        st.subheader("Registrar pago")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Pago completo")
            with st.form("form_completo"):
                cursor.execute("""
                    SELECT numero_cuota, total_programado, total_pagado, fecha_programada
                    FROM CuotaPrestamo
                    WHERE ID_Prestamo = %s AND estado != 'pagado'
                    ORDER BY numero_cuota ASC
                """, (id_prestamo,))
                pendientes = cursor.fetchall()
                if pendientes:
                    opciones = [f"Cuota {r['numero_cuota']} - ${r['total_programado']:,.2f} - {r['fecha_programada']}" for r in pendientes]
                    sel_c = st.selectbox("Selecciona cuota:", opciones, key="c_complete")
                    num_sel = int(sel_c.split(" ")[1])
                    fecha_pago = st.date_input("Fecha pago:", value=date.today(), key="fecha_complete")
                    enviar = st.form_submit_button("Pagar completa")
                    if enviar:
                        fila = next(r for r in pendientes if r['numero_cuota'] == num_sel)
                        monto_cuota = fila['total_programado']
                        ok, msg = aplicar_pago_cuota(id_prestamo, monto_cuota, fecha_pago, "completo", con, id_grupo, num_sel)
                        if ok:
                            cursor.execute("""
                                INSERT INTO Pago_prestamo (ID_Prestamo, ID_Reunion, fecha_pago, monto_capital, monto_interes, total_cancelado)
                                VALUES (%s, %s, %s, %s, %s, %s)
                            """, (id_prestamo, id_reunion, fecha_pago, 0, 0, float(monto_cuota)))
                            con.commit()
                            st.success("✅ Pago completo registrado.")
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")
                else:
                    st.info("No hay cuotas pendientes para pago completo.")
                    
        with col2:
            st.markdown("### Pago parcial")
            with st.form("form_parcial"):
                cursor.execute("""
                    SELECT numero_cuota, total_programado, total_pagado, fecha_programada,
                           (total_programado - COALESCE(total_pagado,0)) as pendiente
                    FROM CuotaPrestamo
                    WHERE ID_Prestamo = %s AND estado != 'pagado'
                    ORDER BY numero_cuota ASC
                    LIMIT 1
                """, (id_prestamo,))
                prox = cursor.fetchone()
                if prox:
                    num = prox['numero_cuota']
                    total_prog = prox['total_programado']
                    total_pag = prox['total_pagado'] or 0
                    pendiente = prox['pendiente']
                    st.write(f"Próxima cuota: #{num}")
                    st.write(f"Total pendiente: ${pendiente:,.2f}")
                    st.write(f"Fecha programada: {prox['fecha_programada']}")
                    fecha_pago_par = st.date_input("Fecha pago:", value=date.today(), key="fecha_parcial")
                    monto_par = st.number_input("Monto a pagar:", min_value=0.01, max_value=float(pendiente), 
                                              value=float(min(pendiente, 100)), step=1.0, format="%.2f")
                    enviar_par = st.form_submit_button("Registrar pago parcial")
                    if enviar_par:
                        if monto_par <= 0:
                            st.warning("El monto debe ser mayor a cero.")
                        else:
                            ok, msg = aplicar_pago_cuota(id_prestamo, monto_par, fecha_pago_par, "parcial", con, id_grupo)
                            if ok:
                                cursor.execute("""
                                    INSERT INTO Pago_prestamo (ID_Prestamo, ID_Reunion, fecha_pago, monto_capital, monto_interes, total_cancelado)
                                    VALUES (%s, %s, %s, %s, %s, %s)
                                """, (id_prestamo, id_reunion, fecha_pago_par, 0, 0, float(monto_par)))
                                con.commit()
                                st.success("✅ Pago parcial registrado y cronograma actualizado.")
                                st.rerun()
                            else:
                                st.error(f"❌ {msg}")
                else:
                    st.info("No hay cuotas pendientes para pago parcial.")

        cursor.close()

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
