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
        AND YEAR(fecha) = %s AND MONTH(fecha) = %s
        ORDER BY fecha DESC
        LIMIT 1
    """, (id_grupo, fin_mes.year, fin_mes.month))
    
    reunion_cercana = cursor.fetchone()
    
    if reunion_cercana:
        return reunion_cercana[0]
    
    # Si no hay reuniones programadas, usar fin de mes
    return fin_mes

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
    
    # Obtener información del grupo para determinar periodicidad
    cursor.execute("""
        SELECT nombre FROM Grupo WHERE ID_Grupo = %s
    """, (id_grupo,))
    
    grupo_info = cursor.fetchone()
    nombre_grupo = grupo_info[0] if grupo_info else f"Grupo {id_grupo}"
    
    # OBTENER LA FRECUENCIA DE REUNIONES DESDE REGLAMENTO (COLUMNA CORRECTA)
    try:
        cursor.execute("""
            SELECT fecuencia_reunion 
            FROM Reglamento 
            WHERE ID_Grupo = %s 
            ORDER BY ID_Reglamento DESC 
            LIMIT 1
        """, (id_grupo,))
        
        resultado_frecuencia = cursor.fetchone()
        frecuencia = resultado_frecuencia[0] if resultado_frecuencia else "Mensual"
        st.info(f"🔄 **Frecuencia de reuniones del grupo:** {frecuencia}")
        
    except Exception as e:
        frecuencia = "Mensual"
        st.warning(f"⚠️ Error al obtener frecuencia de reuniones: {e}. Usando valor por defecto: Mensual")
    
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
        
        # Obtener fecha de pago basada en reuniones
        fecha_pago = obtener_reunion_fin_de_mes(con, id_grupo, fecha_desembolso, i)
        
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
    st.info(f"👥 **Grupo:** {nombre_grupo}")
    
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

        # Obtener frecuencia de reuniones del grupo
        cursor.execute("""
            SELECT fecuencia_reunion 
            FROM Reglamento 
            WHERE ID_Grupo = %s 
            ORDER BY ID_Reglamento DESC 
            LIMIT 1
        """, (id_grupo,))
        
        frecuencia_result = cursor.fetchone()
        frecuencia = frecuencia_result[0] if frecuencia_result else "Mensual"
        
        st.info(f"🔄 **Frecuencia de reuniones:** {frecuencia}")
        st.info(f"🎯 **Estrategia de pagos:** Cada cuota se asigna a la reunión más cercana al fin de mes")

        # -----------------------------
        # CARGAR MIEMBROS QUE ASISTIERON A ESTA REUNIÓN (SOLO LOS QUE MARCARON SI)
        # -----------------------------
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

        # Obtener IDs de miembros presentes para filtrar préstamos
        ids_miembros_presentes = [m[0] for m in miembros_presentes]
        
        # Cargar préstamos activos SOLO de miembros presentes
        if ids_miembros_presentes:
            placeholders = ','.join(['%s'] * len(ids_miembros_presentes))
            cursor.execute(f"""
                SELECT p.ID_Prestamo, p.ID_Miembro, p.monto, p.total_interes, 
                       p.plazo, p.fecha_desembolso, m.nombre, p.proposito
                FROM Prestamo p
                JOIN Miembro m ON p.ID_Miembro = m.ID_Miembro
                WHERE p.ID_Estado_prestamo != 3  -- Excluir cancelados
                AND p.ID_Miembro IN ({placeholders})
            """, ids_miembros_presentes)
        else:
            cursor.execute("""
                SELECT p.ID_Prestamo, p.ID_Miembro, p.monto, p.total_interes, 
                       p.plazo, p.fecha_desembolso, m.nombre, p.proposito
                FROM Prestamo p
                JOIN Miembro m ON p.ID_Miembro = m.ID_Miembro
                WHERE p.ID_Estado_prestamo != 3
                AND 1=0  -- No mostrar nada si no hay miembros presentes
            """)
        
        prestamos = cursor.fetchall()
        
        if not prestamos:
            st.warning("⚠️ No hay préstamos activos para los miembros presentes en esta reunión.")
            return
        
        # Lista de préstamos
        prestamos_dict = {
            f"Préstamo {p[0]} - {p[6]} - ${p[2]:,.2f} - {p[4]} meses": p[0]
            for p in prestamos
        }
        
        # Selección de préstamo
        prestamo_sel = st.selectbox(
            "Selecciona el préstamo:",
            list(prestamos_dict.keys())
        )
        
        id_prestamo = prestamos_dict[prestamo_sel]
        prestamo_info = [p for p in prestamos if p[0] == id_prestamo][0]
        
        # ✅ CORRECCIÓN: Calcular interés monetario real
        monto = prestamo_info[2]
        total_interes_porcentaje = prestamo_info[3]  # Este es el porcentaje
        plazo = prestamo_info[4]
        
        # Convertir porcentaje a valor monetario
        interes_monetario = monto * (total_interes_porcentaje / 100)
        monto_total = monto + interes_monetario
        cuota_mensual = monto_total / plazo
        
        # ✅ Tasa real (ya es el porcentaje)
        tasa_real = total_interes_porcentaje
        
        # Mostrar información del préstamo en un layout más organizado
        st.subheader("📋 RESUMEN DEL PRÉSTAMO")
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Información Básica**")
            st.write(f"• **Fecha inicio:** {prestamo_info[5]}")
            st.write(f"• **Tasa interés:** {tasa_real:.1f}%")
            st.write(f"• **Plazo:** {plazo} meses")
            st.write(f"• **Propósito:** {prestamo_info[7]}")
            st.write(f"• **Reuniones:** {frecuencia}")
        
        with col2:
            st.markdown("**Montos**")
            st.write(f"• **Monto préstamo:** ${monto:,.2f}")
            st.write(f"• **Interés total:** ${interes_monetario:,.2f}")
            st.write(f"• **Total a pagar:** ${monto_total:,.2f}")
            st.write(f"• **Cuota mensual:** ${cuota_mensual:,.2f}")
        
        st.markdown("---")
        
        # Verificar si existe cronograma
        cursor.execute("""
            SELECT COUNT(*) FROM CuotaPrestamo WHERE ID_Prestamo = %s
        """, (id_prestamo,))
        
        tiene_cronograma = cursor.fetchone()[0] > 0
        
        if not tiene_cronograma:
            st.info("📅 Este préstamo no tiene cronograma de pagos generado.")
            if st.button("🔄 Generar Plan de Pagos", type="primary"):
                if generar_cronograma_pagos(id_prestamo, con):
                    st.success("✅ Plan de pagos generado correctamente!")
                    st.rerun()
                else:
                    st.error("❌ Error al generar plan de pagos")
            return
        
        # Obtener todas las cuotas para mostrar
        cursor.execute("""
            SELECT numero_cuota, fecha_programada, capital_programado, 
                   interes_programado, total_programado, capital_pagado, 
                   interes_pagado, total_pagado, estado
            FROM CuotaPrestamo
            WHERE ID_Prestamo = %s
            ORDER BY fecha_programada ASC
        """, (id_prestamo,))
        
        cuotas = cursor.fetchall()
        
        # Mostrar plan de pagos en formato tabla simple
        st.subheader("📅 PLAN DE PAGOS - BASADO EN REUNIONES DEL GRUPO")
        st.markdown("---")
        
        # Crear tabla usando st.dataframe en lugar de HTML
        tabla_data = []
        for cuota in cuotas:
            numero, fecha_prog, capital_prog, interes_prog, total_prog, \
            capital_pag, interes_pag, total_pag, estado = cuota
            
            capital_pag = capital_pag or 0
            interes_pag = interes_pag or 0
            total_pag = total_pag or 0
            
            # Determinar emoji para el estado
            estado_emoji = {
                'pendiente': '⚪',
                'parcial': '🟡', 
                'pagado': '🟢'
            }
            
            # Mostrar montos pagados si hay pago, sino los programados
            if estado == 'pagado':
                capital_mostrar = f"${capital_pag:,.2f}"
                interes_mostrar = f"${interes_pag:,.2f}"
                total_mostrar = f"${total_pag:,.2f}"
            elif estado == 'parcial':
                capital_mostrar = f"${capital_pag:,.2f} de ${capital_prog:,.2f}"
                interes_mostrar = f"${interes_pag:,.2f} de ${interes_prog:,.2f}"
                total_mostrar = f"${total_pag:,.2f} de ${total_prog:,.2f}"
            else:
                capital_mostrar = f"${capital_prog:,.2f}"
                interes_mostrar = f"${interes_prog:,.2f}"
                total_mostrar = f"${total_prog:,.2f}"
            
            # ✅ AQUÍ SE MUESTRAN LAS FECHAS CALCULADAS SEGÚN LAS REUNIONES
            tabla_data.append({
                "Cuota": numero,
                "Fecha Pago": fecha_prog,  # Esta es la fecha calculada basada en reuniones
                "Estado": f"{estado_emoji.get(estado, '⚪')} {estado.upper()}",
                "Capital": capital_mostrar,
                "Interés": interes_mostrar,
                "Total": total_mostrar
            })

        # Mostrar la tabla usando st.dataframe
        if tabla_data:
            st.dataframe(tabla_data, use_container_width=True)
            
            # Mostrar información adicional sobre las fechas
            st.info("📅 **Nota:** Las fechas de pago se asignan automáticamente a las reuniones más cercanas al fin de cada mes")
        else:
            st.warning("No hay cuotas generadas para este préstamo")
        
        # El resto del código se mantiene igual...
        # [Aquí iría el resto del código de pagos completos, parciales y estadísticas]
        
    except Exception as e:
        st.error(f"❌ Error general: {e}")
    
    finally:
        if "cursor" in locals():
            cursor.close()
        if "con" in locals():
            con.close()
