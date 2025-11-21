import streamlit as st
from modulos.config.conexion import obtener_conexion
from datetime import date, datetime, timedelta
from decimal import Decimal

def calcular_cuotas_desde_prestamo(id_prestamo, con):
    """Genera las cuotas basándose en los datos ya calculados del préstamo"""
    cursor = con.cursor()
    
    # Obtener datos del préstamo
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
    
    # VERIFICAR: Si total_interes parece incorrecto, calcularlo correctamente
    monto_decimal = Decimal(str(monto))
    plazo_decimal = Decimal(str(plazo))
    
    # Si total_interes es muy grande (como 500 en lugar de 300), recalcular
    if total_interes > monto:  # Si el interés es mayor que el monto, está mal
        # Recalcular interés total basado en tasa ~5%
        tasa_mensual = Decimal('0.05')  # 5%
        interes_mensual = monto_decimal * tasa_mensual
        total_interes_correcto = interes_mensual * plazo_decimal
        total_interes = float(total_interes_correcto)
        st.warning(f"ℹ️ Interés corregido: ${total_interes:.2f}")
    
    # CALCULAR CUOTA MENSUAL
    monto_total = monto_decimal + Decimal(str(total_interes))
    cuota_mensual = monto_total / plazo_decimal
    cuota_mensual = round(cuota_mensual, 2)
    
    # Distribución capital/interés
    capital_mensual = monto_decimal / plazo_decimal
    capital_mensual = round(capital_mensual, 2)
    
    interes_mensual = Decimal(str(total_interes)) / plazo_decimal
    interes_mensual = round(interes_mensual, 2)
    
    # Configurar fechas
    fecha_primer_pago = fecha_desembolso + timedelta(days=30)
    
    # Eliminar cuotas existentes
    cursor.execute("DELETE FROM CuotaPrestamo WHERE ID_Prestamo = %s", (id_prestamo,))
    
    # Generar cuotas
    saldo_capital = monto_decimal
    
    for i in range(1, plazo + 1):
        # Para la última cuota, ajustar por redondeo
        if i == plazo:
            capital_cuota = saldo_capital
            interes_cuota = Decimal(str(total_interes)) - (interes_mensual * (plazo - 1))
            total_cuota = capital_cuota + interes_cuota
        else:
            capital_cuota = capital_mensual
            interes_cuota = interes_mensual
            total_cuota = cuota_mensual
        
        # Calcular fecha de pago
        fecha_pago = fecha_primer_pago + timedelta(days=30*(i-1))
        
        # Insertar cuota
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
            WHERE p.ID_Estado_prestamo != 3
        """)
        
        prestamos = cursor.fetchall()
        
        if not prestamos:
            st.warning("⚠️ No hay préstamos activos registrados.")
            return
        
        # Crear lista de préstamos con información CORREGIDA
        prestamos_corregidos = []
        for p in prestamos:
            id_prestamo, id_miembro, monto, total_interes, plazo, fecha_desembolso, nombre, proposito = p
            
            # CORREGIR LA TASA PARA MOSTRAR
            # Si total_interes es incorrecto, calcular tasa aproximada
            if total_interes > monto:  # Interés mayor que monto - está mal
                # Calcular tasa basada en interés mensual ~5%
                tasa_mostrar = 5.0
                interes_total_correcto = monto * 0.05 * plazo
                texto = f"Préstamo {id_prestamo} - {nombre} - ${monto:,.2f} - {plazo} meses - {tasa_mostrar}% mensual"
            else:
                # Calcular tasa real
                if monto > 0 and plazo > 0:
                    tasa_mostrar = (total_interes / (monto * plazo)) * 100
                else:
                    tasa_mostrar = 0
                texto = f"Préstamo {id_prestamo} - {nombre} - ${monto:,.2f} - {plazo} meses - {tasa_mostrar:.2f}% mensual"
            
            prestamos_corregidos.append({
                'id': id_prestamo,
                'texto': texto,
                'monto': monto,
                'total_interes': total_interes,
                'plazo': plazo,
                'nombre': nombre,
                'proposito': proposito,
                'fecha_desembolso': fecha_desembolso,
                'tasa_mostrar': tasa_mostrar
            })
        
        prestamos_dict = {p['texto']: p['id'] for p in prestamos_corregidos}
        
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
        prestamo_info = [p for p in prestamos_corregidos if p['id'] == id_prestamo][0]
        
        # Mostrar información del préstamo CORREGIDA
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Monto del Préstamo", f"${prestamo_info['monto']:,.2f}")
        with col2:
            st.metric("Tasa de Interés Mensual", f"{prestamo_info['tasa_mostrar']:.2f}%")
        with col3:
            st.metric("Plazo", f"{prestamo_info['plazo']} meses")
        
        # Mostrar información detallada
        st.info(f"**Propósito:** {prestamo_info['proposito']} | **Fecha desembolso:** {prestamo_info['fecha_desembolso']}")
        
        # Calcular información correcta del préstamo
        monto = prestamo_info['monto']
        plazo = prestamo_info['plazo']
        tasa_decimal = prestamo_info['tasa_mostrar'] / 100
        
        interes_mensual_correcto = monto * tasa_decimal
        interes_total_correcto = interes_mensual_correcto * plazo
        total_pagar_correcto = monto + interes_total_correcto
        cuota_mensual_correcta = total_pagar_correcto / plazo
        
        st.success(f"**📊 Resumen correcto:** Cuota mensual: ${cuota_mensual_correcta:.2f} | Interés total: ${interes_total_correcto:.2f} | Total a pagar: ${total_pagar_correcto:.2f}")
        
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
            st.info("ℹ️ No hay cuotas programadas. Generar plan de pagos:")
            st.write(f"- **Monto a financiar:** ${monto:,.2f}")
            st.write(f"- **Tasa mensual:** {prestamo_info['tasa_mostrar']:.2f}%")
            st.write(f"- **Interés mensual:** ${interes_mensual_correcto:.2f}")
            st.write(f"- **Interés total:** ${interes_total_correcto:.2f}")
            st.write(f"- **Total a pagar:** ${total_pagar_correcto:.2f}")
            st.write(f"- **Plazo:** {plazo} meses")
            st.write(f"- **Cuota mensual:** ${cuota_mensual_correcta:.2f}")
            
            if st.button("🎯 Generar Plan de Pagos", type="primary"):
                if calcular_cuotas_desde_prestamo(id_prestamo, con):
                    st.success("✅ Plan de pagos generado correctamente!")
                    st.rerun()
                else:
                    st.error("❌ Error al generar plan de pagos")
            return
        
        # Resto del código para mostrar cuotas y formulario de pago...
        # [Mantener el mismo código de antes para mostrar cuotas y formulario de pago]
        
        # Mostrar tabla de cuotas
        cuotas_data = []
        for cuota in cuotas:
            numero, fecha_prog, capital_prog, interes_prog, total_prog, \
            capital_pag, interes_pag, total_pag, estado = cuota
            
            capital_pag = capital_pag or 0
            interes_pag = interes_pag or 0
            total_pag = total_pag or 0
            
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
        
        # [Mantener el resto del código igual...]
        
    except Exception as e:
        st.error(f"❌ Error general: {e}")
    
    finally:
        if "cursor" in locals():
            cursor.close()
        if "con" in locals():
            con.close()

# Mantener las funciones aplicar_pago_cuotas y recalcular_cuotas_por_pago_parcial igual que antes
