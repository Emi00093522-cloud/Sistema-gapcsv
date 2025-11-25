import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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

def obtener_ahorros_por_grupo_rango(id_grupo, fecha_inicio, fecha_fin):
    """Obtiene ahorros totales por grupo en rango de fechas"""
    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                COALESCE(SUM(a.monto_ahorro), 0) as total_ahorros,
                COALESCE(SUM(a.monto_otros), 0) as total_otros,
                COALESCE(SUM(a.monto_ahorro + a.monto_otros), 0) as total_general
            FROM Ahorro a
            JOIN Reunion r ON a.ID_Reunion = r.ID_Reunion
            WHERE r.ID_Grupo = %s 
            AND r.fecha BETWEEN %s AND %s
        """, (id_grupo, fecha_inicio, fecha_fin))
        
        resultado = cursor.fetchone()
        return resultado or {'total_ahorros': 0, 'total_otros': 0, 'total_general': 0}
        
    except Exception as e:
        st.error(f"❌ Error obteniendo ahorros: {e}")
        return {'total_ahorros': 0, 'total_otros': 0, 'total_general': 0}
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'con' in locals(): con.close()

def obtener_prestamos_por_grupo_rango(id_grupo, fecha_inicio, fecha_fin):
    """Obtiene préstamos otorgados por grupo en rango de fechas"""
    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                COALESCE(SUM(p.monto), 0) as total_prestamos,
                COALESCE(SUM(p.total_interes), 0) as total_intereses,
                COALESCE(SUM(p.monto_total_pagar), 0) as total_a_pagar
            FROM Prestamo p
            JOIN Miembro m ON p.ID_Miembro = m.ID_Miembro
            WHERE m.ID_Grupo = %s 
            AND p.fecha_desembolso BETWEEN %s AND %s
            AND p.ID_Estado_prestamo != 3  -- Excluir cancelados
        """, (id_grupo, fecha_inicio, fecha_fin))
        
        resultado = cursor.fetchone()
        return resultado or {'total_prestamos': 0, 'total_intereses': 0, 'total_a_pagar': 0}
        
    except Exception as e:
        st.error(f"❌ Error obteniendo préstamos: {e}")
        return {'total_prestamos': 0, 'total_intereses': 0, 'total_a_pagar': 0}
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'con' in locals(): con.close()

def obtener_multas_por_grupo_rango(id_grupo, fecha_inicio, fecha_fin):
    """Obtiene multas recaudadas por grupo en rango de fechas"""
    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                COALESCE(SUM(pm.monto_pagado), 0) as total_multas
            FROM PagoMulta pm
            JOIN Miembro m ON pm.ID_Miembro = m.ID_Miembro
            WHERE m.ID_Grupo = %s 
            AND pm.fecha_pago BETWEEN %s AND %s
        """, (id_grupo, fecha_inicio, fecha_fin))
        
        resultado = cursor.fetchone()
        return resultado or {'total_multas': 0}
        
    except Exception as e:
        st.error(f"❌ Error obteniendo multas: {e}")
        return {'total_multas': 0}
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'con' in locals(): con.close()

def obtener_pagos_prestamos_por_grupo_rango(id_grupo, fecha_inicio, fecha_fin):
    """Obtiene pagos de préstamos recibidos por grupo en rango de fechas"""
    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                COALESCE(SUM(pp.total_cancelado), 0) as total_pagos,
                COALESCE(SUM(pp.monto_capital), 0) as capital_recuperado,
                COALESCE(SUM(pp.monto_interes), 0) as intereses_recuperados
            FROM Pago_prestamo pp
            JOIN Prestamo p ON pp.ID_Prestamo = p.ID_Prestamo
            JOIN Miembro m ON p.ID_Miembro = m.ID_Miembro
            WHERE m.ID_Grupo = %s 
            AND pp.fecha_pago BETWEEN %s AND %s
        """, (id_grupo, fecha_inicio, fecha_fin))
        
        resultado = cursor.fetchone()
        return resultado or {'total_pagos': 0, 'capital_recuperado': 0, 'intereses_recuperados': 0}
        
    except Exception as e:
        st.error(f"❌ Error obteniendo pagos de préstamos: {e}")
        return {'total_pagos': 0, 'capital_recuperado': 0, 'intereses_recuperados': 0}
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'con' in locals(): con.close()

def mostrar_consolidado_promotora():
    """Función principal que muestra el consolidado"""
    
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
    
    # Selector de grupo
    grupo_options = {f"{g['nombre_grupo']}": g['ID_Grupo'] for g in grupos}
    grupo_seleccionado = st.selectbox(
        "🏢 Selecciona el Grupo a Consultar:",
        options=list(grupo_options.keys())
    )
    
    id_grupo_seleccionado = grupo_options[grupo_seleccionado]
    
    st.markdown("---")
    
    # Filtro de fechas
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
    
    st.markdown("---")
    
    # Botón para actualizar datos
    if st.button("🔄 Generar Reporte Consolidado", type="primary", use_container_width=True):
        
        # Obtener datos consolidados
        with st.spinner("📊 Calculando datos consolidados..."):
            # INGRESOS
            ahorros_data = obtener_ahorros_por_grupo_rango(id_grupo_seleccionado, fecha_inicio, fecha_fin)
            multas_data = obtener_multas_por_grupo_rango(id_grupo_seleccionado, fecha_inicio, fecha_fin)
            prestamos_data = obtener_prestamos_por_grupo_rango(id_grupo_seleccionado, fecha_inicio, fecha_fin)
            
            # EGRESOS
            pagos_prestamos_data = obtener_pagos_prestamos_por_grupo_rango(id_grupo_seleccionado, fecha_inicio, fecha_fin)
            
            # Cálculos finales
            total_ingresos = (
                ahorros_data['total_general'] + 
                multas_data['total_multas'] + 
                prestamos_data['total_intereses']
            )
            
            total_egresos = pagos_prestamos_data['total_pagos']
            balance_general = total_ingresos - total_egresos
        
        # MOSTRAR MÉTRICAS PRINCIPALES
        st.subheader("💰 Métricas Financieras Principales")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "📈 Total Ingresos", 
                f"${total_ingresos:,.2f}",
                delta=None
            )
        
        with col2:
            st.metric(
                "📉 Total Egresos", 
                f"${total_egresos:,.2f}",
                delta=None
            )
        
        with col3:
            balance_color = "normal" if balance_general >= 0 else "inverse"
            st.metric(
                "⚖️ Balance General", 
                f"${balance_general:,.2f}",
                delta=None
            )
        
        st.markdown("---")
        
        # DETALLE DE INGRESOS
        st.subheader("📥 Desglose de Ingresos")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("💰 Ahorros", f"${ahorros_data['total_general']:,.2f}")
            st.caption(f"Ahorros: ${ahorros_data['total_ahorros']:,.2f}")
            st.caption(f"Otros: ${ahorros_data['total_otros']:,.2f}")
        
        with col2:
            st.metric("⚖️ Multas", f"${multas_data['total_multas']:,.2f}")
        
        with col3:
            st.metric("🏦 Préstamos", f"${prestamos_data['total_prestamos']:,.2f}")
        
        with col4:
            st.metric("📈 Intereses", f"${prestamos_data['total_intereses']:,.2f}")
        
        st.markdown("---")
        
        # DETALLE DE EGRESOS
        st.subheader("📤 Desglose de Egresos")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("💸 Pagos Préstamos", f"${pagos_prestamos_data['total_pagos']:,.2f}")
        
        with col2:
            st.metric("🔙 Capital Recuperado", f"${pagos_prestamos_data['capital_recuperado']:,.2f}")
        
        with col3:
            st.metric("🎯 Intereses Recibidos", f"${pagos_prestamos_data['intereses_recuperados']:,.2f}")
        
        st.markdown("---")
        
        # TABLA RESUMEN DETALLADA
        st.subheader("📋 Resumen Detallado por Concepto")
        
        resumen_data = {
            'Concepto': [
                'AHORROS TOTALES',
                ' - Ahorros Regulares',
                ' - Otros Ingresos',
                'MULTAS RECAUDADAS',
                'PRÉSTAMOS OTORGADOS',
                'INTERESES GENERADOS',
                'PAGOS RECIBIDOS',
                ' - Capital Recuperado',
                ' - Intereses Recibidos',
                '**TOTAL INGRESOS**',
                '**TOTAL EGRESOS**',
                '**BALANCE GENERAL**'
            ],
            'Monto ($)': [
                f"{ahorros_data['total_general']:,.2f}",
                f"{ahorros_data['total_ahorros']:,.2f}",
                f"{ahorros_data['total_otros']:,.2f}",
                f"{multas_data['total_multas']:,.2f}",
                f"{prestamos_data['total_prestamos']:,.2f}",
                f"{prestamos_data['total_intereses']:,.2f}",
                f"{pagos_prestamos_data['total_pagos']:,.2f}",
                f"{pagos_prestamos_data['capital_recuperado']:,.2f}",
                f"{pagos_prestamos_data['intereses_recuperados']:,.2f}",
                f"**{total_ingresos:,.2f}**",
                f"**{total_egresos:,.2f}**",
                f"**{balance_general:,.2f}**"
            ]
        }
        
        df_resumen = pd.DataFrame(resumen_data)
        st.dataframe(df_resumen, use_container_width=True, hide_index=True)
        
        # GRÁFICAS SIMPLES (sin datos mensuales por ahora)
        st.markdown("---")
        st.subheader("📊 Distribución de Ingresos")
        
        # Gráfica de torta de ingresos
        labels = ['Ahorros', 'Multas', 'Intereses']
        values = [
            ahorros_data['total_general'],
            multas_data['total_multas'], 
            prestamos_data['total_intereses']
        ]
        
        if sum(values) > 0:
            fig = px.pie(
                names=labels, 
                values=values,
                title="Distribución de Ingresos",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de ingresos para mostrar gráficas")

# Para pruebas independientes
if __name__ == "__main__":
    # Simular que hay una promotora logueada
    st.session_state.id_promotora = 1
    mostrar_consolidado_promotora()
