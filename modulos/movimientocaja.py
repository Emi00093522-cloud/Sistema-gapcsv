import streamlit as st
from modulos.config.conexion import obtener_conexion
from datetime import datetime

def mostrar_movimiento_caja():
    st.header("💰 Movimientos de Caja - Sistema Automático")

    # Verificar si hay una reunión seleccionada
    if 'reunion_actual' not in st.session_state:
        st.warning("⚠️ Primero debes seleccionar una reunión en el módulo de Asistencia.")
        return

    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)

        # Obtener la reunión del session_state
        reunion_info = st.session_state.reunion_actual
        id_reunion = reunion_info['id_reunion']
        id_grupo = reunion_info['id_grupo']
        nombre_reunion = reunion_info['nombre_reunion']

        # Mostrar información de la reunión actual
        st.info(f"📅 **Reunión actual:** {nombre_reunion}")

        # OBTENER SALDO ANTERIOR (último saldo_final de la reunión anterior)
        saldo_anterior = obtener_saldo_anterior(cursor, id_reunion, id_grupo)
        
        # Mostrar saldo anterior (saldo inicial de esta reunión)
        st.success(f"💰 **Saldo inicial en caja fuerte: ${saldo_anterior:,.2f}**")

        # Pestañas para diferentes funcionalidades
        tab1, tab2 = st.tabs(["📊 Resumen Automático", "📋 Detalle de Movimientos"])

        with tab1:
            resumen_automatico(cursor, con, id_reunion, saldo_anterior)

        with tab2:
            detalle_movimientos(cursor, id_reunion, saldo_anterior)

    except Exception as e:
        st.error(f"❌ Error general: {e}")

    finally:
        if "cursor" in locals():
            cursor.close()
        if "con" in locals():
            con.close()

def obtener_saldo_anterior(cursor, id_reunion_actual, id_grupo):
    """
    Obtiene el último saldo_final de la reunión anterior para este grupo
    """
    try:
        # Buscar la reunión anterior para este grupo - USANDO EL NOMBRE CORRECTO DE TABLA
        cursor.execute("""
            SELECT ID_Reunion 
            FROM Reunion 
            WHERE ID_Grupo = %s AND ID_Reunion < %s 
            ORDER BY ID_Reunion DESC 
            LIMIT 1
        """, (id_grupo, id_reunion_actual))
        
        reunion_anterior = cursor.fetchone()
        
        if reunion_anterior:
            # Obtener el último saldo_final de esa reunión
            cursor.execute("""
                SELECT saldo_final 
                FROM Movimiento_de_caja 
                WHERE ID_Reunion = %s 
                ORDER BY fecha DESC, ID_Movimiento_caja DESC 
                LIMIT 1
            """, (reunion_anterior['ID_Reunion'],))
            
            movimiento_anterior = cursor.fetchone()
            return movimiento_anterior['saldo_final'] if movimiento_anterior else 0
        else:
            return 0  # Primera reunión del grupo
            
    except Exception as e:
        st.error(f"Error al obtener saldo anterior: {e}")
        return 0

def obtener_tipo_movimiento_id(cursor, tipo_ingreso_egreso, categoria):
    """
    Obtiene el ID_Tipo_movimiento basado en tipo y categoría
    """
    try:
        # USANDO EL NOMBRE CORRECTO DE COLUMNAS
        cursor.execute("""
            SELECT ID_Tipo_movimiento 
            FROM Tipo_de_movimiento 
            WHERE tipo = %s AND nombre = %s
        """, (tipo_ingreso_egreso, categoria))
        
        resultado = cursor.fetchone()
        return resultado['ID_Tipo_movimiento'] if resultado else None
        
    except Exception as e:
        st.error(f"Error al obtener ID_Tipo_movimiento: {e}")
        return None

def obtener_movimientos_automaticos(cursor, id_reunion):
    """
    Obtiene todos los movimientos automáticos de los diferentes módulos
    """
    movimientos = []
    
    try:
        # 1. AHORROS (INGRESOS) - USANDO NOMBRES CORRECTOS DE TABLAS
        cursor.execute("""
            SELECT Monto_Ahorro as monto, Fecha_Ahorro as fecha, 'Ahorro' as categoria, 
                   CONCAT('Ahorro de ', m.Nombre) as descripcion,
                   'Ingreso' as tipo_ingreso_egreso
            FROM Ahorro a
            JOIN Miembro m ON a.ID_Miembro = m.ID_Miembro
            WHERE a.ID_Reunion = %s
        """, (id_reunion,))
        ahorros = cursor.fetchall()
        for ahorro in ahorros:
            ahorro['ID_Tipo_movimiento'] = obtener_tipo_movimiento_id(cursor, 'Ingreso', 'Ahorro')
        movimientos.extend(ahorros)
        
        # 2. PRÉSTAMOS DESEMBOLSADOS (EGRESOS)
        cursor.execute("""
            SELECT Monto_Prestamo as monto, Fecha_Desembolso as fecha, 'Préstamo' as categoria,
                   CONCAT('Préstamo para ', m.Nombre) as descripcion,
                   'Egreso' as tipo_ingreso_egreso
            FROM Prestamo p
            JOIN Miembro m ON p.ID_Miembro = m.ID_Miembro
            WHERE p.ID_Reunion = %s AND p.Estado = 'APROBADO'
        """, (id_reunion,))
        prestamos = cursor.fetchall()
        for prestamo in prestamos:
            prestamo['ID_Tipo_movimiento'] = obtener_tipo_movimiento_id(cursor, 'Egreso', 'Préstamo')
        movimientos.extend(prestamos)
        
        # 3. PAGOS DE PRÉSTAMOS (INGRESOS)
        cursor.execute("""
            SELECT Monto_Pagado as monto, Fecha_Pago as fecha, 'Pago Préstamo' as categoria,
                   CONCAT('Pago préstamo de ', m.Nombre) as descripcion,
                   'Ingreso' as tipo_ingreso_egreso
            FROM Pago_Prestamo pp
            JOIN Prestamo p ON pp.ID_Prestamo = p.ID_Prestamo
            JOIN Miembro m ON p.ID_Miembro = m.ID_Miembro
            WHERE pp.ID_Reunion = %s
        """, (id_reunion,))
        pagos_prestamos = cursor.fetchall()
        for pago in pagos_prestamos:
            pago['ID_Tipo_movimiento'] = obtener_tipo_movimiento_id(cursor, 'Ingreso', 'Pago Préstamo')
        movimientos.extend(pagos_prestamos)
        
        # 4. PAGOS DE MULTAS (INGRESOS)
        cursor.execute("""
            SELECT Monto_Pagado as monto, Fecha_Pago as fecha, 'Pago Multa' as categoria,
                   CONCAT('Pago multa de ', m.Nombre) as descripcion,
                   'Ingreso' as tipo_ingreso_egreso
            FROM Pago_Multa pm
            JOIN Multa mt ON pm.ID_Multa = mt.ID_Multa
            JOIN Miembro m ON mt.ID_Miembro = m.ID_Miembro
            WHERE pm.ID_Reunion = %s
        """, (id_reunion,))
        pagos_multas = cursor.fetchall()
        for pago in pagos_multas:
            pago['ID_Tipo_movimiento'] = obtener_tipo_movimiento_id(cursor, 'Ingreso', 'Pago Multa')
        movimientos.extend(pagos_multas)
        
        return movimientos
        
    except Exception as e:
        st.error(f"Error al obtener movimientos automáticos: {e}")
        return []

def actualizar_saldos_finales(cursor, con, id_reunion, movimientos, saldo_anterior):
    """
    Actualiza los saldos_finales en la tabla Movimiento_de_caja
    """
    try:
        # Primero eliminar movimientos existentes de esta reunión para evitar duplicados
        cursor.execute("DELETE FROM Movimiento_de_caja WHERE ID_Reunion = %s", (id_reunion,))
        
        # Ordenar movimientos por fecha
        movimientos_ordenados = sorted(movimientos, key=lambda x: x['fecha'])
        
        saldo_actual = saldo_anterior
        
        # Insertar cada movimiento con su saldo_final
        for mov in movimientos_ordenados:
            if mov['tipo_ingreso_egreso'] == 'Ingreso':
                saldo_actual += mov['monto']
            else:
                saldo_actual -= mov['monto']
            
            # Insertar nuevo movimiento con saldo_final
            cursor.execute("""
                INSERT INTO Movimiento_de_caja 
                (ID_Reunion, ID_Tipo_movimiento, monto, categoria, descripcion, fecha, saldo_final)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (id_reunion, mov['ID_Tipo_movimiento'], mov['monto'], 
                  mov['categoria'], mov['descripcion'], mov['fecha'], saldo_actual))
        
        con.commit()
        return saldo_actual  # Retorna el saldo final
        
    except Exception as e:
        con.rollback()
        st.error(f"Error al actualizar saldos: {e}")
        return saldo_anterior

def resumen_automatico(cursor, con, id_reunion, saldo_anterior):
    st.subheader("📊 Resumen Automático de Caja")
    
    # Obtener movimientos automáticos
    movimientos = obtener_movimientos_automaticos(cursor, id_reunion)
    
    if not movimientos:
        st.info("📭 No hay movimientos registrados en los módulos para esta reunión")
        return saldo_anterior
    
    # Botón para actualizar/calcular movimientos
    if st.button("🔄 Calcular Movimientos Automáticos", type="primary"):
        # Actualizar saldos finales en la base de datos
        saldo_final = actualizar_saldos_finales(cursor, con, id_reunion, movimientos, saldo_anterior)
        
        # Calcular totales para mostrar
        total_ingresos = sum(mov['monto'] for mov in movimientos if mov['tipo_ingreso_egreso'] == 'Ingreso')
        total_egresos = sum(mov['monto'] for mov in movimientos if mov['tipo_ingreso_egreso'] == 'Egreso')
        
        # Mostrar fórmula del cuadre
        st.info("""
        **🧮 Fórmula del Cuadre Automático:**
        ```
        SALDO FINAL = Saldo Inicial + Total Ingresos - Total Egresos
        ```
        **Los movimientos vienen automáticamente de:**
        - ✅ Módulo de Ahorros
        - ✅ Módulo de Préstamos  
        - ✅ Módulo de Pagos de Préstamos
        - ✅ Módulo de Pagos de Multas
        """)
        
        # Mostrar métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("💰 Saldo Inicial", f"${saldo_anterior:,.2f}")
        
        with col2:
            st.metric("📈 Total Ingresos", f"${total_ingresos:,.2f}")
        
        with col3:
            st.metric("📉 Total Egresos", f"${total_egresos:,.2f}")
        
        with col4:
            balance_color = "normal" if saldo_final >= 0 else "inverse"
            st.metric("💵 Saldo Final", f"${saldo_final:,.2f}", delta_color=balance_color)
        
        # Mostrar cálculo detallado
        st.divider()
        st.write("**🧾 Desglose automático del cálculo:**")
        
        st.write(f"**Saldo inicial de caja fuerte:** ${saldo_anterior:,.2f}")
        st.write(f"**+ Total ingresos (Ahorros + Pagos):** ${total_ingresos:,.2f}")
        st.write(f"**- Total egresos (Préstamos):** ${total_egresos:,.2f}")
        st.write(f"**= Saldo final para caja fuerte:** **${saldo_final:,.2f}**")
        
        # Mostrar resumen por categoría
        st.divider()
        st.write("**📈 Resumen por Categoría:**")
        
        categorias = {}
        for mov in movimientos:
            categoria = mov['categoria']
            if categoria not in categorias:
                categorias[categoria] = {'ingresos': 0, 'egresos': 0, 'cantidad': 0}
            
            if mov['tipo_ingreso_egreso'] == 'Ingreso':
                categorias[categoria]['ingresos'] += mov['monto']
            else:
                categorias[categoria]['egresos'] += mov['monto']
            categorias[categoria]['cantidad'] += 1
        
        for categoria, datos in categorias.items():
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"📁 {categoria}")
            with col2:
                if datos['ingresos'] > 0:
                    st.write(f"🟢 ${datos['ingresos']:,.2f}")
                if datos['egresos'] > 0:
                    st.write(f"🔴 ${datos['egresos']:,.2f}")
            with col3:
                st.write(f"({datos['cantidad']} movimientos)")
            st.divider()
        
        return saldo_final
    else:
        st.info("👆 Presiona el botón para calcular los movimientos automáticos")
        return saldo_anterior

def detalle_movimientos(cursor, id_reunion, saldo_anterior):
    st.subheader("📋 Detalle de Movimientos con Saldo Acumulado")
    
    # Obtener movimientos de Movimiento_de_caja con información del tipo - CORREGIDO
    cursor.execute("""
        SELECT mc.*, tm.tipo, tm.nombre as nombre_movimiento
        FROM Movimiento_de_caja mc
        JOIN Tipo_de_movimiento tm ON mc.ID_Tipo_movimiento = tm.ID_Tipo_movimiento
        WHERE mc.ID_Reunion = %s 
        ORDER BY mc.fecha ASC, mc.ID_Movimiento_caja ASC
    """, (id_reunion,))
    
    movimientos = cursor.fetchall()
    
    if not movimientos:
        st.info("📭 No hay movimientos registrados para esta reunión")
        st.info("💡 Ve a la pestaña 'Resumen Automático' y presiona 'Calcular Movimientos'")
        return
    
    # Mostrar todos los movimientos con saldo acumulado
    st.write("**📋 Evolución del Saldo:**")
    
    # Mostrar saldo inicial
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.write("**💰 Saldo Inicial**")
    with col2:
        st.write("")
    with col3:
        st.write(f"**${saldo_anterior:,.2f}**")
    st.divider()
    
    for mov in movimientos:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                st.write(f"**{mov['descripcion']}**")
                st.caption(f"📁 {mov['nombre_movimiento']} • 📅 {mov['fecha'].strftime('%d/%m/%Y')}")
            
            with col2:
                tipo_color = "🟢" if mov['tipo'] == "Ingreso" else "🔴"
                st.write(f"{tipo_color} {mov['tipo']}")
            
            with col3:
                monto_style = "color: green; font-weight: bold;" if mov['tipo'] == "Ingreso" else "color: red; font-weight: bold;"
                st.markdown(f"<p style='{monto_style}'>${mov['monto']:,.2f}</p>", unsafe_allow_html=True)
            
            with col4:
                # Mostrar saldo después de este movimiento
                st.write(f"💰 ${mov['saldo_final']:,.2f}")
            
            st.divider()

# Para usar en tu app principal
def main():
    mostrar_movimiento_caja()

if __name__ == "__main__":
    main()
