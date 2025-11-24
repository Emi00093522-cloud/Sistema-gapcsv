import streamlit as st
from modulos.config.conexion import obtener_conexion
from datetime import datetime

# =====================================================================================
#  MÓDULO PRINCIPAL - MOVIMIENTO DE CAJA SIMPLIFICADO
# =====================================================================================

def mostrar_movimiento_caja():
    st.header("💰 Movimientos de Caja - Resumen por Reunión")

    if 'reunion_actual' not in st.session_state:
        st.warning("⚠️ Primero debes seleccionar una reunión en el módulo de Asistencia.")
        return

    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)

        # Datos de sesión
        reunion_info = st.session_state.reunion_actual
        id_reunion = reunion_info['id_reunion']
        id_grupo = reunion_info['id_grupo']
        nombre_reunion = reunion_info['nombre_reunion']

        st.info(f"📅 **Reunión actual:** {nombre_reunion}")

        # SALDO INICIAL = saldo_final de reunión previa
        saldo_anterior = obtener_saldo_anterior(cursor, id_reunion, id_grupo)
        st.success(f"💰 **Saldo inicial: ${saldo_anterior:,.2f}**")

        # Obtener y mostrar resumen automático
        resumen_automatico(cursor, con, id_reunion, saldo_anterior)

    except Exception as e:
        st.error(f"❌ Error general: {e}")

    finally:
        try:
            cursor.close()
            con.close()
        except:
            pass

# =====================================================================================
#  OBTENER SALDO ANTERIOR
# =====================================================================================

def obtener_saldo_anterior(cursor, id_reunion_actual, id_grupo):
    try:
        cursor.execute("""
            SELECT ID_Reunion
            FROM Reunion
            WHERE ID_Grupo = %s AND ID_Reunion < %s
            ORDER BY ID_Reunion DESC
            LIMIT 1
        """, (id_grupo, id_reunion_actual))

        reunion_anterior = cursor.fetchone()

        if not reunion_anterior:
            return 0

        cursor.execute("""
            SELECT saldo_final
            FROM Movimiento_de_caja
            WHERE ID_Reunion = %s
            ORDER BY ID_Movimiento_caja DESC
            LIMIT 1
        """, (reunion_anterior['ID_Reunion'],))

        mov = cursor.fetchone()

        return float(mov['saldo_final']) if mov else 0

    except Exception as e:
        st.error(f"Error al obtener saldo anterior: {e}")
        return 0

# =====================================================================================
#  OBTENER TOTALES POR REUNIÓN - CON NOMBRES CORRECTOS
# =====================================================================================

def obtener_totales_reunion(cursor, id_reunion):
    try:
        totales = {
            'total_ingresos': 0,
            'total_egresos': 0,
            'detalle_ingresos': [],
            'detalle_egresos': []
        }
        
        # =============================================================================
        # INGRESOS - SUMAR TODOS LOS INGRESOS DE DIFERENTES MÓDULOS
        # =============================================================================
        
        # 1) TOTAL AHORROS (INGRESO)
        cursor.execute("""
            SELECT COALESCE(SUM(Monto_Ahorro), 0) as total
            FROM Ahorro 
            WHERE ID_Reunion = %s
        """, (id_reunion,))
        resultado = cursor.fetchone()
        total_ahorros = float(resultado['total']) if resultado else 0
        
        if total_ahorros > 0:
            totales['total_ingresos'] += total_ahorros
            totales['detalle_ingresos'].append({
                'concepto': 'Ahorros',
                'monto': total_ahorros,
                'descripcion': 'Total de ahorros de los miembros'
            })

        # 2) TOTAL PAGOS PRÉSTAMOS (INGRESO) - Usando total_cancelado
        try:
            cursor.execute("""
                SELECT COALESCE(SUM(total_cancelado), 0) as total
                FROM Pago_prestamo 
                WHERE ID_Reunion = %s
            """, (id_reunion,))
            resultado = cursor.fetchone()
            total_pagos_prestamos = float(resultado['total']) if resultado else 0
            
            if total_pagos_prestamos > 0:
                totales['total_ingresos'] += total_pagos_prestamos
                totales['detalle_ingresos'].append({
                    'concepto': 'Pagos de Préstamos',
                    'monto': total_pagos_prestamos,
                    'descripcion': 'Total de pagos recibidos de préstamos (capital + interés)'
                })
        except Exception as e:
            st.warning(f"ℹ️ No se pudieron obtener pagos de préstamos: {e}")

        # 3) TOTAL PAGOS MULTAS (INGRESO) - Usando ID_Reunion_pago
        try:
            cursor.execute("""
                SELECT COALESCE(SUM(monto_pagado), 0) as total
                FROM PagoMulta 
                WHERE ID_Reunion_pago = %s
            """, (id_reunion,))
            resultado = cursor.fetchone()
            total_pagos_multas = float(resultado['total']) if resultado else 0
            
            if total_pagos_multas > 0:
                totales['total_ingresos'] += total_pagos_multas
                totales['detalle_ingresos'].append({
                    'concepto': 'Pagos de Multas',
                    'monto': total_pagos_multas,
                    'descripcion': 'Total de pagos recibidos por multas'
                })
        except Exception as e:
            st.warning(f"ℹ️ No se pudieron obtener pagos de multas: {e}")

        # =============================================================================
        # EGRESOS - SUMAR TODOS LOS EGRESOS DE DIFERENTES MÓDULOS
        # =============================================================================
        
        # 1) TOTAL PRÉSTAMOS APROBADOS (EGRESO)
        cursor.execute("""
            SELECT COALESCE(SUM(monto), 0) as total
            FROM Prestamo 
            WHERE ID_Reunion = %s AND ID_Estado_prestamo = 1
        """, (id_reunion,))
        resultado = cursor.fetchone()
        total_prestamos = float(resultado['total']) if resultado else 0
        
        if total_prestamos > 0:
            totales['total_egresos'] += total_prestamos
            totales['detalle_egresos'].append({
                'concepto': 'Préstamos Otorgados',
                'monto': total_prestamos,
                'descripcion': 'Total de préstamos aprobados y desembolsados'
            })

        # Mostrar información de depuración
        st.write("🔍 **Información de depuración:**")
        st.write(f"- Total préstamos encontrados: ${total_prestamos:,.2f}")
        st.write(f"- Total egresos calculados: ${totales['total_egresos']:,.2f}")
        st.write(f"- Cantidad de egresos en detalle: {len(totales['detalle_egresos'])}")

        return totales

    except Exception as e:
        st.error(f"Error al obtener totales de reunión: {e}")
        return {'total_ingresos': 0, 'total_egresos': 0, 'detalle_ingresos': [], 'detalle_egresos': []}

# =====================================================================================
#  RESUMEN AUTOMÁTICO SIMPLIFICADO
# =====================================================================================

def resumen_automatico(cursor, con, id_reunion, saldo_anterior):
    st.subheader("📊 Resumen Automático de Movimientos")

    # Obtener totales de la reunión
    totales = obtener_totales_reunion(cursor, id_reunion)
    
    # Calcular saldo final
    saldo_final = saldo_anterior + totales['total_ingresos'] - totales['total_egresos']

    # Mostrar métricas principales
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💰 Saldo Inicial", f"${saldo_anterior:,.2f}")
    with col2:
        st.metric("📈 Total Ingresos", f"${totales['total_ingresos']:,.2f}")
    with col3:
        st.metric("📉 Total Egresos", f"${totales['total_egresos']:,.2f}")
    with col4:
        st.metric("💵 Saldo Final", f"${saldo_final:,.2f}")

    st.divider()

    # Mostrar detalles de ingresos
    if totales['detalle_ingresos']:
        st.subheader("📈 Detalle de Ingresos")
        for ingreso in totales['detalle_ingresos']:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{ingreso['concepto']}**")
                st.caption(ingreso['descripcion'])
            with col2:
                st.success(f"💰 ${ingreso['monto']:,.2f}")
    else:
        st.info("📭 No hay ingresos registrados en esta reunión")

    # Mostrar detalles de egresos
    if totales['detalle_egresos']:
        st.subheader("📉 Detalle de Egresos")
        for egreso in totales['detalle_egresos']:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{egreso['concepto']}**")
                st.caption(egreso['descripcion'])
            with col2:
                st.error(f"📤 ${egreso['monto']:,.2f}")
    else:
        st.info("📭 No hay egresos registrados en esta reunión")

    # Mostrar información de consultas ejecutadas
    with st.expander("🔍 Ver consultas ejecutadas"):
        st.write("**Consultas utilizadas:**")
        st.code("""
        -- Ahorros: SUM(Monto_Ahorro) FROM Ahorro WHERE ID_Reunion = ?
        -- Pagos Préstamos: SUM(total_cancelado) FROM Pago_prestamo WHERE ID_Reunion = ?
        -- Pagos Multas: SUM(monto_pagado) FROM PagoMulta WHERE ID_Reunion_pago = ?
        -- Préstamos: SUM(monto) FROM Prestamo WHERE ID_Reunion = ? AND ID_Estado_prestamo = 1
        """)

    # Botón para guardar el resumen en la base de datos
    st.divider()
    if st.button("💾 Guardar Resumen de Caja", type="primary"):
        with st.spinner("Guardando resumen en el sistema..."):
            guardar_resumen_caja(cursor, con, id_reunion, totales, saldo_anterior, saldo_final)
            st.success("✅ Resumen de caja guardado correctamente!")
            st.rerun()

# =====================================================================================
#  GUARDAR RESUMEN EN BASE DE DATOS
# =====================================================================================

def guardar_resumen_caja(cursor, con, id_reunion, totales, saldo_anterior, saldo_final):
    try:
        # Eliminar movimientos existentes para esta reunión
        cursor.execute("DELETE FROM Movimiento_de_caja WHERE ID_Reunion = %s", (id_reunion,))
        
        fecha_actual = datetime.now()
        saldo_actual = saldo_anterior

        # Guardar cada ingreso individualmente
        for ingreso in totales['detalle_ingresos']:
            saldo_actual += ingreso['monto']
            cursor.execute("""
                INSERT INTO Movimiento_de_caja 
                (ID_Reunion, ID_Tipo_movimiento, monto, categoria, descripcion, fecha, saldo_final)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                id_reunion, 
                1,  # ID para Ingreso
                ingreso['monto'],
                ingreso['concepto'],
                ingreso['descripcion'],
                fecha_actual,
                saldo_actual
            ))

        # Guardar cada egreso individualmente
        for egreso in totales['detalle_egresos']:
            saldo_actual -= egreso['monto']
            cursor.execute("""
                INSERT INTO Movimiento_de_caja 
                (ID_Reunion, ID_Tipo_movimiento, monto, categoria, descripcion, fecha, saldo_final)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                id_reunion, 
                2,  # ID para Egreso
                egreso['monto'],
                egreso['concepto'],
                egreso['descripcion'],
                fecha_actual,
                saldo_actual
            ))

        con.commit()
        return True

    except Exception as e:
        con.rollback()
        st.error(f"Error al guardar resumen de caja: {e}")
        return False

# =====================================================================================
#  EJECUTABLE
# =====================================================================================

def main():
    mostrar_movimiento_caja()

if __name__ == "__main__":
    main()
