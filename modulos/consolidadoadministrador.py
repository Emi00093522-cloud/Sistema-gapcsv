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
#  CONEXIÓN A BASE DE DATOS
# =============================================

def obtener_conexion():
    """Obtiene conexión a la base de datos."""
    try:
        from modulos.config.conexion import obtener_conexion as conectar
        return conectar()
    except Exception as e:
        st.error(f"❌ Error de conexión: {e}")
        return None

# =============================================
#  FUNCIONES PARA OBTENER DATOS DE TODOS LOS GRUPOS
# =============================================

def obtener_todos_los_grupos():
    """Obtiene todos los grupos activos de la base de datos."""
    try:
        con = obtener_conexion()
        if con is None:
            return []
        
        cursor = con.cursor(dictionary=True)
        cursor.execute("""
            SELECT g.ID_Grupo, g.nombre as nombre_grupo, 
                   d.nombre as nombre_distrito, g.fecha_creacion
            FROM Grupo g
            LEFT JOIN Distrito d ON g.ID_Distrito = d.ID_Distrito
            WHERE g.estado = 1
            ORDER BY d.nombre, g.nombre
        """)
        
        grupos = cursor.fetchall()
        cursor.close()
        con.close()
        
        return grupos
    except Exception as e:
        st.error(f"❌ Error obteniendo grupos: {e}")
        return []

def obtener_ahorros_todos_grupos(fecha_inicio=None, fecha_fin=None):
    """Obtiene los ahorros de TODOS los grupos."""
    try:
        con = obtener_conexion()
        if con is None:
            return []
        
        cursor = con.cursor(dictionary=True)
        
        query = """
            SELECT 
                g.ID_Grupo,
                g.nombre as nombre_grupo,
                d.nombre as nombre_distrito,
                COALESCE(SUM(a.monto_ahorro), 0) as total_ahorros,
                COALESCE(SUM(a.monto_otros), 0) as total_otros,
                COALESCE(SUM(a.monto_ahorro + a.monto_otros), 0) as total_general,
                COUNT(DISTINCT m.ID_Miembro) as total_miembros
            FROM Grupo g
            LEFT JOIN Distrito d ON g.ID_Distrito = d.ID_Distrito
            LEFT JOIN Miembro m ON g.ID_Grupo = m.ID_Grupo AND m.ID_Estado = 1
            LEFT JOIN Ahorro a ON m.ID_Miembro = a.ID_Miembro
            LEFT JOIN Reunion r ON a.ID_Reunion = r.ID_Reunion
            WHERE g.estado = 1
        """
        
        params = []
        
        # Filtro por rango de fechas
        if fecha_inicio and fecha_fin:
            query += " AND r.fecha BETWEEN %s AND %s"
            params.extend([fecha_inicio, fecha_fin])
        
        query += """
            GROUP BY g.ID_Grupo, g.nombre, d.nombre
            ORDER BY d.nombre, g.nombre
        """
        
        cursor.execute(query, tuple(params))
        ahorros_grupos = cursor.fetchall()
        
        resultado = []
        for row in ahorros_grupos:
            resultado.append({
                "id_grupo": row["ID_Grupo"],
                "grupo": row["nombre_grupo"],
                "distrito": row["nombre_distrito"] or "Sin distrito",
                "total_ahorros": float(row["total_ahorros"]),
                "total_otros": float(row["total_otros"]),
                "total_general": float(row["total_general"]),
                "total_miembros": row["total_miembros"]
            })
        
        cursor.close()
        con.close()
        return resultado

    except Exception as e:
        st.error(f"❌ Error obteniendo ahorros de todos los grupos: {e}")
        return []

def obtener_prestamos_todos_grupos(fecha_inicio=None, fecha_fin=None):
    """Obtiene los préstamos de TODOS los grupos."""
    try:
        con = obtener_conexion()
        if con is None:
            return []
        
        cursor = con.cursor(dictionary=True)
        
        query = """
            SELECT 
                g.ID_Grupo,
                g.nombre as nombre_grupo,
                d.nombre as nombre_distrito,
                COALESCE(SUM(p.monto), 0) as total_capital,
                COALESCE(SUM(p.total_interes), 0) as total_intereses,
                COALESCE(SUM(p.monto_total_pagar), 0) as total_pagar,
                COUNT(p.ID_Prestamo) as total_prestamos
            FROM Grupo g
            LEFT JOIN Distrito d ON g.ID_Distrito = d.ID_Distrito
            LEFT JOIN Miembro m ON g.ID_Grupo = m.ID_Grupo
            LEFT JOIN Prestamo p ON m.ID_Miembro = p.ID_Miembro
            WHERE g.estado = 1 
              AND p.ID_Estado_prestamo != 3  -- Excluir cancelados/rechazados
        """
        
        params = []
        
        # Filtro por fecha de desembolso
        if fecha_inicio and fecha_fin:
            query += " AND p.fecha_desembolso BETWEEN %s AND %s"
            params.extend([fecha_inicio, fecha_fin])
        
        query += """
            GROUP BY g.ID_Grupo, g.nombre, d.nombre
            ORDER BY d.nombre, g.nombre
        """
        
        cursor.execute(query, tuple(params))
        prestamos_grupos = cursor.fetchall()
        
        resultado = []
        for row in prestamos_grupos:
            resultado.append({
                "id_grupo": row["ID_Grupo"],
                "grupo": row["nombre_grupo"],
                "distrito": row["nombre_distrito"] or "Sin distrito",
                "total_capital": float(row["total_capital"]),
                "total_intereses": float(row["total_intereses"]),
                "total_pagar": float(row["total_pagar"]),
                "total_prestamos": row["total_prestamos"]
            })
        
        cursor.close()
        con.close()
        return resultado

    except Exception as e:
        st.error(f"❌ Error obteniendo préstamos de todos los grupos: {e}")
        return []

def obtener_multas_todos_grupos(fecha_inicio=None, fecha_fin=None):
    """Obtiene las multas de TODOS los grupos."""
    try:
        con = obtener_conexion()
        if con is None:
            return []
        
        cursor = con.cursor(dictionary=True)
        
        query = """
            SELECT 
                g.ID_Grupo,
                g.nombre as nombre_grupo,
                d.nombre as nombre_distrito,
                COALESCE(SUM(pm.monto_pagado), 0) as total_multas,
                COUNT(pm.ID_PagoMulta) as total_multas_pagadas
            FROM Grupo g
            LEFT JOIN Distrito d ON g.ID_Distrito = d.ID_Distrito
            LEFT JOIN Miembro m ON g.ID_Grupo = m.ID_Grupo
            LEFT JOIN PagoMulta pm ON m.ID_Miembro = pm.ID_Miembro
            WHERE g.estado = 1
        """
        
        params = []
        
        # Filtro por fecha de pago
        if fecha_inicio and fecha_fin:
            query += " AND pm.fecha_pago BETWEEN %s AND %s"
            params.extend([fecha_inicio, fecha_fin])
        
        query += """
            GROUP BY g.ID_Grupo, g.nombre, d.nombre
            ORDER BY d.nombre, g.nombre
        """
        
        cursor.execute(query, tuple(params))
        multas_grupos = cursor.fetchall()
        
        resultado = []
        for row in multas_grupos:
            resultado.append({
                "id_grupo": row["ID_Grupo"],
                "grupo": row["nombre_grupo"],
                "distrito": row["nombre_distrito"] or "Sin distrito",
                "total_multas": float(row["total_multas"]),
                "total_multas_pagadas": row["total_multas_pagadas"]
            })
        
        cursor.close()
        con.close()
        return resultado

    except Exception as e:
        st.error(f"❌ Error obteniendo multas de todos los grupos: {e}")
        return []

def obtener_pagos_prestamos_todos_grupos(fecha_inicio=None, fecha_fin=None):
    """Obtiene los pagos de préstamos de TODOS los grupos."""
    try:
        con = obtener_conexion()
        if con is None:
            return []
        
        cursor = con.cursor(dictionary=True)
        
        query = """
            SELECT 
                g.ID_Grupo,
                g.nombre as nombre_grupo,
                d.nombre as nombre_distrito,
                COALESCE(SUM(pp.monto_pagado), 0) as total_pagos,
                COUNT(pp.ID_PagoPrestamo) as total_pagos_realizados
            FROM Grupo g
            LEFT JOIN Distrito d ON g.ID_Distrito = d.ID_Distrito
            LEFT JOIN Miembro m ON g.ID_Grupo = m.ID_Grupo
            LEFT JOIN Prestamo p ON m.ID_Miembro = p.ID_Miembro
            LEFT JOIN PagoPrestamo pp ON p.ID_Prestamo = pp.ID_Prestamo
            WHERE g.estado = 1
        """
        
        params = []
        
        # Filtro por fecha de pago
        if fecha_inicio and fecha_fin:
            query += " AND pp.fecha_pago BETWEEN %s AND %s"
            params.extend([fecha_inicio, fecha_fin])
        
        query += """
            GROUP BY g.ID_Grupo, g.nombre, d.nombre
            ORDER BY d.nombre, g.nombre
        """
        
        cursor.execute(query, tuple(params))
        pagos_grupos = cursor.fetchall()
        
        resultado = []
        for row in pagos_grupos:
            resultado.append({
                "id_grupo": row["ID_Grupo"],
                "grupo": row["nombre_grupo"],
                "distrito": row["nombre_distrito"] or "Sin distrito",
                "total_pagos": float(row["total_pagos"]),
                "total_pagos_realizados": row["total_pagos_realizados"]
            })
        
        cursor.close()
        con.close()
        return resultado

    except Exception as e:
        st.error(f"❌ Error obteniendo pagos de préstamos de todos los grupos: {e}")
        return []

# =============================================
#  CÁLCULO DE TOTALES GENERALES
# =============================================

def calcular_totales_generales(fecha_inicio=None, fecha_fin=None):
    """Calcula los totales generales de TODOS los grupos."""
    
    with st.spinner("🔄 Calculando datos de todos los grupos..."):
        # Obtener datos de todos los grupos
        ahorros_data = obtener_ahorros_todos_grupos(fecha_inicio, fecha_fin)
        prestamos_data = obtener_prestamos_todos_grupos(fecha_inicio, fecha_fin)
        multas_data = obtener_multas_todos_grupos(fecha_inicio, fecha_fin)
        pagos_data = obtener_pagos_prestamos_todos_grupos(fecha_inicio, fecha_fin)
    
    # Calcular totales
    total_ahorros = sum(item["total_general"] for item in ahorros_data)
    total_prestamos_capital = sum(item["total_capital"] for item in prestamos_data)
    total_prestamos_intereses = sum(item["total_intereses"] for item in prestamos_data)
    total_multas = sum(item["total_multas"] for item in multas_data)
    total_pagos_prestamos = sum(item["total_pagos"] for item in pagos_data)
    
    total_ingresos = total_ahorros + total_multas + total_prestamos_capital + total_prestamos_intereses
    total_grupos = len(ahorros_data)
    total_miembros = sum(item["total_miembros"] for item in ahorros_data)
    
    return {
        "total_ahorros": total_ahorros,
        "total_prestamos_capital": total_prestamos_capital,
        "total_prestamos_intereses": total_prestamos_intereses,
        "total_multas": total_multas,
        "total_pagos_prestamos": total_pagos_prestamos,
        "total_ingresos": total_ingresos,
        "total_grupos": total_grupos,
        "total_miembros": total_miembros,
        "ahorros_detalle": ahorros_data,
        "prestamos_detalle": prestamos_data,
        "multas_detalle": multas_data,
        "pagos_detalle": pagos_data
    }

# =============================================
#  GRÁFICOS DE CONSOLIDADO GENERAL
# =============================================

def crear_graficos_consolidado_general(totales, fecha_inicio, fecha_fin):
    """Crea gráficos para el consolidado general de TODOS los grupos."""
    
    st.subheader("📊 Gráficos de Consolidado General")
    
    # Datos para gráficos principales
    categorias_ingresos = ['Ahorros', 'Multas', 'Préstamos Capital', 'Intereses']
    valores_ingresos = [
        totales["total_ahorros"], 
        totales["total_multas"], 
        totales["total_prestamos_capital"], 
        totales["total_prestamos_intereses"]
    ]
    
    # Gráfico 1: Distribución de Ingresos
    col1, col2 = st.columns(2)
    
    with col1:
        fig_ingresos = px.pie(
            names=categorias_ingresos,
            values=valores_ingresos,
            title="📈 Distribución de Ingresos Totales",
            color=categorias_ingresos,
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_ingresos.update_traces(textposition='inside', textinfo='percent+label+value')
        st.plotly_chart(fig_ingresos, use_container_width=True)
    
    # Gráfico 2: Métricas Principales
    with col2:
        fig_metricas = go.Figure()
        
        metricas = ['Grupos', 'Miembros', 'Ahorros', 'Préstamos']
        valores = [
            totales["total_grupos"],
            totales["total_miembros"],
            totales["total_ahorros"],
            totales["total_prestamos_capital"]
        ]
        
        fig_metricas.add_trace(go.Bar(
            x=metricas,
            y=valores,
            marker_color=['blue', 'green', 'orange', 'red']
        ))
        
        fig_metricas.update_layout(
            title="📊 Métricas Generales del Sistema",
            xaxis_title="Categorías",
            yaxis_title="Valores",
            showlegend=False
        )
        st.plotly_chart(fig_metricas, use_container_width=True)
    
    # Gráfico 3: Comparación por Distrito (si hay datos)
    if totales["ahorros_detalle"]:
        st.subheader("🏢 Distribución por Distrito")
        
        # Agrupar por distrito
        distritos_data = {}
        for item in totales["ahorros_detalle"]:
            distrito = item["distrito"]
            if distrito not in distritos_data:
                distritos_data[distrito] = {
                    "total_ahorros": 0,
                    "total_grupos": 0,
                    "total_miembros": 0
                }
            distritos_data[distrito]["total_ahorros"] += item["total_general"]
            distritos_data[distrito]["total_grupos"] += 1
            distritos_data[distrito]["total_miembros"] += item["total_miembros"]
        
        if distritos_data:
            distritos = list(distritos_data.keys())
            ahorros_por_distrito = [distritos_data[d]["total_ahorros"] for d in distritos]
            grupos_por_distrito = [distritos_data[d]["total_grupos"] for d in distritos]
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_distritos_ahorros = px.bar(
                    x=distritos,
                    y=ahorros_por_distrito,
                    title="💰 Ahorros por Distrito",
                    labels={'x': 'Distrito', 'y': 'Total Ahorros ($)'},
                    color=distritos
                )
                st.plotly_chart(fig_distritos_ahorros, use_container_width=True)
            
            with col2:
                fig_distritos_grupos = px.pie(
                    names=distritos,
                    values=grupos_por_distrito,
                    title="👥 Grupos por Distrito"
                )
                st.plotly_chart(fig_distritos_grupos, use_container_width=True)

# =============================================
#  FILTRO DE FECHAS
# =============================================

def mostrar_filtro_fechas():
    """Muestra el filtro de fechas para seleccionar el rango del ciclo."""
    st.subheader("📅 Seleccionar Rango de Fechas")
    
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
    
    dias = (fecha_fin - fecha_inicio).days
    st.info(f"**📊 Rango seleccionado:** {fecha_inicio} a {fecha_fin} ({dias} días)")
    
    return fecha_inicio, fecha_fin

# =============================================
#  PESTAÑA PRINCIPAL - CONSOLIDADO GENERAL
# =============================================

def mostrar_consolidado_general():
    """Muestra el consolidado general de TODOS los grupos."""
    st.header("👑 Panel de Administradora - Consolidado General")
    
    # Filtro de fechas
    fecha_inicio, fecha_fin = mostrar_filtro_fechas()
    if fecha_inicio is None or fecha_fin is None:
        return
    
    st.markdown("---")
    
    if st.button("🚀 Generar Consolidado General", type="primary", use_container_width=True):
        # Calcular totales generales
        totales = calcular_totales_generales(fecha_inicio, fecha_fin)
        
        # Mostrar métricas principales
        st.subheader("🎯 Métricas Principales del Sistema")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Grupos", f"{totales['total_grupos']}")
        with col2:
            st.metric("Total Miembros", f"{totales['total_miembros']}")
        with col3:
            st.metric("Total Ahorros", f"${totales['total_ahorros']:,.2f}")
        with col4:
            st.metric("Total Préstamos", f"${totales['total_prestamos_capital']:,.2f}")
        
        # Mostrar gráficos
        crear_graficos_consolidado_general(totales, fecha_inicio, fecha_fin)
        
        # Mostrar tabla resumen
        st.subheader("📋 Resumen Numérico General")
        
        resumen_data = {
            'Concepto': [
                'Total Grupos Activos',
                'Total Miembros Activos', 
                'Total Ahorros',
                'Total Préstamos (Capital)',
                'Total Intereses',
                'Total Multas',
                'Total Pagos de Préstamos',
                '**TOTAL INGRESOS**',
                '**FLUJO NETO**'
            ],
            'Valor': [
                f"{totales['total_grupos']}",
                f"{totales['total_miembros']}",
                f"${totales['total_ahorros']:,.2f}",
                f"${totales['total_prestamos_capital']:,.2f}",
                f"${totales['total_prestamos_intereses']:,.2f}",
                f"${totales['total_multas']:,.2f}",
                f"${totales['total_pagos_prestamos']:,.2f}",
                f"**${totales['total_ingresos']:,.2f}**",
                f"**${totales['total_ingresos'] - totales['total_pagos_prestamos']:,.2f}**"
            ]
        }
        
        df_resumen = pd.DataFrame(resumen_data)
        st.dataframe(df_resumen, use_container_width=True, hide_index=True)
        
        # Mostrar detalles por grupo
        st.subheader("📊 Detalles por Grupo")
        
        tab1, tab2, tab3, tab4 = st.tabs(["Ahorros", "Préstamos", "Multas", "Pagos Préstamos"])
        
        with tab1:
            if totales["ahorros_detalle"]:
                df_ahorros = pd.DataFrame(totales["ahorros_detalle"])
                st.dataframe(df_ahorros, use_container_width=True)
            else:
                st.info("No hay datos de ahorros para mostrar.")
        
        with tab2:
            if totales["prestamos_detalle"]:
                df_prestamos = pd.DataFrame(totales["prestamos_detalle"])
                st.dataframe(df_prestamos, use_container_width=True)
            else:
                st.info("No hay datos de préstamos para mostrar.")
        
        with tab3:
            if totales["multas_detalle"]:
                df_multas = pd.DataFrame(totales["multas_detalle"])
                st.dataframe(df_multas, use_container_width=True)
            else:
                st.info("No hay datos de multas para mostrar.")
        
        with tab4:
            if totales["pagos_detalle"]:
                df_pagos = pd.DataFrame(totales["pagos_detalle"])
                st.dataframe(df_pagos, use_container_width=True)
            else:
                st.info("No hay datos de pagos de préstamos para mostrar.")

# =============================================
#  FUNCIÓN PRINCIPAL
# =============================================

def main():
    """Función principal del panel de administradora."""
    # Configurar página
    st.set_page_config(
        page_title="Panel de Administradora",
        page_icon="👑",
        layout="wide"
    )
    
    # Sidebar
    st.sidebar.title("👑 Panel de Administradora")
    st.sidebar.markdown("---")
    
    # Navegación
    opcion = st.sidebar.radio(
        "Navegación",
        ["Consolidado General", "Registrar Usuario", "Cerrar sesión"]
    )
    
    if opcion == "Consolidado General":
        mostrar_consolidado_general()
    elif opcion == "Registrar Usuario":
        st.info("🔧 Módulo de registro de usuarios - En desarrollo")
    elif opcion == "Cerrar sesión":
        st.info("👋 Sesión cerrada")

if __name__ == "__main__":
    main()
