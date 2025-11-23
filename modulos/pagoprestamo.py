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

def obtener_reunion_mas_cercana_fin_mes(con, id_grupo, fecha_referencia, mes_offset=0):
    """
    Retorna la fecha de la reunión más cercana al fin del mes objetivo.
    Usa la tabla Reglamento para obtener frecuencia (solo para referencia; la función
    busca reuniones en la tabla Reunion y devuelve la que esté más cerca del fin de mes).
    """
    cursor = con.cursor()
    cursor.execute("""
        SELECT frecuencia_reunion
        FROM Reglamento
        WHERE ID_Grupo = %s
        ORDER BY ID_Reglamento DESC
        LIMIT 1
    """, (id_grupo,))
    row = cursor.fetchone()
    # frecuencia la mostramos en UI; la lógica para elegir reunión sigue siendo por fecha
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


def generar_cronograma_pagos(id_prestamo, con, id_grupo=None):
    """
    Genera cronograma usando solo valores guardados en Prestamo:
      - monto
      - total_interes (EN $)  <- IMPORTANTÍSIMO: debe venir en moneda, no en %
      - monto_total_pagar (EN $)
      - cuota_mensual (EN $, opcional)
      - plazo (meses)
      - fecha_desembolso
    Si falta 'monto_total_pagar' o 'plazo' devuelve error y no genera.
    Las fechas se asignan usando 'obtener_reunion_mas_cercana_fin_mes' (si se pasa id_grupo).
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
    total_interes = p.get('total_interes') or 0        # EN $ según flujo que indicas
    monto_total_pagar = p.get('monto_total_pagar')     # EN $
    cuota_mensual_reg = p.get('cuota_mensual')         # EN $, opcional
    plazo = p.get('plazo')
    fecha_desembolso = p.get('fecha_desembolso')

    # Requerimos mínimo: monto_total_pagar, plazo, fecha_desembolso
    if monto_total_pagar is None or plazo is None or fecha_desembolso is None:
        st.error("❌ No se puede generar cronograma: faltan campos guardados en Prestamo (monto_total_pagar / plazo / fecha_desembolso).")
        cursor.close()
        return False

    # Eliminar cronograma anterior del préstamo
    cursor.execute("DELETE FROM CuotaPrestamo WHERE ID_Prestamo = %s", (id_prestamo,))

    # Preparar Decimals
    monto_d = Decimal(str(monto)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    monto_total_d = Decimal(str(monto_total_pagar)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    total_interes_d = Decimal(str(total_interes)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    plazo_i = int(plazo)

    # Determinar total por cuota:
    if cuota_mensual_reg is not None:
        cuota_d = Decimal(str(cuota_mensual_reg)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    else:
        cuota_d = (monto_total_d / plazo_i).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Interés por cuota (distribuir interés total si existe)
    interes_por_cuota = (total_interes_d / plazo_i).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if total_interes_d > 0 else Decimal("0.00")

    saldo_capital = monto_d
    saldo_interes = total_interes_d

    # Fecha base: para cada mes tomamos la reunión más cercana al fin de mes (mes_offset = i)
    for i in range(1, plazo_i + 1):
        # calcular capital/interés/total por cuota usando solo valores guardados
        if i == plazo_i:
            # última cuota: absorber los saldos por redondeo
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

        # Determinar fecha de pago: la reunión más cercana al fin del mes i desde fecha_desembolso
        if id_grupo is not None:
            fecha_pago = obtener_reunion_mas_cercana_fin_mes(con, id_grupo, fecha_desembolso, i)
        else:
            # si no hay id_grupo, programar simplemente cada 30 días
            fecha_pago = fecha_desembolso + timedelta(days=30*i)

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
        saldo_interes -= interes_cuota

    con.commit()
    cursor.close()
    return True


def aplicar_pago_cuota(id_prestamo, monto_pagado, fecha_pago, tipo_pago, con, id_grupo=None, numero_cuota=None):
    """
    Aplica pago completo o parcial y RECALCULA SIEMPRE todo el cronograma pendiente
    """
    cursor = con.cursor(dictionary=True)

    try:
        # Obtener información del préstamo
        cursor.execute("""
            SELECT monto, total_interes, monto_total_pagar, plazo, fecha_desembolso
            FROM Prestamo
            WHERE ID_Prestamo = %s
        """, (id_prestamo,))
        prestamo_info = cursor.fetchone()
        
        if not prestamo_info:
            return False, "No se encontró información del préstamo"

        monto_total_prestamo = Decimal(str(prestamo_info['monto_total_pagar']))
        monto_pagado_d = Decimal(str(monto_pagado))

        # 1. REGISTRAR EL PAGO PRIMERO
        if tipo_pago == "completo" and numero_cuota:
            # Pago completo de cuota específica
            cursor.execute("""
                SELECT ID_Cuota, capital_programado, interes_programado, total_programado
                FROM CuotaPrestamo
                WHERE ID_Prestamo = %s AND numero_cuota = %s
            """, (id_prestamo, numero_cuota))
            cuota = cursor.fetchone()
            
            if not cuota:
                return False, "No se encontró la cuota especificada"
            
            # Registrar pago completo de esta cuota
            cursor.execute("""
                UPDATE CuotaPrestamo
                SET capital_pagado = capital_programado,
                    interes_pagado = interes_programado,
                    total_pagado = total_programado,
                    estado = 'pagado'
                WHERE ID_Cuota = %s
            """, (cuota['ID_Cuota'],))
            
            # Registrar en Pago_prestamo
            cursor.execute("""
                INSERT INTO Pago_prestamo (ID_Prestamo, ID_Reunion, fecha_pago, monto_capital, monto_interes, total_cancelado)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (id_prestamo, st.session_state.reunion_actual['id_reunion'], fecha_pago,
                  float(cuota['capital_programado']), float(cuota['interes_programado']), float(cuota['total_programado'])))
        
        else:
            # Pago parcial a la próxima cuota pendiente
            cursor.execute("""
                SELECT ID_Cuota, numero_cuota, capital_programado, interes_programado, total_programado,
                       COALESCE(capital_pagado,0) AS capital_pagado, COALESCE(interes_pagado,0) AS interes_pagado
                FROM CuotaPrestamo
                WHERE ID_Prestamo = %s AND estado != 'pagado'
                ORDER BY numero_cuota ASC
                LIMIT 1
            """, (id_prestamo,))
            cuota_actual = cursor.fetchone()
            
            if not cuota_actual:
                return False, "No hay cuotas pendientes"

            # Aplicar pago a la cuota actual
            capital_pendiente = Decimal(str(cuota_actual['capital_programado'])) - Decimal(str(cuota_actual['capital_pagado']))
            interes_pendiente = Decimal(str(cuota_actual['interes_programado'])) - Decimal(str(cuota_actual['interes_pagado']))
            total_pendiente = capital_pendiente + interes_pendiente
            
            if monto_pagado_d > total_pendiente:
                return False, f"El pago (${monto_pagado_d}) excede el total pendiente (${total_pendiente})"

            # Aplicar pago: primero interés, luego capital
            nuevo_interes_pagado = Decimal(str(cuota_actual['interes_pagado']))
            nuevo_capital_pagado = Decimal(str(cuota_actual['capital_pagado']))
            
            # Pagar interés primero
            if interes_pendiente > 0:
                if monto_pagado_d >= interes_pendiente:
                    nuevo_interes_pagado += interes_pendiente
                    monto_pagado_d -= interes_pendiente
                else:
                    nuevo_interes_pagado += monto_pagado_d
                    monto_pagado_d = Decimal('0')
            
            # Pagar capital con lo que queda
            if monto_pagado_d > 0 and capital_pendiente > 0:
                if monto_pagado_d >= capital_pendiente:
                    nuevo_capital_pagado += capital_pendiente
                    monto_pagado_d -= capital_pendiente
                else:
                    nuevo_capital_pagado += monto_pagado_d
                    monto_pagado_d = Decimal('0')
            
            nuevo_total_pagado = nuevo_capital_pagado + nuevo_interes_pagado
            
            # Determinar nuevo estado
            if nuevo_total_pagado >= Decimal(str(cuota_actual['total_programado'])):
                nuevo_estado = 'pagado'
            else:
                nuevo_estado = 'parcial'

            # Actualizar la cuota actual
            cursor.execute("""
                UPDATE CuotaPrestamo
                SET capital_pagado = %s, interes_pagado = %s, total_pagado = %s, estado = %s
                WHERE ID_Cuota = %s
            """, (float(nuevo_capital_pagado), float(nuevo_interes_pagado), float(nuevo_total_pagado), nuevo_estado, cuota_actual['ID_Cuota']))

            # Registrar en Pago_prestamo
            cursor.execute("""
                INSERT INTO Pago_prestamo (ID_Prestamo, ID_Reunion, fecha_pago, monto_capital, monto_interes, total_cancelado)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (id_prestamo, st.session_state.reunion_actual['id_reunion'], fecha_pago,
                  float(nuevo_capital_pagado - Decimal(str(cuota_actual['capital_pagado']))),
                  float(nuevo_interes_pagado - Decimal(str(cuota_actual['interes_pagado']))),
                  float(monto_pagado)))

        # 2. RECALCULAR SIEMPRE TODAS LAS CUOTAS PENDIENTES
        # Obtener total pagado hasta ahora
        cursor.execute("""
            SELECT COALESCE(SUM(total_pagado), 0) as total_pagado_hasta_ahora
            FROM CuotaPrestamo
            WHERE ID_Prestamo = %s
        """, (id_prestamo,))
        total_pagado_hasta_ahora = Decimal(str(cursor.fetchone()['total_pagado_hasta_ahora']))
        
        # Calcular nuevo saldo pendiente
        nuevo_saldo_pendiente = monto_total_prestamo - total_pagado_hasta_ahora
        
        # Si ya está pagado completamente, no hay nada que recalcular
        if nuevo_saldo_pendiente <= 0:
            con.commit()
            return True, "Préstamo completamente pagado"
        
        # Obtener cuotas pendientes
        cursor.execute("""
            SELECT ID_Cuota, numero_cuota, fecha_programada, 
                   COALESCE(capital_pagado, 0) as capital_pagado,
                   COALESCE(interes_pagado, 0) as interes_pagado
            FROM CuotaPrestamo
            WHERE ID_Prestamo = %s AND estado != 'pagado'
            ORDER BY numero_cuota
        """, (id_prestamo,))
        cuotas_pendientes = cursor.fetchall()
        
        if not cuotas_pendientes:
            con.commit()
            return True, "Pago registrado"
        
        # Calcular nueva cuota mensual equitativa
        cuotas_pendientes_count = len(cuotas_pendientes)
        nueva_cuota_mensual = (nuevo_saldo_pendiente / cuotas_pendientes_count).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        
        # Calcular proporción capital/interés del saldo pendiente
        cursor.execute("""
            SELECT 
                COALESCE(SUM(capital_programado - COALESCE(capital_pagado, 0)), 0) as capital_pendiente,
                COALESCE(SUM(interes_programado - COALESCE(interes_pagado, 0)), 0) as interes_pendiente
            FROM CuotaPrestamo
            WHERE ID_Prestamo = %s AND estado != 'pagado'
        """, (id_prestamo,))
        saldos = cursor.fetchone()
        
        capital_pendiente_total = Decimal(str(saldos['capital_pendiente']))
        interes_pendiente_total = Decimal(str(saldos['interes_pendiente']))
        total_pendiente_actual = capital_pendiente_total + interes_pendiente_total
        
        if total_pendiente_actual > 0:
            proporcion_capital = capital_pendiente_total / total_pendiente_actual
            proporcion_interes = interes_pendiente_total / total_pendiente_actual
        else:
            proporcion_capital = Decimal("0.5")
            proporcion_interes = Decimal("0.5")
        
        # RECALCULAR TODAS LAS CUOTAS PENDIENTES
        saldo_restante = nuevo_saldo_pendiente
        
        for i, cuota in enumerate(cuotas_pendientes):
            id_cuota = cuota['ID_Cuota']
            capital_ya_pagado = Decimal(str(cuota['capital_pagado']))
            interes_ya_pagado = Decimal(str(cuota['interes_pagado']))
            total_ya_pagado = capital_ya_pagado + interes_ya_pagado
            
            if i == len(cuotas_pendientes) - 1:
                # Última cuota: tomar todo el saldo restante
                capital_cuota = (saldo_restante * proporcion_capital).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                interes_cuota = saldo_restante - capital_cuota
            else:
                # Cuotas intermedias: distribución equitativa
                capital_cuota = (nueva_cuota_mensual * proporcion_capital).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                interes_cuota = nueva_cuota_mensual - capital_cuota
                saldo_restante -= nueva_cuota_mensual
            
            # Los nuevos valores programados son: lo ya pagado + lo pendiente
            nuevo_capital_programado = capital_ya_pagado + capital_cuota
            nuevo_interes_programado = interes_ya_pagado + interes_cuota
            nuevo_total_programado = nuevo_capital_programado + nuevo_interes_programado
            
            # Determinar estado basado en lo pagado vs programado
            if total_ya_pagado >= nuevo_total_programado:
                nuevo_estado = 'pagado'
            elif total_ya_pagado > 0:
                nuevo_estado = 'parcial'
            else:
                nuevo_estado = 'pendiente'
            
            # ACTUALIZAR LA CUOTA CON LOS NUEVOS VALORES
            cursor.execute("""
                UPDATE CuotaPrestamo
                SET capital_programado = %s,
                    interes_programado = %s,
                    total_programado = %s,
                    estado = %s
                WHERE ID_Cuota = %s
            """, (float(nuevo_capital_programado), float(nuevo_interes_programado), 
                  float(nuevo_total_programado), nuevo_estado, id_cuota))

        con.commit()
        return True, "Pago registrado y cronograma actualizado"

    except Exception as e:
        con.rollback()
        return False, f"Error al procesar pago: {str(e)}"
    
    finally:
        cursor.close()


def mostrar_pago_prestamo():
    """
    Muestra resumen del préstamo usando SOLO LOS VALORES GUARDADOS EN LA TABLA Prestamo.
    No hacer cálculos de interés ni convertir porcentajes en esta vista.
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

        # Leer préstamos solo de miembros presentes; SOLO campos de la tabla Prestamo (sin columnas que no existan)
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

        # selector
        prestamos_dict = {
            f"Préstamo {p['ID_Prestamo']} - {p['miembro_nombre']} - ${p['monto']:,.2f} - {p['plazo']} meses": p['ID_Prestamo']
            for p in prestamos
        }
        sel = st.selectbox("Selecciona el préstamo:", list(prestamos_dict.keys()))
        id_prestamo = prestamos_dict[sel]
        prestamo = next(p for p in prestamos if p['ID_Prestamo'] == id_prestamo)

        # === Mostrar SOLO lo registrado (sin recalculos) ===
        monto = prestamo.get('monto')
        total_interes = prestamo.get('total_interes')         # INTERÉS TOTAL guardado en $
        monto_total_pagar = prestamo.get('monto_total_pagar') # TOTAL guardado en $
        cuota_mensual = prestamo.get('cuota_mensual')         # puede ser None
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
            # total_interes es INTERÉS TOTAL EN $
            st.write(f"• Interés total (registrado): ${total_interes:,.2f}")
            if monto_total_pagar is not None:
                st.write(f"• Total a pagar (registrado): ${monto_total_pagar:,.2f}")
            else:
                st.warning("⚠️ En Prestamo no hay 'monto_total_pagar' guardado. No puedo mostrar el total exacto.")
            if cuota_mensual is not None:
                st.write(f"• Cuota mensual (registrada): ${cuota_mensual:,.2f}")
            else:
                st.info("• Cuota mensual (registrada): (no existe o no fue guardada)")

        st.markdown("---")

        # Mostrar frecuencia del reglamento (solo llamar y mostrar)
        if id_grupo is not None:
            cursor.execute("""
                SELECT frecuencia_reunion
                FROM Reglamento
                WHERE ID_Grupo = %s
                ORDER BY ID_Reglamento DESC
                LIMIT 1
            """, (id_grupo,))
            frow = cursor.fetchone()
            frecuencia = frow.get('frecuencia_reunion') if frow else "Mensual"
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
                    st.error("❌ No se pudo generar el cronograma. Verifica que 'monto_total_pagar' y 'plazo' estén guardados.")
            cursor.close()
            return

        # Mostrar cuotas
        cursor.execute("""
            SELECT numero_cuota, fecha_programada, capital_programado, interes_programado, total_programado,
                   COALESCE(capital_pagado,0) AS capital_pagado, COALESCE(interes_pagado,0) AS interes_pagado,
                   COALESCE(total_pagado,0) AS total_pagado, estado
            FROM CuotaPrestamo
            WHERE ID_Prestamo = %s
            ORDER BY fecha_programada ASC
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
            st.markdown("Pago completo")
            with st.form("form_completo"):
                cursor.execute("""
                    SELECT numero_cuota, total_programado, total_pagado, fecha_programada
                    FROM CuotaPrestamo
                    WHERE ID_Prestamo = %s AND estado != 'pagado'
                    ORDER BY numero_cuota
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
                            st.success("✅ Pago completo registrado.")
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")
                else:
                    st.info("No hay cuotas pendientes para pago completo.")
        with col2:
            st.markdown("Pago parcial")
            with st.form("form_parcial"):
                cursor.execute("""
                    SELECT numero_cuota, total_programado, total_pagado, fecha_programada
                    FROM CuotaPrestamo
                    WHERE ID_Prestamo = %s AND estado != 'pagado'
                    ORDER BY fecha_programada ASC
                    LIMIT 1
                """, (id_prestamo,))
                prox = cursor.fetchone()
                if prox:
                    num = prox['numero_cuota']
                    total_prog = prox['total_programado']
                    total_pag = prox['total_pagado'] or 0
                    pendiente = total_prog - total_pag
                    st.write(f"Próxima cuota: #{num}")
                    st.write(f"Total pendiente: ${pendiente:,.2f}")
                    st.write(f"Fecha programada: {prox['fecha_programada']}")
                    fecha_pago_par = st.date_input("Fecha pago:", value=date.today(), key="fecha_parcial")
                    monto_par = st.number_input("Monto a pagar:", min_value=0.01, max_value=float(pendiente), value=float(min(pendiente,100)), step=1.0, format="%.2f")
                    enviar_par = st.form_submit_button("Registrar pago parcial")
                    if enviar_par:
                        if monto_par <= 0:
                            st.warning("El monto debe ser mayor a cero.")
                        else:
                            ok, msg = aplicar_pago_cuota(id_prestamo, monto_par, fecha_pago_par, "parcial", con, id_grupo)
                            if ok:
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
