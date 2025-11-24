import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

def mostrar_consolidado_financiero():
    """
    Módulo principal para mostrar consolidados financieros
    según el tipo de usuario
    """
    
    if not st.session_state.get("logged_in", False):
        st.warning("Debe iniciar sesión primero")
        return
    
    usuario = st.session_state["usuario"]
    tipo_usuario = st.session_state["tipo_usuario"]
    
    st.title("📊 Consolidado Financiero")
    
    # Filtros generales
    st.subheader("Filtros")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        fecha_inicio = st.date_input(
            "Fecha de inicio", 
            value=datetime.now().replace(day=1),
            key="fecha_inicio_consolidado"
        )
    
    with col2:
        fecha_fin = st.date_input(
            "Fecha de fin", 
            value=datetime.now(),
            key="fecha_fin_consolidado"
        )
    
    with col3:
        if tipo_usuario == "administrador":
            distritos = st.session_state.df_movimientos['distrito'].unique()
            distrito_seleccionado = st.selectbox(
                "Distrito",
                options=["Todos"] + list(distritos),
                key="distrito_consolidado"
            )
        else:
            # Para promotora, mostrar grupos asignados
            grupos_asignados = obtener_grupos_por_promotora(usuario)
            grupo_seleccionado = st.selectbox(
                "Grupo",
                options=["Todos"] + list(grupos_asignados),
                key="grupo_consolidado"
            )
    
    # Aplicar filtros
    df_filtrado = aplicar_filtros(fecha_inicio, fecha_fin, tipo_usuario, usuario)
    
    # Mostrar resumen ejecutivo
    mostrar_resumen_ejecutivo(df_filtrado, tipo_usuario)
    
    # Mostrar gráficas según tipo de usuario
    if tipo_usuario == "promotora":
        mostrar_consolidado_promotora(df_filtrado, usuario)
    else:
        mostrar_consolidado_administrador(df_filtrado)

def obtener_grupos_por_promotora(promotora):
    """Obtiene los grupos asignados a una promotora"""
    try:
        df_movimientos = st.session_state.df_movimientos
        grupos = df_movimientos[df_movimientos['promotora'] == promotora]['grupo'].unique()
        return list(grupos)
    except:
        return []

def aplicar_filtros(fecha_inicio, fecha_fin, tipo_usuario, usuario):
    """Aplica los filtros seleccionados al DataFrame"""
    df = st.session_state.df_movimientos.copy()
    
    # Convertir fecha
    df['fecha'] = pd.to_datetime(df['fecha'])
    
    # Filtrar por fecha
    mask = (df['fecha'].dt.date >= fecha_inicio) & (df['fecha'].dt.date <= fecha_fin)
    df_filtrado = df.loc[mask]
    
    # Filtrar por tipo de usuario
    if tipo_usuario == "promotora":
        df_filtrado = df_filtrado[df_filtrado['promotora'] == usuario]
    
    return df_filtrado

def mostrar_resumen_ejecutivo(df, tipo_usuario):
    """Muestra el resumen ejecutivo con métricas clave"""
    st.subheader("📈 Resumen Ejecutivo")
    
    # Calcular métricas
    ingresos = df[df['tipo'] == 'ingreso']['monto'].sum()
    egresos = df[df['tipo'] == 'egreso']['monto'].sum()
    balance = ingresos - egresos
    
    # Métricas por categoría
    ahorros = df[df['concepto'].str.contains('ahorro|ahorros', case=False, na=False)]['monto'].sum()
    prestamos = df[df['concepto'].str.contains('préstamo|prestamo', case=False, na=False)]['monto'].sum()
    pagos_prestamos = df[df['concepto'].str.contains('pago préstamo|pago prestamo', case=False, na=False)]['monto'].sum()
    multas = df[df['concepto'].str.contains('multa', case=False, na=False)]['monto'].sum()
    
    # Mostrar métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Ingresos", f"S/. {ingresos:,.2f}", delta=f"S/. {ingresos:,.2f}")
    
    with col2:
        st.metric("Total Egresos", f"S/. {egresos:,.2f}", delta=f"-S/. {egresos:,.2f}", delta_color="inverse")
    
    with col3:
        st.metric("Balance", f"S/. {balance:,.2f}", 
                 delta=f"S/. {balance:,.2f}" if balance >= 0 else f"-S/. {abs(balance):,.2f}")
    
    with col4:
        total_transacciones = len(df)
        st.metric("Total Transacciones", f"{total_transacciones}")
    
    # Mostrar métricas por categoría
    st.subheader("💵 Desglose por Concepto")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Ahorros", f"S/. {ahorros:,.2f}")
    
    with col2:
        st.metric("Préstamos", f"S/. {prestamos:,.2f}")
    
    with col3:
        st.metric("Pagos Préstamos", f"S/. {pagos_prestamos:,.2f}")
    
    with col4:
        st.metric("Multas", f"S/. {multas:,.2f}")

def mostrar_consolidado_promotora(df, promotora):
    """Muestra el consolidado para promotora"""
    st.header(f"👥 Consolidado - Promotora: {promotora}")
    
    # Pestañas para diferentes vistas
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Resumen por Grupo", 
        "📈 Evolución Temporal", 
        "💰 Flujo de Caja", 
        "📋 Detalle Completo"
    ])
    
    with tab1:
        mostrar_resumen_por_grupo(df)
    
    with tab2:
        mostrar_evolucion_temporal(df, f"Promotora: {promotora}")
    
    with tab3:
        mostrar_flujo_caja(df)
    
    with tab4:
        mostrar_detalle_completo(df)

def mostrar_consolidado_administrador(df):
    """Muestra el consolidado para administrador"""
    st.header("🏢 Consolidado por Distrito")
    
    # Pestañas para diferentes vistas
    tab1, tab2, tab3, tab4 = st.tabs([
        "🗺️ Resumen por Distrito", 
        "📈 Evolución Temporal", 
        "💰 Flujo de Caja", 
        "📋 Detalle Completo"
    ])
    
    with tab1:
        mostrar_resumen_por_distrito(df)
    
    with tab2:
        mostrar_evolucion_temporal(df, "Todos los Distritos")
    
    with tab3:
        mostrar_flujo_caja(df)
    
    with tab4:
        mostrar_detalle_completo(df)

def mostrar_resumen_por_grupo(df):
    """Muestra resumen financiero por grupo"""
    if df.empty:
        st.warning("No hay datos para mostrar")
        return
    
    # Agrupar por grupo
    resumen_grupos = df.groupby('grupo').agg({
        'monto': lambda x: df[df['tipo'] == 'ingreso'].groupby('grupo')['monto'].sum().get(x.name, 0),
        'monto_egresos': lambda x: df[df['tipo'] == 'egreso'].groupby('grupo')['monto'].sum().get(x.name, 0)
    }).reset_index()
    
    resumen_grupos.columns = ['Grupo', 'Ingresos', 'Egresos']
    resumen_grupos['Balance'] = resumen_grupos['Ingresos'] - resumen_grupos['Egresos']
    
    # Mostrar tabla
    st.subheader("Resumen por Grupo")
    st.dataframe(resumen_grupos.style.format({
        'Ingresos': 'S/. {:,.2f}',
        'Egresos': 'S/. {:,.2f}',
        'Balance': 'S/. {:,.2f}'
    }), use_container_width=True)
    
    # Gráfica de barras
    fig = px.bar(resumen_grupos, 
                 x='Grupo', 
                 y=['Ingresos', 'Egresos'],
                 title="Ingresos vs Egresos por Grupo",
                 barmode='group')
    st.plotly_chart(fig, use_container_width=True)

def mostrar_resumen_por_distrito(df):
    """Muestra resumen financiero por distrito"""
    if df.empty:
        st.warning("No hay datos para mostrar")
        return
    
    # Agrupar por distrito
    resumen_distritos = df.groupby('distrito').agg({
        'monto': lambda x: df[df['tipo'] == 'ingreso'].groupby('distrito')['monto'].sum().get(x.name, 0),
        'monto_egresos': lambda x: df[df['tipo'] == 'egreso'].groupby('distrito')['monto'].sum().get(x.name, 0)
    }).reset_index()
    
    resumen_distritos.columns = ['Distrito', 'Ingresos', 'Egresos']
    resumen_distritos['Balance'] = resumen_distritos['Ingresos'] - resumen_distritos['Egresos']
    
    # Mostrar tabla
    st.subheader("Resumen por Distrito")
    st.dataframe(resumen_distritos.style.format({
        'Ingresos': 'S/. {:,.2f}',
        'Egresos': 'S/. {:,.2f}',
        'Balance': 'S/. {:,.2f}'
    }), use_container_width=True)
    
    # Gráfica de barras
    fig = px.bar(resumen_distritos, 
                 x='Distrito', 
                 y=['Ingresos', 'Egresos'],
                 title="Ingresos vs Egresos por Distrito",
                 barmode='group')
    st.plotly_chart(fig, use_container_width=True)
    
    # Mapa de calor de balances
    fig_heatmap = px.treemap(resumen_distritos,
                            path=['Distrito'],
                            values='Balance',
                            title="Balance por Distrito (Mapa de Calor)")
    st.plotly_chart(fig_heatmap, use_container_width=True)

def mostrar_evolucion_temporal(df, titulo):
    """Muestra la evolución temporal de ingresos y egresos"""
    if df.empty:
        st.warning("No hay datos para mostrar")
        return
    
    # Preparar datos temporales
    df_temp = df.copy()
    df_temp['fecha'] = pd.to_datetime(df_temp['fecha'])
    df_temp['mes'] = df_temp['fecha'].dt.to_period('M').astype(str)
    
    # Agrupar por mes
    evolucion_mensual = df_temp.groupby(['mes', 'tipo'])['monto'].sum().reset_index()
    
    # Gráfica de líneas
    fig = px.line(evolucion_mensual, 
                  x='mes', 
                  y='monto', 
                  color='tipo',
                  color_discrete_map={'ingreso': 'green', 'egreso': 'red'},
                  title=f"Evolución Mensual - {titulo}",
                  markers=True)
    st.plotly_chart(fig, use_container_width=True)

def mostrar_flujo_caja(df):
    """Muestra el flujo de caja por concepto"""
    if df.empty:
        st.warning("No hay datos para mostrar")
        return
    
    # Análisis por concepto
    conceptos_ingresos = df[df['tipo'] == 'ingreso'].groupby('concepto')['monto'].sum().reset_index()
    conceptos_egresos = df[df['tipo'] == 'egreso'].groupby('concepto')['monto'].sum().reset_index()
    
    col1, col2 = st.columns(2)
    
    with col1:
        if not conceptos_ingresos.empty:
            fig_ingresos = px.pie(conceptos_ingresos, 
                                 values='monto', 
                                 names='concepto',
                                 title="Distribución de Ingresos por Concepto")
            st.plotly_chart(fig_ingresos, use_container_width=True)
    
    with col2:
        if not conceptos_egresos.empty:
            fig_egresos = px.pie(conceptos_egresos, 
                                values='monto', 
                                names='concepto',
                                title="Distribución de Egresos por Concepto")
            st.plotly_chart(fig_egresos, use_container_width=True)

def mostrar_detalle_completo(df):
    """Muestra el detalle completo de transacciones"""
    st.subheader("Detalle Completo de Transacciones")
    
    if df.empty:
        st.warning("No hay transacciones en el período seleccionado")
        return
    
    # Formatear DataFrame para mostrar
    df_detalle = df[['fecha', 'grupo', 'distrito', 'concepto', 'tipo', 'monto', 'promotora']].copy()
    df_detalle['monto'] = df_detalle['monto'].apply(lambda x: f"S/. {x:,.2f}")
    
    st.dataframe(df_detalle, use_container_width=True)
    
    # Opción de descarga
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Descargar Reporte Completo",
        data=csv,
        file_name=f"reporte_financiero_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )
