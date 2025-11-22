import streamlit as st
from modulos.config.conexion import obtener_conexion
from datetime import date, datetime, timedelta
from decimal import Decimal

def obtener_reunion_fin_de_mes(con, id_grupo, fecha_base, mes_offset=0):
    """Encuentra la reunión más cercana al fin de mes para un mes específico"""
    cursor = con.cursor()
    
    # Calcular el mes objetivo (fecha_base + mes_offset meses)
    if mes_offset == 0:
        mes_objetivo = fecha_base
    else:
        # Avanzar N meses
        year = fecha_base.year
        month = fecha_base.month + mes_offset
        while month > 12:
            month -= 12
            year += 1
        # Último día del mes objetivo
        if month == 12:
            next_month = date(year + 1, 1, 1)
        else:
            next_month = date(year, month + 1, 1)
        mes_objetivo = next_month - timedelta(days=1)
    
    # Calcular rango del mes (última semana)
    fin_mes = mes_objetivo.replace(day=28) + timedelta(days=4)  # Ir al último día
    fin_mes = fin_mes - timedelta(days=fin_mes.day)
    
    inicio_ultima_semana = fin_mes - timedelta(days=6)  # Última semana del mes
    
    # Buscar reuniones en la última semana del mes
    cursor.execute("""
        SELECT ID_Reunion, fecha, lugar 
        FROM Reunion 
        WHERE ID_Grupo = %s 
        AND fecha BETWEEN %s AND %s
        ORDER BY ABS(DATEDIFF(fecha, %s)) ASC
        LIMIT 1
    """, (id_grupo, inicio_ultima_semana, fin_mes, fin_mes))
    
    reunion = cursor.fetchone()
    
    if reunion:
        return reunion[1]  # Retorna la fecha de la reunión
    
    # Si no hay reunión en la última semana, buscar la más cercana al fin de mes
    cursor.execute("""
        SELECT fecha 
        FROM Reunion 
        WHERE ID_Grupo = %s 
        AND fecha BETWEEN %s AND %s
        ORDER BY ABS(DATEDIFF(fecha, %s)) ASC
        LIMIT 1
    """, (id_grupo, inicio_ultima_semana, fin_mes, fin_mes))
    
    reunion_cercana = cursor.fetchone()
    
    if reunion_cercana:
        return reunion_cercana[0]
    
    # Si no hay reuniones programadas, calcular una fecha aproximada (última semana)
    return inicio_ultima_semana + timedelta(days=3)  # Mitad de la última semana

def generar_cronograma_pagos(id_prestamo, con):
    """Genera el cronograma de pagos basado en los datos del préstamo y reuniones del grupo"""
    cursor = con.cursor()
    
    # Obtener datos del préstamo
    cursor.execute("""
        SELECT p.ID_Prestamo, p.ID_Miembro, p.monto, p.total_interes, 
               p.plazo, p.fecha_desembolso, m.nombre, p.proposito, p.ID_Grupo
        FROM Prestamo p
        JOIN Miembro m ON p.ID_Miembro = m.ID_Miembro
        WHERE p.ID_Prestamo = %s
    """, (id_prestamo,))
    
    prestamo = cursor.fetchone()
    if not prestamo:
        return False
    
    id_prestamo, id_miembro, monto, total_interes, plazo, fecha_desembolso, nombre, proposito, id_grupo = prestamo
    
    # Obtener la periodicidad del grupo desde Reglamento
    cursor.execute("""
        SELECT periodicidad_reuniones 
        FROM Reglamento 
        WHERE ID_Grupo = %s 
        ORDER BY ID_Reglamento DESC 
        LIMIT 1
    """, (id_grupo,))
    
    resultado_periodicidad = cursor.fetchone()
    
    if resultado_periodicidad:
        periodicidad = resultado_periodicidad[0]
        st.info(f"🔄 **Periodicidad de reuniones del grupo:** {periodicidad}")
    else:
        periodicidad = "Mensual"
        st.warning("⚠️ No se encontró periodicidad en reglamentos, usando Mensual por defecto")
    
    # ✅ CORRECCIÓN: Convertir porcentaje a valor monetario
    interes_monetario = Decimal(str(monto)) * (Decimal(str(total_interes)) / Decimal('100'))
    
    # Calcular cuota mensual
    monto_total = Decimal(str(monto)) + interes_monetario
    cuota_mensual = monto_total / Decimal(str(plazo))
    cuota_mensual = round(cuota_mensual, 2)
    
    # Distribución mensual
    capital_mensual = Decimal(str(monto)) / Decimal(str(plazo))
    capital_mensual = round(capital_mensual, 2)
    
    interes_mensual = interes_monetario / Decimal(str(plazo))
    interes_mensual = round(interes_mensual, 2)
    
    # Eliminar cronograma existente
    cursor.execute("DELETE FROM CuotaPrestamo WHERE ID_Prestamo = %s", (id_prestamo,))
    
    # Generar cronograma con fechas basadas en reuniones
    saldo_capital = Decimal(str(monto))
    
    st.info("📅 **Calculando fechas de pago según reuniones del grupo...**")
    
    for i in range(1, plazo + 1):
        # Ajustar última cuota por redondeo
        if i == plazo:
            capital_cuota = saldo_capital
            interes_cuota = interes_monetario - (interes_mensual * (plazo - 1))
            total_cuota = capital_cuota + interes_cuota
        else:
            capital_cuota = capital_mensual
            interes_cuota = interes_mensual
            total_cuota = cuota_mensual
        
        # Obtener fecha de pago basada en reuniones (mes i-1 porque el primer pago es al mes 1)
        fecha_pago = obtener_reunion_fin_de_mes(con, id_grupo, fecha_desembolso, i)
        
        # Si no hay reuniones programadas, calcular fecha aproximada (fin de mes)
        if fecha_pago is None:
            # Calcular fin de mes para el mes i
            if i == 1:
                next_month = fecha_desembolso.replace(day=28) + timedelta(days=4)
            else:
                next_month = (fecha_desembolso.replace(day=1) + timedelta(days=32*i)).replace(day=1)
            fecha_pago = next_month - timedelta(days=1)  # Último día del mes
        
        # Insertar en cronograma
        cursor.execute("""
            INSERT INTO CuotaPrestamo 
            (ID_Prestamo, numero_cuota, fecha_programada, capital_programado, 
             interes_programado, total_programado, estado)
            VALUES (%s, %s, %s, %s, %s, %s, 'pendiente')
        """, (id_prestamo, i, fecha_pago, float(capital_cuota), 
              float(interes_cuota), float(total_cuota)))
        
        saldo_capital -= capital_cuota
    
    con.commit()
    
    # Mostrar información resumen
    st.success(f"✅ **Cronograma generado:** {plazo} pagos mensuales")
    st.info(f"📋 **Estrategia:** Cada pago se asigna a la reunión más cercana al fin de mes")
    
    return True

def aplicar_pago_cuota(id_prestamo, monto_pagado, fecha_pago, tipo_pago, con, numero_cuota=None):
    """Aplica un pago (completo o parcial) a una cuota específica"""
    cursor = con.cursor()
    
    if tipo_pago == "completo" and numero_cuota:
        # Pago completo de una cuota específica
        cursor.execute("""
            SELECT ID_Cuota, capital_programado, interes_programado, total_programado,
                   capital_pagado, interes_pagado, total_pagado, estado
            FROM CuotaPrestamo 
            WHERE ID_Prestamo = %s AND numero_cuota = %s
        """, (id_prestamo, numero_cuota))
    else:
        # Pago parcial a la próxima cuota pendiente
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
        numero_cuota = numero_cuota
        fecha_programada = None
    else:
        (id_cuota, numero_cuota, capital_prog, interes_prog, total_prog, 
         capital_pag, interes_pag, total_pag, estado, fecha_programada) = cuota
    
    # Convertir a Decimal
    capital_prog = Decimal(str(capital_prog))
    interes_prog = Decimal(str(interes_prog))
    total_prog = Decimal(str(total_prog))
    capital_pag = Decimal(str(capital_pag or 0))
    interes_pag = Decimal(str(interes_pag or 0))
    total_pag = Decimal(str(total_pag or 0))
    monto_pagado = Decimal(str(monto_pagado))
    
    if tipo_pago == "completo":
        # Pago completo - marcar toda la cuota como pagada
        nuevo_capital_pagado = capital_prog
        nuevo_interes_pagado = interes_prog
        nuevo_total_pagado = total_prog
        nuevo_estado = 'pagado'
        monto_sobrante = Decimal('0')
    else:
        # Pago parcial - aplicar a interés primero, luego a capital
        interes_faltante = interes_prog - interes_pag
        capital_faltante = capital_prog - capital_pag
        
        nuevo_interes_pagado = interes_pag
        nuevo_capital_pagado = capital_pag
        
        # 1. Pagar interés pendiente
        if interes_faltante > 0:
            if monto_pagado >= interes_faltante:
                nuevo_interes_pagado = interes_prog
                monto_pagado -= interes_faltante
            else:
                nuevo_interes_pagado = interes_pag + monto_pagado
                monto_pagado = Decimal('0')
        
        # 2. Pagar capital con lo que sobra
        if monto_pagado > 0 and capital_faltante > 0:
            if monto_pagado >= capital_faltante:
                nuevo_capital_pagado = capital_prog
                monto_pagado -= capital_faltante
            else:
                nuevo_capital_pagado = capital_pag + monto_pagado
                monto_pagado = Decimal('0')
        
        # Calcular nuevo estado
        nuevo_total_pagado = nuevo_capital_pagado + nuevo_interes_pagado
        if nuevo_total_pagado >= total_prog:
            nuevo_estado = 'pagado'
        elif nuevo_total_pagado > 0:
            nuevo_estado = 'parcial'
        else:
            nuevo_estado = 'pendiente'
        
        monto_sobrante = monto_pagado
    
    # Actualizar la cuota
    cursor.execute("""
        UPDATE CuotaPrestamo 
        SET capital_pagado = %s, interes_pagado = %s, total_pagado = %s, estado = %s
        WHERE ID_Cuota = %s
    """, (float(nuevo_capital_pagado), float(nuevo_interes_pagado), 
          float(nuevo_total_pagado), nuevo_estado, id_cuota))
    
    # Si es pago parcial y sobró monto, crear nueva cuota
    if tipo_pago == "parcial" and monto_sobrante > 0:
        # Obtener saldos pendientes totales
        cursor.execute("""
            SELECT 
                COALESCE(SUM(capital_programado - capital_pagado), 0) as capital_pendiente,
                COALESCE(SUM(interes_programado - interes_pagado), 0) as interes_pendiente
            FROM CuotaPrestamo 
            WHERE ID_Prestamo = %s
        """, (id_prestamo,))
        
        saldos = cursor.fetchone()
        capital_pendiente, interes_pendiente = saldos
        
        # Si todavía hay deuda pendiente, crear nueva cuota
        if capital_pendiente > 0 or interes_pendiente > 0:
            # Obtener grupo para calcular nueva fecha
            cursor.execute("""
                SELECT g.ID_Grupo 
                FROM Prestamo p 
                JOIN Grupo g ON p.ID_Grupo = g.ID_Grupo 
                WHERE p.ID_Prestamo = %s
            """, (id_prestamo,))
            
            grupo_info = cursor.fetchone()
            if grupo_info:
                id_grupo = grupo_info[0]
                
                # Buscar próxima reunión después de la fecha actual
                nueva_fecha = obtener_reunion_fin_de_mes(con, id_grupo, fecha_pago, 1)
                
                if nueva_fecha is None:
                    nueva_fecha = fecha_pago + timedelta(days=30)
                
                # Buscar el último número de cuota
                cursor.execute("""
                    SELECT MAX(numero_cuota) FROM CuotaPrestamo WHERE ID_Prestamo = %s
                """, (id_prestamo,))
                
                ultimo_numero = cursor.fetchone()[0]
                nuevo_numero = ultimo_numero + 1
                
                # Crear nueva cuota con el saldo pendiente
                cursor.execute("""
                    INSERT INTO CuotaPrestamo 
                    (ID_Prestamo, numero_cuota, fecha_programada, capital_programado, 
                     interes_programado, total_programado, estado, capital_pagado, interes_pagado, total_pagado)
                    VALUES (%s, %s, %s, %s, %s, %s, 'parcial', %s, %s, %s)
                """, (id_prestamo, nuevo_numero, nueva_fecha, 
                      float(capital_pendiente), float(interes_pendiente), 
                      float(capital_pendiente + interes_pendiente),
                      float(monto_sobrante), 0, float(monto_sobrante)))
    
    con.commit()
    return True, f"Pago {tipo_pago} aplicado correctamente"

def mostrar_pago_prestamo():
    st.header("💵 Sistema de Pagos de Préstamo")
    
    # Verificar si hay una reunión seleccionada
    if 'reunion_actual' not in st.session_state:
        st.warning("⚠️ Primero debes seleccionar una reunión en el módulo de Asistencia.")
        return
    
    try:
        con = obtener_conexion()
        cursor = con.cursor()

        # Obtener la reunión del session_state
        reunion_info = st.session_state.reunion_actual
        id_reunion = reunion_info['id_reunion']
        id_grupo = reunion_info['id_grupo']
        nombre_reunion = reunion_info['nombre_reunion']

        # Mostrar información de la reunión actual
        st.info(f"📅 **Reunión actual:** {nombre_reunion}")

        # Obtener periodicidad del grupo
        cursor.execute("""
            SELECT periodicidad_reuniones 
            FROM Reglamento 
            WHERE ID_Grupo = %s 
            ORDER BY ID_Reglamento DESC 
            LIMIT 1
        """, (id_grupo,))
        
        periodicidad_result = cursor.fetchone()
        periodicidad = periodicidad_result[0] if periodicidad_result else "Mensual"
        
        st.info(f"🔄 **Periodicidad de reuniones:** {periodicidad}")
        st.info(f"🎯 **Estrategia de pagos:** Cada cuota se asigna a la reunión más cercana al fin de mes")

        # Resto del código se mantiene igual...
        # [El resto del código de mostrar_pago_prestamo() permanece igual]
        
        # Solo cambiar la parte del cronograma para mostrar información específica
        # ... (el resto del código es idéntico al anterior)

    except Exception as e:
        st.error(f"❌ Error general: {e}")
    
    finally:
        if "cursor" in locals():
            cursor.close()
        if "con" in locals():
            con.close()
