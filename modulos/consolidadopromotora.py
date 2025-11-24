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
    Esta función se adapta a tu estructura real de base de datos.
    """
    try:
        # Obtener el ID del usuario logueado
        id_usuario = st.session_state.get("id_usuario")
        if not id_usuario:
            st.error("❌ No se encontró 'id_usuario' en session_state")
            return None
        
        from modulos.config.conexion import obtener_conexion
        
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        # Intentar diferentes posibles estructuras de tabla
        consultas = [
            "SELECT ID_Promotora FROM Promotora WHERE ID_Usuario = %s",
            "SELECT id_promotora FROM promotora WHERE id_usuario = %s",
            "SELECT ID_Promotora FROM Promotora WHERE usuario_id = %s"
        ]
        
        id_promotora = None
        for consulta in consultas:
            try:
                cursor.execute(consulta, (id_usuario,))
                resultado = cursor.fetchone()
                if resultado:
                    id_promotora = resultado.get('ID_Promotora') or resultado.get('id_promotora')
                    break
            except:
                continue
        
        cursor.close()
        con.close()
        
        if id_promotora:
            return id_promotora
        else:
            st.error("❌ No se encontró promotora asociada a este usuario")
            return None
            
    except Exception as e:
        st.error(f"❌ Error obteniendo ID de promotora: {e}")
        return None

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
            GROUP BY g.ID_Grupo, g.nombre, g.fecha_creacion
            ORDER BY g.nombre
        """, (id_promotora,))
        
        grupos = cursor.fetchall()
        cursor.close()
        con.close()
        
        return grupos
    except Exception as e:
        st.error(f"❌ Error obteniendo grupos: {e}")
        return []

# =============================================
#  FUNCIONES PARA OBTENER DATOS POR MES Y GRUPO (SERIE TEMPORAL)
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

def obtener_intereses_por_mes_grupo(id_grupo, año, mes):
    """Obtiene los intereses generados por préstamos en un mes específico."""
    try:
        from modulos.config.conexion import obtener_conexion
        
        fecha_inicio = datetime(año, mes, 1)
        ultimo_dia = calendar.monthrange(año, mes)[1]
        fecha_fin = datetime(año, mes, ultimo_dia)
        
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                COALESCE(SUM(pp.monto_interes), 0) as total_intereses
            FROM PagoPrestamo pp
            JOIN Prestamo p ON pp.ID_Prestamo = p.ID_Prestamo
            JOIN Miembro m ON p.ID_Miembro = m.ID_Miembro
            WHERE m.ID_Grupo = %s 
            AND pp.fecha_pago BETWEEN %s AND %s
        """, (id_grupo, fecha_inicio, fecha_fin))
        
        resultado = cursor.fetchone()
        cursor.close()
        con.close()
        
        return float(resultado['total_intereses'] or 0)
        
    except Exception as e:
        st.error(f"❌ Error obteniendo intereses: {e}")
        return 0.0

# =============================================
#  CÁLCULO DE SERIE TEMPORAL COMPLETA
# =============================================

def calcular_serie_temporal_grupo(id_grupo, año_inicio, año_fin):
    """Calcula serie temporal completa para un grupo en un rango de años."""
    serie_temporal = []
    
    for año in range(año_inicio, año_fin + 1):
        for mes in range(1, 13):
            # Obtener datos básicos
            ahorros = obtener_ahorros_por_mes_grupo(id_grupo, año, mes)
            prestamos = obtener_prestamos_por_mes_grupo(id_grupo, año, mes)
            pagos_prestamos = obtener_pagos_prestamos_por_mes_grupo(id_grupo, año, mes)
            pagos_multas = obtener_pagos_multas_por_mes_grupo(id_grupo, año, mes)
            intereses = obtener_intereses_por_mes_grupo(id_grupo, año, mes)
            
            # Cálculos derivados
            total_ingresos = ahorros + pagos_multas + pagos_prestamos
            total_egresos = prestamos
            balance = total_ingresos - total_egresos
            rentabilidad = intereses / prestamos * 100 if prestamos > 0 else 0
            
            serie_temporal.append({
                'año': año,
                'mes': mes,
                'nombre_mes': calendar.month_name[mes],
                'periodo': f"{año}-{mes:02d}",
                'fecha': datetime(año, mes, 1),
                # Datos básicos
                'ahorros': ahorros,
                'prestamos_desembolsados': prestamos,
                'pagos_prestamos': pagos_prestamos,
                'pagos_multas': pagos_multas,
                'intereses': intereses,
                # Totales
                'total_ingresos': total_ingresos,
                'total_egresos': total_egresos,
                'balance': balance,
                # Métricas de rendimiento
                'rentabilidad': rentabilidad,
                'tasa_recuperacion': (pagos_prestamos / prestamos * 100) if prestamos > 0 else 0,
                'participacion_ahorros': (ahorros / total_ingresos * 100) if total_ingresos > 0 else 0
            })
    
    return serie_temporal

def calcular_serie_temporal_consolidada(grupos, año_inicio, año_fin):
    """Calcula serie temporal consolidada para todos los grupos."""
    serie_consolidada = []
    
    for año in range(año_inicio, año_fin + 1):
        for mes in range(1, 13):
            total_ahorros = 0
            total_prestamos = 0
            total_pagos_prestamos = 0
            total_pagos_multas = 0
            total_intereses = 0
            
            for grupo in grupos:
                ahorros = obtener_ahorros_por_mes_grupo(grupo['ID_Grupo'], año, mes)
                prestamos = obtener_prestamos_por_mes_grupo(grupo['ID_Grupo'], año, mes)
                pagos_prestamos = obtener_pagos_prestamos_por_mes_grupo(grupo['ID_Grupo'], año, mes)
                pagos_multas = obtener_pagos_multas_por_mes_grupo(grupo['ID_Grupo'], año, mes)
                intereses = obtener_intereses_por_mes_grupo(grupo['ID_Grupo'], año, mes)
                
                total_ahorros += ahorros
                total_prestamos += prestamos
                total_pagos_prestamos += pagos_prestamos
                total_pagos_multas += pagos_multas
                total_intereses += intereses
            
            total_ingresos = total_ahorros + total_pagos_multas + total_pagos_prestamos
            total_egresos = total_prestamos
            balance = total_ingresos - total_egresos
            
            serie_consolidada.append({
                'año': año,
                'mes': mes,
                'nombre_mes': calendar.month_name[mes],
                'periodo': f"{año}-{mes:02d}",
                'fecha': datetime(año, mes, 1),
                'total_ahorros': total_ahorros,
                'total_prestamos': total_prestamos,
                'total_pagos_prestamos': total_pagos_prestamos,
                'total_pagos_multas': total_pagos_multas,
                'total_intereses': total_intereses,
                'total_ingresos': total_ingresos,
                'total_egresos': total_egresos,
                'balance': balance,
                'rentabilidad_promedio': (total_intereses / total_prestamos * 100) if total_prestamos > 0 else 0
            })
    
    return serie_consolidada

# =============================================
#  GRÁFICAS DE SERIE TEMPORAL MEJORADAS
# =============================================

def crear_grafica_serie_temporal_completa(df, titulo):
    """Crea gráfica de serie temporal completa con múltiples métricas."""
    fig = go.Figure()
    
    # Ingresos vs Egresos
    fig.add_trace(go.Scatter(
        x=df['periodo'], y=df['total_ingresos'],
        mode='lines+markers', name='Ingresos Totales',
        line=dict(color='#2E8B57', width=3),
        marker=dict(size=6)
    ))
    
    fig.add_trace(go.Scatter(
        x=df['periodo'], y=df['total_egresos'],
        mode='lines+markers', name='Egresos Totales',
        line=dict(color='#DC143C', width=3),
        marker=dict(size=6)
    ))
    
    # Balance
    fig.add_trace(go.Scatter(
        x=df['periodo'], y=df['balance'],
        mode='lines+markers', name='Balance',
        line=dict(color='#1E90FF', width=3),
        marker=dict(size=6)
    ))
    
    fig.update_layout(
        title=f'📈 {titulo} - Serie Temporal Completa',
        xaxis_title='Periodo',
        yaxis_title='Monto ($)',
        hovermode='x unified',
        height=500,
        showlegend=True
    )
    
    return fig

def crear_grafica_composicion_ingresos_evolutiva(df):
    """Crea gráfica de área mostrando la evolución de la composición de ingresos."""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['periodo'], y=df['ahorros'],
        mode='lines', name='Ahorros',
        stackgroup='one',
        line=dict(width=0.5, color='#2E8B57'),
        fillcolor='rgba(46, 139, 87, 0.6)'
    ))
    
    fig.add_trace(go.Scatter(
        x=df['periodo'], y=df['pagos_multas'],
        mode='lines', name='Pagos Multas',
        stackgroup='one',
        line=dict(width=0.5, color='#FFA500'),
        fillcolor='rgba(255, 165, 0, 0.6)'
    ))
    
    fig.add_trace(go.Scatter(
        x=df['periodo'], y=df['pagos_prestamos'],
        mode='lines', name='Pagos Préstamos',
        stackgroup='one',
        line=dict(width=0.5, color='#9370DB'),
        fillcolor='rgba(147, 112, 219, 0.6)'
    ))
    
    fig.update_layout(
        title='📊 Evolución de la Composición de Ingresos',
        xaxis_title='Periodo',
        yaxis_title='Monto ($)',
        hovermode='x unified',
        height=400
    )
    
    return fig

def crear_grafica_rentabilidad(df):
    """Crea gráfica de rentabilidad y tasas de recuperación."""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['periodo'], y=df['rentabilidad'],
        mode='lines+markers', name='Rentabilidad (%)',
        line=dict(color='#00CED1', width=3),
        marker=dict(size=6),
        yaxis='y1'
    ))
    
    fig.add_trace(go.Scatter(
        x=df['periodo'], y=df['tasa_recuperacion'],
        mode='lines+markers', name='Tasa Recuperación (%)',
        line=dict(color='#FF69B4', width=3),
        marker=dict(size=6),
        yaxis='y1'
    ))
    
    fig.update_layout(
        title='📈 Métricas de Rendimiento',
        xaxis_title='Periodo',
        yaxis_title='Porcentaje (%)',
        hovermode='x unified',
        height=400,
        yaxis=dict(
            title='Porcentaje (%)',
            range=[0, 100]
        )
    )
    
    return fig

def crear_grafica_comparativa_grupos(series_grupos):
    """Crea gráfica comparativa entre grupos."""
    fig = go.Figure()
    
    colores = px.colors.qualitative.Set3
    for i, (nombre_grupo, df_grupo) in enumerate(series_grupos.items()):
        fig.add_trace(go.Scatter(
            x=df_grupo['periodo'], y=df_grupo['balance'],
            mode='lines+markers', name=nombre_grupo,
            line=dict(color=colores[i % len(colores)], width=2),
            marker=dict(size=4)
        ))
    
    fig.update_layout(
        title='📊 Comparativa de Balance entre Grupos',
        xaxis_title='Periodo',
        yaxis_title='Balance ($)',
        hovermode='x unified',
        height=500
    )
    
    return fig

# =============================================
#  INTERFAZ PRINCIPAL MEJORADA
# =============================================

def mostrar_consolidado_promotora():
    """Función principal para mostrar el consolidado de la promotora."""
    
    st.title("📊 Serie Temporal Completa - Consolidado Promotora")
    
    # Obtener ID de promotora
    id_promotora = obtener_id_promotora_desde_usuario()
    if not id_promotora:
        # Modo testing para desarrollo
        st.warning("🔧 Modo desarrollo: Usando ID de promotora de prueba")
        id_promotora = st.number_input("ID Promotora (testing):", min_value=1, value=1)
        if not id_promotora:
            return
    
    # Obtener grupos de la promotora
    grupos = obtener_grupos_promotora(id_promotora)
    if not grupos:
        st.info("ℹ️ No tienes grupos asignados.")
        return
    
    st.sidebar.write("### ⚙️ Configuración del Reporte")
    
    # Selector de rango de años
    año_actual = datetime.now().year
    año_inicio = st.sidebar.selectbox(
        "Año Inicio",
        range(año_actual - 3, año_actual + 1),
        index=2
    )
    año_fin = st.sidebar.selectbox(
        "Año Fin",
        range(año_inicio, año_actual + 1),
        index=min(1, año_actual - año_inicio)
    )
    
    # Selector de vista
    vista = st.sidebar.radio(
        "Tipo de Vista",
        [
            "📈 Vista Consolidada General",
            "🔍 Vista Detallada por Grupo", 
            "📊 Comparativa entre Grupos",
            "📋 Reporte Ejecutivo"
        ]
    )
    
    # Calcular series temporales
    with st.spinner("🔄 Calculando series temporales..."):
        serie_consolidada = calcular_serie_temporal_consolidada(grupos, año_inicio, año_fin)
        df_consolidado = pd.DataFrame(serie_consolidada)
        
        # Calcular series por grupo individual
        series_grupos = {}
        for grupo in grupos:
            serie_grupo = calcular_serie_temporal_grupo(grupo['ID_Grupo'], año_inicio, año_fin)
            series_grupos[grupo['nombre_grupo']] = pd.DataFrame(serie_grupo)
    
    # Mostrar vista seleccionada
    if vista == "📈 Vista Consolidada General":
        mostrar_vista_consolidada_general(df_consolidado, grupos)
    elif vista == "🔍 Vista Detallada por Grupo":
        mostrar_vista_detallada_grupo(grupos, series_grupos)
    elif vista == "📊 Comparativa entre Grupos":
        mostrar_vista_comparativa_grupos(series_grupos)
    elif vista == "📋 Reporte Ejecutivo":
        mostrar_reporte_ejecutivo(df_consolidado, grupos)

def mostrar_vista_consolidada_general(df, grupos):
    """Muestra vista consolidada de todos los grupos."""
    
    st.header("📈 Vista Consolidada General")
    st.write(f"**Periodo:** {df['año'].min()} - {df['año'].max()} | **Grupos:** {len(grupos)}")
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        ingresos_totales = df['total_ingresos'].sum()
        st.metric("💰 Ingresos Totales", f"${ingresos_totales:,.2f}")
    
    with col2:
        egresos_totales = df['total_egresos'].sum()
        st.metric("💸 Egresos Totales", f"${egresos_totales:,.2f}")
    
    with col3:
        balance_total = df['balance'].sum()
        st.metric("⚖️ Balance Total", f"${balance_total:,.2f}")
    
    with col4:
        rentabilidad_promedio = df['rentabilidad_promedio'].mean()
        st.metric("📈 Rentabilidad Promedio", f"{rentabilidad_promedio:.1f}%")
    
    # Gráfica principal
    st.plotly_chart(crear_grafica_serie_temporal_completa(df, "Consolidado General"), 
                   use_container_width=True)
    
    # Gráficas secundarias
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(crear_grafica_composicion_ingresos_evolutiva(df), 
                       use_container_width=True)
    
    with col2:
        # Tabla de resumen por año
        resumen_anual = df.groupby('año').agg({
            'total_ingresos': 'sum',
            'total_egresos': 'sum',
            'balance': 'sum',
            'rentabilidad_promedio': 'mean'
        }).round(2)
        
        st.write("**📋 Resumen Anual**")
        st.dataframe(resumen_anual.style.format({
            'total_ingresos': '${:,.2f}',
            'total_egresos': '${:,.2f}', 
            'balance': '${:,.2f}',
            'rentabilidad_promedio': '{:.1f}%'
        }), use_container_width=True)

def mostrar_vista_detallada_grupo(grupos, series_grupos):
    """Muestra vista detallada para un grupo específico."""
    
    st.header("🔍 Vista Detallada por Grupo")
    
    # Selector de grupo
    nombres_grupos = [f"{g['nombre_grupo']} ({g['total_miembros']} miembros)" for g in grupos]
    grupo_seleccionado = st.selectbox("Seleccionar Grupo", nombres_grupos)
    
    grupo_idx = nombres_grupos.index(grupo_seleccionado)
    nombre_grupo_real = grupos[grupo_idx]['nombre_grupo']
    df_grupo = series_grupos[nombre_grupo_real]
    
    st.subheader(f"📊 Serie Temporal - {nombre_grupo_real}")
    
    # Métricas del grupo
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Ingresos Totales", f"${df_grupo['total_ingresos'].sum():,.2f}")
    with col2:
        st.metric("Egresos Totales", f"${df_grupo['total_egresos'].sum():,.2f}")
    with col3:
        st.metric("Balance Total", f"${df_grupo['balance'].sum():,.2f}")
    with col4:
        st.metric("Rentabilidad Prom.", f"{df_grupo['rentabilidad'].mean():.1f}%")
    
    # Gráficas del grupo
    st.plotly_chart(crear_grafica_serie_temporal_completa(df_grupo, nombre_grupo_real), 
                   use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(crear_grafica_composicion_ingresos_evolutiva(df_grupo), 
                       use_container_width=True)
    
    with col2:
        st.plotly_chart(crear_grafica_rentabilidad(df_grupo), 
                       use_container_width=True)
    
    # Tabla detallada
    st.write("### 📋 Datos Detallados por Mes")
    columnas_detalle = ['periodo', 'ahorros', 'prestamos_desembolsados', 'pagos_prestamos', 
                       'pagos_multas', 'intereses', 'total_ingresos', 'total_egresos', 'balance']
    
    df_detalle = df_grupo[columnas_detalle].copy()
    df_detalle = df_detalle.round(2)
    
    st.dataframe(df_detalle, use_container_width=True)

def mostrar_vista_comparativa_grupos(series_grupos):
    """Muestra vista comparativa entre todos los grupos."""
    
    st.header("📊 Comparativa entre Grupos")
    
    # Gráfica comparativa
    st.plotly_chart(crear_grafica_comparativa_grupos(series_grupos), 
                   use_container_width=True)
    
    # Tabla comparativa
    st.write("### 📋 Métricas Comparativas")
    
    datos_comparativa = []
    for nombre_grupo, df in series_grupos.items():
        datos_comparativa.append({
            'Grupo': nombre_grupo,
            'Ingresos Totales': f"${df['total_ingresos'].sum():,.2f}",
            'Egresos Totales': f"${df['total_egresos'].sum():,.2f}",
            'Balance Total': f"${df['balance'].sum():,.2f}",
            'Rentabilidad Prom.': f"{df['rentabilidad'].mean():.1f}%",
            'Mejor Mes': df.loc[df['balance'].idxmax(), 'periodo'],
            'Peor Mes': df.loc[df['balance'].idxmin(), 'periodo']
        })
    
    st.dataframe(pd.DataFrame(datos_comparativa), use_container_width=True)

def mostrar_reporte_ejecutivo(df, grupos):
    """Muestra un reporte ejecutivo resumido."""
    
    st.header("📋 Reporte Ejecutivo")
    
    # Resumen ejecutivo
    st.write("### 🎯 Resumen Ejecutivo")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Grupos", len(grupos))
        st.metric("Periodo Analizado", f"{df['año'].min()} - {df['año'].max()}")
        st.metric("Meses Analizados", len(df))
    
    with col2:
        st.metric("Crecimiento Ingresos", 
                 f"{(df['total_ingresos'].iloc[-1] / df['total_ingresos'].iloc[0] - 1) * 100:.1f}%" 
                 if len(df) > 1 else "N/A")
        st.metric("Balance Promedio Mensual", f"${df['balance'].mean():,.2f}")
        st.metric("Rentabilidad Promedio", f"{df['rentabilidad_promedio'].mean():.1f}%")
    
    # Análisis de tendencias
    st.write("### 📈 Análisis de Tendencias")
    
    ultimo_mes = df.iloc[-1]
    primer_mes = df.iloc[0]
    
    tendencia_data = {
        'Métrica': ['Ingresos Mensuales', 'Egresos Mensuales', 'Balance Mensual', 'Rentabilidad'],
        'Primer Mes': [
            f"${primer_mes['total_ingresos']:,.2f}",
            f"${primer_mes['total_egresos']:,.2f}", 
            f"${primer_mes['balance']:,.2f}",
            f"{primer_mes['rentabilidad_promedio']:.1f}%"
        ],
        'Último Mes': [
            f"${ultimo_mes['total_ingresos']:,.2f}",
            f"${ultimo_mes['total_egresos']:,.2f}",
            f"${ultimo_mes['balance']:,.2f}",
            f"{ultimo_mes['rentabilidad_promedio']:.1f}%"
        ],
        'Evolución': [
            f"{(ultimo_mes['total_ingresos'] / primer_mes['total_ingresos'] - 1) * 100:+.1f}%" if primer_mes['total_ingresos'] > 0 else "N/A",
            f"{(ultimo_mes['total_egresos'] / primer_mes['total_egresos'] - 1) * 100:+.1f}%" if primer_mes['total_egresos'] > 0 else "N/A",
            f"{(ultimo_mes['balance'] / primer_mes['balance'] - 1) * 100:+.1f}%" if primer_mes['balance'] > 0 else "N/A",
            f"{(ultimo_mes['rentabilidad_promedio'] - primer_mes['rentabilidad_promedio']):+.1f}%"
        ]
    }
    
    st.dataframe(pd.DataFrame(tendencia_data), use_container_width=True)
    
    # Recomendaciones
    st.write("### 💡 Recomendaciones")
    
    if df['balance'].mean() < 0:
        st.error("**⚠️ Alerta:** Balance promedio negativo. Revisar estrategia de préstamos.")
    elif df['rentabilidad_promedio'].mean() < 5:
        st.warning("**🔶 Oportunidad:** Rentabilidad baja. Considerar ajustar tasas de interés.")
    else:
        st.success("**✅ Excelente:** Rentabilidad y balance saludables.")
    
    if df['total_egresos'].sum() > df['total_ingresos'].sum() * 0.8:
        st.warning("**🔶 Precaución:** Los egresos representan más del 80% de los ingresos.")

# =============================================
#  EJECUCIÓN PRINCIPAL
# =============================================

if __name__ == "__main__":
    # Para testing - simular usuario logueado
    if "id_usuario" not in st.session_state:
        st.info("🔧 Modo desarrollo - Simulando usuario")
        st.session_state.id_usuario = 1
    
    mostrar_consolidado_promotora()
