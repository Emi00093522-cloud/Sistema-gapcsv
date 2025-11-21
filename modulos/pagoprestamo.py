import streamlit as st
from modulos.config.conexion import obtener_conexion
from datetime import date, datetime, timedelta
from decimal import Decimal

def calcular_cuotas_prestamo(id_prestamo, con):
    """Calcula y genera las cuotas programadas para un préstamo"""
    cursor = con.cursor()
    
    # Obtener datos del préstamo
    cursor.execute("""
        SELECT monto, total_interes, plazo, fecha_desembolso
        FROM Prestamo WHERE ID_Prestamo = %s
    """, (id_prestamo,))
    
    prestamo = cursor.fetchone()
    if not prestamo:
        return False
    
    monto, tasa_interes, plazo, fecha_desembolso = prestamo
    
    # Configurar fechas automáticamente
    fecha_primer_pago = fecha_desembolso + timedelta(days=30)  # Primer pago a 30 días
    dia_pago = fecha_primer_pago.day  # Usar el día del primer pago
    
    # Eliminar cuotas existentes
    cursor.execute("DELETE FROM CuotaPrestamo WHERE ID_Prestamo = %s", (id_prestamo,))
    
    # Calcular cuota usando fórmula de cuota fija
    tasa_mensual_decimal = Decimal(str(tasa_interes))
    factor = (1 + tasa_mensual_decimal) ** plazo
    cuota_mensual = (Decimal(str(monto)) * tasa_mensual_decimal * factor) / (factor - 1)
    cuota_mensual = round(cuota_mensual, 2)
    
    saldo_capital = Decimal(str(monto))
    
    # Generar cuotas
    for i in range(1, plazo + 1):
        # Calcular interés y capital para esta cuota
        interes_cuota = round(saldo_capital * tasa_mensual_decimal, 2)
        capital_cuota = round(cuota_mensual - interes_cuota, 2)
        
        # Ajustar última cuota por redondeo
        if i == plazo:
            capital_cuota = saldo_capital
            cuota_mensual = capital_cuota + interes_cuota
        
        # Calcular fecha de pago (cada 30 días desde la fecha de primer pago)
        fecha_pago = fecha_primer_pago + timedelta(days=30*(i-1))
        
        # Insertar cuota
        cursor.execute("""
            INSERT INTO CuotaPrestamo 
            (ID_Prestamo, numero_cuota, fecha_programada, capital_programado, 
             interes_programado, total_programado, estado)
            VALUES (%s, %s, %s, %s, %s, %s, 'pendiente')
        """, (id_prestamo, i, fecha_pago, float(capital_cuota), 
              float(interes_cuota), float(cuota_mensual)))
        
        saldo_capital -= capital_cuota
    
    con.commit()
    return True

def aplicar_pago_cuotas(id_prestamo, monto_capital, monto_interes, fecha_pago, con):
    """Aplica el pago a las cuotas correspondientes"""
    cursor = con.cursor()
    
    # Obtener cuotas pendientes ordenadas por fecha
    cursor.execute("""
        SELECT ID_Cuota, capital_programado, interes_programado, total_programado,
               capital_pagado, interes_pagado, total_pagado, estado
        FROM CuotaPrestamo 
        WHERE ID_Prestamo = %s AND estado != 'pagado'
        ORDER BY fecha_programada ASC
    """, (id_prestamo,))
    
    cuotas = cursor.fetchall()
    
    capital_restante = Decimal(str(monto_capital))
    interes_restante = Decimal(str(monto_interes))
    
    for cuota in cuotas:
        if capital_restante <= 0 and interes_restante <= 0:
            break
            
        id_cuota, capital_prog, interes_prog, total_prog, capital_pag, interes_pag, total_pag, estado = cuota
        
        capital_prog = Decimal(str(capital_prog))
        interes_prog = Decimal(str(interes_prog))
        capital_pag = Decimal(str(capital_pag or 0))
        interes_pag = Decimal(str(interes_pag or 0))
        
        # Aplicar pago a intereses
        interes_faltante = interes_prog - interes_pag
        if interes_restante > 0 and interes_faltante > 0:
            interes_a_pagar = min(interes_restante, interes_faltante)
            interes_pag += interes_a_pagar
            interes_restante -= interes_a_pagar
        
        # Aplicar pago a capital
        capital_faltante = capital_prog - capital_pag
        if capital_restante > 0 and capital_faltante > 0:
            capital_a_pagar = min(capital_restante, capital_faltante)
            capital_pag += capital_a_pagar
            capital_restante -= capital_a_pagar
        
        # Calcular total pagado y estado
        total_pagado = capital_pag + interes_pag
        nuevo_estado = 'pagado' if total_pagado >= total_prog else 'parcial' if total_pagado > 0 else 'pendiente'
        
        # Actualizar cuota
        cursor.execute("""
            UPDATE CuotaPrestamo 
            SET capital_pagado = %s, interes_pagado = %s, total_pagado = %s, estado = %s
            WHERE ID_Cuota = %s
        """, (float(capital_pag), float(interes_pag), float(total_pagado), nuevo_estado, id_cuota))
    
    con.commit()
    return capital_restante, interes_restante

def recalcular_cuotas_restantes(id_prestamo, con):
    """Recalcula las cuotas pendientes después de un pago"""
    cursor = con.cursor()
    
    # Obtener datos del préstamo
    cursor.execute("""
        SELECT p.monto, p.total_interes, p.plazo, p.fecha_desembolso
        FROM Prestamo p WHERE p.ID_Prestamo = %s
    """, (id_prestamo,))
    
    prestamo = cursor.fetchone()
    if not prestamo:
        return False
    
    monto_total, tasa_interes, plazo_total, fecha_desembolso = prestamo
    
    # Obtener capital total pagado
    cursor.execute("""
        SELECT COALESCE(SUM(capital_pagado), 0) 
        FROM CuotaPrestamo 
        WHERE ID_Prestamo = %s
    """, (id_prestamo,))
    
    capital_pagado_total = cursor.fetchone()[0]
    saldo_capital = Decimal(str(monto_total)) - Decimal(str(capital_pagado_total))
    
    # Obtener cuotas pagadas y última cuota
    cursor.execute("""
        SELECT MAX(numero_cuota) 
        FROM CuotaPrestamo 
        WHERE ID_Prestamo = %s AND estado = 'pagado'
    """, (id_prestamo,))
    
    ultima_cuota_pagada = cursor.fetchone()[0] or 0
    cuotas_restantes = plazo_total - ultima_cuota_pagada
    
    if cuotas_restantes <= 0:
        return True
    
    # Obtener última fecha de pago de cuotas pagadas
    cursor.execute("""
        SELECT MAX(fecha_programada) 
        FROM CuotaPrestamo 
        WHERE ID_Prestamo = %s AND estado = 'pagado'
    """, (id_prestamo,))
    
    ultima_fecha_result = cursor.fetchone()[0]
    if ultima_fecha_result:
        ultima_fecha_pago = ultima_fecha_result
    else:
        # Si no hay cuotas pagadas, usar fecha actual
        ultima_fecha_pago = date.today()
    
    # Eliminar cuotas futuras no pagadas
    cursor.execute("""
        DELETE FROM CuotaPrestamo 
        WHERE ID_Prestamo = %s AND numero_cuota > %s AND estado != 'pagado'
    """, (id_prestamo, ultima_cuota_pagada))
    
    # Recalcular nuevas cuotas
    tasa_mensual_decimal = Decimal(str(tasa_interes))
    
    if cuotas_restantes > 0:
        factor = (1 + tasa_mensual_decimal) ** cuotas_restantes
        nueva_cuota = (saldo_capital * tasa_mensual_decimal * factor) / (factor - 1)
        nueva_cuota = round(nueva_cuota, 2)
    else:
        nueva_cuota = Decimal('0')
    
    # Generar nuevas cuotas
    for i in range(1, cuotas_restantes + 1):
        numero_cuota = ultima_cuota_pagada + i
        
        # Calcular interés y capital
        interes_cuota = round(saldo_capital * tasa_mensual_decimal, 2)
        capital_cuota = round(nueva_cuota - interes_cuota, 2)
        
        # Ajustar última cuota por redondeo
        if i == cuotas_restantes:
            capital_cuota = saldo_capital
            nueva_cuota = capital_cuota + interes_cuota
        
        # Calcular nueva fecha (30 días después de la última fecha)
        nueva_fecha = ultima_fecha_pago + timedelta(days=30*i)
        
        # Insertar nueva cuota
        cursor.execute("""
            INSERT INTO CuotaPrestamo 
            (ID_Prestamo, numero_cuota, fecha_programada, capital_programado, 
             interes_programado, total_programado, estado)
            VALUES (%s, %s, %s, %s, %s, %s, 'pendiente')
        """, (id_prestamo, numero_cuota, nueva_fecha, float(capital_cuota), 
              float(interes_cuota), float(nueva_cuota)))
        
        saldo_capital -= capital_cuota
    
    con.commit()
    return True

def mostrar_pago_prestamo():
    st.header("💵 Sistema de Pagos de Préstamo")
    
    try:
        con = obtener_conexion()
        cursor = con.cursor()
        
        # Cargar préstamos
        cursor.execute("""
            SELECT p.ID_Prestamo, p.ID_Miembro, p.monto, p.total_interes, 
                   p.plazo, p.fecha_desembolso, m.nombre, p.proposito
            FROM Prestamo p
            JOIN Miembro m ON p.ID_Miembro = m.ID_Miembro
            WHERE p.ID_Estado_prestamo != 3  -- Excluir préstamos cancelados
        """)
        
        prestamos = cursor.fetchall()
        
        if not prestamos:
            st.warning("⚠️ No hay préstamos activos registrados.")
            return
        
        prestamos_dict = {
            f"Préstamo {p[0]} - {p[6]} - ${p[2]:,.2f} - {p[4]} meses - {p[3]*100:.2f}% mensual": p[0]
            for p in prestamos
        }
        
        # Cargar reuniones
        cursor.execute("SELECT ID_Reunion, fecha FROM Reunion")
        reuniones = cursor.fetchall()
        
        reuniones_dict = {
            f"Reunión {r[0]} - {r[1]}": r[0]
            for r in reuniones
        } if reuniones else {"No hay reuniones": 0}
        
        # Selección de préstamo
        prestamo_sel = st.selectbox(
            "Selecciona el préstamo:",
            list(prestamos_dict.keys())
        )
        
        id_prestamo = prestamos_dict[prestamo_sel]
        
        # Mostrar información del préstamo
        prestamo_info = [p for p in prestamos if p[0] == id_prestamo][0]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Monto del Préstamo", f"${prestamo_info[2]:,.2f}")
        with col2:
            st.metric("Tasa de Interés", f"{prestamo_info[3]*100:.2f}% mensual")
        with col3:
            st.metric("Plazo", f"{prestamo_info[4]} meses")
        
        # Mostrar propósito y fecha de desembolso
        st.info(f"**Propósito:** {prestamo_info[7]} | **Fecha desembolso:** {prestamo_info[5]}")
        
        # Mostrar cuotas programadas
        st.subheader("📅 Cuotas Programadas")
        cursor.execute("""
            SELECT numero_cuota, fecha_programada, capital_programado, 
                   interes_programado, total_programado, capital_pagado, 
                   interes_pagado, total_pagado, estado
            FROM CuotaPrestamo
            WHERE ID_Prestamo = %s
            ORDER BY numero_cuota
        """, (id_prestamo,))
        
        cuotas = cursor.fetchall()
        
        if not cuotas:
            st.info("ℹ️ No hay cuotas programadas. El sistema calculará automáticamente las cuotas basándose en:")
            st.write(f"- **Monto:** ${prestamo_info[2]:,.2f}")
            st.write(f"- **Tasa:** {prestamo_info[3]*100:.2f}% mensual")
            st.write(f"- **Plazo:** {prestamo_info[4]} meses")
            st.write(f"- **Primer pago:** Aproximadamente 30 días después del desembolso ({prestamo_info[5]})")
            
            if st.button("🎯 Generar Cuotas Automáticamente", type="primary"):
                if calcular_cuotas_prestamo(id_prestamo, con):
                    st.success("✅ Cuotas generadas correctamente!")
                    st.rerun()
                else:
                    st.error("❌ Error al generar cuotas")
            return
        
        # Mostrar tabla de cuotas
        cuotas_data = []
        for cuota in cuotas:
            numero, fecha_prog, capital_prog, interes_prog, total_prog, \
            capital_pag, interes_pag, total_pag, estado = cuota
            
            capital_pag = capital_pag or 0
            interes_pag = interes_pag or 0
            total_pag = total_pag or 0
            
            # Determinar color según estado
            estado_color = {
                'pendiente': '⚪',
                'parcial': '🟡', 
                'pagado': '🟢'
            }
            
            cuotas_data.append({
                "Cuota": numero,
                "Fecha Programada": fecha_prog,
                "Capital Programado": f"${capital_prog:,.2f}",
                "Interés Programado": f"${interes_prog:,.2f}",
                "Total Programado": f"${total_prog:,.2f}",
                "Capital Pagado": f"${capital_pag:,.2f}",
                "Interés Pagado": f"${interes_pag:,.2f}",
                "Total Pagado": f"${total_pag:,.2f}",
                "Estado": f"{estado_color.get(estado, '⚪')} {estado.upper()}"
            })
        
        st.dataframe(cuotas_data, use_container_width=True)
        
        # Calcular totales
        cursor.execute("""
            SELECT 
                SUM(total_programado) as total_programado,
                SUM(total_pagado) as total_pagado,
                SUM(capital_programado) as capital_programado,
                SUM(capital_pagado) as capital_pagado,
                SUM(interes_programado) as interes_programado,
                SUM(interes_pagado) as interes_pagado
            FROM CuotaPrestamo 
            WHERE ID_Prestamo = %s
        """, (id_prestamo,))
        
        totales = cursor.fetchone()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Programado", f"${totales[0]:,.2f}" if totales[0] else "$0.00")
            st.metric("Capital Programado", f"${totales[2]:,.2f}" if totales[2] else "$0.00")
            st.metric("Interés Programado", f"${totales[4]:,.2f}" if totales[4] else "$0.00")
        with col2:
            total_pagado = totales[1] or 0
            capital_pagado = totales[3] or 0
            interes_pagado = totales[5] or 0
            st.metric("Total Pagado", f"${total_pagado:,.2f}")
            st.metric("Capital Pagado", f"${capital_pagado:,.2f}")
            st.metric("Interés Pagado", f"${interes_pagado:,.2f}")
        with col3:
            total_programado = totales[0] or 0
            pendiente = total_programado - total_pagado
            st.metric("Total Pendiente", f"${pendiente:,.2f}", delta=f"-${pendiente:,.2f}")
        
        # Formulario de pago
        st.subheader("💰 Registrar Pago")
        
        with st.form("form_pago_prestamo"):
            if reuniones_dict:
                reunion_sel = st.selectbox(
                    "Selecciona la reunión:",
                    list(reuniones_dict.keys())
                )
                id_reunion = reuniones_dict[reunion_sel]
            else:
                st.warning("No hay reuniones disponibles")
                id_reunion = None
            
            fecha_pago = st.date_input(
                "Fecha del pago:",
                value=date.today()
            )
            
            col1, col2 = st.columns(2)
            with col1:
                monto_capital = st.number_input(
                    "Monto a capital:",
                    min_value=0.00, format="%.2f", step=10.0
                )
            with col2:
                monto_interes = st.number_input(
                    "Monto a interés:",
                    min_value=0.00, format="%.2f", step=10.0
                )
            
            total_cancelado = monto_capital + monto_interes
            
            if total_cancelado > 0:
                st.info(f"💲 **Total a cancelar: ${total_cancelado:,.2f}**")
                st.info(f"📊 **Distribución:** Capital: ${monto_capital:,.2f} | Interés: ${monto_interes:,.2f}")
            
            enviar = st.form_submit_button("💾 Registrar Pago y Recalcular Cuotas")
            
            if enviar:
                if total_cancelado <= 0:
                    st.warning("⚠️ Debes ingresar un monto mayor a cero.")
                else:
                    try:
                        # Iniciar transacción
                        con.start_transaction()
                        
                        # Registrar pago en PagoPrestamo
                        cursor.execute("""
                            INSERT INTO PagoPrestamo
                            (ID_Prestamo, ID_Reunion, fecha_pago, monto_capital, monto_interes, total_cancelado)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (id_prestamo, id_reunion, fecha_pago, monto_capital, monto_interes, total_cancelado))
                        
                        # Aplicar pago a cuotas
                        capital_sobrante, interes_sobrante = aplicar_pago_cuotas(
                            id_prestamo, monto_capital, monto_interes, fecha_pago, con
                        )
                        
                        # Recalcular cuotas si hubo pago a capital
                        if monto_capital > 0:
                            recalcular_cuotas_restantes(id_prestamo, con)
                        
                        # Verificar si el préstamo está completamente pagado
                        cursor.execute("""
                            SELECT COUNT(*) 
                            FROM CuotaPrestamo 
                            WHERE ID_Prestamo = %s AND estado != 'pagado'
                        """, (id_prestamo,))
                        
                        cuotas_pendientes = cursor.fetchone()[0]
                        
                        if cuotas_pendientes == 0:
                            cursor.execute("""
                                UPDATE Prestamo 
                                SET ID_Estado_prestamo = 3  -- Estado: Cancelado
                                WHERE ID_Prestamo = %s
                            """, (id_prestamo,))
                            st.balloons()
                            st.success("🎉 ¡PRÉSTAMO COMPLETAMENTE PAGADO!")
                        
                        con.commit()
                        
                        st.success("✅ Pago registrado y cuotas recalculadas correctamente!")
                        
                        if capital_sobrante > 0 or interes_sobrante > 0:
                            st.warning(f"⚠️ Sobrante no aplicado: Capital: ${capital_sobrante:.2f}, Interés: ${interes_sobrante:.2f}")
                        
                        st.rerun()
                        
                    except Exception as e:
                        con.rollback()
                        st.error(f"❌ Error al procesar el pago: {e}")
        
        # Opción para regenerar cuotas
        st.subheader("🔄 Regenerar Cuotas")
        if st.button("🔄 Regenerar Todas las Cuotas", type="secondary"):
            if calcular_cuotas_prestamo(id_prestamo, con):
                st.success("✅ Cuotas regeneradas correctamente!")
                st.rerun()
            else:
                st.error("❌ Error al regenerar cuotas")
    
    except Exception as e:
        st.error(f"❌ Error general: {e}")
    
    finally:
        if "cursor" in locals():
            cursor.close()
        if "con" in locals():
            con.close()
