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
        
        # DEBUG: Mostrar qué grupos encontró
        st.sidebar.write(f"🔍 Grupos encontrados: {len(grupos)}")
        for grupo in grupos:
            st.sidebar.write(f"   - {grupo['nombre_grupo']} (ID: {grupo['ID_Grupo']})")
        
        return grupos
        
    except Exception as e:
        st.error(f"Error obteniendo grupos: {e}")
        return []
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'con' in locals(): con.close()

def obtener_total_ahorros(id_grupo, fecha_inicio, fecha_fin):
    """Obtiene total de ahorros del módulo ahorros.py"""
    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT COALESCE(SUM(a.monto_ahorro), 0) as total
            FROM Ahorro a
            JOIN Reunion r ON a.ID_Reunion = r.ID_Reunion
            WHERE r.ID_Grupo = %s 
            AND r.fecha BETWEEN %s AND %s
        """, (id_grupo, fecha_inicio, fecha_fin))
        
        resultado = cursor.fetchone()
        total = float(resultado['total']) if resultado else 0.0
        st.sidebar.write(f"💰 Ahorros grupo {id_grupo}: ${total:,.2f}")
        return total
        
    except Exception as e:
        st.error(f"Error en ahorros: {e}")
        return 0.0
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'con' in locals(): con.close()

def obtener_total_prestamos(id_grupo, fecha_inicio, fecha_fin):
    """Obtiene total de préstamos del módulo prestamos.py"""
    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT COALESCE(SUM(p.monto), 0) as total
            FROM Prestamo p
            JOIN Miembro m ON p.ID_Miembro = m.ID_Miembro
            WHERE m.ID_Grupo = %s 
            AND p.fecha_desembolso BETWEEN %s AND %s
        """, (id_grupo, fecha_inicio, fecha_fin))
        
        resultado = cursor.fetchone()
        total = float(resultado['total']) if resultado else 0.0
        st.sidebar.write(f"🏦 Préstamos grupo {id_grupo}: ${total:,.2f}")
        return total
        
    except Exception as e:
        st.error(f"Error en préstamos: {e}")
        return 0.0
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'con' in locals(): con.close()

def obtener_total_pagos_prestamos(id_grupo, fecha_inicio, fecha_fin):
    """Obtiene total de pagos de préstamos del módulo pagoprestamo.py"""
    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT COALESCE(SUM(pp.total_cancelado), 0) as total
            FROM Pago_prestamo pp
            JOIN Prestamo p ON pp.ID_Prestamo = p.ID_Prestamo
            JOIN Miembro m ON p.ID_Miembro = m.ID_Miembro
            WHERE m.ID_Grupo = %s 
            AND pp.fecha_pago BETWEEN %s AND %s
        """, (id_grupo, fecha_inicio, fecha_fin))
        
        resultado = cursor.fetchone()
        total = float(resultado['total']) if resultado else 0.0
        st.sidebar.write(f"💵 Pagos préstamos grupo {id_grupo}: ${total:,.2f}")
        return total
        
    except Exception as e:
        st.error(f"Error en pagos de préstamos: {e}")
        return 0.0
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'con' in locals(): con.close()

def obtener_total_multas(id_grupo, fecha_inicio, fecha_fin):
    """Obtiene total de multas del módulo pagomulta.py"""
    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT COALESCE(SUM(pm.monto_pagado), 0) as total
            FROM PagoMulta pm
            JOIN Miembro m ON pm.ID_Miembro = m.ID_Miembro
            WHERE m.ID_Grupo = %s 
            AND pm.fecha_pago BETWEEN %s AND %s
        """, (id_grupo, fecha_inicio, fecha_fin))
        
        resultado = cursor.fetchone()
        total = float(resultado['total']) if resultado else 0.0
        st.sidebar.write(f"⚖️ Multas grupo {id_grupo}: ${total:,.2f}")
        return total
        
    except Exception as e:
        st.error(f"Error en multas: {e}")
        return 0.0
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'con' in locals(): con.close()

def mostrar_consolidado_promotora():
    """Función principal del consolidado de promotora"""
    
    st.header("📊 Consolidado de Promotora - DEBUG")
    
    # DEBUG: Mostrar session_state completo
    st.sidebar.subheader("🔍 DEBUG Session State")
    st.sidebar.write(st.session_state)
    
    # Verificar que la promotora esté logueada - MÚLTIPLES FORMAS
    if 'id_promotora' not in st.session_state:
        st.error("🔒 ERROR: No hay 'id_promotora' en session_state")
        
        # Intentar otras posibles formas de identificar promotora
        if 'usuario_actual' in st.session_state:
            st.info(f"💡 Hay 'usuario_actual': {st.session_state.usuario_actual}")
        if 'user_id' in st.session_state:
            st.info(f"💡 Hay 'user_id': {st.session_state.user_id}")
        if 'id_grupo' in st.session_state:
            st.info(f"💡 Hay 'id_grupo': {st.session_state.id_grupo}")
            
        st.info("""
        **Posibles soluciones:**
        1. Inicia sesión como promotora
        2. Verifica que el login guarde 'id_promotora' en session_state
        3. O usa este ID de prueba:
        """)
        
        # Botón para usar ID de prueba
        if st.button("🧪 Usar ID de Prueba (1)"):
            st.session_state.id_promotora = 1
            st.rerun()
            
        return
    
    id_promotora = st.session_state.id_promotora
    st.success(f"✅ Promotora ID: {id_promotora}")
    
    # Obtener grupos de la promotora
    st.write("🔄 Buscando grupos...")
    grupos = obtener_grupos_promotora(id_promotora)
    
    if not grupos:
        st.error("❌ ERROR: No se encontraron grupos para esta promotora")
        st.info("""
        **Posibles causas:**
        1. No tienes grupos asignados en la base de datos
        2. El ID de promotora no existe en la tabla Grupo
        3. Hay error en la conexión a la base de datos
        """)
        
        # Mostrar consulta SQL para debug
        st.code("""
        CONSULTA SQL EJECUTADA:
        SELECT g.ID_Grupo, g.nombre_grupo, g.descripcion
        FROM Grupo g
        WHERE g.ID_Promotora = %s
        """, language='sql')
        
        return
    
    st.success(f"✅ Se encontraron {len(grupos)} grupo(s)")
    
    # PRIMERA FILA: Filtros de fecha
    st.subheader("📅 Seleccionar Período de Análisis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fecha_inicio = st.date_input(
            "Fecha de Inicio",
            value=datetime.now().date() - timedelta(days=30),
            max_value=datetime.now().date(),
            key="fecha_inicio_consolidado"
        )
    
    with col2:
        fecha_fin = st.date_input(
            "Fecha de Fin", 
            value=datetime.now().date(),
            max_value=datetime.now().date(),
            key="fecha_fin_consolidado"
        )
    
    if fecha_inicio > fecha_fin:
        st.error("❌ La fecha de inicio no puede ser mayor que la fecha de fin")
        return
    
    # SEGUNDA FILA: Selector de grupo
    st.subheader("🏢 Seleccionar Grupo")
    
    grupo_options = {f"{g['nombre_grupo']} (ID: {g['ID_Grupo']})": g['ID_Grupo'] for g in grupos}
    grupo_seleccionado = st.selectbox(
        "Selecciona el grupo a analizar:",
        options=list(grupo_options.keys()),
        key="grupo_selector_consolidado"
    )
    
    id_grupo_seleccionado = grupo_options[grupo_seleccionado]
    
    st.markdown("---")
    
    # Obtener datos automáticamente
    st.write("📊 Consultando datos financieros...")
    with st.spinner("Calculando datos consolidados..."):
        # Obtener los 4 datos específicos de cada módulo
        total_ahorros = obtener_total_ahorros(id_grupo_seleccionado, fecha_inicio, fecha_fin)
        total_prestamos = obtener_total_prestamos(id_grupo_seleccionado, fecha_inicio, fecha_fin)
        total_pagos_prestamos = obtener_total_pagos_prestamos(id_grupo_seleccionado, fecha_inicio, fecha_fin)
        total_multas = obtener_total_multas(id_grupo_seleccionado, fecha_inicio, fecha_fin)
    
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
    
    # Preparar datos para el gráfico - SIEMPRE mostrar aunque sean 0
    datos_grafico = {
        'Categoría': ['Ahorros', 'Préstamos', 'Pagos Préstamos', 'Multas'],
        'Monto': [total_ahorros, total_prestamos, total_pagos_prestamos, total_multas],
        'Color': ['#00CC96', '#636EFA', '#EF553B', '#AB63FA']
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
    
    # Mostrar gráfico (SIEMPRE mostrarlo aunque los datos sean 0)
    st.plotly_chart(fig, use_container_width=True)
    
    # Mostrar mensaje si no hay datos
    if total_ahorros == 0 and total_prestamos == 0 and total_pagos_prestamos == 0 and total_multas == 0:
        st.info("💡 **Nota:** No se encontraron datos en el período seleccionado. El gráfico se actualizará automáticamente cuando se registren datos.")
    
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
    st.info(f"**📅 Período analizado:** {fecha_inicio} al {fecha_fin}")

# Para pruebas independientes
if __name__ == "__main__":
    # Simular que hay una promotora logueada para pruebas
    if 'id_promotora' not in st.session_state:
        st.session_state.id_promotora = 1
        st.info("🔧 **MODO PRUEBA:** Usando ID de promotora = 1")
    
    mostrar_consolidado_promotora()
