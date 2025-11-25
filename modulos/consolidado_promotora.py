import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os

# Agregar la ruta de tus módulos
sys.path.append(os.path.dirname(__file__))

# =============================================
#  CONFIGURACIÓN INICIAL
# =============================================

def verificar_sesion_promotora():
    """Verifica que la promotora tenga sesión activa."""
    if "id_promotora" not in st.session_state or st.session_state.id_promotora is None:
        st.error("🚫 No hay sesión de promotora activa. Por favor inicia sesión.")
        st.stop()
    return True

def obtener_grupos_promotora():
    """Obtiene los grupos que maneja la promotora actual."""
    try:
        from modulos.config.conexion import obtener_conexion
        
        id_promotora = st.session_state.id_promotora
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT ID_Grupo, nombre_grupo 
            FROM Grupo 
            WHERE ID_Promotora = %s
            ORDER BY nombre_grupo
        """, (id_promotora,))
        
        grupos = cursor.fetchall()
        cursor.close()
        con.close()
        
        return grupos
        
    except Exception as e:
        st.error(f"❌ Error obteniendo grupos de la promotora: {e}")
        return []

# =============================================
#  FUNCIONES PARA OBTENER DATOS (SIMILARES A CICLO)
# =============================================

def obtener_ahorros_grupo_rango(id_grupo, fecha_inicio, fecha_fin):
    """Obtiene ahorros de un grupo en rango de fechas - igual que en ciclo.py"""
    try:
        from modulos.config.conexion import obtener_conexion
        
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        query = """
            SELECT 
                COALESCE(SUM(a.monto_ahorro), 0) AS total_ahorros,
                COALESCE(SUM(a.monto_otros), 0) AS total_otros,
                COALESCE(SUM(a.monto_ahorro + a.monto_otros), 0) AS total_general
            FROM Miembro m
            LEFT JOIN Ahorro a ON m.ID_Miembro = a.ID_Miembro
            LEFT JOIN Reunion r ON a.ID_Reunion = r.ID_Reunion
            WHERE m.ID_Grupo = %s
              AND m.ID_Estado = 1
              AND r.fecha BETWEEN %s AND %s
        """
        
        cursor.execute(query, (id_grupo, fecha_inicio, fecha_fin))
        resultado = cursor.fetchone()
        
        cursor.close()
        con.close()
        
        return {
            "total_ahorros": float(resultado["total_ahorros"]),
            "total_otros": float(resultado["total_otros"]),
            "total_general": float(resultado["total_general"])
        }
        
    except Exception as e:
        st.error(f"❌ Error obteniendo ahorros del grupo {id_grupo}: {e}")
        return {"total_ahorros": 0, "total_otros": 0, "total_general": 0}

def obtener_prestamos_grupo_rango(id_grupo, fecha_inicio, fecha_fin):
    """Obtiene préstamos de un grupo en rango de fechas - igual que en ciclo.py"""
    try:
        from modulos.config.conexion import obtener_conexion
        
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        query = """
            SELECT 
                COALESCE(SUM(p.monto), 0) AS total_capital,
                COALESCE(SUM(p.total_interes), 0) AS total_intereses
            FROM Prestamo p
            JOIN Miembro m ON p.ID_Miembro = m.ID_Miembro
            WHERE m.ID_Grupo = %s 
              AND p.ID_Estado_prestamo != 3
              AND p.fecha_desembolso BETWEEN %s AND %s
        """
        
        cursor.execute(query, (id_grupo, fecha_inicio, fecha_fin))
        resultado = cursor.fetchone()
        
        cursor.close()
        con.close()
        
        return {
            "total_capital": float(resultado["total_capital"]),
            "total_intereses": float(resultado["total_intereses"]),
            "total_prestamos": float(resultado["total_capital"] + resultado["total_intereses"])
        }
        
    except Exception as e:
        st.error(f"❌ Error obteniendo préstamos del grupo {id_grupo}: {e}")
        return {"total_capital": 0, "total_intereses": 0, "total_prestamos": 0}

def obtener_multas_grupo_rango(id_grupo, fecha_inicio, fecha_fin):
    """Obtiene multas de un grupo en rango de fechas - igual que en ciclo.py"""
    try:
        from modulos.config.conexion import obtener_conexion
        
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        query = """
            SELECT 
                COALESCE(SUM(pm.monto_pagado), 0) AS total_multas
            FROM PagoMulta pm
            JOIN Multa mult ON pm.ID_Multa = mult.ID_Multa
            JOIN Miembro m ON pm.ID_Miembro = m.ID_Miembro
            WHERE m.ID_Grupo = %s
              AND pm.fecha_pago BETWEEN %s AND %s
        """
        
        cursor.execute(query, (id_grupo, fecha_inicio, fecha_fin))
        resultado = cursor.fetchone()
        
        cursor.close()
        con.close()
        
        return {
            "total_multas": float(resultado["total_multas"])
        }
        
    except Exception as e:
        st.error(f"❌ Error obteniendo multas del grupo {id_grupo}: {e}")
        return {"total_multas": 0}

def obtener_miembros_activos_grupo(id_grupo):
    """Obtiene miembros activos de un grupo - igual que en ciclo.py"""
    try:
        from modulos.config.conexion import obtener_conexion
        
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT COUNT(*) AS total_miembros
            FROM Miembro 
            WHERE ID_Grupo = %s AND ID_Estado = 1
        """, (id_grupo,))
        
        resultado = cursor.fetchone()
        total_miembros = resultado["total_miembros"] if resultado else 0
        
        cursor.close()
        con.close()
        
        return total_miembros
        
    except Exception as e:
        st.error(f"❌ Error obteniendo miembros del grupo {id_grupo}: {e}")
        return 0

# =============================================
#  CÁLCULO DE CONSOLDADO POR GRUPO
# =============================================

def calcular_consolidado_grupo(id_grupo, nombre_grupo, fecha_inicio, fecha_fin):
    """Calcula el consolidado completo para un grupo - similar a ciclo.py"""
    
    # Obtener datos del grupo
    ahorros = obtener_ahorros_grupo_rango(id_grupo, fecha_inicio, fecha_fin)
    prestamos = obtener_prestamos_grupo_rango(id_grupo, fecha_inicio, fecha_fin)
    multas = obtener_multas_grupo_rango(id_grupo, fecha_inicio, fecha_fin)
    miembros = obtener_miembros_activos_grupo(id_grupo)
    
    # Calcular totales (igual que en ciclo.py)
    total_ahorros = ahorros["total_general"]
    total_prestamos_capital = prestamos["total_capital"]
    total_intereses = prestamos["total_intereses"]
    total_multas = multas["total_multas"]
    total_ingresos = total_ahorros + total_multas + total_prestamos_capital + total_intereses
    
    return {
        "id_grupo": id_grupo,
        "nombre_grupo": nombre_grupo,
        "total_miembros": miembros,
        "total_ahorros": total_ahorros,
        "total_prestamos_capital": total_prestamos_capital,
        "total_intereses": total_intereses,
        "total_multas": total_multas,
        "total_ingresos": total_ingresos
    }

# =============================================
#  VISUALIZACIONES Y GRÁFICOS
# =============================================

def crear_grafico_barras_consolidado(datos_consolidado):
    """Crea gráfico de barras con los datos consolidados"""
    if not datos_consolidado:
        return None
    
    # Preparar datos para el gráfico
    grupos = [f"{d['nombre_grupo']}\n({d['total_miembros']} miembros)" for d in datos_consolidado]
    
    df_grafico = pd.DataFrame({
        'Grupo': grupos,
        'Ahorros': [d["total_ahorros"] for d in datos_consolidado],
        'Préstamos Capital': [d["total_prestamos_capital"] for d in datos_consolidado],
        'Intereses': [d["total_intereses"] for d in datos_consolidado],
        'Multas': [d["total_multas"] for d in datos_consolidado]
    })
    
    # Crear gráfico de barras
    fig = px.bar(df_grafico, 
                 x='Grupo', 
                 y=['Ahorros', 'Préstamos Capital', 'Intereses', 'Multas'],
                 title='📊 Consolidado Financiero por Grupo',
                 labels={'value': 'Monto ($)', 'variable': 'Concepto', 'Grupo': 'Grupos'},
                 barmode='group',
                 color_discrete_sequence=['#2E86AB', '#A23B72', '#F18F01', '#C73E1D'])
    
    fig.update_layout(
        xaxis_tickangle=-45,
        showlegend=True,
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig

def crear_grafico_totales(datos_consolidado):
    """Crea gráfico de totales por concepto"""
    if not datos_consolidado:
        return None
    
    totales = {
        'Ahorros': sum(d["total_ahorros"] for d in datos_consolidado),
        'Préstamos Capital': sum(d["total_prestamos_capital"] for d in datos_consolidado),
        'Intereses': sum(d["total_intereses"] for d in datos_consolidado),
        'Multas': sum(d["total_multas"] for d in datos_consolidado)
    }
    
    fig = px.pie(
        names=list(totales.keys()),
        values=list(totales.values()),
        title='📈 Distribución de Totales por Concepto',
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    
    return fig

# =============================================
#  INTERFAZ PRINCIPAL
# =============================================

def mostrar_filtros():
    """Muestra los filtros de fechas y grupos"""
    st.subheader("📅 Seleccionar Rango del Consolidado")
    
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
        return None, None
    
    dias_ciclo = (fecha_fin - fecha_inicio).days
    st.info(f"**📊 Rango seleccionado:** {fecha_inicio} a {fecha_fin} ({dias_ciclo} días)")
    
    return fecha_inicio, fecha_fin

def mostrar_tabla_consolidado(datos_consolidado):
    """Muestra la tabla de consolidado - similar a ciclo.py"""
    if not datos_consolidado:
        st.warning("No hay datos para mostrar en la tabla.")
        return
    
    # Preparar datos para la tabla (igual formato que ciclo.py)
    tabla_data = []
    for dato in datos_consolidado:
        tabla_data.append({
            "Grupo": dato["nombre_grupo"],
            "Miembros Activos": f"{dato['total_miembros']}",
            "💰 Total Ahorros": f"${dato['total_ahorros']:,.2f}",
            "🏦 Total Préstamos (Capital)": f"${dato['total_prestamos_capital']:,.2f}",
            "📈 Total Intereses": f"${dato['total_intereses']:,.2f}",
            "⚖️ Total Multas": f"${dato['total_multas']:,.2f}",
            "💵 TOTAL INGRESOS": f"${dato['total_ingresos']:,.2f}"
        })
    
    df_tabla = pd.DataFrame(tabla_data)
    st.dataframe(df_tabla, use_container_width=True, hide_index=True)
    
    # Mostrar totales generales
    if datos_consolidado:
        total_general = {
            "ahorros": sum(d["total_ahorros"] for d in datos_consolidado),
            "prestamos_capital": sum(d["total_prestamos_capital"] for d in datos_consolidado),
            "intereses": sum(d["total_intereses"] for d in datos_consolidado),
            "multas": sum(d["total_multas"] for d in datos_consolidado),
            "ingresos": sum(d["total_ingresos"] for d in datos_consolidado)
        }
        
        st.success(f"**📊 TOTALES GENERALES PROMOTORA:** "
                  f"Ahorros: ${total_general['ahorros']:,.2f} | "
                  f"Préstamos: ${total_general['prestamos_capital']:,.2f} | "
                  f"Intereses: ${total_general['intereses']:,.2f} | "
                  f"Multas: ${total_general['multas']:,.2f} | "
                  f"**TOTAL: ${total_general['ingresos']:,.2f}**")

def mostrar_metricas_consolidado(datos_consolidado):
    """Muestra métricas del consolidado - similar a ciclo.py"""
    if not datos_consolidado:
        return
    
    total_general = {
        "ahorros": sum(d["total_ahorros"] for d in datos_consolidado),
        "prestamos_capital": sum(d["total_prestamos_capital"] for d in datos_consolidado),
        "intereses": sum(d["total_intereses"] for d in datos_consolidado),
        "multas": sum(d["total_multas"] for d in datos_consolidado),
        "ingresos": sum(d["total_ingresos"] for d in datos_consolidado),
        "miembros": sum(d["total_miembros"] for d in datos_consolidado),
        "grupos": len(datos_consolidado)
    }
    
    st.subheader("📈 Métricas del Consolidado")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Grupos", f"{total_general['grupos']}")
        st.metric("Total Miembros", f"{total_general['miembros']}")
    with col2:
        st.metric("Total Ahorros", f"${total_general['ahorros']:,.2f}")
        st.metric("Total Multas", f"${total_general['multas']:,.2f}")
    with col3:
        st.metric("Total Préstamos", f"${total_general['prestamos_capital']:,.2f}")
        st.metric("Total Intereses", f"${total_general['intereses']:,.2f}")
    with col4:
        st.metric("Total Ingresos", f"${total_general['ingresos']:,.2f}")
        st.metric("Promedio x Grupo", f"${total_general['ingresos']/max(1, total_general['grupos']):,.2f}")

# =============================================
#  FUNCIÓN PRINCIPAL
# =============================================

def mostrar_consolidado_promotora():
    """Función principal - similar estructura a ciclo.py"""
    
    # Verificar sesión
    verificar_sesion_promotora()
    
    st.header("📊 Consolidado de Promotora - Resumen Financiero")
    
    # Obtener grupos de la promotora
    grupos = obtener_grupos_promotora()
    if not grupos:
        st.warning("ℹ️ No tienes grupos asignados como promotora.")
        return
    
    st.success(f"✅ Promotora tiene {len(grupos)} grupo(s) asignado(s)")
    
    # Mostrar filtros
    fecha_inicio, fecha_fin = mostrar_filtros()
    if fecha_inicio is None:
        return
    
    st.markdown("---")
    
    # Botón para generar consolidado
    if st.button("🚀 Generar Consolidado de Promotora", type="primary", use_container_width=True):
        
        with st.spinner("🔍 Calculando consolidado de todos los grupos..."):
            datos_consolidado = []
            
            for grupo in grupos:
                consolidado = calcular_consolidado_grupo(
                    grupo["ID_Grupo"],
                    grupo["nombre_grupo"],
                    fecha_inicio,
                    fecha_fin
                )
                datos_consolidado.append(consolidado)
            
            # MOSTRAR RESULTADOS - IGUAL QUE EN CICLO.PY
            
            # 1. Tabla de Consolidado
            st.subheader(f"📋 Tabla de Consolidado: {fecha_inicio} a {fecha_fin}")
            mostrar_tabla_consolidado(datos_consolidado)
            
            # 2. Métricas
            mostrar_metricas_consolidado(datos_consolidado)
            
            st.markdown("---")
            
            # 3. Gráficos de Barras (NUEVO - lo que solicitaste)
            st.subheader("📊 Gráficos de Consolidado")
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_barras = crear_grafico_barras_consolidado(datos_consolidado)
                if fig_barras:
                    st.plotly_chart(fig_barras, use_container_width=True)
            
            with col2:
                fig_totales = crear_grafico_totales(datos_consolidado)
                if fig_totales:
                    st.plotly_chart(fig_totales, use_container_width=True)
            
            # 4. Detalles por grupo
            st.markdown("---")
            st.subheader("👥 Detalles por Grupo")
            
            for dato in datos_consolidado:
                with st.expander(f"📊 {dato['nombre_grupo']} - {dato['total_miembros']} miembros"):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Ahorros", f"${dato['total_ahorros']:,.2f}")
                    with col2:
                        st.metric("Préstamos", f"${dato['total_prestamos_capital']:,.2f}")
                    with col3:
                        st.metric("Intereses", f"${dato['total_intereses']:,.2f}")
                    with col4:
                        st.metric("Multas", f"${dato['total_multas']:,.2f}")

if __name__ == "__main__":
    mostrar_consolidado_promotora()
