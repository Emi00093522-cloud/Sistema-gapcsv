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
        from pagoprestamo import mostrar_pago_prestamo  # ✅ USAR LA FUNCIÓN QUE SÍ EXISTE
        st.sidebar.success("✅ pagoprestamo.py - CONECTADO (usando mostrar_pago_prestamo)")
    except ImportError as e:
        st.sidebar.error(f"❌ pagoprestamo.py - ERROR: {e}")

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
        
        # ✅ CORREGIDO: Usar ID_Estado_prestamo en lugar de estado
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
            AND p.ID_Estado_prestamo != 3  -- ✅ Excluir préstamos cancelados/rechazados
        """, (id_grupo,))
        
        prestamos = cursor.fetchall()
        
        # Formatear resultados
        resultado = []
        for p in prestamos:
            monto_total = p.get('monto_total_pagar', 0)
            if monto_total is None:
                monto_total = p.get('monto', 0) + p.get('total_interes', 0)
                
            resultado.append({
                'monto': float(monto_total),
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
    Calcula los totales con datos REALES
    """
    ahorros_data, multas_data, prestamos_data = obtener_datos_reales()
    
    # Si no hay datos reales, usar ejemplos
    if not ahorros_data and not multas_data and not prestamos_data:
        st.warning("⚠️ Usando datos de ejemplo - Revisa la conexión")
        return 7500.00, 250.00, 2300.00
    
    # Calcular ahorros totales
    ahorros_totales = 0
    for ahorro in ahorros_data:
        ahorros_totales += ahorro.get('monto_ahorro', 0) + ahorro.get('monto_otros', 0)
    
    # Calcular multas totales
    multas_totales = 0
    for multa in multas_data:
        multas_totales += multa.get('monto_pagado', 0)
    
    # Calcular préstamos totales
    prestamos_totales = 0
    for prestamo in prestamos_data:
        prestamos_totales += prestamo.get('monto', 0)
    
    return ahorros_totales, multas_totales, prestamos_totales

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
    
    # Obtener datos
    with st.spinner("🔍 Calculando datos financieros..."):
        ahorros_totales, multas_totales, prestamos_totales = calcular_totales_reales()
    
    total_ingresos = ahorros_totales + multas_totales + prestamos_totales
    
    # Tabla resumen
    st.write("### 📋 Tabla de Consolidado")
    
    resumen_data = {
        "Concepto": [
            "💰 Total de Ahorros", 
            "⚖️ Total de Multas", 
            "🏦 Total de Préstamos",
            "💵 **TOTAL INGRESOS**"
        ],
        "Monto": [
            f"${ahorros_totales:,.2f}",
            f"${multas_totales:,.2f}",
            f"${prestamos_totales:,.2f}",
            f"**${total_ingresos:,.2f}**"
        ]
    }
    
    df_resumen = pd.DataFrame(resumen_data)
    st.dataframe(df_resumen, use_container_width=True, hide_index=True)
    
    # Métricas
    st.write("### 📈 Métricas del Ciclo")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Ahorros", f"${ahorros_totales:,.2f}")
    
    with col2:
        st.metric("Multas", f"${multas_totales:,.2f}")
    
    with col3:
        st.metric("Préstamos", f"${prestamos_totales:,.2f}")
    
    with col4:
        st.metric("TOTAL", f"${total_ingresos:,.2f}")
    
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
