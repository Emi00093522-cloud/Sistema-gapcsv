def aplicar_pago_cuota(id_prestamo, monto_pagado, fecha_pago, tipo_pago, con, id_grupo=None, numero_cuota=None):
    """
    Aplica pago completo o parcial a la próxima cuota (o número específico si tipo='completo').
    Si es parcial, recalcula la deuda restante y regenera el cronograma completo.
    """
    cursor = con.cursor(dictionary=True)

    if tipo_pago == "completo" and numero_cuota:
        cursor.execute("""
            SELECT ID_Cuota, capital_programado, interes_programado, total_programado,
                   capital_pagado, interes_pagado, total_pagado, estado, fecha_programada
            FROM CuotaPrestamo
            WHERE ID_Prestamo = %s AND numero_cuota = %s
        """, (id_prestamo, numero_cuota))
    else:
        cursor.execute("""
            SELECT ID_Cuota, numero_cuota, capital_programado, interes_programado, total_programado,
                   COALESCE(capital_pagado,0) AS capital_pagado, COALESCE(interes_pagado,0) AS interes_pagado,
                   COALESCE(total_pagado,0) AS total_pagado, estado, fecha_programada
            FROM CuotaPrestamo
            WHERE ID_Prestamo = %s AND estado != 'pagado'
            ORDER BY fecha_programada ASC
            LIMIT 1
        """, (id_prestamo,))

    cuota = cursor.fetchone()
    if not cuota:
        cursor.close()
        return False, "No hay cuotas pendientes"

    # extraer campos
    if tipo_pago == "completo" and numero_cuota:
        id_cuota = cuota['ID_Cuota']
        capital_prog = Decimal(str(cuota['capital_programado']))
        interes_prog = Decimal(str(cuota['interes_programado']))
        total_prog = Decimal(str(cuota['total_programado']))
        capital_pag = Decimal(str(cuota.get('capital_pagado', 0)))
        interes_pag = Decimal(str(cuota.get('interes_pagado', 0)))
    else:
        id_cuota = cuota['ID_Cuota']
        numero_cuota = cuota['numero_cuota']
        capital_prog = Decimal(str(cuota['capital_programado']))
        interes_prog = Decimal(str(cuota['interes_programado']))
        total_prog = Decimal(str(cuota['total_programado']))
        capital_pag = Decimal(str(cuota.get('capital_pagado', 0)))
        interes_pag = Decimal(str(cuota.get('interes_pagado', 0)))

    monto_pagado_d = Decimal(str(monto_pagado))

    if tipo_pago == "completo":
        nuevo_capital_pagado = capital_prog
        nuevo_interes_pagado = interes_prog
        nuevo_total_pagado = total_prog
        nuevo_estado = 'pagado'
        monto_sobrante = Decimal('0')
    else:
        # aplicar a interés primero
        interes_faltante = interes_prog - interes_pag
        capital_faltante = capital_prog - capital_pag

        nuevo_interes_pagado = interes_pag
        nuevo_capital_pagado = capital_pag

        if interes_faltante > 0:
            if monto_pagado_d >= interes_faltante:
                nuevo_interes_pagado = interes_prog
                monto_pagado_d -= interes_faltante
            else:
                nuevo_interes_pagado = interes_pag + monto_pagado_d
                monto_pagado_d = Decimal('0')

        if monto_pagado_d > 0 and capital_faltante > 0:
            if monto_pagado_d >= capital_faltante:
                nuevo_capital_pagado = capital_prog
                monto_pagado_d -= capital_faltante
            else:
                nuevo_capital_pagado = capital_pag + monto_pagado_d
                monto_pagado_d = Decimal('0')

        nuevo_total_pagado = (nuevo_capital_pagado + nuevo_interes_pagado).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        if nuevo_total_pagado >= total_prog:
            nuevo_estado = 'pagado'
        elif nuevo_total_pagado > 0:
            nuevo_estado = 'parcial'
        else:
            nuevo_estado = 'pendiente'

        monto_sobrante = monto_pagado_d

    # actualizar cuota actual
    cursor.execute("""
        UPDATE CuotaPrestamo
        SET capital_pagado = %s, interes_pagado = %s, total_pagado = %s, estado = %s
        WHERE ID_Cuota = %s
    """, (float(nuevo_capital_pagado), float(nuevo_interes_pagado), float(nuevo_total_pagado), nuevo_estado, id_cuota))

    # SI ES PAGO PARCIAL: RECALCULAR DEUDA Y REGENERAR CRONOGRAMA
    if tipo_pago == "parcial" and monto_sobrante == 0:
        # Obtener datos actuales del préstamo
        cursor.execute("""
            SELECT p.monto, p.total_interes, p.monto_total_pagar, p.plazo, p.fecha_desembolso
            FROM Prestamo p
            WHERE p.ID_Prestamo = %s
        """, (id_prestamo,))
        prestamo = cursor.fetchone()
        
        if prestamo:
            # Calcular total pagado hasta ahora
            cursor.execute("""
                SELECT 
                    COALESCE(SUM(capital_pagado), 0) as capital_pagado_total,
                    COALESCE(SUM(interes_pagado), 0) as interes_pagado_total
                FROM CuotaPrestamo 
                WHERE ID_Prestamo = %s
            """, (id_prestamo,))
            totales = cursor.fetchone()
            
            capital_pagado_total = Decimal(str(totales['capital_pagado_total']))
            interes_pagado_total = Decimal(str(totales['interes_pagado_total']))
            
            # Calcular saldos pendientes
            capital_original = Decimal(str(prestamo['monto']))
            interes_original = Decimal(str(prestamo['total_interes']))
            monto_total_original = Decimal(str(prestamo['monto_total_pagar']))
            plazo_original = prestamo['plazo']
            
            capital_pendiente = capital_original - capital_pagado_total
            interes_pendiente = interes_original - interes_pagado_total
            monto_total_pendiente = capital_pendiente + interes_pendiente
            
            # Contar cuotas pendientes (incluyendo la actual que puede estar parcial)
            cursor.execute("""
                SELECT COUNT(*) as cuotas_pendientes
                FROM CuotaPrestamo 
                WHERE ID_Prestamo = %s AND estado != 'pagado'
            """, (id_prestamo,))
            cuotas_pendientes = cursor.fetchone()['cuotas_pendientes']
            
            if cuotas_pendientes > 0 and monto_total_pendiente > 0:
                # Eliminar todas las cuotas pendientes futuras
                cursor.execute("""
                    DELETE FROM CuotaPrestamo 
                    WHERE ID_Prestamo = %s AND estado != 'pagado' AND numero_cuota > %s
                """, (id_prestamo, numero_cuota))
                
                # Recalcular nueva cuota mensual
                nueva_cuota_mensual = (monto_total_pendiente / cuotas_pendientes).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                interes_por_cuota = (interes_pendiente / cuotas_pendientes).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                capital_por_cuota = (capital_pendiente / cuotas_pendientes).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                
                # Obtener la última fecha de pago para programar las nuevas cuotas
                cursor.execute("""
                    SELECT MAX(fecha_programada) as ultima_fecha
                    FROM CuotaPrestamo 
                    WHERE ID_Prestamo = %s
                """, (id_prestamo,))
                ultima_fecha = cursor.fetchone()['ultima_fecha']
                
                if not ultima_fecha:
                    ultima_fecha = fecha_pago
                
                # Generar nuevas cuotas para los meses restantes
                for i in range(1, cuotas_pendientes):
                    if i == cuotas_pendientes - 1:  # Última cuota
                        capital_cuota = capital_pendiente - (capital_por_cuota * (cuotas_pendientes - 1))
                        interes_cuota = interes_pendiente - (interes_por_cuota * (cuotas_pendientes - 1))
                        total_cuota = capital_cuota + interes_cuota
                    else:
                        capital_cuota = capital_por_cuota
                        interes_cuota = interes_por_cuota
                        total_cuota = nueva_cuota_mensual
                    
                    # Determinar fecha de pago
                    if id_grupo is not None:
                        fecha_nueva = obtener_reunion_mas_cercana_fin_mes(con, id_grupo, ultima_fecha, i)
                    else:
                        fecha_nueva = ultima_fecha + timedelta(days=30*i)
                    
                    nuevo_numero = numero_cuota + i
                    
                    cursor.execute("""
                        INSERT INTO CuotaPrestamo
                        (ID_Prestamo, numero_cuota, fecha_programada, capital_programado,
                         interes_programado, total_programado, estado, capital_pagado, interes_pagado, total_pagado)
                        VALUES (%s, %s, %s, %s, %s, %s, 'pendiente', 0, 0, 0)
                    """, (
                        id_prestamo, nuevo_numero, fecha_nueva,
                        float(capital_cuota), float(interes_cuota), float(total_cuota)
                    ))

    con.commit()
    cursor.close()
    return True, "Pago aplicado correctamente"
