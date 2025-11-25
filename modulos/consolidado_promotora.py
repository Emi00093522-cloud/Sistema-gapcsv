import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from modulos.config.conexion import obtener_conexion

def obtener_grupos_promotora(id_promotora):
    """Obtiene los grupos asignados a la promotora"""
    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT g.ID_Grupo, g.nombre_grupo, g.descripcion
            FROM Grupo g
            WHERE g.ID_Promotora = %s
            ORDER BY g.nombre_grupo
        """, (id_promotora,))
        
        grupos = cursor.fetchall()
        return grupos
        
    except Exception as e:
        st.error(f"❌ Error obteniendo grupos: {e}")
        return []
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'con' in locals(): con.close()

def obtener_total_ahorros_grupo(id_grupo, fecha_inicio, fecha_fin):
    """Obtiene la sumatoria de TODOS los ahorros realizados"""
    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT COALESCE(SUM(a.monto_ahorro), 0) as total_ahorros
            FROM Ahorro a
            JOIN Reunion r ON a.ID_Reunion = r.ID_Reunion
            WHERE r.ID_Grupo = %s 
            AND r.fecha BETWEEN %s AND %s
        """, (id_grupo, fecha_inicio, fecha_fin))
        
        resultado = cursor.fetchone()
        return float(resultado['total_ahorros']) if resultado else 0.0
        
    except Exception as e:
        st.error(f"❌ Error obteniendo ahorros: {e}")
        return 0.0
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'con' in locals(): con.close()

def obtener_total_prestamos_grupo(id_grupo, fecha_inicio, fecha_fin):
    """Obtiene la sumatoria de TODOS los préstamos hechos"""
    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT COALESCE(SUM(p.monto), 0) as total_prestamos
            FROM Prestamo p
            JOIN Miembro m ON p.ID_Miembro = m.ID_Miembro
            WHERE m.ID_Grupo = %s 
            AND p.fecha_desembolso BETWEEN %s AND %s
        """, (id_grupo, fecha_inicio, fecha_fin))
        
        resultado = cursor.fetchone()
        return float(resultado['total_prestamos']) if resultado else 0.0
        
    except Exception as e:
        st.error(f"❌ Error obteniendo préstamos: {e}")
        return 0.0
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'con' in locals(): con.close()

def obtener_total_pagos_prestamos_grupo(id_grupo, fecha_inicio, fecha_fin):
    """Obtiene el total de TODOS los préstamos pagados"""
    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT COALESCE(SUM(pp.total_cancelado), 0) as total_pagos
            FROM Pago_prestamo pp
            JOIN Prestamo p ON pp.ID_Prestamo = p.ID_Prestamo
            JOIN Miembro m ON p.ID_Miembro = m.ID_Miembro
            WHERE m.ID_Grupo = %s 
            AND pp.fecha_pago BETWEEN %s AND %s
        """, (id_grupo, fecha_inicio, fecha_fin))
        
        resultado = cursor.fetchone()
        return float(resultado['total_pagos']) if resultado else 0.0
        
    except Exception as e:
        st.error(f"❌ Error obteniendo pagos de préstamos: {e}")
        return 0.0
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'con' in locals(): con.close()

def obtener_total_multas_grupo(id_grupo, fecha_inicio, fecha_fin):
    """Obtiene el total de TODAS las multas hechas"""
    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT COALESCE(SUM(pm.monto_pagado), 0) as total_multas
            FROM PagoMulta pm
            JOIN Miembro m ON pm.ID_Miembro = m.ID_Miembro
            WHERE m.ID_Grupo = %s 
            AND pm.fecha_pago BETWEEN %s AND %s
        """, (id_grupo, fecha_inicio, fecha_fin))
        
        resultado = cursor.fetchone()
        return float(resultado['total_multas']) if resultado else 0.0
        
    except Exception as e:
        st.error(f"❌ Error obteniendo multas: {e}")
        return 0.0
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'con' in locals(): con.close()

def mostrar_consolidado_promotora():
    """Función principal que muestra el consolidado simplificado"""
    
    st.header("📊 Consolidado de Promotora")
    
    # Verificar que la promotora esté logueada
    if 'id_promotora' not in st.session_state:
        st.error("🔒 Debes iniciar sesión como promotora para acceder a este panel")
        return
    
    id_promotora = st.session_state.id_promotora
    
    # Obtener grupos de la promotora
    grupos = obtener_grupos_promotora(id_promotora)
    
    if not grupos:
        st.warning("⚠️ No tienes grupos asignados. Contacta al administrador.")
        return
    
    # Filtro de fechas - PRIMERA FILA
    st.subheader("📅 Seleccionar Período de Análisis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fecha_inicio = st.date_input(
            "Fecha de Inicio",
            value=datetime.now().date() - timedelta(days=30),
            max_value=datetime.now().date(),
        )
    
    with col2:
        fecha_fin = st.date_input(
            "Fecha de Fin",
            value=datetime.now().date(),
            max_value=datetime.now().date(),
        )
    
    if fecha_inicio > fecha_fin:
        st.error("❌ La fecha de inicio no puede ser mayor que la fecha de fin")
        return
    
    # Selector de grupo - SEGUNDA FILA
    st.subheader("🏢 Seleccionar Grupo")
    
    grupo_options = {f"{g['nombre_grupo']}": g['ID_Grupo'] for g in grupos}
    grupo_seleccionado = st.selectbox(
        "Selecciona el grupo a analizar:",
        options=list(grupo_options.keys()),
        key="grupo_selector"
    )
    
    id_grupo_seleccionado = grupo_options[grupo_seleccionado]
    
    st.markdown("---")
    
    # Obtener datos automáticamente al seleccionar grupo y fechas
    with st.spinner("📊 Calculando datos consolidados..."):
        # Obtener los 4 datos específicos que necesitas
        total_ahorros = obtener_total_ahorros_grupo(id_grupo_seleccionado, fecha_inicio, fecha_fin)
        total_prestamos = obtener_total_prestamos_grupo(id_grupo_seleccionado, fecha_inicio, fecha_fin)
        total_pagos_prestamos = obtener_total_pagos_prestamos_grupo(id_grupo_seleccionado, fecha_inicio, fecha_fin)
        total_multas = obtener_total_multas_grupo(id_grupo_seleccionado, fecha_inicio, fecha_fin)
    
    # Mostrar métricas principales
    st.subheader(f"💰 Resumen Financiero - {grupo_seleccionado}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "💰 Ahorros", 
            f"${total_ahorros:,.2f}",
            help="Total de ahorros realizados por los miembros"
        )
    
    with col2:
        st.metric(
            "🏦 Préstamos", 
            f"${total_prestamos:,.2f}",
            help="Total de préstamos otorgados a los miembros"
        )
    
    with col3:
        st.metric(
            "💵 Pagos Préstamos", 
            f"${total_pagos_prestamos:,.2f}",
            help="Total de préstamos que han sido pagados"
        )
    
    with col4:
        st.metric(
            "⚖️ Multas", 
            f"${total_multas:,.2f}",
            help="Total de multas recaudadas"
        )
    
    st.markdown("---")
    
    # GRÁFICO DE BARRAS COMPARATIVO
    st.subheader("📊 Comparativa de Desempeño del Grupo")
    
    # Preparar datos para el gráfico
    datos_grafico = {
        'Categoría': ['Ahorros', 'Préstamos', 'Pagos Préstamos', 'Multas'],
        'Monto': [total_ahorros, total_prestamos, total_pagos_prestamos, total_multas],
        'Color': ['#00CC96', '#636EFA', '#EF553B', '#AB63FA']  # Colores distintivos
    }
    
    df_grafico = pd.DataFrame(datos_grafico)
    
    # Crear gráfico de barras
    fig = px.bar(
        df_grafico,
        x='Categoría',
        y='Monto',
        text='Monto',
        color='Categoría',
        color_discrete_sequence=datos_grafico['Color'],
        title=f"Desempeño Financiero - {grupo_seleccionado}",
        labels={'Monto': 'Monto ($)', 'Categoría': 'Categoría Financiera'}
    )
    
    # Mejorar formato del gráfico
    fig.update_traces(
        texttemplate='$%{y:,.2f}',
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>$%{y:,.2f}<extra></extra>'
    )
    
    fig.update_layout(
        showlegend=False,
        yaxis_title="Monto ($)",
        xaxis_title="",
        height=500,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )
    
    # Mostrar gráfico
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabla resumen debajo del gráfico
    st.subheader("📋 Detalle de Montos")
    
    resumen_data = {
        'Concepto': ['Ahorros Totales', 'Préstamos Otorgados', 'Préstamos Pagados', 'Multas Recaudadas'],
        'Monto ($)': [
            f"${total_ahorros:,.2f}",
            f"${total_prestamos:,.2f}", 
            f"${total_pagos_prestamos:,.2f}",
            f"${total_multas:,.2f}"
        ],
        'Descripción': [
            'Sumatoria de todos los ahorros realizados',
            'Sumatoria de todos los préstamos hechos', 
            'Total de todos los préstamos pagados',
            'Total de todas las multas hechas'
        ]
    }
    
    df_resumen = pd.DataFrame(resumen_data)
    st.dataframe(df_resumen, use_container_width=True, hide_index=True)
    
    # Información del período
    st.info(f"**Período analizado:** {fecha_inicio} al {fecha_fin}")

# Para pruebas independientes
if __name__ == "__main__":
    # Simular que hay una promotora logueada
    st.session_state.id_promotora = 1
    mostrar_consolidado_promotora()
