import streamlit as st
from modulos.config.conexion import obtener_conexion
from datetime import date, datetime, timedelta
from decimal import Decimal

def generar_cronograma_pagos(id_prestamo, con):
    """Genera el cronograma de pagos basado en los datos del préstamo"""
    cursor = con.cursor()
    
    # Obtener datos del préstamo YA CALCULADOS
    cursor.execute("""
        SELECT p.ID_Prestamo, p.ID_Miembro, p.monto, p.total_interes, 
               p.plazo, p.fecha_desembolso, m.nombre, p.proposito
        FROM Prestamo p
        JOIN Miembro m ON p.ID_Miembro = m.ID_Miembro
        WHERE p.ID_Prestamo = %s
    """, (id_prestamo,))
    
    prestamo = cursor.fetchone()
    if not prestamo:
        return False
    
    id_prestamo, id_miembro, monto, total_interes, plazo, fecha_desembolso, nombre, proposito = prestamo
    
    # Calcular cuota mensual (debería ser igual a la del módulo préstamo)
    monto_total = Decimal(str(monto)) + Decimal(str(total_interes))
    cuota_mensual = monto_total / Decimal(str(plazo))
    cuota_mensual = round(cuota_mensual, 2)
    
    # Distribución mensual
    capital_mensual = Decimal(str(monto)) / Decimal(str(plazo))
    capital_mensual = round(capital_mensual, 2)
    
    interes_mensual = Decimal(str(total_interes)) / Decimal(str(plazo))
    interes_mensual = round(interes_mensual, 2)
    
    # Fechas - primer pago a 30 días del desembolso
    fecha_primer_pago = fecha_desembolso + timedelta(days=30)
    
    # Eliminar cronograma existente
    cursor.execute("DELETE FROM CuotaPrestamo WHERE ID_Prestamo = %s", (id_prestamo,))
    
    # Generar cronograma
    saldo_capital = Decimal(str(monto))
    
    for i in range(1, plazo + 1):
        # Ajustar última cuota por redondeo
        if i == plazo:
            capital_cuota = saldo_capital
            interes_cuota = Decimal(str(total_interes)) - (interes_mensual * (plazo - 1))
            total_cuota = capital_cuota + interes_cuota
        else:
            capital_cuota = capital_mensual
            interes_cuota = interes_mensual
            total_cuota = cuota_mensual
        
        # Fecha de pago - cada 30 días
        fecha_pago = fecha_primer_pago + timedelta(days=30*(i-1))
        
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
    return True

def aplicar_pago_parcial(id_prestamo, monto_pagado, fecha_pago, con):
    """Aplica un pago parcial y recalcula la deuda"""
    cursor = con.cursor()
    
    # Obtener la próxima cuota pendiente
    cursor.execute("""
        SELECT ID_Cuota, numero_cuota, capital_programado, interes_programado, total_programado,
               capital_pagado, interes_pagado, total_pagado, estado, fecha_programada
        FROM CuotaPrestamo 
        WHERE ID_Prestamo = %s AND estado != 'pagado'
        ORDER BY fecha_programada ASC
        LIMIT 1
    """, (id_prestamo,))
    
    cuota_actual = cursor.fetchone()
    
    if not cuota_actual:
        return False, "No hay cuotas pendientes"
    
    (id_cuota, numero_cuota, capital_prog, interes_prog, total_prog, 
     capital_pag, interes_pag, total_pag, estado, fecha_programada) = cuota_actual
    
    # Convertir a Decimal
    capital_prog = Decimal(str(capital_prog))
    interes_prog = Decimal(str(interes_prog))
    total_prog = Decimal(str(total_prog))
    capital_pag = Decimal(str(capital_pag or 0))
    interes_pag = Decimal(str(interes_pag or 0))
    total_pag = Decimal(str(total_pag or 0))
    monto_pagado = Decimal(str(monto_pagado))
    
    # Aplicar pago: primero a interés, luego a capital
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
    
    # Actualizar la cuota actual
    cursor.execute("""
        UPDATE CuotaPrestamo 
        SET capital_pagado = %s, interes_pagado = %s, total_pagado = %s, estado = %s
        WHERE ID_Cuota = %s
    """, (float(nuevo_capital_pagado), float(nuevo_interes_pagado), 
          float(nuevo_total_pagado), nuevo_estado, id_cuota))
    
    # Si sobró monto después de pagar la cuota actual, crear nueva cuota
    if monto_pagado > 0:
        # Obtener datos del préstamo para crear nueva cuota
        cursor.execute("""
            SELECT monto, total_interes, plazo 
            FROM Prestamo WHERE ID_Prestamo = %s
        """, (id_prestamo,))
        
        prestamo_data = cursor.fetchone()
        monto_total_prestamo, total_interes_prestamo, plazo_total = prestamo_data
        
        # Calcular saldos pendientes
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
            # Nueva fecha: 30 días después del pago actual
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
                  float(monto_pagado), 0, float(monto_pagado)))
    
    con.commit()
    return True, "Pago aplicado correctamente"

def mostrar_pago_prestamo():
    st.header("💵 Sistema de Pagos de Préstamo")
    
    try:
        con = obtener_conexion()
        cursor = con.cursor()
        
        # Cargar préstamos activos
        cursor.execute("""
            SELECT p.ID_Prestamo, p.ID_Miembro, p.monto, p.total_interes, 
                   p.plazo, p.fecha_desembolso, m.nombre, p.proposito
            FROM Prestamo p
            JOIN Miembro m ON p.ID_Miembro = m.ID_Miembro
            WHERE p.ID_Estado_prestamo != 3  -- Excluir cancelados
        """)
        
        prestamos = cursor.fetchall()
        
        if not prestamos:
            st.warning("⚠️ No hay préstamos activos registrados.")
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
        
        # Mostrar información del préstamo
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Monto del Préstamo", f"${prestamo_info[2]:,.2f}")
        with col2:
            st.metric("Interés Total", f"${prestamo_info[3]:,.2f}")
        with col3:
            st.metric("Plazo", f"{prestamo_info[4]} meses")
        
        st.info(f"**Propósito:** {prestamo_info[7]} | **Fecha desembolso:** {prestamo_info[5]}")
        
        # Calcular información de cuotas
        monto_total = prestamo_info[2] + prestamo_info[3]
        cuota_mensual = monto_total / prestamo_info[4]
        
        st.success(f"**📊 Información de pagos:** Cuota mensual: ${cuota_mensual:,.2f} | Total a pagar: ${monto_total:,.2f}")
        
        # Verificar si existe cronograma
        cursor.execute("""
            SELECT COUNT(*) FROM CuotaPrestamo WHERE ID_Prestamo = %s
        """, (id_prestamo,))
        
        tiene_cronograma = cursor.fetchone()[0] > 0
        
        if not tiene_cronograma:
            st.info("📅 Este préstamo no tiene cronograma de pagos generado.")
            if st.button("🔄 Generar Cronograma de Pagos", type="primary"):
                if generar_cronograma_pagos(id_prestamo, con):
                    st.success("✅ Cronograma generado correctamente!")
                    st.rerun()
                else:
                    st.error("❌ Error al generar cronograma")
            return
        
        # Formulario para pago parcial
        st.subheader("💰 Registrar Pago Parcial")
        
        with st.form("form_pago_parcial"):
            # Obtener cuota actual pendiente
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
                
                st.write(f"**Cuota actual:** #{numero_cuota}")
                st.write(f"**Total programado:** ${total_programado:,.2f}")
                st.write(f"**Pagado hasta ahora:** ${total_pagado or 0:,.2f}")
                st.write(f"**Pendiente:** ${pendiente_actual:,.2f}")
                st.write(f"**Fecha programada:** {fecha_programada}")
            
            fecha_pago = st.date_input(
                "Fecha del pago:",
                value=date.today()
            )
            
            monto_pago = st.number_input(
                "Monto a pagar:",
                min_value=0.01,
                max_value=float(pendiente_actual) if cuota_actual else 10000.0,
                value=float(pendiente_actual) if cuota_actual else 0.0,
                step=10.0,
                format="%.2f"
            )
            
            enviar = st.form_submit_button("💾 Registrar Pago Parcial")
            
            if enviar:
                if monto_pago <= 0:
                    st.warning("⚠️ El monto debe ser mayor a cero.")
                else:
                    try:
                        success, mensaje = aplicar_pago_parcial(id_prestamo, monto_pago, fecha_pago, con)
                        
                        if success:
                            st.success(f"✅ {mensaje}")
                            
                            # Registrar en tabla PagoPrestamo
                            cursor.execute("""
                                INSERT INTO PagoPrestamo 
                                (ID_Prestamo, ID_Reunion, fecha_pago, monto_capital, monto_interes, total_cancelado)
                                VALUES (%s, %s, %s, %s, %s, %s)
                            """, (id_prestamo, None, fecha_pago, 0, 0, float(monto_pago)))
                            
                            con.commit()
                            st.rerun()
                        else:
                            st.error(f"❌ {mensaje}")
                            
                    except Exception as e:
                        con.rollback()
                        st.error(f"❌ Error al procesar el pago: {e}")
        
        # Estadísticas del préstamo
        st.subheader("📊 Resumen de Pagos")
        
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
            st.metric("Cuotas Pagadas", f"{stats[3]}")
        with col2:
            st.metric("Total Pagado", f"${stats[2] or 0:,.2f}")
            st.metric("Cuotas Parciales", f"{stats[4]}")
        with col3:
            pendiente = stats[1] - (stats[2] or 0)
            st.metric("Total Pendiente", f"${pendiente:,.2f}")
            st.metric("Cuotas Pendientes", f"{stats[5]}")
    
    except Exception as e:
        st.error(f"❌ Error general: {e}")
    
    finally:
        if "cursor" in locals():
            cursor.close()
        if "con" in locals():
            con.close()
