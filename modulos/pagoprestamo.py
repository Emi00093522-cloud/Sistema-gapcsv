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
    fin_mes = mes_objetivo.replace(day=28) + timedelta(days=4)
    fin_mes = fin_mes - timedelta(days=fin_mes.day)
    
    inicio_ultima_semana = fin_mes - timedelta(days=6)
    
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
        return reunion[1]
    
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
    """Genera el cronograma de pagos basado en los datos REALES del préstamo"""
    cursor = con.cursor()
    
    # Obtener datos REALES del préstamo - EXACTAMENTE como se registraron
    cursor.execute("""
        SELECT 
            p.ID_Prestamo, 
            p.ID_Miembro, 
            p.monto_solicitado,
            p.tasa_interes,
            p.plazo,
            p.fecha_aprobacion,
            m.nombre, 
            p.proposito,
            p.ID_Grupo,
            p.cuota_mensual,
            p.monto_total_pagar,
            p.total_interes
        FROM Prestamo p
        JOIN Miembro m ON p.ID_Miembro = m.ID_Miembro
        WHERE p.ID_Prestamo = %s
    """, (id_prestamo,))
    
    prestamo = cursor.fetchone()
    if not prestamo:
        return False
    
    # Desempaquetar los datos REALES
    (id_prestamo, id_miembro, monto_solicitado, tasa_interes, plazo, 
     fecha_aprobacion, nombre, proposito, id_grupo, cuota_mensual, 
     monto_total_pagar, total_interes) = prestamo
    
    # Obtener frecuencia de reuniones del grupo
    try:
        cursor.execute("""
            SELECT frecuencia_reunion 
            FROM Reglamento 
            WHERE ID_Grupo = %s 
            ORDER BY ID_Reglamento DESC 
            LIMIT 1
        """, (id_grupo,))
        
        resultado_frecuencia = cursor.fetchone()
        frecuencia = resultado_frecuencia[0] if resultado_frecuencia else "Mensual"
        
    except Exception as e:
        frecuencia = "Mensual"
    
    # Eliminar cronograma existente
    cursor.execute("DELETE FROM CuotaPrestamo WHERE ID_Prestamo = %s", (id_prestamo,))
    
    # Calcular distribución de capital e interés por cuota
    capital_por_cuota = Decimal(str(monto_solicitado)) / Decimal(str(plazo))
    interes_por_cuota = Decimal(str(total_interes)) / Decimal(str(plazo))
    
    # Generar cronograma con fechas basadas en reuniones
    saldo_capital = Decimal(str(monto_solicitado))
    
    for i in range(1, plazo + 1):
        # Calcular capital e interés para esta cuota
        if i == plazo:  # Última cuota - ajustar por redondeo
            capital_cuota = saldo_capital
            interes_cuota = Decimal(str(total_interes)) - (interes_por_cuota * (plazo - 1))
        else:
            capital_cuota = capital_por_cuota
            interes_cuota = interes_por_cuota
        
        total_cuota = capital_cuota + interes_cuota
        
        # Obtener fecha de pago basada en reuniones (mes i)
        fecha_pago = obtener_reunion_fin_de_mes(con, id_grupo, fecha_aprobacion, i)
        
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
    st.info(f"🔄 **Frecuencia de reuniones:** {frecuencia}")
    
    return True

def recalcular_nueva_cuota(id_prestamo, monto_sobrante, fecha_pago, con):
    """Recalcula una nueva cuota después de un pago parcial con sobrante"""
    cursor = con.cursor()
    
    # Obtener datos del préstamo
    cursor.execute("""
        SELECT p.monto_solicitado, p.total_interes, p.plazo, p.ID_Grupo
        FROM Prestamo p WHERE p.ID_Prestamo = %s
    """, (id_prestamo,))
    
    prestamo_data = cursor.fetchone()
    if not prestamo_data:
        return False
    
    monto_solicitado, total_interes, plazo_original, id_grupo = prestamo_data
    
    # Calcular saldos pendientes totales
    cursor.execute("""
        SELECT 
            COALESCE(SUM(capital_programado - COALESCE(capital_pagado, 0)), 0) as capital_pendiente,
            COALESCE(SUM(interes_programado - COALESCE(interes_pagado, 0)), 0) as interes_pendiente,
            COUNT(*) as cuotas_pendientes
        FROM CuotaPrestamo 
        WHERE ID_Prestamo = %s AND estado != 'pagado'
    """, (id_prestamo,))
    
    saldos = cursor.fetchone()
    capital_pendiente, interes_pendiente, cuotas_pendientes = saldos
    
    # Agregar el monto sobrante al capital pendiente
    capital_pendiente += Decimal(str(monto_sobrante))
    
    # Buscar el último número de cuota
    cursor.execute("SELECT MAX(numero_cuota) FROM CuotaPrestamo WHERE ID_Prestamo = %s", (id_prestamo,))
    ultimo_numero = cursor.fetchone()[0]
    nuevo_numero = ultimo_numero + 1
    
    # Buscar próxima reunión para la nueva fecha
    nueva_fecha = obtener_reunion_fin_de_mes(con, id_grupo, fecha_pago, 1)
    if nueva_fecha is None:
        nueva_fecha = fecha_pago + timedelta(days=30)
    
    # Crear nueva cuota con el saldo pendiente
    cursor.execute("""
        INSERT INTO CuotaPrestamo 
        (ID_Prestamo, numero_cuota, fecha_programada, capital_programado, 
         interes_programado, total_programado, estado, capital_pagado, interes_pagado, total_pagado)
        VALUES (%s, %s, %s, %s, %s, %s, 'pendiente', 0, 0, 0)
    """, (id_prestamo, nuevo_numero, nueva_fecha, 
          float(capital_pendiente), float(interes_pendiente), 
          float(capital_pendiente + interes_pendiente)))
    
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
        recalcular_nueva_cuota(id_prestamo, monto_sobrante, fecha_pago, con)
    
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
            SELECT frecuencia_reunion 
            FROM Reglamento 
            WHERE ID_Grupo = %s 
            ORDER BY ID_Reglamento DESC 
            LIMIT 1
        """, (id_grupo,))
        
        frecuencia_result = cursor.fetchone()
        frecuencia = frecuencia_result[0] if frecuencia_result else "Mensual"
        
        st.info(f"🔄 **Frecuencia de reuniones del grupo:** {frecuencia}")

        # Cargar miembros que asistieron a esta reunión
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
        
        # Cargar préstamos activos SOLO de miembros presentes - USANDO DATOS REALES
        if ids_miembros_presentes:
            placeholders = ','.join(['%s'] * len(ids_miembros_presentes))
            cursor.execute(f"""
                SELECT 
                    p.ID_Prestamo, 
                    p.ID_Miembro, 
                    p.monto_solicitado,
                    p.tasa_interes,
                    p.plazo,
                    p.fecha_aprobacion,
                    m.nombre, 
                    p.proposito,
                    p.cuota_mensual,
                    p.monto_total_pagar,
                    p.total_interes
                FROM Prestamo p
                JOIN Miembro m ON p.ID_Miembro = m.ID_Miembro
                WHERE p.ID_Estado_prestamo != 3  -- Excluir cancelados
                AND p.ID_Miembro IN ({placeholders})
            """, ids_miembros_presentes)
        else:
            cursor.execute("""
                SELECT 
                    p.ID_Prestamo, 
                    p.ID_Miembro, 
                    p.monto_solicitado,
                    p.tasa_interes,
                    p.plazo,
                    p.fecha_aprobacion,
                    m.nombre, 
                    p.proposito,
                    p.cuota_mensual,
                    p.monto_total_pagar,
                    p.total_interes
                FROM Prestamo p
                JOIN Miembro m ON p.ID_Miembro = m.ID_Miembro
                WHERE p.ID_Estado_prestamo != 3
                AND 1=0
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
        
        # ✅ USAR DATOS REALES DEL PRÉSTAMO - SIN CÁLCULOS
        monto_solicitado = prestamo_info[2]
        tasa_interes = prestamo_info[3]
        plazo = prestamo_info[4]
        fecha_aprobacion = prestamo_info[5]
        cuota_mensual = prestamo_info[8]
        monto_total_pagar = prestamo_info[9]
        total_interes = prestamo_info[10]
        
        # Mostrar información del préstamo en un layout más organizado
        st.subheader("📋 RESUMEN DEL PRÉSTAMO")
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Información Básica**")
            st.write(f"• **Fecha aprobación:** {fecha_aprobacion}")
            st.write(f"• **Tasa interés:** {tasa_interes}%")
            st.write(f"• **Plazo:** {plazo} meses")
            st.write(f"• **Propósito:** {prestamo_info[7]}")
        
        with col2:
            st.markdown("**Montos**")
            st.write(f"• **Monto solicitado:** ${monto_solicitado:,.2f}")
            st.write(f"• **Interés total:** ${total_interes:,.2f}")
            st.write(f"• **Total a pagar:** ${monto_total_pagar:,.2f}")
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
        st.subheader("📅 PLAN DE PAGOS")
        st.markdown("---")
        
        # Crear tabla usando st.dataframe
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
            
            tabla_data.append({
                "Cuota": numero,
                "Fecha": fecha_prog,
                "Estado": f"{estado_emoji.get(estado, '⚪')} {estado.upper()}",
                "Capital": capital_mostrar,
                "Interés": interes_mostrar,
                "Total": total_mostrar
            })
        
        # Mostrar la tabla
        st.dataframe(tabla_data, use_container_width=True)
        
        # Calcular totales
        total_capital_pagado = sum(c[5] or 0 for c in cuotas)
        total_interes_pagado = sum(c[6] or 0 for c in cuotas)
        total_pagado = sum(c[7] or 0 for c in cuotas)
        
        st.markdown("---")
        st.markdown(f"**TOTAL:** ${monto_solicitado:,.2f} (capital) + ${total_interes:,.2f} (interés) = **${monto_total_pagar:,.2f}**")
        
        saldo_pendiente = monto_total_pagar - total_pagado
        if saldo_pendiente <= 0:
            st.success(f"**SALDO: $0 (COMPLETAMENTE PAGADO)** 🎉")
        else:
            st.warning(f"**SALDO PENDIENTE: ${saldo_pendiente:,.2f}**")
        
        # Sección de pagos
        st.subheader("💰 REGISTRAR PAGO")
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 💵 Pago Completo")
            with st.form("form_pago_completo"):
                # Seleccionar cuota para pago completo
                cursor.execute("""
                    SELECT numero_cuota, total_programado, total_pagado, fecha_programada
                    FROM CuotaPrestamo 
                    WHERE ID_Prestamo = %s AND estado != 'pagado'
                    ORDER BY numero_cuota
                """, (id_prestamo,))
                
                cuotas_pendientes = cursor.fetchall()
                
                if cuotas_pendientes:
                    cuotas_opciones = [f"Cuota {c[0]} - ${c[1]:,.2f} - {c[3]}" for c in cuotas_pendientes]
                    cuota_seleccionada = st.selectbox("Selecciona la cuota a pagar:", cuotas_opciones, key="completo")
                    
                    # Extraer número de cuota seleccionada
                    numero_cuota = int(cuota_seleccionada.split(" ")[1])
                    
                    fecha_pago_completo = st.date_input(
                        "Fecha del pago:",
                        value=date.today(),
                        key="fecha_completo"
                    )
                    
                    enviar_completo = st.form_submit_button("✅ Pagar Cuota Completa")
                    
                    if enviar_completo:
                        try:
                            # Obtener el monto total de la cuota
                            cuota_info = [c for c in cuotas_pendientes if c[0] == numero_cuota][0]
                            monto_cuota = cuota_info[1]
                            
                            success, mensaje = aplicar_pago_cuota(id_prestamo, monto_cuota, fecha_pago_completo, "completo", con, numero_cuota)
                            
                            if success:
                                # Registrar en tabla PagoPrestamo
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
        
        with col2:
            st.markdown("### 💳 Pago Parcial")
            with st.form("form_pago_parcial"):
                # Obtener cuota actual pendiente para pago parcial
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
                    pendiente_actual = total_programado - (total_pagado or 0)
                    
                    st.write(f"**Próxima cuota:** #{numero_cuota}")
                    st.write(f"**Total pendiente:** ${pendiente_actual:,.2f}")
                    st.write(f"**Fecha programada:** {fecha_programada}")
                    
                    fecha_pago_parcial = st.date_input(
                        "Fecha del pago:",
                        value=date.today(),
                        key="fecha_parcial"
                    )
                    
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
                                    # Registrar en tabla PagoPrestamo
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
        
        # Estadísticas rápidas
        st.subheader("📊 RESUMEN DE PAGOS")
        st.markdown("---")
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_cuotas,
                SUM(total_programado) as total_programado,
                SUM(total_pagado) as total_pagado,
                SUM(CASE WHEN estado = 'pagado' THEN 1 ELSE 0 END) as cuotas_pagadas,
                SUM(CASE WHEN estado = 'parcial' THEN 1 ELSE 0 END) as cuotas_parciales,
                SUM(CASE WHEN estado = 'pendiente' THEN 1 ELSE 0 END) as cuotas_pendientes
            FROM CuotaPrestamo 
            WHERE ID_Prestamo = %s
        """, (id_prestamo,))
        
        stats = cursor.fetchone()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Programado", f"${stats[1]:,.2f}")
            st.metric("Cuotas Pagadas", stats[3])
        with col2:
            st.metric("Total Pagado", f"${stats[2] or 0:,.2f}")
            st.metric("Cuotas Parciales", stats[4])
        with col3:
            pendiente = stats[1] - (stats[2] or 0)
            st.metric("Total Pendiente", f"${pendiente:,.2f}")
            st.metric("Cuotas Pendientes", stats[5])
    
    except Exception as e:
        st.error(f"❌ Error general: {e}")
    
    finally:
        if "cursor" in locals():
            cursor.close()
        if "con" in locals():
            con.close()
