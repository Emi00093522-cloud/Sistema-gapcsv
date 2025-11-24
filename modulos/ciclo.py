import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Agregar la ruta de tus módulos
sys.path.append(os.path.dirname(__file__))

def verificar_modulos():
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
        st.sidebar.success("✅ pagoprestamo.py - CONECTADO (usando mostrar_pago_prestamo)")
    except ImportError as e:
        st.sidebar.error(f"❌ pagoprestamo.py - ERROR: {e}")

def obtener_ahorros_por_miembro_ciclo():
    """
    Obtiene los ahorros totales por miembro de TODAS las reuniones del ciclo
    """
    try:
        from modulos.config.conexion import obtener_conexion
        
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        if 'reunion_actual' not in st.session_state:
            st.error("No hay reunión activa seleccionada")
            return []
        
        id_grupo = st.session_state.reunion_actual['id_grupo']
        
        # Consulta para obtener ahorros agrupados por miembro de TODAS las reuniones
        cursor.execute("""
            SELECT 
                m.ID_Miembro,
                m.nombre as nombre_miembro,
                COALESCE(SUM(a.monto_ahorro), 0) as total_ahorros,
                COALESCE(SUM(a.monto_otros), 0) as total_otros,
                COALESCE(SUM(a.monto_ahorro + a.monto_otros), 0) as total_general
            FROM Miembro m
            LEFT JOIN Ahorro a ON m.ID_Miembro = a.ID_Miembro
            LEFT JOIN Reunion r ON a.ID_Reunion = r.ID_Reunion
            WHERE m.ID_Grupo = %s AND m.ID_Estado = 1
            GROUP BY m.ID_Miembro, m.nombre
            ORDER BY m.nombre
        """, (id_grupo,))
        
        ahorros_miembros = cursor.fetchall()
        
        # Formatear resultados
        resultado = []
        for row in ahorros_miembros:
            resultado.append({
                'miembro': row['nombre_miembro'],
                'total_ahorros': float(row['total_ahorros']),
                'total_otros': float(row['total_otros']),
                'total_general': float(row['total_general'])
            })
        
        cursor.close()
        con.close()
        
        return resultado
        
    except Exception as e:
        st.error(f"❌ Error obteniendo ahorros por miembro: {e}")
        return []

def obtener_total_miembros_activos():
    """
    Obtiene el total de miembros activos en el grupo
    CORREGIDO: Usa ID_Estado = 1 para miembros activos
    """
    try:
        from modulos.config.conexion import obtener_conexion
        
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        if 'reunion_actual' not in st.session_state:
            st.error("No hay reunión activa seleccionada")
            return 0
        
        id_grupo = st.session_state.reunion_actual['id_grupo']
        
        # ✅ CORREGIDO: Usar ID_Estado = 1 para miembros activos
        cursor.execute("""
            SELECT COUNT(*) as total_miembros
            FROM Miembro 
            WHERE ID_Grupo = %s AND ID_Estado = 1
        """, (id_grupo,))
        
        resultado = cursor.fetchone()
        total_miembros = resultado['total_miembros'] if resultado else 0
        
        cursor.close()
        con.close()
        
        return total_miembros
        
    except Exception as e:
        st.error(f"❌ Error obteniendo miembros activos: {e}")
        return 0

def obtener_datos_prestamos_desde_bd():
    """
    Obtiene datos de préstamos directamente desde la base de datos
    ya que pagoprestamo.py no tiene obtener_prestamos_grupo
    """
    try:
        from modulos.config.conexion import obtener_conexion
        
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        if 'reunion_actual' not in st.session_state:
            st.error("No hay reunión activa seleccionada")
            return []
        
        id_grupo = st.session_state.reunion_actual['id_grupo']
        
        # Consulta para obtener préstamos del grupo
        cursor.execute("""
            SELECT 
                p.ID_Prestamo,
                p.monto,
                p.total_interes,
                p.monto_total_pagar,
                p.ID_Estado_prestamo,
                m.nombre as nombre_miembro
            FROM Prestamo p
            JOIN Miembro m ON p.ID_Miembro = m.ID_Miembro
            WHERE m.ID_Grupo = %s 
            AND p.ID_Estado_prestamo != 3  -- Excluir préstamos cancelados/rechazados
        """, (id_grupo,))
        
        prestamos = cursor.fetchall()
        
        # Formatear resultados - AHORA SEPARAMOS CAPITAL E INTERESES
        resultado = []
        for p in prestamos:
            monto_capital = p.get('monto', 0)
            monto_intereses = p.get('total_interes', 0)
            monto_total = p.get('monto_total_pagar', 0)
            
            # Si monto_total no existe, calcularlo
            if monto_total is None:
                monto_total = monto_capital + monto_intereses
                
            resultado.append({
                'monto_capital': float(monto_capital),
                'monto_intereses': float(monto_intereses),
                'monto_total': float(monto_total),
                'estado': p['ID_Estado_prestamo'],
                'nombre_miembro': p['nombre_miembro']
            })
        
        cursor.close()
        con.close()
        
        return resultado
        
    except Exception as e:
        st.error(f"❌ Error obteniendo préstamos desde BD: {e}")
        return []

def obtener_datos_reales():
    """
    Obtiene datos REALES de tus módulos
    """
    ahorros_data, multas_data, prestamos_data = [], [], []
    
    # Obtener ahorros
    try:
        from ahorros import obtener_ahorros_grupo
        ahorros_data = obtener_ahorros_grupo() or []
        st.success(f"✅ Ahorros: {len(ahorros_data)} registros")
    except Exception as e:
        st.error(f"❌ Error en ahorros: {e}")
    
    # Obtener multas
    try:
        from pagomulta import obtener_multas_grupo
        multas_data = obtener_multas_grupo() or []
        st.success(f"✅ Multas: {len(multas_data)} registros")
    except Exception as e:
        st.error(f"❌ Error en multas: {e}")
    
    # Obtener préstamos
    try:
        prestamos_data = obtener_datos_prestamos_desde_bd()
        st.success(f"✅ Préstamos: {len(prestamos_data)} registros")
    except Exception as e:
        st.error(f"❌ Error en préstamos: {e}")
    
    return ahorros_data, multas_data, prestamos_data

def calcular_totales_reales():
    """
    Calcula los totales con datos REALES - AHORA SEPARA CAPITAL E INTERESES
    """
    ahorros_data, multas_data, prestamos_data = obtener_datos_reales()
    
    # Si no hay datos reales, usar ejemplos
    if not ahorros_data and not multas_data and not prestamos_data:
        st.warning("⚠️ Usando datos de ejemplo - Revisa la conexión")
        return 7500.00, 250.00, 5000.00, 500.00  # capital, intereses
    
    # Calcular ahorros totales
    ahorros_totales = 0
    for ahorro in ahorros_data:
        ahorros_totales += ahorro.get('monto_ahorro', 0) + ahorro.get('monto_otros', 0)
    
    # Calcular multas totales
    multas_totales = 0
    for multa in multas_data:
        multas_totales += multa.get('monto_pagado', 0)
    
    # Calcular préstamos - AHORA SEPARADOS
    prestamos_capital = 0
    prestamos_intereses = 0
    
    for prestamo in prestamos_data:
        prestamos_capital += prestamo.get('monto_capital', 0)
        prestamos_intereses += prestamo.get('monto_intereses', 0)
    
    return ahorros_totales, multas_totales, prestamos_capital, prestamos_intereses

def mostrar_informacion_ciclo():
    st.header("🔒 Cierre de Ciclo - Resumen Financiero")
    
    st.subheader("📊 Gestión de Cierre de Ciclo")
    
    # Información básica
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("**📅 Fecha de Inicio del Grupo:** 2024-01-01")
    
    with col2:
        st.info("**⏰ Duración Actual:** 120 días")
    
    st.markdown("---")
    
    # Inicializar el estado
    if 'mostrar_resumen' not in st.session_state:
        st.session_state.mostrar_resumen = False
    
    # Botón principal
    if st.button("🚀 ¿Desea cerrar el ciclo? Sí", type="primary", use_container_width=True):
        st.session_state.mostrar_resumen = True
    
    # Mostrar resumen si el usuario presionó "Sí"
    if st.session_state.mostrar_resumen:
        mostrar_resumen_cierre()

def mostrar_resumen_cierre():
    st.subheader("💰 Resumen Financiero del Ciclo")
    
    st.success("✅ Has seleccionado cerrar el ciclo. Calculando datos...")
    
    # Obtener datos - AHORA CON 4 VALORES
    with st.spinner("🔍 Calculando datos financieros..."):
        ahorros_totales, multas_totales, prestamos_capital, prestamos_intereses = calcular_totales_reales()
    
    # Calcular total de préstamos (capital + intereses)
    prestamos_total = prestamos_capital + prestamos_intereses
    
    # Calcular total general
    total_ingresos = ahorros_totales + multas_totales + prestamos_total
    
    # Tabla resumen - AHORA CON 5 FILAS
    st.write("### 📋 Tabla de Consolidado")
    
    resumen_data = {
        "Concepto": [
            "💰 Total de Ahorros", 
            "⚖️ Total de Multas", 
            "🏦 Total Préstamos (Capital)",
            "📈 Total Intereses",
            "💵 **TOTAL INGRESOS**"
        ],
        "Monto": [
            f"${ahorros_totales:,.2f}",
            f"${multas_totales:,.2f}",
            f"${prestamos_capital:,.2f}",
            f"${prestamos_intereses:,.2f}",
            f"**${total_ingresos:,.2f}**"
        ]
    }
    
    df_resumen = pd.DataFrame(resumen_data)
    st.dataframe(df_resumen, use_container_width=True, hide_index=True)
    
    # Métricas - AHORA CON 5 COLUMNAS
    st.write("### 📈 Métricas del Ciclo")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Ahorros", f"${ahorros_totales:,.2f}")
    
    with col2:
        st.metric("Multas", f"${multas_totales:,.2f}")
    
    with col3:
        st.metric("Préstamos", f"${prestamos_capital:,.2f}")
    
    with col4:
        st.metric("Intereses", f"${prestamos_intereses:,.2f}")
    
    with col5:
        st.metric("TOTAL", f"${total_ingresos:,.2f}")
    
    # NUEVA SECCIÓN: AHORROS POR MIEMBRO (CICLO COMPLETO)
    st.write("### 📊 Ahorros por Miembro (Ciclo Completo)")
    
    # Obtener ahorros agrupados por miembro
    ahorros_por_miembro = obtener_ahorros_por_miembro_ciclo()
    
    if ahorros_por_miembro:
        # Crear DataFrame para la tabla
        df_ahorros_miembros = pd.DataFrame(ahorros_por_miembro)
        
        # Renombrar columnas para mejor presentación
        df_ahorros_miembros = df_ahorros_miembros.rename(columns={
            'miembro': 'Miembro',
            'total_ahorros': 'Total Ahorros',
            'total_otros': 'Total Otros',
            'total_general': 'TOTAL'
        })
        
        # Formatear columnas numéricas
        df_ahorros_miembros['Total Ahorros'] = df_ahorros_miembros['Total Ahorros'].apply(lambda x: f"${x:,.2f}")
        df_ahorros_miembros['Total Otros'] = df_ahorros_miembros['Total Otros'].apply(lambda x: f"${x:,.2f}")
        df_ahorros_miembros['TOTAL'] = df_ahorros_miembros['TOTAL'].apply(lambda x: f"${x:,.2f}")
        
        # Mostrar tabla
        st.dataframe(
            df_ahorros_miembros,
            use_container_width=True,
            hide_index=True
        )
        
        # Mostrar total general de ahorros por miembros
        total_general_miembros = sum(item['total_general'] for item in ahorros_por_miembro)
        st.info(f"**💵 Total general de ahorros de todos los miembros: ${total_general_miembros:,.2f}**")
        
    else:
        st.info("ℹ️ No se encontraron datos de ahorros por miembro")
    
    # SECCIÓN: DISTRIBUCIÓN DE BENEFICIOS
    st.write("### 📊 Distribución de Beneficios")
    
    # Obtener total de miembros activos
    total_miembros_activos = obtener_total_miembros_activos()
    
    if total_miembros_activos > 0 and prestamos_intereses > 0:
        # Calcular distribución
        distribucion_por_miembro = prestamos_intereses / total_miembros_activos
        
        # Mostrar cálculo
        col1, col2 = st.columns(2)
        
        with col1:
            st.info(f"**👥 Total de Miembros Activos:** {total_miembros_activos}")
        
        with col2:
            st.info(f"**💰 Total de Intereses a Distribuir:** ${prestamos_intereses:,.2f}")
        
        # Resultado de la distribución
        st.success(f"**🎯 A cada miembro activo le corresponde: ${distribucion_por_miembro:,.2f}**")
        
        # Mostrar cálculo detallado
        with st.expander("🔍 Ver Cálculo Detallado"):
            st.write(f"""
            **Fórmula de distribución:**
            - Total Intereses: ${prestamos_intereses:,.2f}
            - Total Miembros Activos: {total_miembros_activos}
            - Distribución: ${prestamos_intereses:,.2f} ÷ {total_miembros_activos} = **${distribucion_por_miembro:,.2f} por miembro**
            """)
    
    elif total_miembros_activos == 0:
        st.warning("⚠️ No se encontraron miembros activos en el grupo")
    
    elif prestamos_intereses == 0:
        st.info("ℹ️ No hay intereses para distribuir en este ciclo")
    
    # Mostrar detalles de préstamos
    with st.expander("📊 Ver Detalles de Préstamos"):
        try:
            prestamos_detalle = obtener_datos_prestamos_desde_bd()
            if prestamos_detalle:
                df_prestamos = pd.DataFrame(prestamos_detalle)
                st.dataframe(df_prestamos[['nombre_miembro', 'monto_capital', 'monto_intereses', 'monto_total']], 
                           use_container_width=True)
            else:
                st.info("No hay datos detallados de préstamos")
        except:
            st.info("No se pudieron cargar los detalles de préstamos")
    
    # Botón de confirmación
    st.markdown("---")
    st.write("### ✅ Confirmar Cierre Definitivo")
    
    if st.button("🔐 CONFIRMAR CIERRE DEL CICLO", type="primary", use_container_width=True):
        st.success("🎉 ¡Ciclo cerrado exitosamente!")
        st.balloons()
        st.session_state.mostrar_resumen = False

# 🔥 FUNCIÓN QUE APP.PY ESTÁ BUSCANDO
def mostrar_ciclo():
    """Función que llama app.py"""
    verificar_modulos()
    mostrar_informacion_ciclo()

if __name__ == "__main__":
    mostrar_ciclo()
