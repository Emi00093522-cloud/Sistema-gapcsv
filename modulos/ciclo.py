import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
from io import BytesIO, StringIO
import csv
import json

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
    """
    try:
        from modulos.config.conexion import obtener_conexion
        
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        if 'reunion_actual' not in st.session_state:
            st.error("No hay reunión activa seleccionada")
            return 0
        
        id_grupo = st.session_state.reunion_actual['id_grupo']
        
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
        
        # Formatear resultados
        resultado = []
        for p in prestamos:
            monto_capital = p.get('monto', 0)
            monto_intereses = p.get('total_interes', 0)
            monto_total = p.get('monto_total_pagar', 0)
            
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
    except Exception as e:
        st.error(f"❌ Error en ahorros: {e}")
    
    # Obtener multas
    try:
        from pagomulta import obtener_multas_grupo
        multas_data = obtener_multas_grupo() or []
    except Exception as e:
        st.error(f"❌ Error en multas: {e}")
    
    # Obtener préstamos
    try:
        prestamos_data = obtener_datos_prestamos_desde_bd()
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
        return 7500.00, 250.00, 5000.00, 500.00  # capital, intereses
    
    # Calcular ahorros totales
    ahorros_totales = 0
    for ahorro in ahorros_data:
        ahorros_totales += ahorro.get('monto_ahorro', 0) + ahorro.get('monto_otros', 0)
    
    # Calcular multas totales
    multas_totales = 0
    for multa in multas_data:
        multas_totales += multa.get('monto_pagado', 0)
    
    # Calcular préstamos
    prestamos_capital = 0
    prestamos_intereses = 0
    
    for prestamo in prestamos_data:
        prestamos_capital += prestamo.get('monto_capital', 0)
        prestamos_intereses += prestamo.get('monto_intereses', 0)
    
    return ahorros_totales, multas_totales, prestamos_capital, prestamos_intereses

def guardar_ciclo_en_bd(datos_ciclo):
    """
    Guarda el ciclo cerrado en la base de datos - SIMPLIFICADO
    """
    try:
        from modulos.config.conexion import obtener_conexion
        
        con = obtener_conexion()
        cursor = con.cursor()
        
        # Obtener el número del próximo ciclo
        cursor.execute("""
            SELECT COALESCE(MAX(ID_Ciclo), 0) + 1 as siguiente_ciclo 
            FROM Cierre_de_ciclo 
            WHERE ID_Grupo = %s
        """, (datos_ciclo['id_grupo'],))
        
        resultado = cursor.fetchone()
        numero_ciclo = resultado[0] if resultado else 1
        
        # Insertar directamente en Cierre_de_ciclo - SIN tablas adicionales
        cursor.execute("""
            INSERT INTO Cierre_de_ciclo 
            (ID_Grupo, ID_Ciclo, fecha_cierre, total_ahorros, total_multas, total_prestamos, 
             total_intereses, miembros_activos, distribucion_por_miembro, ahorros_por_miembro)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            datos_ciclo['id_grupo'],
            numero_ciclo,
            datos_ciclo['fecha_cierre'],
            datos_ciclo['total_ahorros'],
            datos_ciclo['total_multas'],
            datos_ciclo['total_prestamos'],
            datos_ciclo['total_intereses'],
            datos_ciclo['miembros_activos'],
            datos_ciclo['distribucion_por_miembro'],
            datos_ciclo['ahorros_por_miembro']
        ))
        
        con.commit()
        cursor.close()
        con.close()
        
        return numero_ciclo
    except Exception as e:
        st.error(f"❌ Error guardando ciclo en BD: {e}")
        return None

def obtener_ciclos_historicos():
    """
    Obtiene todos los ciclos cerrados del grupo
    """
    try:
        from modulos.config.conexion import obtener_conexion
        
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        if 'reunion_actual' not in st.session_state:
            return []
        
        id_grupo = st.session_state.reunion_actual['id_grupo']
        
        cursor.execute("""
            SELECT * FROM Cierre_de_ciclo 
            WHERE ID_Grupo = %s 
            ORDER BY ID_Ciclo DESC
        """, (id_grupo,))
        
        ciclos = cursor.fetchall()
        cursor.close()
        con.close()
        
        return ciclos
    except Exception as e:
        st.error(f"❌ Error obteniendo ciclos históricos: {e}")
        return []

def generar_csv_ciclos():
    """
    Genera archivo CSV con todos los ciclos históricos
    """
    ciclos = obtener_ciclos_historicos()
    
    try:
        output = StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            'Ciclo', 'Fecha Cierre', 'Total Ahorros', 'Total Multas',
            'Total Prestamos', 'Total Intereses', 'Miembros Activos',
            'Distribucion por Miembro'
        ])
        
        if ciclos:
            for ciclo in ciclos:
                writer.writerow([
                    f"Ciclo {ciclo['ID_Ciclo']}",
                    ciclo['fecha_cierre'].strftime('%Y-%m-%d') if ciclo['fecha_cierre'] else 'N/A',
                    f"${ciclo['total_ahorros']:,.2f}" if ciclo['total_ahorros'] is not None else '$0.00',
                    f"${ciclo['total_multas']:,.2f}" if ciclo['total_multas'] is not None else '$0.00',
                    f"${ciclo['total_prestamos']:,.2f}" if ciclo['total_prestamos'] is not None else '$0.00',
                    f"${ciclo['total_intereses']:,.2f}" if ciclo['total_intereses'] is not None else '$0.00',
                    ciclo['miembros_activos'] if ciclo['miembros_activos'] is not None else 0,
                    f"${ciclo['distribucion_por_miembro']:,.2f}" if ciclo['distribucion_por_miembro'] is not None else '$0.00'
                ])
        else:
            writer.writerow(['No hay ciclos registrados', '', '', '', '', '', '', ''])
        
        csv_text = output.getvalue()
        return csv_text.encode('utf-8')
        
    except Exception as e:
        st.error(f"❌ Error generando CSV: {e}")
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Error', 'Al generar', 'CSV', 'Contacte', 'Al administrador', '', '', ''])
        return output.getvalue().encode('utf-8')

def mostrar_tab_generar_cierre():
    """
    TAB 1: Formulario para generar nuevo cierre de ciclo
    """
    st.subheader("📋 Generar Cierre de Ciclo")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("**📅 Fecha de Inicio del Grupo:** 2024-01-01")
    
    with col2:
        st.info("**⏰ Duración Actual:** 120 días")
    
    st.markdown("---")
    
    if 'mostrar_resumen' not in st.session_state:
        st.session_state.mostrar_resumen = False
    
    if st.button("🚀 ¿Desea cerrar el ciclo? Sí", type="primary", use_container_width=True):
        st.session_state.mostrar_resumen = True
    
    if st.session_state.mostrar_resumen:
        mostrar_resumen_cierre()

def mostrar_resumen_cierre():
    """
    Muestra el resumen completo del cierre de ciclo
    """
    st.subheader("💰 Resumen Financiero del Ciclo")
    
    st.success("✅ Has seleccionado cerrar el ciclo. Calculando datos...")
    
    with st.spinner("🔍 Calculando datos financieros..."):
        ahorros_totales, multas_totales, prestamos_capital, prestamos_intereses = calcular_totales_reales()
    
    prestamos_total = prestamos_capital + prestamos_intereses
    total_ingresos = ahorros_totales + multas_totales + prestamos_total
    
    # Tabla resumen
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
    
    # Métricas
    st.write("### 📈 Métricas del Ciclo")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Ahorros", f"${ahorros_totales:,.2f}")
    
    with col2:
        st.metric("Multas", f"${multas_totales:,.2f}")
    
    with col3:
        st.metric("Préstamos", f"${prestamos_capital:,.2f}")
    
    with col4:
        st.metric("Intereses", f"${prestamos_intereses:,.2f}")
    
    # AHORROS POR MIEMBRO
    st.write("### 📊 Ahorros por Miembro (Ciclo Completo)")
    
    ahorros_por_miembro = obtener_ahorros_por_miembro_ciclo()
    
    if ahorros_por_miembro:
        tabla_data = {
            "Miembro": [m['miembro'] for m in ahorros_por_miembro],
            "Total Ahorros": [f"${m['total_ahorros']:,.2f}" for m in ahorros_por_miembro],
            "Total Otros": [f"${m['total_otros']:,.2f}" for m in ahorros_por_miembro],
            "TOTAL": [f"${m['total_general']:,.2f}" for m in ahorros_por_miembro]
        }
        
        df_tabla = pd.DataFrame(tabla_data)
        st.dataframe(df_tabla, use_container_width=True, hide_index=True)
        
        total_general_miembros = sum(item['total_general'] for item in ahorros_por_miembro)
        st.info(f"**💵 Total general de ahorros de todos los miembros: ${total_general_miembros:,.2f}**")
        
    else:
        st.info("ℹ️ No se encontraron datos de ahorros por miembro")
    
    # DISTRIBUCIÓN DE BENEFICIOS
    st.write("### 📊 Distribución de Beneficios")
    
    total_miembros_activos = obtener_total_miembros_activos()
    
    if total_miembros_activos > 0 and prestamos_intereses > 0:
        distribucion_por_miembro = prestamos_intereses / total_miembros_activos
        
        distribucion_data = {
            "Concepto": [
                "Total de Miembros Activos",
                "Total de Intereses a Distribuir", 
                "Distribución por Miembro"
            ],
            "Valor": [
                f"{total_miembros_activos}",
                f"${prestamos_intereses:,.2f}",
                f"${distribucion_por_miembro:,.2f}"
            ]
        }
        
        df_distribucion = pd.DataFrame(distribucion_data)
        st.dataframe(df_distribucion, use_container_width=True, hide_index=True)
        
        st.success(f"**🎯 A cada miembro activo le corresponde: ${distribucion_por_miembro:,.2f}**")
        
        # Guardar datos para el cierre
        datos_ciclo = {
            'id_grupo': st.session_state.reunion_actual['id_grupo'],
            'fecha_cierre': datetime.now(),
            'total_ahorros': ahorros_totales,
            'total_multas': multas_totales,
            'total_prestamos': prestamos_capital,
            'total_intereses': prestamos_intereses,
            'miembros_activos': total_miembros_activos,
            'distribucion_por_miembro': distribucion_por_miembro,
            'ahorros_por_miembro': json.dumps(ahorros_por_miembro)
        }
        
        st.session_state.datos_ciclo_actual = datos_ciclo
    
    elif total_miembros_activos == 0:
        st.warning("⚠️ No se encontraron miembros activos en el grupo")
    
    elif prestamos_intereses == 0:
        st.info("ℹ️ No hay intereses para distribuir en este ciclo")
    
    # Botón de confirmación
    st.markdown("---")
    st.write("### ✅ Confirmar Cierre Definitivo")
    
    if st.button("🔐 CONFIRMAR CIERRE DEL CICLO", type="primary", use_container_width=True):
        if 'datos_ciclo_actual' in st.session_state:
            numero_ciclo = guardar_ciclo_en_bd(st.session_state.datos_ciclo_actual)
            if numero_ciclo:
                st.success(f"🎉 ¡Ciclo {numero_ciclo} cerrado exitosamente!")
                st.balloons()
                st.session_state.mostrar_resumen = False
                if 'datos_ciclo_actual' in st.session_state:
                    del st.session_state.datos_ciclo_actual
                st.rerun()
            else:
                st.error("❌ Error al guardar el ciclo en la base de datos")
        else:
            st.error("❌ No hay datos de ciclo para guardar")

def mostrar_tab_ciclos_finalizados():
    """
    TAB 2: Mostrar todos los ciclos cerrados del grupo
    """
    st.subheader("📊 Ciclos Finalizados del Grupo")
    
    try:
        csv_data = generar_csv_ciclos()
        st.download_button(
            label="📥 Descargar CSV de Ciclos",
            data=csv_data,
            file_name=f"ciclos_grupo_{datetime.now().strftime('%Y-%m-%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"❌ Error al generar archivo CSV: {e}")
    
    st.markdown("---")
    
    ciclos = obtener_ciclos_historicos()
    
    if ciclos:
        datos_tabla = []
        for ciclo in ciclos:
            datos_tabla.append({
                "Ciclo": f"Ciclo {ciclo['ID_Ciclo']}",
                "Fecha de Cierre": ciclo['fecha_cierre'].strftime('%Y-%m-%d') if ciclo['fecha_cierre'] else 'N/A',
                "Total Ahorros": f"${ciclo['total_ahorros']:,.2f}" if ciclo['total_ahorros'] is not None else '$0.00',
                "Total Multas": f"${ciclo['total_multas']:,.2f}" if ciclo['total_multas'] is not None else '$0.00',
                "Total Préstamos": f"${ciclo['total_prestamos']:,.2f}" if ciclo['total_prestamos'] is not None else '$0.00',
                "Total Intereses": f"${ciclo['total_intereses']:,.2f}" if ciclo['total_intereses'] is not None else '$0.00',
                "Miembros Activos": ciclo['miembros_activos'] if ciclo['miembros_activos'] is not None else 0,
                "Distribución": f"${ciclo['distribucion_por_miembro']:,.2f}" if ciclo['distribucion_por_miembro'] is not None else '$0.00'
            })
        
        df_ciclos = pd.DataFrame(datos_tabla)
        st.dataframe(df_ciclos, use_container_width=True, hide_index=True)
        
    else:
        st.info("ℹ️ No se ha finalizado ningún ciclo todavía. Ve a la pestaña 'Generar Cierre' para crear el primer ciclo.")

def mostrar_informacion_ciclo():
    """
    Función principal con estructura de tabs
    """
    st.header("🔒 Cierre de Ciclo - Resumen Financiero")
    
    if 'reunion_actual' not in st.session_state:
        st.error("❌ No hay reunión activa seleccionada. Por favor, selecciona una reunión primero.")
        return
    
    tab1, tab2 = st.tabs(["📋 Generar Cierre de Ciclo", "📊 Ciclos Finalizados"])
    
    with tab1:
        mostrar_tab_generar_cierre()
    
    with tab2:
        mostrar_tab_ciclos_finalizados()

def mostrar_ciclo():
    """Función que llama app.py"""
    verificar_modulos()
    mostrar_informacion_ciclo()

if __name__ == "__main__":
    mostrar_ciclo()
