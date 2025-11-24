import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

def obtener_datos_movimientos():
    """
    Obtiene los datos de movimientos de la sesión
    """
    if 'df_movimientos' in st.session_state:
        return st.session_state.df_movimientos.copy()
    else:
        st.error("No se encontraron datos de movimientos")
        return pd.DataFrame()

def obtener_grupos_por_promotora(promotora):
    """
    Obtiene los grupos asignados a una promotora
    """
    df = obtener_datos_movimientos()
    if df.empty:
        return []
    
    # Buscar grupos donde la promotora esté asignada
    grupos = df[df['promotora'] == promotora]['grupo'].unique()
    return list(grupos)

def filtrar_datos_por_promotora(df, promotora, fecha_inicio, fecha_fin):
    """
    Filtra los datos para una promotora específica
    """
    if df.empty:
        return df
    
    # Filtrar por promotora
    df_filtrado = df[df['promotora'] == promotora].copy()
    
    # Filtrar por fecha si las columnas existen
    if 'fecha' in df_filtrado.columns:
        df_filtrado['fecha'] = pd.to_datetime(df_filtrado['fecha'])
        mask = (df_filtrado['fecha'].dt.date >= fecha_inicio) & (df_filtrado['fecha'].dt.date <= fecha_fin)
        df_filtrado = df_filtrado[mask]
    
    return df_filtrado

def mostrar_consolidado_promotora_real(usuario, fecha_inicio, fecha_fin):
    """
    Muestra el consolidado REAL para promotora con datos reales
    """
    st.subheader(f"📊 Consolidado de Grupos - {usuario}")
    
    # Obtener datos
    df = obtener_datos_movimientos()
    if df.empty:
        st.warning("No hay datos de movimientos disponibles")
        return
    
    # Filtrar datos para esta promotora
    df_promotora = filtrar_datos_por_promotora(df, usuario, fecha_inicio, fecha_fin)
    
    if df_promotora.empty:
        st.warning(f"No se encontraron movimientos para la promotora {usuario} en el período seleccionado")
        return
    
    # Obtener grupos de esta promotora
    grupos = obtener_grupos_por_promotora(usuario)
    st.info(f"📋 Grupos asignados: {', '.join(grupos) if grupos else 'No hay grupos asignados'}")
    
    # Mostrar métricas principales
    mostrar_metricas_principales(df_promotora)
    
    # Mostrar gráficas
    mostrar_graficas_por_grupo(df_promotora, grupos)
    
    # Mostrar detalle de movimientos
    mostrar_detalle_movimientos(df_promotora)

def mostrar_metricas_principales(df):
    """
    Muestra las métricas principales de ingresos y egresos
    """
    st.subheader("📈 Métricas Principales")
    
    # Calcular totales
    if 'tipo' in df.columns and 'monto' in df.columns:
        total_ingresos = df[df['tipo'].str.lower() == 'ingreso']['monto'].sum()
        total_egresos = df[df['tipo'].str.lower() == 'egreso']['monto'].sum()
        balance = total_ingresos - total_egresos
        
        # Contar transacciones
        num_ingresos = len(df[df['tipo'].str.lower() == 'ingreso'])
        num_egresos = len(df[df['tipo'].str.lower() == 'egreso'])
    else:
        total_ingresos = total_egresos = balance = num_ingresos = num_egresos = 0
    
    # Mostrar métricas
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Ingresos", f"S/. {total_ingresos:,.2f}")
    
    with col2:
        st.metric("Total Egresos", f"S/. {total_egresos:,.2f}")
    
    with col3:
        st.metric("Balance", f"S/. {balance:,.2f}")
    
    with col4:
        st.metric("Trans. Ingresos", f"{num_ingresos}")
    
    with col5:
        st.metric("Trans. Egresos", f"{num_egresos}")

def mostrar_graficas_por_grupo(df, grupos):
    """
    Muestra gráficas desglosadas por grupo
    """
    st.subheader("📊 Análisis por Grupo")
    
    if not grupos:
        st.warning("No hay grupos asignados para mostrar gráficas")
        return
    
    # Crear pestañas para diferentes gráficas
    tab1, tab2, tab3 = st.tabs(["📈 Ingresos vs Egresos", "🥧 Distribución", "📅 Evolución Mensual"])
    
    with tab1:
        mostrar_grafica_comparativa_grupos(df, grupos)
    
    with tab2:
        mostrar_grafica_distribucion(df, grupos)
    
    with tab3:
        mostrar_grafica_evolucion(df)

def mostrar_grafica_comparativa_grupos(df, grupos):
    """
    Muestra gráfica comparativa de ingresos vs egresos por grupo
    """
    # Preparar datos para la gráfica
    datos_grafica = []
    
    for grupo in grupos:
        df_grupo = df[df['grupo'] == grupo]
        
        if not df_grupo.empty and 'tipo' in df_grupo.columns and 'monto' in df_grupo.columns:
            ingresos = df_grupo[df_grupo['tipo'].str.lower() == 'ingreso']['monto'].sum()
            egresos = df_grupo[df_grupo['tipo'].str.lower() == 'egreso']['monto'].sum()
            
            datos_grafica.append({
                'Grupo': grupo,
                'Ingresos': ingresos,
                'Egresos': egresos
            })
    
    if datos_grafica:
        df_grafica = pd.DataFrame(datos_grafica)
        
        # Gráfica de barras
        fig = go.Figure()
        fig.add_trace(go.Bar(name='Ingresos', x=df_grafica['Grupo'], y=df_grafica['Ingresos'], marker_color='green'))
        fig.add_trace(go.Bar(name='Egresos', x=df_grafica['Grupo'], y=df_grafica['Egresos'], marker_color='red'))
        
        fig.update_layout(
            title='Ingresos vs Egresos por Grupo',
            xaxis_title='Grupo',
            yaxis_title='Monto (S/.)',
            barmode='group'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos suficientes para generar la gráfica por grupos")

def mostrar_grafica_distribucion(df, grupos):
    """
    Muestra gráficas de distribución por concepto
    """
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribución de ingresos por concepto
        if 'concepto' in df.columns and 'tipo' in df.columns:
            df_ingresos = df[df['tipo'].str.lower() == 'ingreso']
            if not df_ingresos.empty:
                ingresos_por_concepto = df_ingresos.groupby('concepto')['monto'].sum().reset_index()
                if not ingresos_por_concepto.empty:
                    fig_ingresos = px.pie(ingresos_por_concepto, 
                                         values='monto', 
                                         names='concepto',
                                         title='Distribución de Ingresos por Concepto')
                    st.plotly_chart(fig_ingresos, use_container_width=True)
    
    with col2:
        # Distribución de egresos por concepto
        if 'concepto' in df.columns and 'tipo' in df.columns:
            df_egresos = df[df['tipo'].str.lower() == 'egreso']
            if not df_egresos.empty:
                egresos_por_concepto = df_egresos.groupby('concepto')['monto'].sum().reset_index()
                if not egresos_por_concepto.empty:
                    fig_egresos = px.pie(egresos_por_concepto, 
                                        values='monto', 
                                        names='concepto',
                                        title='Distribución de Egresos por Concepto')
                    st.plotly_chart(fig_egresos, use_container_width=True)

def mostrar_grafica_evolucion(df):
    """
    Muestra la evolución mensual de ingresos y egresos
    """
    if 'fecha' not in df.columns or df.empty:
        st.info("No hay datos de fecha para mostrar evolución")
        return
    
    # Preparar datos temporales
    df_temp = df.copy()
    df_temp['fecha'] = pd.to_datetime(df_temp['fecha'])
    df_temp['mes'] = df_temp['fecha'].dt.to_period('M').astype(str)
    
    # Agrupar por mes y tipo
    if 'tipo' in df_temp.columns and 'monto' in df_temp.columns:
        evolucion_mensual = df_temp.groupby(['mes', 'tipo'])['monto'].sum().reset_index()
        
        if not evolucion_mensual.empty:
            fig = px.line(evolucion_mensual, 
                         x='mes', 
                         y='monto', 
                         color='tipo',
                         color_discrete_map={'ingreso': 'green', 'egreso': 'red'},
                         title='Evolución Mensual de Ingresos y Egresos',
                         markers=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos suficientes para la evolución mensual")

def mostrar_detalle_movimientos(df):
    """
    Muestra el detalle de movimientos
    """
    st.subheader("📋 Detalle de Movimientos")
    
    # Seleccionar columnas a mostrar
    columnas_a_mostrar = []
    for col in ['fecha', 'grupo', 'concepto', 'tipo', 'monto', 'descripcion']:
        if col in df.columns:
            columnas_a_mostrar.append(col)
    
    if columnas_a_mostrar:
        df_detalle = df[columnas_a_mostrar].copy()
        
        # Formatear monto si existe
        if 'monto' in df_detalle.columns:
            df_detalle['monto'] = df_detalle['monto'].apply(lambda x: f"S/. {x:,.2f}")
        
        st.dataframe(df_detalle, use_container_width=True)
        
        # Opción de descarga
        csv = df[columnas_a_mostrar].to_csv(index=False)
        st.download_button(
            label="📥 Descargar Reporte",
            data=csv,
            file_name=f"reporte_promotora_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No hay columnas disponibles para mostrar el detalle")

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
    cargo = st.session_state.get("cargo_de_usuario", "").upper()
    
    st.title("📊 Consolidado Financiero")
    
    # Filtros generales
    st.subheader("Filtros")
    col1, col2 = st.columns(2)
    
    with col1:
        fecha_inicio = st.date_input(
            "Fecha de inicio", 
            value=datetime.now().replace(day=1)
        )
    
    with col2:
        fecha_fin = st.date_input(
            "Fecha de fin", 
            value=datetime.now()
        )
    
    # Determinar el tipo de usuario real
    if cargo == "PROMOTORA" or tipo_usuario == "promotora":
        tipo_vista = "promotora"
        st.subheader(f"👥 Vista Promotora: {usuario}")
        
        # MOSTRAR DATOS REALES DE LA PROMOTORA
        mostrar_consolidado_promotora_real(usuario, fecha_inicio, fecha_fin)
        
    else:
        tipo_vista = "administrador"
        st.subheader("🏢 Vista Administradora - Todos los Distritos")
        
        # Para administradora (por ahora mantenemos el ejemplo)
        st.info("🔍 **Vista de Administradora**: Mostrando datos consolidados de todos los distritos")
        
        # Aquí puedes agregar la lógica similar para administradora
        # mostrando datos por distrito en lugar de por grupo
        
        # Ejemplo temporal para administradora
        datos_administradora = pd.DataFrame({
            'Distrito': ['Distrito Norte', 'Distrito Sur', 'Distrito Este', 'Distrito Oeste'],
            'Total Ingresos': [50000, 45000, 60000, 40000],
            'Total Egresos': [35000, 30000, 45000, 28000],
            'Balance': [15000, 15000, 15000, 12000]
        })
        
        st.dataframe(datos_administradora)
        
        fig_admin = px.pie(datos_administradora, 
                          values='Total Ingresos', 
                          names='Distrito',
                          title='Distribución de Ingresos por Distrito')
        st.plotly_chart(fig_admin, use_container_width=True)
