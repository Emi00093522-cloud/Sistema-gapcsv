import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import sys
import os

# Agregar la ruta de tus módulos
sys.path.append(os.path.dirname(__file__))

# =============================================
#  UTILIDADES DE MÓDULOS
# =============================================

def verificar_modulos():
    """Solo muestra en el sidebar si los otros módulos están accesibles."""
    st.sidebar.write("### 🔧 Verificación de Módulos")
    
    try:
        from ahorros import obtener_ahorros_grupo
        st.sidebar.success("✅ ahorros.py - CONECTADO")
    except ImportError as e:
        st.sidebar.error(f"❌ ahorros.py - ERROR: {e}")
    
    try:
        from pagomulta import obtener_multas_grupo
        st.sidebar.success("✅ pagomulta.py - CONECTADO")  
    except ImportError as e:
        st.sidebar.error(f"❌ pagomulta.py - ERROR: {e}")
    
    try:
        from pagoprestamo import mostrar_pago_prestamo
        st.sidebar.success("✅ pagoprestamo.py - CONECTADO")
    except ImportError as e:
        st.sidebar.error(f"❌ pagoprestamo.py - ERROR: {e}")

# =============================================
#  IDENTIFICACIÓN DE PROMOTORA
# =============================================

def obtener_id_promotora():
    """Obtiene el ID de la promotora logueada desde session_state."""
    return st.session_state.get("id_promotora")

def obtener_grupos_promotora():
    """Obtiene los grupos que maneja la promotora actual."""
    try:
        from modulos.config.conexion import obtener_conexion
        
        id_promotora = obtener_id_promotora()
        if id_promotora is None:
            return []
        
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
#  FUNCIONES PARA OBTENER DATOS POR GRUPO
# =============================================

def obtener_ahorros_grupo_consolidado(id_grupo, fecha_inicio=None, fecha_fin=None):
    """Obtiene los ahorros totales de un grupo en un rango de fechas."""
    try:
        from modulos.config.conexion import obtener_conexion
        
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        query = """
            SELECT 
                COALESCE(SUM(a.monto_ahorro), 0)                 AS total_ahorros,
                COALESCE(SUM(a.monto_otros), 0)                  AS total_otros,
                COALESCE(SUM(a.monto_ahorro + a.monto_otros), 0) AS total_general
            FROM Miembro m
            LEFT JOIN Ahorro a ON m.ID_Miembro = a.ID_Miembro
            LEFT JOIN Reunion r ON a.ID_Reunion = r.ID_Reunion
            WHERE m.ID_Grupo = %s
              AND m.ID_Estado = 1
        """
        
        params = [id_grupo]
        
        if fecha_inicio and fecha_fin:
            query += " AND r.fecha BETWEEN %s AND %s"
            params.extend([fecha_inicio, fecha_fin])
        
        cursor.execute(query, tuple(params))
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

def obtener_prestamos_grupo_consolidado(id_grupo, fecha_inicio=None, fecha_fin=None):
    """Obtiene los préstamos totales de un grupo en un rango de fechas."""
    try:
        from modulos.config.conexion import obtener_conexion
        
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        query = """
            SELECT 
                COALESCE(SUM(p.monto), 0) AS total_capital,
                COALESCE(SUM(p.total_interes), 0) AS total_intereses,
                COALESCE(SUM(p.monto_total_pagar), 0) AS total_pagar
            FROM Prestamo p
            JOIN Miembro m ON p.ID_Miembro = m.ID_Miembro
            WHERE m.ID_Grupo = %s 
              AND p.ID_Estado_prestamo != 3
        """
        
        params = [id_grupo]
        
        if fecha_inicio and fecha_fin:
            query += " AND p.fecha_desembolso BETWEEN %s AND %s"
            params.extend([fecha_inicio, fecha_fin])
        
        cursor.execute(query, tuple(params))
        resultado = cursor.fetchone()
        
        cursor.close()
        con.close()
        
        total_pagar = resultado["total_pagar"]
        if total_pagar == 0:
            total_pagar = resultado["total_capital"] + resultado["total_intereses"]
            
        return {
            "total_capital": float(resultado["total_capital"]),
            "total_intereses": float(resultado["total_intereses"]),
            "total_pagar": float(total_pagar)
        }
        
    except Exception as e:
        st.error(f"❌ Error obteniendo préstamos del grupo {id_grupo}: {e}")
        return {"total_capital": 0, "total_intereses": 0, "total_pagar": 0}

def obtener_multas_grupo_consolidado(id_grupo, fecha_inicio=None, fecha_fin=None):
    """Obtiene las multas totales de un grupo en un rango de fechas."""
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
        """
        
        params = [id_grupo]
        
        if fecha_inicio and fecha_fin:
            query += " AND pm.fecha_pago BETWEEN %s AND %s"
            params.extend([fecha_inicio, fecha_fin])
        
        cursor.execute(query, tuple(params))
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
    """Obtiene el número de miembros activos de un grupo."""
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
#  CONSOLIDADO POR GRUPO
# =============================================

def obtener_consolidado_grupo(id_grupo, nombre_grupo, fecha_inicio=None, fecha_fin=None):
    """Obtiene el consolidado completo de un grupo."""
    
    # Obtener datos financieros
    ahorros = obtener_ahorros_grupo_consolidado(id_grupo, fecha_inicio, fecha_fin)
    prestamos = obtener_prestamos_grupo_consolidado(id_grupo, fecha_inicio, fecha_fin)
    multas = obtener_multas_grupo_consolidado(id_grupo, fecha_inicio, fecha_fin)
    miembros = obtener_miembros_activos_grupo(id_grupo)
    
    # Calcular totales
    total_ahorros = ahorros["total_general"]
    total_prestamos = prestamos["total_capital"]
    total_intereses = prestamos["total_intereses"]
    total_multas = multas["total_multas"]
    total_ingresos = total_ahorros + total_multas + total_prestamos + total_intereses
    
    return {
        "id_grupo": id_grupo,
        "nombre_grupo": nombre_grupo,
        "total_miembros": miembros,
        "total_ahorros": total_ahorros,
        "total_prestamos": total_prestamos,
        "total_intereses": total_intereses,
        "total_multas": total_multas,
        "total_ingresos": total_ingresos,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin
    }

# =============================================
#  VISUALIZACIONES
# =============================================

def crear_grafico_barras_consolidado(datos_consolidado):
    """Crea un gráfico de barras con los datos consolidados."""
    if not datos_consolidado:
        st.warning("No hay datos para mostrar en el gráfico.")
        return None
    
    # Preparar datos para el gráfico
    grupos = [d["nombre_grupo"] for d in datos_consolidado]
    
    df_grafico = pd.DataFrame({
        'Grupo': grupos,
        'Ahorros': [d["total_ahorros"] for d in datos_consolidado],
        'Préstamos': [d["total_prestamos"] for d in datos_consolidado],
        'Multas': [d["total_multas"] for d in datos_consolidado],
        'Intereses': [d["total_intereses"] for d in datos_consolidado]
    })
    
    # Crear gráfico de barras apiladas
    fig = px.bar(df_grafico, 
                 x='Grupo', 
                 y=['Ahorros', 'Préstamos', 'Multas', 'Intereses'],
                 title='Consolidado Financiero por Grupo',
                 labels={'value': 'Monto ($)', 'variable': 'Concepto'},
                 barmode='group',
                 color_discrete_sequence=px.colors.qualitative.Set3)
    
    fig.update_layout(
        xaxis_tickangle=-45,
        showlegend=True,
        height=500
    )
    
    return fig

def mostrar_tabla_consolidado(datos_consolidado):
    """Muestra una tabla con los datos consolidados."""
    if not datos_consolidado:
        st.warning("No hay datos para mostrar en la tabla.")
        return
    
    # Preparar datos para la tabla
    tabla_data = []
    for dato in datos_consolidado:
        tabla_data.append({
            "Grupo": dato["nombre_grupo"],
            "Miembros": f"{dato['total_miembros']}",
            "Ahorros": f"${dato['total_ahorros']:,.2f}",
            "Préstamos": f"${dato['total_prestamos']:,.2f}",
            "Intereses": f"${dato['total_intereses']:,.2f}",
            "Multas": f"${dato['total_multas']:,.2f}",
            "Total": f"${dato['total_ingresos']:,.2f}"
        })
    
    df_tabla = pd.DataFrame(tabla_data)
    st.dataframe(df_tabla, use_container_width=True, hide_index=True)
    
    # Mostrar totales generales
    if datos_consolidado:
        total_general = {
            "ahorros": sum(d["total_ahorros"] for d in datos_consolidado),
            "prestamos": sum(d["total_prestamos"] for d in datos_consolidado),
            "intereses": sum(d["total_intereses"] for d in datos_consolidado),
            "multas": sum(d["total_multas"] for d in datos_consolidado),
            "ingresos": sum(d["total_ingresos"] for d in datos_consolidado)
        }
        
        st.success(f"**📊 Totales Generales:** "
                  f"Ahorros: ${total_general['ahorros']:,.2f} | "
                  f"Préstamos: ${total_general['prestamos']:,.2f} | "
                  f"Intereses: ${total_general['intereses']:,.2f} | "
                  f"Multas: ${total_general['multas']:,.2f} | "
                  f"**TOTAL: ${total_general['ingresos']:,.2f}**")

# =============================================
#  FILTROS Y CONFIGURACIÓN
# =============================================

def inicializar_session_state():
    """Inicializa el estado de la sesión."""
    if "filtro_fechas_promotora" not in st.session_state:
        st.session_state.filtro_fechas_promotora = {
            "fecha_inicio": datetime.now().date() - timedelta(days=30),
            "fecha_fin": datetime.now().date(),
        }
    if "grupo_seleccionado" not in st.session_state:
        st.session_state.grupo_seleccionado = "Todos los grupos"

def mostrar_filtros_consolidado():
    """Muestra los filtros para el consolidado de promotora."""
    st.subheader("📅 Filtros del Consolidado")
    
    # Filtro de fechas
    col1, col2 = st.columns(2)
    
    with col1:
        fecha_inicio = st.date_input(
            "Fecha de Inicio",
            value=st.session_state.filtro_fechas_promotora["fecha_inicio"],
            max_value=datetime.now().date(),
        )
    
    with col2:
        fecha_fin = st.date_input(
            "Fecha de Fin",
            value=st.session_state.filtro_fechas_promotora["fecha_fin"],
            max_value=datetime.now().date(),
        )
    
    if fecha_inicio > fecha_fin:
        st.error("❌ La fecha de inicio no puede ser mayor que la fecha de fin")
        return None, None
    
    st.session_state.filtro_fechas_promotora = {
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
    }
    
    # Menu desplegable de grupos
    grupos = obtener_grupos_promotora()
    opciones_grupos = ["Todos los grupos"] + [f"{g['ID_Grupo']} - {g['nombre_grupo']}" for g in grupos]
    
    grupo_seleccionado = st.selectbox(
        "👥 Seleccionar Grupo",
        options=opciones_grupos,
        index=0,
        key="select_grupo"
    )
    
    st.session_state.grupo_seleccionado = grupo_seleccionado
    
    dias_rango = (fecha_fin - fecha_inicio).days
    st.info(f"**📊 Rango seleccionado:** {fecha_inicio} a {fecha_fin} ({dias_rango} días) | "
           f"**Grupo:** {grupo_seleccionado}")
    
    return fecha_inicio, fecha_fin, grupo_seleccionado

# =============================================
#  FUNCIÓN PRINCIPAL
# =============================================

def mostrar_consolidado_promotora():
    """Función principal que muestra el consolidado de la promotora."""
    
    # Verificar que la promotora esté logueada
    id_promotora = obtener_id_promotora()
    if id_promotora is None:
        st.error("⚠️ No tienes permisos de promotora. Debes iniciar sesión como promotora.")
        return
    
    st.title("📊 Consolidado de Promotora")
    
    verificar_modulos()
    inicializar_session_state()
    
    # Mostrar filtros
    fecha_inicio, fecha_fin, grupo_seleccionado = mostrar_filtros_consolidado()
    if fecha_inicio is None:
        return
    
    # Obtener grupos de la promotora
    grupos = obtener_grupos_promotora()
    if not grupos:
        st.warning("ℹ️ No tienes grupos asignados como promotora.")
        return
    
    # Filtrar grupos si se seleccionó uno específico
    grupos_a_procesar = grupos
    if grupo_seleccionado != "Todos los grupos":
        grupo_id = int(grupo_seleccionado.split(" - ")[0])
        grupos_a_procesar = [g for g in grupos if g["ID_Grupo"] == grupo_id]
    
    # Botón para generar reporte
    if st.button("🚀 Generar Reporte Consolidado", type="primary", use_container_width=True):
        with st.spinner("🔍 Calculando consolidado..."):
            datos_consolidado = []
            
            for grupo in grupos_a_procesar:
                consolidado = obtener_consolidado_grupo(
                    grupo["ID_Grupo"],
                    grupo["nombre_grupo"],
                    fecha_inicio,
                    fecha_fin
                )
                datos_consolidado.append(consolidado)
            
            # Mostrar resultados
            st.markdown("---")
            st.subheader("📋 Tabla de Consolidado")
            mostrar_tabla_consolidado(datos_consolidado)
            
            st.markdown("---")
            st.subheader("📊 Gráfico de Consolidado")
            fig = crear_grafico_barras_consolidado(datos_consolidado)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            
            # Métricas resumen
            st.markdown("---")
            st.subheader("📈 Métricas Resumen")
            
            if datos_consolidado:
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    total_ahorros = sum(d["total_ahorros"] for d in datos_consolidado)
                    st.metric("Total Ahorros", f"${total_ahorros:,.2f}")
                with col2:
                    total_prestamos = sum(d["total_prestamos"] for d in datos_consolidado)
                    st.metric("Total Préstamos", f"${total_prestamos:,.2f}")
                with col3:
                    total_multas = sum(d["total_multas"] for d in datos_consolidado)
                    st.metric("Total Multas", f"${total_multas:,.2f}")
                with col4:
                    total_intereses = sum(d["total_intereses"] for d in datos_consolidado)
                    st.metric("Total Intereses", f"${total_intereses:,.2f}")

if __name__ == "__main__":
    mostrar_consolidado_promotora()
