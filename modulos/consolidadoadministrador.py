import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar
import sys
import os

# Agregar la ruta de tus módulos
sys.path.append(os.path.dirname(__file__))

# =============================================
#  CONFIGURACIÓN INICIAL
# =============================================

def verificar_modulos():
    """Verifica que los módulos necesarios estén disponibles."""
    st.sidebar.write("### 🔧 Verificación de Módulos")
    
    try:
        from modulos.config.conexion import obtener_conexion
        st.sidebar.success("✅ Módulos de BD - CONECTADOS")
        return True
    except ImportError as e:
        st.sidebar.error(f"❌ Error conectando a BD: {e}")
        return False

# =============================================
#  VERIFICACIÓN DE USUARIO ADMINISTRADOR
# =============================================

def verificar_usuario_administrador():
    """Verifica que el usuario sea administrador."""
    user_type = st.session_state.get("user_type")
    if user_type != "administrador":
        st.error("🔒 Esta funcionalidad es exclusiva para administradores.")
        return False
    return True

# =============================================
#  OBTENER DISTRITOS DISPONIBLES
# =============================================

def obtener_distritos():
    """Obtiene todos los distritos disponibles en la base de datos."""
    try:
        from modulos.config.conexion import obtener_conexion
        
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT DISTINCT 
                d.ID_Distrito,
                d.nombre_distrito,
                COUNT(DISTINCT g.ID_Grupo) as total_grupos,
                COUNT(DISTINCT m.ID_Miembro) as total_miembros
            FROM Distrito d
            LEFT JOIN Grupo g ON d.ID_Distrito = g.ID_Distrito
            LEFT JOIN Miembro m ON g.ID_Grupo = m.ID_Grupo AND m.ID_Estado = 1
            GROUP BY d.ID_Distrito, d.nombre_distrito
            ORDER BY d.nombre_distrito
        """)
        
        distritos = cursor.fetchall()
        cursor.close()
        con.close()
        
        return distritos
    except Exception as e:
        st.error(f"❌ Error obteniendo distritos: {e}")
        return []

# =============================================
#  FUNCIONES PARA OBTENER DATOS POR MES Y DISTRITO
# =============================================

def obtener_ahorros_por_mes_distrito(id_distrito, año, mes):
    """Obtiene los ahorros de un distrito en un mes específico."""
    try:
        from modulos.config.conexion import obtener_conexion
        
        fecha_inicio = datetime(año, mes, 1)
        ultimo_dia = calendar.monthrange(año, mes)[1]
        fecha_fin = datetime(año, mes, ultimo_dia)
        
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                COALESCE(SUM(a.monto_ahorro), 0) as total_ahorros,
                COALESCE(SUM(a.monto_otros), 0) as total_otros,
                COUNT(DISTINCT a.ID_Miembro) as miembros_ahorrando
            FROM Ahorro a
            JOIN Miembro m ON a.ID_Miembro = m.ID_Miembro
            JOIN Grupo g ON m.ID_Grupo = g.ID_Grupo
            JOIN Reunion r ON a.ID_Reunion = r.ID_Reunion
            WHERE g.ID_Distrito = %s 
            AND r.fecha BETWEEN %s AND %s
        """, (id_distrito, fecha_inicio, fecha_fin))
        
        resultado = cursor.fetchone()
        cursor.close()
        con.close()
        
        total_ahorros = float(resultado['total_ahorros'] or 0)
        total_otros = float(resultado['total_otros'] or 0)
        
        return total_ahorros + total_otros
        
    except Exception as e:
        st.error(f"❌ Error obteniendo ahorros del distrito: {e}")
        return 0.0

def obtener_prestamos_por_mes_distrito(id_distrito, año, mes):
    """Obtiene los préstamos desembolsados de un distrito en un mes específico."""
    try:
        from modulos.config.conexion import obtener_conexion
        
        fecha_inicio = datetime(año, mes, 1)
        ultimo_dia = calendar.monthrange(año, mes)[1]
        fecha_fin = datetime(año, mes, ultimo_dia)
        
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                COALESCE(SUM(p.monto), 0) as total_prestamos,
                COUNT(*) as total_desembolsos
            FROM Prestamo p
            JOIN Miembro m ON p.ID_Miembro = m.ID_Miembro
            JOIN Grupo g ON m.ID_Grupo = g.ID_Grupo
            WHERE g.ID_Distrito = %s 
            AND p.fecha_desembolso BETWEEN %s AND %s
            AND p.ID_Estado_prestamo != 3  -- Excluir cancelados/rechazados
        """, (id_distrito, fecha_inicio, fecha_fin))
        
        resultado = cursor.fetchone()
        cursor.close()
        con.close()
        
        return float(resultado['total_prestamos'] or 0)
        
    except Exception as e:
        st.error(f"❌ Error obteniendo préstamos del distrito: {e}")
        return 0.0

def obtener_pagos_prestamos_por_mes_distrito(id_distrito, año, mes):
    """Obtiene los pagos de préstamos de un distrito en un mes específico."""
    try:
        from modulos.config.conexion import obtener_conexion
        
        fecha_inicio = datetime(año, mes, 1)
        ultimo_dia = calendar.monthrange(año, mes)[1]
        fecha_fin = datetime(año, mes, ultimo_dia)
        
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                COALESCE(SUM(pp.monto_pagado), 0) as total_pagos,
                COUNT(*) as total_pagos_realizados
            FROM PagoPrestamo pp
            JOIN Prestamo p ON pp.ID_Prestamo = p.ID_Prestamo
            JOIN Miembro m ON p.ID_Miembro = m.ID_Miembro
            JOIN Grupo g ON m.ID_Grupo = g.ID_Grupo
            WHERE g.ID_Distrito = %s 
            AND pp.fecha_pago BETWEEN %s AND %s
        """, (id_distrito, fecha_inicio, fecha_fin))
        
        resultado = cursor.fetchone()
        cursor.close()
        con.close()
        
        return float(resultado['total_pagos'] or 0)
        
    except Exception as e:
        st.error(f"❌ Error obteniendo pagos de préstamos del distrito: {e}")
        return 0.0

def obtener_pagos_multas_por_mes_distrito(id_distrito, año, mes):
    """Obtiene los pagos de multas de un distrito en un mes específico."""
    try:
        from modulos.config.conexion import obtener_conexion
        
        fecha_inicio = datetime(año, mes, 1)
        ultimo_dia = calendar.monthrange(año, mes)[1]
        fecha_fin = datetime(año, mes, ultimo_dia)
        
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                COALESCE(SUM(pm.monto_pagado), 0) as total_multas,
                COUNT(*) as total_multas_pagadas
            FROM PagoMulta pm
            JOIN Miembro m ON pm.ID_Miembro = m.ID_Miembro
            JOIN Grupo g ON m.ID_Grupo = g.ID_Grupo
            WHERE g.ID_Distrito = %s 
            AND pm.fecha_pago BETWEEN %s AND %s
        """, (id_distrito, fecha_inicio, fecha_fin))
        
        resultado = cursor.fetchone()
        cursor.close()
        con.close()
        
        return float(resultado['total_multas'] or 0)
        
    except Exception as e:
        st.error(f"❌ Error obteniendo pagos de multas del distrito: {e}")
        return 0.0

def obtener_intereses_por_mes_distrito(id_distrito, año, mes):
    """Obtiene los intereses generados por préstamos de un distrito en un mes específico."""
    try:
        from modulos.config.conexion import obtener_conexion
        
        fecha_inicio = datetime(año, mes, 1)
        ultimo_dia = calendar.monthrange(año, mes)[1]
        fecha_fin = datetime(año, mes, ultimo_dia)
        
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                COALESCE(SUM(p.total_interes), 0) as total_intereses
            FROM Prestamo p
            JOIN Miembro m ON p.ID_Miembro = m.ID_Miembro
            JOIN Grupo g ON m.ID_Grupo = g.ID_Grupo
            WHERE g.ID_Distrito = %s 
            AND p.fecha_desembolso BETWEEN %s AND %s
            AND p.ID_Estado_prestamo != 3  -- Excluir cancelados/rechazados
        """, (id_distrito, fecha_inicio, fecha_fin))
        
        resultado = cursor.fetchone()
        cursor.close()
        con.close()
        
        return float(resultado['total_intereses'] or 0)
        
    except Exception as e:
        st.error(f"❌ Error obteniendo intereses del distrito: {e}")
        return 0.0

# =============================================
#  CÁLCULO DE INGRESOS, EGRESOS Y BALANCE
# =============================================

def calcular_consolidado_mensual_distrito(id_distrito, año, mes):
    """Calcula ingresos, egresos y balance para un distrito en un mes específico."""
    
    # INGRESOS
    ahorros = obtener_ahorros_por_mes_distrito(id_distrito, año, mes)
    pagos_multas = obtener_pagos_multas_por_mes_distrito(id_distrito, año, mes)
    pagos_prestamos = obtener_pagos_prestamos_por_mes_distrito(id_distrito, año, mes)
    intereses = obtener_intereses_por_mes_distrito(id_distrito, año, mes)
    
    # EGRESOS (préstamos desembolsados)
    prestamos_desembolsados = obtener_prestamos_por_mes_distrito(id_distrito, año, mes)
    
    # CÁLCULOS FINALES
    total_ingresos = ahorros + pagos_multas + pagos_prestamos + intereses
    total_egresos = prestamos_desembolsados
    balance = total_ingresos - total_egresos
    
    return {
        'ingresos': total_ingresos,
        'egresos': total_egresos,
        'balance': balance,
        'detalle_ingresos': {
            'ahorros': ahorros,
            'pagos_multas': pagos_multas,
            'pagos_prestamos': pagos_prestamos,
            'intereses': intereses
        },
        'detalle_egresos': {
            'prestamos_desembolsados': prestamos_desembolsados
        }
    }

def obtener_consolidado_anual_distrito(id_distrito, año):
    """Obtiene el consolidado mensual para todo un año de un distrito."""
    consolidado_mensual = []
    
    for mes in range(1, 13):
        datos_mes = calcular_consolidado_mensual_distrito(id_distrito, año, mes)
        consolidado_mensual.append({
            'mes': mes,
            'nombre_mes': calendar.month_name[mes],
            'año': año,
            **datos_mes
        })
    
    return consolidado_mensual

# =============================================
#  GRÁFICAS Y VISUALIZACIONES
# =============================================

def crear_grafica_ingresos_egresos_balance(df):
    """Crea gráfica de líneas para ingresos, egresos y balance."""
    fig = go.Figure()
    
    # Línea de ingresos
    fig.add_trace(go.Scatter(
        x=df['mes_año'],
        y=df['ingresos'],
        mode='lines+markers',
        name='Ingresos',
        line=dict(color='#2E8B57', width=3),
        marker=dict(size=8)
    ))
    
    # Línea de egresos
    fig.add_trace(go.Scatter(
        x=df['mes_año'],
        y=df['egresos'],
        mode='lines+markers',
        name='Egresos',
        line=dict(color='#DC143C', width=3),
        marker=dict(size=8)
    ))
    
    # Línea de balance
    fig.add_trace(go.Scatter(
        x=df['mes_año'],
        y=df['balance'],
        mode='lines+markers',
        name='Balance',
        line=dict(color='#1E90FF', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title='📈 Evolución Mensual: Ingresos, Egresos y Balance',
        xaxis_title='Mes',
        yaxis_title='Monto ($)',
        hovermode='x unified',
        height=400
    )
    
    return fig

def crear_grafica_composicion_ingresos(df_detalle):
    """Crea gráfica de torta para la composición de ingresos."""
    labels = ['Ahorros', 'Pagos de Multas', 'Pagos de Préstamos', 'Intereses']
    values = [
        df_detalle['ahorros'],
        df_detalle['pagos_multas'],
        df_detalle['pagos_prestamos'],
        df_detalle['intereses']
    ]
    
    # Filtrar valores cero
    filtered_labels = []
    filtered_values = []
    for label, value in zip(labels, values):
        if value > 0:
            filtered_labels.append(label)
            filtered_values.append(value)
    
    if not filtered_values:
        return None
    
    fig = px.pie(
        names=filtered_labels,
        values=filtered_values,
        title='📊 Composición de Ingresos',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return fig

def crear_grafica_barras_comparativa(df_distritos):
    """Crea gráfica de barras comparativa entre distritos."""
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Ingresos',
        x=df_distritos['nombre_distrito'],
        y=df_distritos['ingresos'],
        marker_color='#2E8B57'
    ))
    
    fig.add_trace(go.Bar(
        name='Egresos',
        x=df_distritos['nombre_distrito'],
        y=df_distritos['egresos'],
        marker_color='#DC143C'
    ))
    
    fig.add_trace(go.Bar(
        name='Balance',
        x=df_distritos['nombre_distrito'],
        y=df_distritos['balance'],
        marker_color='#1E90FF'
    ))
    
    fig.update_layout(
        title='📊 Comparativa de Distritos',
        xaxis_title='Distritos',
        yaxis_title='Monto ($)',
        barmode='group',
        height=400
    )
    
    return fig

# =============================================
#  INTERFAZ PRINCIPAL
# =============================================

def mostrar_consolidado_administrador():
    """Función principal para mostrar el consolidado del administrador por distritos."""
    
    st.title("🏢 Consolidado Mensual - Administrador")
    
    # Verificar que el usuario sea administrador
    if not verificar_usuario_administrador():
        return
    
    # Obtener distritos
    distritos = obtener_distritos()
    if not distritos:
        st.info("ℹ️ No se encontraron distritos en la base de datos.")
        return
    
    st.sidebar.write("### ⚙️ Configuración del Reporte")
    
    # Selector de año
    año_actual = datetime.now().year
    años = list(range(año_actual - 2, año_actual + 1))
    año_seleccionado = st.sidebar.selectbox(
        "Seleccionar Año",
        años,
        index=años.index(año_actual)
    )
    
    # Selector de vista
    vista = st.sidebar.radio(
        "Tipo de Vista",
        ["📈 Vista Detallada por Distrito", "📊 Vista Comparativa entre Distritos"]
    )
    
    if vista == "📈 Vista Detallada por Distrito":
        mostrar_vista_detallada_distritos(distritos, año_seleccionado)
    else:
        mostrar_vista_comparativa_distritos(distritos, año_seleccionado)

def mostrar_vista_detallada_distritos(distritos, año):
    """Muestra vista detallada para cada distrito."""
    
    st.header("📈 Vista Detallada por Distrito")
    
    # Selector de distrito
    nombres_distritos = [f"{d['nombre_distrito']} ({d['total_grupos']} grupos, {d['total_miembros']} miembros)" for d in distritos]
    distrito_seleccionado = st.selectbox("Seleccionar Distrito", nombres_distritos)
    
    distrito_idx = nombres_distritos.index(distrito_seleccionado)
    distrito = distritos[distrito_idx]
    
    st.subheader(f"📋 Consolidado Anual {año} - {distrito['nombre_distrito']}")
    
    # Obtener datos del año completo
    with st.spinner("Calculando consolidado mensual del distrito..."):
        consolidado_anual = obtener_consolidado_anual_distrito(distrito['ID_Distrito'], año)
    
    # Crear DataFrame para gráficas
    df_mensual = pd.DataFrame(consolidado_anual)
    df_mensual['mes_año'] = df_mensual['nombre_mes'] + ' ' + df_mensual['año'].astype(str)
    
    # Mostrar métricas principales
    total_ingresos = df_mensual['ingresos'].sum()
    total_egresos = df_mensual['egresos'].sum()
    total_balance = df_mensual['balance'].sum()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💰 Ingresos Totales", f"${total_ingresos:,.2f}")
    with col2:
        st.metric("💸 Egresos Totales", f"${total_egresos:,.2f}")
    with col3:
        st.metric("⚖️ Balance Total", f"${total_balance:,.2f}")
    with col4:
        st.metric("🏘️ Grupos", distrito['total_grupos'])
    
    # Gráfica principal
    st.plotly_chart(crear_grafica_ingresos_egresos_balance(df_mensual), 
                   use_container_width=True)
    
    # Gráficas de composición (último mes con datos)
    ultimo_mes_con_datos = None
    for mes_data in reversed(consolidado_anual):
        if mes_data['ingresos'] > 0:
            ultimo_mes_con_datos = mes_data
            break
    
    if ultimo_mes_con_datos:
        col1, col2 = st.columns(2)
        
        with col1:
            grafica_torta = crear_grafica_composicion_ingresos(
                ultimo_mes_con_datos['detalle_ingresos']
            )
            if grafica_torta:
                st.plotly_chart(grafica_torta, use_container_width=True)
        
        with col2:
            # Tabla detallada del último mes
            st.write(f"**📋 Detalle del Mes: {ultimo_mes_con_datos['nombre_mes']}**")
            detalle_data = {
                'Concepto': ['Ahorros', 'Pagos Multas', 'Pagos Préstamos', 'Intereses', 'Préstamos Desembolsados'],
                'Monto': [
                    f"${ultimo_mes_con_datos['detalle_ingresos']['ahorros']:,.2f}",
                    f"${ultimo_mes_con_datos['detalle_ingresos']['pagos_multas']:,.2f}",
                    f"${ultimo_mes_con_datos['detalle_ingresos']['pagos_prestamos']:,.2f}",
                    f"${ultimo_mes_con_datos['detalle_ingresos']['intereses']:,.2f}",
                    f"${ultimo_mes_con_datos['detalle_egresos']['prestamos_desembolsados']:,.2f}"
                ]
            }
            st.dataframe(pd.DataFrame(detalle_data), use_container_width=True)
    
    # Tabla resumen anual
    st.write("### 📊 Tabla Resumen Anual")
    resumen_data = {
        'Mes': [m['nombre_mes'] for m in consolidado_anual],
        'Ingresos': [f"${m['ingresos']:,.2f}" for m in consolidado_anual],
        'Egresos': [f"${m['egresos']:,.2f}" for m in consolidado_anual],
        'Balance': [f"${m['balance']:,.2f}" for m in consolidado_anual],
        'Estado': ['✅ Positivo' if m['balance'] >= 0 else '⚠️ Negativo' for m in consolidado_anual]
    }
    st.dataframe(pd.DataFrame(resumen_data), use_container_width=True)

def mostrar_vista_comparativa_distritos(distritos, año):
    """Muestra vista comparativa entre todos los distritos."""
    
    st.header("📊 Vista Comparativa entre Distritos")
    
    # Obtener datos de todos los distritos
    datos_distritos = []
    
    with st.spinner("Recopilando datos de todos los distritos..."):
        for distrito in distritos:
            consolidado_anual = obtener_consolidado_anual_distrito(distrito['ID_Distrito'], año)
            
            # Calcular totales anuales
            total_ingresos = sum(m['ingresos'] for m in consolidado_anual)
            total_egresos = sum(m['egresos'] for m in consolidado_anual)
            total_balance = sum(m['balance'] for m in consolidado_anual)
            
            datos_distritos.append({
                'nombre_distrito': distrito['nombre_distrito'],
                'total_grupos': distrito['total_grupos'],
                'total_miembros': distrito['total_miembros'],
                'ingresos': total_ingresos,
                'egresos': total_egresos,
                'balance': total_balance
            })
    
    df_distritos = pd.DataFrame(datos_distritos)
    
    # Gráfica comparativa
    st.plotly_chart(crear_grafica_barras_comparativa(df_distritos), 
                   use_container_width=True)
    
    # Tabla comparativa
    st.write("### 📋 Tabla Comparativa de Distritos")
    
    tabla_comparativa = {
        'Distrito': df_distritos['nombre_distrito'],
        'Grupos': df_distritos['total_grupos'],
        'Miembros': df_distritos['total_miembros'],
        'Ingresos Totales': [f"${ing:,.2f}" for ing in df_distritos['ingresos']],
        'Egresos Totales': [f"${egr:,.2f}" for egr in df_distritos['egresos']],
        'Balance Total': [f"${bal:,.2f}" for bal in df_distritos['balance']],
        'Rendimiento': [
            '🟢 Alto' if bal > df_distritos['balance'].mean() * 1.5 else 
            '🟡 Medio' if bal > 0 else 
            '🔴 Bajo' for bal in df_distritos['balance']
        ]
    }
    
    st.dataframe(pd.DataFrame(tabla_comparativa), use_container_width=True)
    
    # Métricas generales
    st.write("### 📈 Métricas Generales")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Distritos", len(distritos))
    with col2:
        st.metric("Ingresos Promedio", f"${df_distritos['ingresos'].mean():,.2f}")
    with col3:
        st.metric("Mejor Balance", f"${df_distritos['balance'].max():,.2f}")
    with col4:
        st.metric("Peor Balance", f"${df_distritos['balance'].min():,.2f}")

# =============================================
#  FUNCIÓN PRINCIPAL
# =============================================

def mostrar_consolidado_distritos():
    """Función principal que se llama desde app.py para administradores."""
    if not verificar_usuario_administrador():
        return
        
    verificar_modulos()
    mostrar_consolidado_administrador()

# =============================================
#  EJECUCIÓN PRINCIPAL (PARA PRUEBAS)
# =============================================

if __name__ == "__main__":
    # Para testing - simular sesión de administrador
    if "user_type" not in st.session_state:
        st.session_state.user_type = "administrador"
        st.session_state.user_id = 1
    
    mostrar_consolidado_distritos()
