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
                  float(monto_sobrante), 0, float(monto_sobrante)))
    
    con.commit()
    return True, f"Pago {tipo_pago} aplicado correctamente"

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
        
        # Calcular información del préstamo
        monto = prestamo_info[2]
        total_interes = prestamo_info[3]
        plazo = prestamo_info[4]
        monto_total = monto + total_interes
        cuota_mensual = monto_total / plazo
        
        # Calcular tasa aproximada
        tasa_aprox = (total_interes / (monto * plazo)) * 100 if monto > 0 and plazo > 0 else 0
        
        # Mostrar información del préstamo en un layout más organizado
        st.subheader("📋 RESUMEN DEL PRÉSTAMO")
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Información Básica**")
            st.write(f"• **Fecha inicio:** {prestamo_info[5]}")
            st.write(f"• **Tasa interés:** {tasa_aprox:.1f}%")
            st.write(f"• **Plazo:** {plazo} meses")
            st.write(f"• **Propósito:** {prestamo_info[7]}")
        
        with col2:
            st.markdown("**Montos**")
            st.write(f"• **Monto préstamo:** ${monto:,.2f}")
            st.write(f"• **Interés total:** ${total_interes:,.2f}")
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
        st.subheader("📅 PLAN DE PAGOS")
        st.markdown("---")
        
        # Crear tabla simple
        tabla_html = """
        <style>
        .plan-pagos {
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
        }
        .plan-pagos th, .plan-pagos td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        .plan-pagos th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
        .estado-pendiente { color: #ff6b35; font-weight: bold; }
        .estado-parcial { color: #ffa500; font-weight: bold; }
        .estado-pagado { color: #28a745; font-weight: bold; }
        </style>
        <table class="plan-pagos">
            <tr>
                <th>Fecha</th>
                <th>Estado</th>
                <th>Capital</th>
                <th>Interés</th>
                <th>Total</th>
            </tr>
        """
        
        for cuota in cuotas:
            numero, fecha_prog, capital_prog, interes_prog, total_prog, \
            capital_pag, interes_pag, total_pag, estado = cuota
            
            capital_pag = capital_pag or 0
            interes_pag = interes_pag or 0
            total_pag = total_pag or 0
            
            # Determinar clase CSS para el estado
            estado_class = f"estado-{estado}"
            
            # Mostrar montos pagados si hay pago, sino los programados
            if estado == 'pagado':
                capital_mostrar = capital_pag
                interes_mostrar = interes_pag
                total_mostrar = total_pag
            elif estado == 'parcial':
                capital_mostrar = f"{capital_pag} de {capital_prog}"
                interes_mostrar = f"{interes_pag} de {interes_prog}"
                total_mostrar = f"{total_pag} de {total_prog}"
            else:
                capital_mostrar = capital_prog
                interes_mostrar = interes_prog
                total_mostrar = total_prog
            
            tabla_html += f"""
            <tr>
                <td>{fecha_prog}</td>
                <td class="{estado_class}">{estado.upper()}</td>
                <td>${capital_mostrar:,.2f}</td>
                <td>${interes_mostrar:,.2f}</td>
                <td>${total_mostrar:,.2f}</td>
            </tr>
            """
        
        tabla_html += "</table>"
        st.markdown(tabla_html, unsafe_allow_html=True)
        
        # Calcular totales
        total_capital_pagado = sum(c[5] or 0 for c in cuotas)
        total_interes_pagado = sum(c[6] or 0 for c in cuotas)
        total_pagado = sum(c[7] or 0 for c in cuotas)
        
        st.markdown("---")
        st.markdown(f"**TOTAL:** ${monto:,.2f} (capital) + ${total_interes:,.2f} (interés) = **${monto_total:,.2f}**")
        
        saldo_pendiente = monto_total - total_pagado
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
                                    INSERT INTO PagoPrestamo 
                                    (ID_Prestamo, ID_Reunion, fecha_pago, monto_capital, monto_interes, total_cancelado)
                                    VALUES (%s, %s, %s, %s, %s, %s)
                                """, (id_prestamo, None, fecha_pago_completo, 0, 0, float(monto_cuota)))
                                
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
                                        INSERT INTO PagoPrestamo 
                                        (ID_Prestamo, ID_Reunion, fecha_pago, monto_capital, monto_interes, total_cancelado)
                                        VALUES (%s, %s, %s, %s, %s, %s)
                                    """, (id_prestamo, None, fecha_pago_parcial, 0, 0, float(monto_parcial)))
                                    
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
