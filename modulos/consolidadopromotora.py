import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar
from dateutil.relativedelta import relativedelta

# =============================================
#  CONFIGURACIÓN INICIAL
# =============================================

def verificar_modulos():
    """Verifica que los módulos necesarios estén disponibles."""
    try:
        from modulos.config.conexion import obtener_conexion
        st.sidebar.success("✅ Módulos de BD - CONECTADOS")
        return True
    except ImportError as e:
        st.sidebar.error(f"❌ Error conectando a BD: {e}")
        return False

# =============================================
#  OBTENER DATOS DEL USUARIO PROMOTORA
# =============================================

def obtener_id_promotora_desde_usuario():
    """
    Obtiene el ID de promotora basado en el usuario logueado.
    Esto asume que hay una relación entre usuarios y promotoras.
    """
    try:
        # Obtener el ID del usuario logueado desde session_state
        id_usuario = st.session_state.get("id_usuario")
        if not id_usuario:
            st.error("❌ No hay usuario logueado")
            return None
        
        from modulos.config.conexion import obtener_conexion
        
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        # Buscar la promotora asociada a este usuario
        cursor.execute("""
            SELECT p.ID_Promotora 
            FROM Promotora p 
            WHERE p.ID_Usuario = %s
        """, (id_usuario,))
        
        resultado = cursor.fetchone()
        cursor.close()
        con.close()
        
        if resultado:
            return resultado['ID_Promotora']
        else:
            st.error("❌ El usuario no está asociado a una promotora")
            return None
            
    except Exception as e:
        st.error(f"❌ Error obteniendo ID de promotora: {e}")
        return None

def verificar_es_promotora():
    """Verifica que el usuario logueado sea una promotora."""
    id_promotora = obtener_id_promotora_desde_usuario()
    return id_promotora is not None

# =============================================
#  OBTENER GRUPOS DE LA PROMOTORA
# =============================================

def obtener_grupos_promotora(id_promotora):
    """Obtiene todos los grupos asignados a una promotora."""
    try:
        from modulos.config.conexion import obtener_conexion
        
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                g.ID_Grupo,
                g.nombre as nombre_grupo,
                g.fecha_creacion,
                COUNT(m.ID_Miembro) as total_miembros
            FROM Grupo g
            LEFT JOIN Miembro m ON g.ID_Grupo = m.ID_Grupo AND m.ID_Estado = 1
            WHERE g.ID_Promotora = %s
            GROUP BY g.ID_Grupo, g.nombre_grupo, g.fecha_creacion
            ORDER BY g.nombre_grupo
        """, (id_promotora,))
        
        grupos = cursor.fetchall()
        cursor.close()
        con.close()
        
        return grupos
    except Exception as e:
        st.error(f"❌ Error obteniendo grupos: {e}")
        return []

# =============================================
#  FUNCIONES PARA OBTENER DATOS POR MES Y GRUPO
# =============================================

def obtener_ahorros_por_mes_grupo(id_grupo, año, mes):
    """Obtiene los ahorros de un grupo en un mes específico."""
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
            WHERE m.ID_Grupo = %s 
            AND a.fecha BETWEEN %s AND %s
        """, (id_grupo, fecha_inicio, fecha_fin))
        
        resultado = cursor.fetchone()
        cursor.close()
        con.close()
        
        total_ahorros = float(resultado['total_ahorros'] or 0)
        total_otros = float(resultado['total_otros'] or 0)
        
        return total_ahorros + total_otros
        
    except Exception as e:
        st.error(f"❌ Error obteniendo ahorros: {e}")
        return 0.0

def obtener_prestamos_por_mes_grupo(id_grupo, año, mes):
    """Obtiene los préstamos desembolsados de un grupo en un mes específico."""
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
            WHERE m.ID_Grupo = %s 
            AND p.fecha_desembolso BETWEEN %s AND %s
            AND p.ID_Estado_prestamo != 3  -- Excluir cancelados/rechazados
        """, (id_grupo, fecha_inicio, fecha_fin))
        
        resultado = cursor.fetchone()
        cursor.close()
        con.close()
        
        return float(resultado['total_prestamos'] or 0)
        
    except Exception as e:
        st.error(f"❌ Error obteniendo préstamos: {e}")
        return 0.0

def obtener_pagos_prestamos_por_mes_grupo(id_grupo, año, mes):
    """Obtiene los pagos de préstamos de un grupo en un mes específico."""
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
            WHERE m.ID_Grupo = %s 
            AND pp.fecha_pago BETWEEN %s AND %s
        """, (id_grupo, fecha_inicio, fecha_fin))
        
        resultado = cursor.fetchone()
        cursor.close()
        con.close()
        
        return float(resultado['total_pagos'] or 0)
        
    except Exception as e:
        st.error(f"❌ Error obteniendo pagos de préstamos: {e}")
        return 0.0

def obtener_pagos_multas_por_mes_grupo(id_grupo, año, mes):
    """Obtiene los pagos de multas de un grupo en un mes específico."""
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
            WHERE m.ID_Grupo = %s 
            AND pm.fecha_pago BETWEEN %s AND %s
        """, (id_grupo, fecha_inicio, fecha_fin))
        
        resultado = cursor.fetchone()
        cursor.close()
        con.close()
        
        return float(resultado['total_multas'] or 0)
        
    except Exception as e:
        st.error(f"❌ Error obteniendo pagos de multas: {e}")
        return 0.0

# =============================================
#  CÁLCULO DE INGRESOS, EGRESOS Y BALANCE
# =============================================

def calcular_consolidado_mensual(id_grupo, año, mes):
    """Calcula ingresos, egresos y balance para un grupo en un mes específico."""
    
    # INGRESOS
    ahorros = obtener_ahorros_por_mes_grupo(id_grupo, año, mes)
    pagos_multas = obtener_pagos_multas_por_mes_grupo(id_grupo, año, mes)
    
    # EGRESOS (préstamos desembolsados)
    prestamos_desembolsados = obtener_prestamos_por_mes_grupo(id_grupo, año, mes)
    
    # PAGOS RECIBIDOS (ingresos por recuperación)
    pagos_prestamos = obtener_pagos_prestamos_por_mes_grupo(id_grupo, año, mes)
    
    # CÁLCULOS FINALES
    total_ingresos = ahorros + pagos_multas + pagos_prestamos
    total_egresos = prestamos_desembolsados
    balance = total_ingresos - total_egresos
    
    return {
        'ingresos': total_ingresos,
        'egresos': total_egresos,
        'balance': balance,
        'detalle_ingresos': {
            'ahorros': ahorros,
            'pagos_multas': pagos_multas,
            'pagos_prestamos': pagos_prestamos
        },
        'detalle_egresos': {
            'prestamos_desembolsados': prestamos_desembolsados
        }
    }

def obtener_consolidado_anual(id_grupo, año):
    """Obtiene el consolidado mensual para todo un año."""
    consolidado_mensual = []
    
    for mes in range(1, 13):
        datos_mes = calcular_consolidado_mensual(id_grupo, año, mes)
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
    labels = ['Ahorros', 'Pagos de Multas', 'Pagos de Préstamos']
    values = [
        df_detalle['ahorros'],
        df_detalle['pagos_multas'],
        df_detalle['pagos_prestamos']
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
    
    fig.update_trace(textposition='inside', textinfo='percent+label')
    return fig

def crear_grafica_barras_comparativa(df_grupos):
    """Crea gráfica de barras comparativa entre grupos."""
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Ingresos',
        x=df_grupos['nombre_grupo'],
        y=df_grupos['ingresos'],
        marker_color='#2E8B57'
    ))
    
    fig.add_trace(go.Bar(
        name='Egresos',
        x=df_grupos['nombre_grupo'],
        y=df_grupos['egresos'],
        marker_color='#DC143C'
    ))
    
    fig.add_trace(go.Bar(
        name='Balance',
        x=df_grupos['nombre_grupo'],
        y=df_grupos['balance'],
        marker_color='#1E90FF'
    ))
    
    fig.update_layout(
        title='📊 Comparativa de Grupos',
        xaxis_title='Grupos',
        yaxis_title='Monto ($)',
        barmode='group',
        height=400
    )
    
    return fig

# =============================================
#  INTERFAZ PRINCIPAL
# =============================================

def mostrar_consolidado_promotora():
    """Función principal para mostrar el consolidado de la promotora."""
    
    st.title("📊 Consolidado Mensual - Promotora")
    
    # Verificar que el usuario sea promotora
    if not verificar_es_promotora():
        st.error("🔒 Esta funcionalidad es exclusiva para promotoras.")
        st.info("ℹ️ Tu usuario no está asociado a una promotora o no tienes grupos asignados.")
        return
    
    id_promotora = obtener_id_promotora_desde_usuario()
    if not id_promotora:
        return
    
    # Obtener grupos de la promotora
    grupos = obtener_grupos_promotora(id_promotora)
    if not grupos:
        st.info("ℹ️ No tienes grupos asignados.")
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
        ["📈 Vista Detallada por Grupo", "📊 Vista Comparativa entre Grupos"]
    )
    
    if vista == "📈 Vista Detallada por Grupo":
        mostrar_vista_detallada(grupos, año_seleccionado)
    else:
        mostrar_vista_comparativa(grupos, año_seleccionado)

def mostrar_vista_detallada(grupos, año):
    """Muestra vista detallada para cada grupo."""
    
    st.header("📈 Vista Detallada por Grupo")
    
    # Selector de grupo
    nombres_grupos = [f"{g['nombre_grupo']} ({g['total_miembros']} miembros)" for g in grupos]
    grupo_seleccionado = st.selectbox("Seleccionar Grupo", nombres_grupos)
    
    grupo_idx = nombres_grupos.index(grupo_seleccionado)
    grupo = grupos[grupo_idx]
    
    st.subheader(f"📋 Consolidado Anual {año} - {grupo['nombre_grupo']}")
    
    # Obtener datos del año completo
    with st.spinner("Calculando consolidado mensual..."):
        consolidado_anual = obtener_consolidado_anual(grupo['ID_Grupo'], año)
    
    # Crear DataFrame para gráficas
    df_mensual = pd.DataFrame(consolidado_anual)
    df_mensual['mes_año'] = df_mensual['nombre_mes'] + ' ' + df_mensual['año'].astype(str)
    
    # Mostrar métricas principales
    total_ingresos = df_mensual['ingresos'].sum()
    total_egresos = df_mensual['egresos'].sum()
    total_balance = df_mensual['balance'].sum()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💰 Ingresos Totales", f"${total_ingresos:,.2f}")
    with col2:
        st.metric("💸 Egresos Totales", f"${total_egresos:,.2f}")
    with col3:
        st.metric("⚖️ Balance Total", f"${total_balance:,.2f}", 
                 delta=f"${total_balance:,.2f}")
    
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
                'Concepto': ['Ahorros', 'Pagos Multas', 'Pagos Préstamos', 'Préstamos Desembolsados'],
                'Monto': [
                    f"${ultimo_mes_con_datos['detalle_ingresos']['ahorros']:,.2f}",
                    f"${ultimo_mes_con_datos['detalle_ingresos']['pagos_multas']:,.2f}",
                    f"${ultimo_mes_con_datos['detalle_ingresos']['pagos_prestamos']:,.2f}",
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

def mostrar_vista_comparativa(grupos, año):
    """Muestra vista comparativa entre todos los grupos."""
    
    st.header("📊 Vista Comparativa entre Grupos")
    
    # Obtener datos de todos los grupos
    datos_grupos = []
    
    with st.spinner("Recopilando datos de todos los grupos..."):
        for grupo in grupos:
            consolidado_anual = obtener_consolidado_anual(grupo['ID_Grupo'], año)
            
            # Calcular totales anuales
            total_ingresos = sum(m['ingresos'] for m in consolidado_anual)
            total_egresos = sum(m['egresos'] for m in consolidado_anual)
            total_balance = sum(m['balance'] for m in consolidado_anual)
            
            datos_grupos.append({
                'nombre_grupo': grupo['nombre_grupo'],
                'total_miembros': grupo['total_miembros'],
                'ingresos': total_ingresos,
                'egresos': total_egresos,
                'balance': total_balance
            })
    
    df_grupos = pd.DataFrame(datos_grupos)
    
    # Gráfica comparativa
    st.plotly_chart(crear_grafica_barras_comparativa(df_grupos), 
                   use_container_width=True)
    
    # Tabla comparativa
    st.write("### 📋 Tabla Comparativa de Grupos")
    
    tabla_comparativa = {
        'Grupo': df_grupos['nombre_grupo'],
        'Miembros': df_grupos['total_miembros'],
        'Ingresos Totales': [f"${ing:,.2f}" for ing in df_grupos['ingresos']],
        'Egresos Totales': [f"${egr:,.2f}" for egr in df_grupos['egresos']],
        'Balance Total': [f"${bal:,.2f}" for bal in df_grupos['balance']],
        'Rendimiento': [
            '🟢 Alto' if bal > df_grupos['balance'].mean() * 1.5 else 
            '🟡 Medio' if bal > 0 else 
            '🔴 Bajo' for bal in df_grupos['balance']
        ]
    }
    
    st.dataframe(pd.DataFrame(tabla_comparativa), use_container_width=True)
    
    # Métricas generales
    st.write("### 📈 Métricas Generales")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Grupos", len(grupos))
    with col2:
        st.metric("Ingresos Promedio", f"${df_grupos['ingresos'].mean():,.2f}")
    with col3:
        st.metric("Mejor Balance", f"${df_grupos['balance'].max():,.2f}")
    with col4:
        st.metric("Peor Balance", f"${df_grupos['balance'].min():,.2f}")

# =============================================
#  EJECUCIÓN PRINCIPAL
# =============================================

if __name__ == "__main__":
    # Para testing - simular que hay un usuario logueado
    if "id_usuario" not in st.session_state:
        st.warning("⚠️ Para probar, necesitas simular un usuario logueado")
        st.info("ℹ️ En tu app real, esto vendrá de tu sistema de autenticación")
        
        # Simular usuario de prueba (eliminar en producción)
        st.session_state.id_usuario = 1
        
    mostrar_consolidado_promotora()
