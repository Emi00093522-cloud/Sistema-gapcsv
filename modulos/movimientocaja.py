import streamlit as st
from modulos.config.conexion import obtener_conexion
from datetime import datetime

# =====================================================================================
#  MÓDULO PRINCIPAL - MOVIMIENTO DE CAJA AUTOMÁTICO
# =====================================================================================

def mostrar_movimiento_caja():
    st.header("💰 Movimientos de Caja - Sistema Automático")

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

        # Tabs
        tab1, tab2 = st.tabs(["📊 Resumen Automático", "📋 Detalle de Movimientos"])

        with tab1:
            resumen_automatico(cursor, con, id_reunion, saldo_anterior)

        with tab2:
            detalle_movimientos(cursor, id_reunion, saldo_anterior)

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
#  OBTENER TOTALES POR REUNIÓN (CORREGIDO CON NOMBRES EXACTOS)
# =====================================================================================

def obtener_totales_reunion(cursor, id_reunion):
    try:
        totales = {
            'total_ahorros': 0,
            'total_prestamos': 0,
            'total_pagos_prestamos': 0,
            'total_pagos_multas': 0
        }
        
        # 1) TOTAL AHORROS - Usando nombre correcto
        cursor.execute("""
            SELECT COALESCE(SUM(Monto_Ahorro), 0) as total
            FROM Ahorro 
            WHERE ID_Reunion = %s
        """, (id_reunion,))
        resultado = cursor.fetchone()
        totales['total_ahorros'] = float(resultado['total']) if resultado else 0

        # 2) TOTAL PRÉSTAMOS - Usando columna 'monto' (no 'Monto_Prestamo')
        cursor.execute("""
            SELECT COALESCE(SUM(monto), 0) as total
            FROM Prestamo 
            WHERE ID_Reunion = %s AND ID_Estado_prestamo = 1  -- 1 = APROBADO
        """, (id_reunion,))
        resultado = cursor.fetchone()
        totales['total_prestamos'] = float(resultado['total']) if resultado else 0

        # 3) TOTAL PAGOS PRÉSTAMOS - Verificar nombre exacto
        # Primero verificamos la estructura de Pago_Prestamo
        cursor.execute("SHOW COLUMNS FROM Pago_Prestamo")
        columnas_pago = cursor.fetchall()
        columnas_pago_nombres = [col['Field'] for col in columnas_pago]
        
        # Buscar la columna correcta para pago de préstamos
        columna_monto_pago = None
        posibles_nombres_pago = ['Monto_Pagado', 'monto_pagado', 'Monto', 'monto', 'cantidad', 'Cantidad']
        
        for nombre in posibles_nombres_pago:
            if nombre in columnas_pago_nombres:
                columna_monto_pago = nombre
                break
        
        if columna_monto_pago:
            cursor.execute(f"""
                SELECT COALESCE(SUM({columna_monto_pago}), 0) as total
                FROM Pago_Prestamo 
                WHERE ID_Reunion = %s
            """, (id_reunion,))
            resultado = cursor.fetchone()
            totales['total_pagos_prestamos'] = float(resultado['total']) if resultado else 0
        else:
            st.error(f"❌ No se encontró columna de monto en Pago_Prestamo. Columnas disponibles: {columnas_pago_nombres}")
            totales['total_pagos_prestamos'] = 0

        # 4) TOTAL PAGOS MULTAS - Verificar nombre exacto
        cursor.execute("SHOW COLUMNS FROM Pago_Multa")
        columnas_multa = cursor.fetchall()
        columnas_multa_nombres = [col['Field'] for col in columnas_multa]
        
        # Buscar la columna correcta para pago de multas
        columna_monto_multa = None
        posibles_nombres_multa = ['Monto_Pagado', 'monto_pagado', 'Monto', 'monto', 'cantidad', 'Cantidad']
        
        for nombre in posibles_nombres_multa:
            if nombre in columnas_multa_nombres:
                columna_monto_multa = nombre
                break
        
        if columna_monto_multa:
            cursor.execute(f"""
                SELECT COALESCE(SUM({columna_monto_multa}), 0) as total
                FROM Pago_Multa 
                WHERE ID_Reunion = %s
            """, (id_reunion,))
            resultado = cursor.fetchone()
            totales['total_pagos_multas'] = float(resultado['total']) if resultado else 0
        else:
            st.error(f"❌ No se encontró columna de monto en Pago_Multa. Columnas disponibles: {columnas_multa_nombres}")
            totales['total_pagos_multas'] = 0

        return totales

    except Exception as e:
        st.error(f"Error al obtener totales de reunión: {e}")
        return {'total_ahorros': 0, 'total_prestamos': 0, 'total_pagos_prestamos': 0, 'total_pagos_multas': 0}

# =====================================================================================
#  CREAR MOVIMIENTOS AUTOMÁTICOS
# =====================================================================================

def crear_movimientos_automaticos(cursor, con, id_reunion, totales, saldo_anterior):
    try:
        # Eliminar movimientos existentes para esta reunión
        cursor.execute("DELETE FROM Movimiento_de_caja WHERE ID_Reunion = %s", (id_reunion,))
        
        saldo_actual = saldo_anterior
        fecha_actual = datetime.now()
        
        # MOVIMIENTO 1: AHORROS (INGRESO)
        if totales['total_ahorros'] > 0:
            saldo_actual += totales['total_ahorros']
            cursor.execute("""
                INSERT INTO Movimiento_de_caja 
                (ID_Reunion, ID_Tipo_movimiento, monto, categoria, descripcion, fecha, saldo_final)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                id_reunion, 
                1,  # ID para Ahorro
                totales['total_ahorros'],
                'Ahorro',
                'Total de ahorros de la reunión',
                fecha_actual,
                saldo_actual
            ))

        # MOVIMIENTO 2: PRÉSTAMOS (EGRESO)
        if totales['total_prestamos'] > 0:
            saldo_actual -= totales['total_prestamos']
            cursor.execute("""
                INSERT INTO Movimiento_de_caja 
                (ID_Reunion, ID_Tipo_movimiento, monto, categoria, descripcion, fecha, saldo_final)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                id_reunion, 
                2,  # ID para Préstamo
                totales['total_prestamos'],
                'Préstamo',
                'Total de préstamos aprobados',
                fecha_actual,
                saldo_actual
            ))

        # MOVIMIENTO 3: PAGOS PRÉSTAMOS (INGRESO)
        if totales['total_pagos_prestamos'] > 0:
            saldo_actual += totales['total_pagos_prestamos']
            cursor.execute("""
                INSERT INTO Movimiento_de_caja 
                (ID_Reunion, ID_Tipo_movimiento, monto, categoria, descripcion, fecha, saldo_final)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                id_reunion, 
                3,  # ID para Pago Préstamo
                totales['total_pagos_prestamos'],
                'Pago Préstamo',
                'Total de pagos de préstamos',
                fecha_actual,
                saldo_actual
            ))

        # MOVIMIENTO 4: PAGOS MULTAS (INGRESO)
        if totales['total_pagos_multas'] > 0:
            saldo_actual += totales['total_pagos_multas']
            cursor.execute("""
                INSERT INTO Movimiento_de_caja 
                (ID_Reunion, ID_Tipo_movimiento, monto, categoria, descripcion, fecha, saldo_final)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                id_reunion, 
                4,  # ID para Pago Multa
                totales['total_pagos_multas'],
                'Pago Multa',
                'Total de pagos de multas',
                fecha_actual,
                saldo_actual
            ))

        con.commit()
        return saldo_actual

    except Exception as e:
        con.rollback()
        st.error(f"Error al crear movimientos automáticos: {e}")
        return saldo_anterior

# =====================================================================================
#  RESUMEN AUTOMÁTICO
# =====================================================================================

def resumen_automatico(cursor, con, id_reunion, saldo_anterior):
    st.subheader("📊 Resumen Automático de Caja")

    # Obtener totales de la reunión
    totales = obtener_totales_reunion(cursor, id_reunion)
    
    # Mostrar resumen de totales
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Ingresos")
        st.info(f"💰 **Ahorros:** ${totales['total_ahorros']:,.2f}")
        st.info(f"💳 **Pagos Préstamos:** ${totales['total_pagos_prestamos']:,.2f}")
        st.info(f"⚖️ **Pagos Multas:** ${totales['total_pagos_multas']:,.2f}")
        
        total_ingresos = totales['total_ahorros'] + totales['total_pagos_prestamos'] + totales['total_pagos_multas']
        st.success(f"**📊 TOTAL INGRESOS:** ${total_ingresos:,.2f}")

    with col2:
        st.subheader("📉 Egresos")
        st.warning(f"📤 **Préstamos:** ${totales['total_prestamos']:,.2f}")
        st.success(f"**📊 TOTAL EGRESOS:** ${totales['total_prestamos']:,.2f}")

    # Calcular saldo final
    total_ingresos = totales['total_ahorros'] + totales['total_pagos_prestamos'] + totales['total_pagos_multas']
    total_egresos = totales['total_prestamos']
    saldo_final_calculado = saldo_anterior + total_ingresos - total_egresos

    # Mostrar métricas principales
    st.divider()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💰 Saldo Inicial", f"${saldo_anterior:,.2f}")
    with col2:
        st.metric("📈 Total Ingresos", f"${total_ingresos:,.2f}")
    with col3:
        st.metric("📉 Total Egresos", f"${total_egresos:,.2f}")
    with col4:
        st.metric("💵 Saldo Final", f"${saldo_final_calculado:,.2f}")

    # Mostrar información de depuración
    with st.expander("🔍 Ver detalles de consultas"):
        st.write("**Estructura de tablas encontradas:**")
        st.write("- Prestamo: usando columna 'monto'")
        st.write("- Ahorro: usando columna 'Monto_Ahorro'")
        
        cursor.execute("SHOW COLUMNS FROM Pago_Prestamo")
        st.write("- Pago_Prestamo:", [col['Field'] for col in cursor.fetchall()])
        
        cursor.execute("SHOW COLUMNS FROM Pago_Multa")
        st.write("- Pago_Multa:", [col['Field'] for col in cursor.fetchall()])

    # Botón para actualizar movimientos en base de datos
    if st.button("🔄 Actualizar Movimientos de Caja", type="primary"):
        with st.spinner("Actualizando movimientos en el sistema..."):
            saldo_final = crear_movimientos_automaticos(cursor, con, id_reunion, totales, saldo_anterior)
            st.success("✅ Movimientos de caja actualizados correctamente!")
            st.rerun()

# =====================================================================================
#  DETALLE DE MOVIMIENTOS
# =====================================================================================

def detalle_movimientos(cursor, id_reunion, saldo_anterior):
    st.subheader("📋 Detalle de Movimientos Registrados")

    try:
        cursor.execute("""
            SELECT mc.*, tm.nombre AS nombre_movimiento
            FROM Movimiento_de_caja mc
            JOIN Tipo_de_movimiento tm ON mc.ID_Tipo_movimiento = tm.ID_Tipo_movimiento
            WHERE mc.ID_Reunion = %s
            ORDER BY mc.fecha ASC, mc.ID_Movimiento_caja ASC
        """, (id_reunion,))

        movimientos = cursor.fetchall()

        if not movimientos:
            st.info("📭 No hay movimientos registrados para esta reunión.")
            st.info("💡 Ve a la pestaña 'Resumen Automático' y haz clic en 'Actualizar Movimientos de Caja'")
            return

        st.write(f"**Saldo Inicial:** ${saldo_anterior:,.2f}")
        st.divider()

        saldo_actual = saldo_anterior
        
        for mov in movimientos:
            # Determinar el tipo basado en la categoría
            categoria = mov['categoria']
            if categoria in ['Préstamo']:
                tipo = "Egreso"
                icono = "📤"
                color = "red"
            else:
                tipo = "Ingreso"
                icono = "💹"
                color = "green"
            
            # Calcular saldo actual
            if tipo == "Ingreso":
                saldo_actual += float(mov['monto'])
            else:
                saldo_actual -= float(mov['monto'])
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{mov['descripcion']}**")
                st.caption(f"📅 {mov['fecha'].strftime('%Y-%m-%d %H:%M')} — {mov['nombre_movimiento']} — {tipo}")
            with col2:
                st.write(f"<span style='color:{color}'>{icono} ${mov['monto']:,.2f}</span>", unsafe_allow_html=True)
                st.write(f"💰 **${saldo_actual:,.2f}**")
            
            st.divider()

    except Exception as e:
        st.error(f"❌ Error al cargar detalle de movimientos: {e}")

# =====================================================================================
#  EJECUTABLE
# =====================================================================================

def main():
    mostrar_movimiento_caja()

if __name__ == "__main__":
    main()
