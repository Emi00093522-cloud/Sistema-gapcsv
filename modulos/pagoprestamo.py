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
    """Genera el cronograma de pagos usando EXACTAMENTE los datos registrados del préstamo"""
    cursor = con.cursor()
    
    # Obtener datos REALES del préstamo - USANDO LAS COLUMNAS EXACTAS DE TU TABLA
    cursor.execute("""
        SELECT 
            p.monto,
            p.total_interes,
            p.plazo,
            p.fecha_desembolso,
            p.ID_Grupo
        FROM Prestamo p
        WHERE p.ID_Prestamo = %s
    """, (id_prestamo,))
    
    prestamo = cursor.fetchone()
    if not prestamo:
        st.error("❌ No se encontró el préstamo")
        return False
    
    # Desempaquetar los datos REALES de tu tabla
    monto, tasa_interes, plazo, fecha_desembolso, id_grupo = prestamo
    
    # Convertir a Decimal para precisión
    monto = Decimal(str(monto))
    tasa_interes = Decimal(str(tasa_interes))
    
    # CALCULAR LOS VALORES EXACTAMENTE COMO SE HACE AL REGISTRAR EL PRÉSTAMO
    # (Estos cálculos deben ser IDÉNTICOS a los que haces al registrar)
    interes_mensual = monto * tasa_interes
    interes_total = interes_mensual * plazo
    monto_total_pagar = monto + interes_total
    cuota_mensual = monto_total_pagar / plazo
    
    st.write("💰 **Datos calculados para el cronograma:**")
    st.write(f"- Monto: ${monto:,.2f}")
    st.write(f"- Tasa interés: {tasa_interes*100:.2f}%")
    st.write(f"- Interés mensual: ${interes_mensual:,.2f}")
    st.write(f"- Interés total: ${interes_total:,.2f}")
    st.write(f"- Total a pagar: ${monto_total_pagar:,.2f}")
    st.write(f"- Cuota mensual: ${cuota_mensual:,.2f}")
    st.write(f"- Plazo: {plazo} meses")
    
    # Eliminar cronograma existente
    cursor.execute("DELETE FROM CuotaPrestamo WHERE ID_Prestamo = %s", (id_prestamo,))
    
    # Generar cronograma usando los valores calculados
    for i in range(1, plazo + 1):
        # Calcular capital e interés para cada cuota
        capital_cuota = monto / plazo
        interes_cuota = interes_total / plazo
        total_cuota = cuota_mensual
        
        # Obtener fecha de pago basada en reuniones (mes i)
        fecha_pago = obtener_reunion_fin_de_mes(con, id_grupo, fecha_desembolso, i)
        
        # Insertar en cronograma
        cursor.execute("""
            INSERT INTO CuotaPrestamo 
            (ID_Prestamo, numero_cuota, fecha_programada, capital_programado, 
             interes_programado, total_programado, estado)
            VALUES (%s, %s, %s, %s, %s, %s, 'pendiente')
        """, (id_prestamo, i, fecha_pago, float(capital_cuota), 
              float(interes_cuota), float(total_cuota)))
    
    con.commit()
    
    st.success(f"✅ **Cronograma generado:** {plazo} pagos mensuales de ${cuota_mensual:,.2f}")
    return True

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
        
        # Cargar préstamos activos SOLO de miembros presentes - USANDO LAS COLUMNAS EXACTAS
        if ids_miembros_presentes:
            placeholders = ','.join(['%s'] * len(ids_miembros_presentes))
            cursor.execute(f"""
                SELECT 
                    p.ID_Prestamo, 
                    p.ID_Miembro, 
                    p.monto,
                    p.total_interes,
                    p.plazo,
                    p.fecha_desembolso,
                    m.nombre, 
                    p.proposito,
                    p.ID_Grupo
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
                    p.monto,
                    p.total_interes,
                    p.plazo,
                    p.fecha_desembolso,
                    m.nombre, 
                    p.proposito,
                    p.ID_Grupo
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
        
        # ✅ USAR DATOS REALES DEL PRÉSTAMO - COLUMNAS EXACTAS DE TU TABLA
        monto = prestamo_info[2]
        tasa_interes = prestamo_info[3]
        plazo = prestamo_info[4]
        fecha_desembolso = prestamo_info[5]
        proposito = prestamo_info[7]
        
        # CALCULAR LOS MISMOS VALORES QUE AL REGISTRAR (para mostrar)
        interes_mensual = monto * tasa_interes
        interes_total = interes_mensual * plazo
        monto_total_pagar = monto + interes_total
        cuota_mensual = monto_total_pagar / plazo
        
        # Mostrar información del préstamo
        st.subheader("📋 RESUMEN DEL PRÉSTAMO")
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Información Básica**")
            st.write(f"• **Fecha desembolso:** {fecha_desembolso}")
            st.write(f"• **Tasa interés:** {tasa_interes*100:.2f}%")
            st.write(f"• **Plazo:** {plazo} meses")
            st.write(f"• **Propósito:** {proposito}")
        
        with col2:
            st.markdown("**Montos**")
            st.write(f"• **Monto solicitado:** ${monto:,.2f}")
            st.write(f"• **Interés mensual:** ${interes_mensual:,.2f}")
            st.write(f"• **Interés total:** ${interes_total:,.2f}")
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
        
        # Mostrar plan de pagos
        st.subheader("📅 PLAN DE PAGOS")
        st.markdown("---")
        
        # Crear tabla
        tabla_data = []
        for cuota in cuotas:
            numero, fecha_prog, capital_prog, interes_prog, total_prog, \
            capital_pag, interes_pag, total_pag, estado = cuota
            
            capital_pag = capital_pag or 0
            interes_pag = interes_pag or 0
            total_pag = total_pag or 0
            
            estado_emoji = {
                'pendiente': '⚪',
                'parcial': '🟡', 
                'pagado': '🟢'
            }
            
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
        
        # Calcular totales
        total_pagado = sum(c[7] or 0 for c in cuotas)
        saldo_pendiente = monto_total_pagar - total_pagado
        
        st.markdown("---")
        st.markdown(f"**TOTAL:** ${monto:,.2f} (capital) + ${interes_total:,.2f} (interés) = **${monto_total_pagar:,.2f}**")
        
        if saldo_pendiente <= 0:
            st.success(f"**SALDO: $0 (COMPLETAMENTE PAGADO)** 🎉")
        else:
            st.warning(f"**SALDO PENDIENTE: ${saldo_pendiente:,.2f}**")
        
        # Sección de pagos (simplificada)
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
                    cuotas_opciones = [f"Cuota {c[0]} - ${c[1]:,.2f} - {c[3]}" for c in cuotas_pendientes]
                    cuota_seleccionada = st.selectbox("Selecciona la cuota a pagar:", cuotas_opciones, key="completo")
                    
                    numero_cuota = int(cuota_seleccionada.split(" ")[1])
                    
                    fecha_pago_completo = st.date_input(
                        "Fecha del pago:",
                        value=date.today(),
                        key="fecha_completo"
                    )
                    
                    enviar_completo = st.form_submit_button("✅ Pagar Cuota Completa")
                    
                    if enviar_completo:
                        try:
                            cuota_info = [c for c in cuotas_pendientes if c[0] == numero_cuota][0]
                            monto_cuota = cuota_info[1]
                            
                            cursor.execute("""
                                UPDATE CuotaPrestamo 
                                SET capital_pagado = capital_programado, 
                                    interes_pagado = interes_programado,
                                    total_pagado = total_programado,
                                    estado = 'pagado'
                                WHERE ID_Prestamo = %s AND numero_cuota = %s
                            """, (id_prestamo, numero_cuota))
                            
                            cursor.execute("""
                                INSERT INTO Pago_prestamo 
                                (ID_Prestamo, ID_Reunion, fecha_pago, monto_capital, monto_interes, total_cancelado)
                                VALUES (%s, %s, %s, %s, %s, %s)
                            """, (id_prestamo, id_reunion, fecha_pago_completo, 0, 0, float(monto_cuota)))
                            
                            con.commit()
                            st.success("✅ Pago completo aplicado correctamente")
                            st.balloons()
                            st.rerun()
                                
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
                                nuevo_total_pagado = (total_pagado or 0) + monto_parcial
                                nuevo_estado = 'parcial' if nuevo_total_pagado < total_programado else 'pagado'
                                
                                cursor.execute("""
                                    UPDATE CuotaPrestamo 
                                    SET total_pagado = %s, estado = %s
                                    WHERE ID_Prestamo = %s AND numero_cuota = %s
                                """, (float(nuevo_total_pagado), nuevo_estado, id_prestamo, numero_cuota))
                                
                                cursor.execute("""
                                    INSERT INTO Pago_prestamo 
                                    (ID_Prestamo, ID_Reunion, fecha_pago, monto_capital, monto_interes, total_cancelado)
                                    VALUES (%s, %s, %s, %s, %s, %s)
                                """, (id_prestamo, id_reunion, fecha_pago_parcial, 0, 0, float(monto_parcial)))
                                
                                con.commit()
                                st.success("✅ Pago parcial aplicado correctamente")
                                st.rerun()
                                    
                            except Exception as e:
                                con.rollback()
                                st.error(f"❌ Error al procesar el pago parcial: {e}")
                else:
                    st.info("🎉 No hay cuotas pendientes para pago parcial")
    
    except Exception as e:
        st.error(f"❌ Error general: {e}")
    
    finally:
        if "cursor" in locals():
            cursor.close()
        if "con" in locals():
            con.close()
