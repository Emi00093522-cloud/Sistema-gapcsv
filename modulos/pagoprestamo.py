import streamlit as st
from modulos.config.conexion import obtener_conexion
from datetime import date, datetime, timedelta
from decimal import Decimal

def obtener_reunion_mas_cercana_fin_mes(con, id_grupo, fecha_referencia, mes_offset=0):
    """Encuentra la reunión más cercana al fin de mes basado en la frecuencia de reuniones"""
    cursor = con.cursor()
    
    cursor.execute("""
        SELECT frecuencia_reunion 
        FROM Reglamento 
        WHERE ID_Grupo = %s 
        ORDER BY ID_Reglamento DESC 
        LIMIT 1
    """, (id_grupo,))
    resultado = cursor.fetchone()
    frecuencia = resultado[0] if resultado else "Mensual"
    
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
    """Genera el cronograma de pagos basado en los datos ya calculados y guardados en Prestamo"""
    cursor = con.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT p.ID_Prestamo, p.ID_Miembro, p.monto, p.total_interes, 
               p.plazo, p.fecha_desembolso, p.monto_total_pagar
        FROM Prestamo p
        WHERE p.ID_Prestamo = %s
    """, (id_prestamo,))
    
    prestamo = cursor.fetchone()
    if not prestamo:
        cursor.close()
        return False
    
    monto = prestamo.get('monto')
    total_interes = prestamo.get('total_interes')  # en MONEDA ($), según lo guardado en Prestamo
    plazo = prestamo.get('plazo')
    fecha_desembolso = prestamo.get('fecha_desembolso')
    monto_total_pagar = prestamo.get('monto_total_pagar')
    
    if monto is None or total_interes is None or plazo is None or fecha_desembolso is None:
        st.error("❌ Datos insuficientes en el préstamo (monto / total_interes / plazo / fecha_desembolso).")
        cursor.close()
        return False
    
    cursor.execute("DELETE FROM CuotaPrestamo WHERE ID_Prestamo = %s", (id_prestamo,))
    
    monto_d = Decimal(str(monto))
    interes_total_d = Decimal(str(total_interes))
    plazo_i = int(plazo)
    
    capital_por_cuota = (monto_d / plazo_i).quantize(Decimal("0.01"))
    interes_por_cuota = (interes_total_d / plazo_i).quantize(Decimal("0.01"))
    
    saldo_capital = monto_d
    saldo_interes = interes_total_d
    
    fecha_primer_pago = fecha_desembolso + timedelta(days=30)
    
    for i in range(1, plazo_i + 1):
        if i == plazo_i:
            capital_cuota = saldo_capital
            interes_cuota = saldo_interes
        else:
            capital_cuota = capital_por_cuota
            interes_cuota = interes_por_cuota
        
        total_cuota = (capital_cuota + interes_cuota).quantize(Decimal("0.01"))
        fecha_pago = fecha_primer_pago + timedelta(days=30*(i-1))
        
        cursor.execute("""
            INSERT INTO CuotaPrestamo 
            (ID_Prestamo, numero_cuota, fecha_programada, capital_programado, 
             interes_programado, total_programado, estado, capital_pagado, interes_pagado, total_pagado)
            VALUES (%s, %s, %s, %s, %s, %s, 'pendiente', 0, 0, 0)
        """, (id_prestamo, i, fecha_pago, float(capital_cuota), 
              float(interes_cuota), float(total_cuota)))
        
        saldo_capital -= capital_cuota
        saldo_interes -= interes_cuota
    
    con.commit()
    cursor.close()
    return True

def aplicar_pago_cuota(id_prestamo, monto_pagado, fecha_pago, tipo_pago, con, numero_cuota=None):
    """Aplica un pago (completo o parcial) a una cuota específica"""
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
        numero_cuota = numero_cuota
        fecha_programada = None
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
    """, (float(nuevo_capital_pagado), float(nuevo_interes_pagado), 
          float(nuevo_total_pagado), nuevo_estado, id_cuota))
    
    if tipo_pago == "parcial" and monto_sobrante > 0:
        cursor.execute("""
            SELECT 
                COALESCE(SUM(capital_programado - COALESCE(capital_pagado, 0)), 0) as capital_pendiente,
                COALESCE(SUM(interes_programado - COALESCE(interes_pagado, 0)), 0) as interes_pendiente
            FROM CuotaPrestamo 
            WHERE ID_Prestamo = %s
        """, (id_prestamo,))
        
        saldos = cursor.fetchone()
        capital_pendiente, interes_pendiente = saldos
        
        if capital_pendiente > 0 or interes_pendiente > 0:
            nueva_fecha = fecha_pago + timedelta(days=30)
            
            cursor.execute("""
                SELECT MAX(numero_cuota) FROM CuotaPrestamo WHERE ID_Prestamo = %s
            """, (id_prestamo,))
            ultimo_numero = cursor.fetchone()[0] or 0
            nuevo_numero = ultimo_numero + 1
            
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
            SELECT frecuencia_reunion 
            FROM Reglamento 
            WHERE ID_Grupo = %s 
            ORDER BY ID_Reglamento DESC 
            LIMIT 1
        """, (id_grupo,))
        frecuencia_result = cursor.fetchone()
        frecuencia = frecuencia_result.get('frecuencia_reunion') if frecuencia_result else "Mensual"
        st.info(f"🔄 **Frecuencia de reuniones del grupo:** {frecuencia}")

        cursor.execute("""
            SELECT m.ID_Miembro, m.nombre 
            FROM Miembro m
            JOIN Miembroxreunion mr ON m.ID_Miembro = mr.ID_Miembro
            WHERE mr.ID_Reunion = %s AND mr.asistio = 1
            ORDER BY m.nombre
        """, (id_reunion,))
        
        miembros_presentes = cursor.fetchall()
        if not miembros_presentes:
            st.warning("⚠️ No hay miembros registrados como presentes en esta reunión.")
            cursor.close()
            return

        ids_miembros_presentes = [m['ID_Miembro'] for m in miembros_presentes]
        placeholders = ','.join(['%s'] * len(ids_miembros_presentes))

        cursor.execute(f"""
            SELECT 
                p.ID_Prestamo, 
                p.ID_Miembro, 
                p.monto,
                p.total_interes,
                p.plazo,
                p.fecha_desembolso,
                m.nombre as miembro_nombre, 
                p.proposito,
                p.monto_total_pagar,
                p.tasa_interes
            FROM Prestamo p
            JOIN Miembro m ON p.ID_Miembro = m.ID_Miembro
            WHERE p.ID_Estado_prestamo != 3
            AND p.ID_Miembro IN ({placeholders})
        """, ids_miembros_presentes)
        
        prestamos = cursor.fetchall()
        if not prestamos:
            st.warning("⚠️ No hay préstamos activos para los miembros presentes en esta reunión.")
            cursor.close()
            return
        
        prestamos_dict = {
            f"Préstamo {p['ID_Prestamo']} - {p['miembro_nombre']} - ${p['monto']:,.2f} - {p['plazo']} meses": p['ID_Prestamo']
            for p in prestamos
        }
        
        prestamo_sel = st.selectbox("Selecciona el préstamo:", list(prestamos_dict.keys()))
        id_prestamo = prestamos_dict[prestamo_sel]
        prestamo_info = next(p for p in prestamos if p['ID_Prestamo'] == id_prestamo)
        
        monto = prestamo_info.get('monto')
        total_interes = prestamo_info.get('total_interes')  # ya en $
        plazo = prestamo_info.get('plazo')
        fecha_desembolso = prestamo_info.get('fecha_desembolso')
        proposito = prestamo_info.get('proposito')
        monto_total_pagar = prestamo_info.get('monto_total_pagar')
        tasa_interes = prestamo_info.get('tasa_interes')
        
        st.subheader("📋 RESUMEN DEL PRÉSTAMO")
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Información Básica**")
            st.write(f"• **Fecha inicio:** {fecha_desembolso}")
            st.write(f"• **Tasa interés:** {tasa_interes if tasa_interes is not None else 'N/A'}")
            st.write(f"• **Plazo:** {plazo} meses")
            st.write(f"• **Propósito:** {proposito}")
            st.write(f"• **Frecuencia reuniones:** {frecuencia}")
        with col2:
            st.markdown("**Montos (Datos Registrados)**")
            st.write(f"• **Monto préstamo:** ${monto:,.2f}")
            st.write(f"• **Interés total a pagar:** ${total_interes:,.2f}")
            st.write(f"• **Total a pagar:** ${monto_total_pagar:,.2f}")
            st.write("• **Cuota mensual:** (usar la registrada en Prestamo si tienes columna; no hay columna en este esquema)")
        st.markdown("---")
        
        cursor.execute("SELECT COUNT(*) as c FROM CuotaPrestamo WHERE ID_Prestamo = %s", (id_prestamo,))
        tiene_cronograma = cursor.fetchone().get('c', 0) > 0
        
        if not tiene_cronograma:
            st.info("📅 Este préstamo no tiene cronograma de pagos generado.")
            if st.button("🔄 Generar Plan de Pagos", type="primary"):
                if generar_cronograma_pagos(id_prestamo, con):
                    st.success("✅ Plan de pagos generado correctamente!")
                    st.rerun()
                else:
                    st.error("❌ Error al generar plan de pagos")
            cursor.close()
            return
        
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
        
        tabla_data = []
        for cuota in cuotas:
            numero = cuota['numero_cuota']
            fecha_prog = cuota['fecha_programada']
            capital_prog = cuota['capital_programado']
            interes_prog = cuota['interes_programado']
            total_prog = cuota['total_programado']
            capital_pag = cuota['capital_pagado'] or 0
            interes_pag = cuota['interes_pagado'] or 0
            total_pag = cuota['total_pagado'] or 0
            estado = cuota['estado']
            
            estado_emoji = {'pendiente': '⚪', 'parcial': '🟡', 'pagado': '🟢'}
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
        
        st.dataframe(tabla_data, use_container_width=True)
        
        total_capital_pagado = sum(c['capital_pagado'] or 0 for c in cuotas)
        total_interes_pagado = sum(c['interes_pagado'] or 0 for c in cuotas)
        total_pagado = sum(c['total_pagado'] or 0 for c in cuotas)
        
        st.markdown("---")
        st.markdown(f"**TOTAL:** ${monto:,.2f} (capital) + ${total_interes:,.2f} (interés) = **${monto_total_pagar:,.2f}**")
        
        saldo_pendiente = monto_total_pagar - total_pagado
        if saldo_pendiente <= 0:
            st.success(f"**SALDO: $0 (COMPLETAMENTE PAGADO)** 🎉")
        else:
            st.warning(f"**SALDO PENDIENTE: ${saldo_pendiente:,.2f}**")
        
        st.subheader("💰 REGISTRAR PAGO")
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 💵 Pago Completo")
            with st.form("form_pago_completo"):
                cursor.execute("""
                    SELECT numero_cuota, total_programado, total_pagado, fecha_programada
                    FROM CuotaPrestamo 
                    WHERE ID_Prestamo = %s AND estado != 'pagado'
                    ORDER BY numero_cuota
                """, (id_prestamo,))
                
                cuotas_pendientes = cursor.fetchall()
                
                if cuotas_pendientes:
                    cuotas_opciones = [f"Cuota {c['numero_cuota']} - ${c['total_programado']:,.2f} - {c['fecha_programada']}" for c in cuotas_pendientes]
                    cuota_seleccionada = st.selectbox("Selecciona la cuota a pagar:", cuotas_opciones, key="completo")
                    numero_cuota = int(cuota_seleccionada.split(" ")[1])
                    fecha_pago_completo = st.date_input("Fecha del pago:", value=date.today(), key="fecha_completo")
                    enviar_completo = st.form_submit_button("✅ Pagar Cuota Completa")
                    
                    if enviar_completo:
                        try:
                            cuota_info = next(c for c in cuotas_pendientes if c['numero_cuota'] == numero_cuota)
                            monto_cuota = cuota_info['total_programado']
                            success, mensaje = aplicar_pago_cuota(id_prestamo, monto_cuota, fecha_pago_completo, "completo", con, numero_cuota)
                            if success:
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
                cursor.execute("""
                    SELECT numero_cuota, total_programado, total_pagado, fecha_programada
                    FROM CuotaPrestamo 
                    WHERE ID_Prestamo = %s AND estado != 'pagado'
                    ORDER BY fecha_programada ASC
                    LIMIT 1
                """, (id_prestamo,))
                
                cuota_actual = cursor.fetchone()
                if cuota_actual:
                    numero_cuota = cuota_actual['numero_cuota']
                    total_programado = cuota_actual['total_programado']
                    total_pagado = cuota_actual['total_pagado'] or 0
                    fecha_programada = cuota_actual['fecha_programada']
                    pendiente_actual = total_programado - total_pagado
                    
                    st.write(f"**Próxima cuota:** #{numero_cuota}")
                    st.write(f"**Total pendiente:** ${pendiente_actual:,.2f}")
                    st.write(f"**Fecha programada:** {fecha_programada}")
                    
                    fecha_pago_parcial = st.date_input("Fecha del pago:", value=date.today(), key="fecha_parcial")
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
        try:
            cursor.close()
        except:
            pass
        try:
            con.close()
        except:
            pass
