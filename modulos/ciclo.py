import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
from io import BytesIO
import csv

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

def guardar_ciclo_en_bd(datos_ciclo):
    """
    Guarda el ciclo cerrado en la base de datos
    """
    try:
        from modulos.config.conexion import obtener_conexion
        
        con = obtener_conexion()
        cursor = con.cursor()
        
        # Obtener el número del próximo ciclo
        cursor.execute("""
            SELECT COALESCE(MAX(numero_ciclo), 0) + 1 as siguiente_ciclo 
            FROM CiclosCerrados 
            WHERE id_grupo = %s
        """, (datos_ciclo['id_grupo'],))
        
        resultado = cursor.fetchone()
        numero_ciclo = resultado[0] if resultado else 1
        
        # Insertar ciclo en la base de datos
        cursor.execute("""
            INSERT INTO CiclosCerrados 
            (id_grupo, numero_ciclo, fecha_cierre, total_ahorros, total_multas, total_prestamos, 
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
            SELECT * FROM CiclosCerrados 
            WHERE id_grupo = %s 
            ORDER BY numero_ciclo DESC
        """, (id_grupo,))
        
        ciclos = cursor.fetchall()
        cursor.close()
        con.close()
        
        return ciclos
    except Exception as e:
        # Si la tabla no existe, retornar lista vacía
        return []

def generar_csv_ciclos():
    """
    Genera archivo CSV con todos los ciclos históricos
    """
    ciclos = obtener_ciclos_historicos()
    
    if not ciclos:
        # Crear CSV vacío si no hay ciclos
        output = BytesIO()
        writer = csv.writer(output)
        writer.writerow([
            'Ciclo', 'Fecha Cierre', 'Total Ahorros', 'Total Multas', 
            'Total Préstamos', 'Total Intereses', 'Miembros Activos', 
            'Distribución por Miembro'
        ])
        return output.getvalue()
    else:
        # Crear CSV con los ciclos
        output = BytesIO()
        writer = csv.writer(output)
        
        # Escribir encabezados
        writer.writerow([
            'Ciclo', 'Fecha Cierre', 'Total Ahorros', 'Total Multas', 
            'Total Préstamos', 'Total Intereses', 'Miembros Activos', 
            'Distribución por Miembro'
        ])
        
        # Escribir datos
        for ciclo in ciclos:
            writer.writerow([
                f"Ciclo {ciclo['numero_ciclo']}",
                ciclo['fecha_cierre'].strftime('%Y-%m-%d'),
                f"${ciclo['total_ahorros']:,.2f}",
                f"${ciclo['total_multas']:,.2f}",
                f"${ciclo['total_prestamos']:,.2f}",
                f"${ciclo['total_intereses']:,.2f}",
                ciclo['miembros_activos'],
                f"${ciclo['distribucion_por_miembro']:,.2f}"
            ])
        
        return output.getvalue()

# ======================================================
# TAB 1: VER Y GENERAR CIERRE DE CICLO
# ======================================================

def mostrar_tab_generar_cierre():
    """
    TAB 1: Formulario para generar nuevo cierre de ciclo
    """
    st.subheader("📋 Generar Cierre de Ciclo")
    
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
    """
    Muestra el resumen completo del cierre de ciclo
    """
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
    
    # Métricas - AHORA CON 4 COLUMNAS (como en tu diseño original)
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
    
    # NUEVA SECCIÓN: AHORROS POR MIEMBRO (CICLO COMPLETO) - EXACTAMENTE COMO PEDISTE
    st.write("### 📊 Ahorros por Miembro (Ciclo Completo)")
    
    # Obtener ahorros agrupados por miembro
    ahorros_por_miembro = obtener_ahorros_por_miembro_ciclo()
    
    if ahorros_por_miembro:
        # Crear tabla EXACTAMENTE como la pediste
        tabla_data = {
            "Miembro": [m['miembro'] for m in ahorros_por_miembro],
            "Total Ahorros": [f"${m['total_ahorros']:,.2f}" for m in ahorros_por_miembro],
            "Total Otros": [f"${m['total_otros']:,.2f}" for m in ahorros_por_miembro],
            "TOTAL": [f"${m['total_general']:,.2f}" for m in ahorros_por_miembro]
        }
        
        df_tabla = pd.DataFrame(tabla_data)
        st.dataframe(df_tabla, use_container_width=True, hide_index=True)
        
        # Mostrar total general de ahorros por miembros
        total_general_miembros = sum(item['total_general'] for item in ahorros_por_miembro)
        st.info(f"**💵 Total general de ahorros de todos los miembros: ${total_general_miembros:,.2f}**")
        
    else:
        st.info("ℹ️ No se encontraron datos de ahorros por miembro")
    
    # SECCIÓN: DISTRIBUCIÓN DE BENEFICIOS - MEJORADA CON TABLA BONITA
    st.write("### 📊 Distribución de Beneficios")
    
    # Obtener total de miembros activos
    total_miembros_activos = obtener_total_miembros_activos()
    
    if total_miembros_activos > 0 and prestamos_intereses > 0:
        # Calcular distribución
        distribucion_por_miembro = prestamos_intereses / total_miembros_activos
        
        # TABLA BONITA PARA DISTRIBUCIÓN - SIN CHECKBOXES FEYOS
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
        
        # Mensaje de resultado
        st.success(f"**🎯 A cada miembro activo le corresponde: ${distribucion_por_miembro:,.2f}**")
        
        # Mostrar cálculo detallado en un expander
        with st.expander("🔍 Ver Cálculo Detallado"):
            st.write(f"""
            **Fórmula de distribución:**
            - Total Intereses: ${prestamos_intereses:,.2f}
            - Total Miembros Activos: {total_miembros_activos}
            - Distribución: ${prestamos_intereses:,.2f} ÷ {total_miembros_activos} = **${distribucion_por_miembro:,.2f} por miembro**
            """)
        
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
            'ahorros_por_miembro': str(ahorros_por_miembro)  # Convertir a string para guardar
        }
        
        st.session_state.datos_ciclo_actual = datos_ciclo
    
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
        if 'datos_ciclo_actual' in st.session_state:
            # Guardar en base de datos
            numero_ciclo = guardar_ciclo_en_bd(st.session_state.datos_ciclo_actual)
            if numero_ciclo:
                st.success(f"🎉 ¡Ciclo {numero_ciclo} cerrado exitosamente!")
                st.balloons()
                st.session_state.mostrar_resumen = False
                # Limpiar datos temporales
                if 'datos_ciclo_actual' in st.session_state:
                    del st.session_state.datos_ciclo_actual
                # Recargar la página para mostrar el nuevo ciclo en el historial
                st.rerun()
            else:
                st.error("❌ Error al guardar el ciclo en la base de datos")
        else:
            st.error("❌ No hay datos de ciclo para guardar")

# ======================================================
# TAB 2: VER CICLOS FINALIZADOS
# ======================================================

def mostrar_tab_ciclos_finalizados():
    """
    TAB 2: Mostrar todos los ciclos cerrados del grupo (Ciclo 1, Ciclo 2, etc.)
    """
    st.subheader("📊 Ciclos Finalizados del Grupo")
    
    # Botón de descarga CSV SIEMPRE visible
    csv_data = generar_csv_ciclos()
    st.download_button(
        label="📥 Descargar CSV de Ciclos",
        data=csv_data,
        file_name=f"ciclos_grupo_{datetime.now().strftime('%Y-%m-%d')}.csv",
        mime="text/csv",
        use_container_width=True
    )
    
    st.markdown("---")
    
    # Obtener ciclos históricos
    ciclos = obtener_ciclos_historicos()
    
    if ciclos:
        # Crear tabla con los ciclos numerados
        datos_tabla = []
        for ciclo in ciclos:
            datos_tabla.append({
                "Ciclo": f"Ciclo {ciclo['numero_ciclo']}",
                "Fecha de Cierre": ciclo['fecha_cierre'].strftime('%Y-%m-%d'),
                "Total Ahorros": f"${ciclo['total_ahorros']:,.2f}",
                "Total Multas": f"${ciclo['total_multas']:,.2f}",
                "Total Préstamos": f"${ciclo['total_prestamos']:,.2f}",
                "Total Intereses": f"${ciclo['total_intereses']:,.2f}",
                "Miembros Activos": ciclo['miembros_activos'],
                "Distribución": f"${ciclo['distribucion_por_miembro']:,.2f}"
            })
        
        df_ciclos = pd.DataFrame(datos_tabla)
        st.dataframe(df_ciclos, use_container_width=True, hide_index=True)
        
        # Mostrar estadísticas
        st.write("### 📈 Estadísticas de Ciclos")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total de Ciclos", len(ciclos))
        
        with col2:
            total_intereses = sum(ciclo['total_intereses'] for ciclo in ciclos)
            st.metric("Intereses Totales", f"${total_intereses:,.2f}")
        
        with col3:
            promedio_distribucion = sum(ciclo['distribucion_por_miembro'] for ciclo in ciclos) / len(ciclos)
            st.metric("Distribución Promedio", f"${promedio_distribucion:,.2f}")
        
        # Mostrar detalles de cada ciclo en expanders
        st.write("### 🔍 Detalles por Ciclo")
        for ciclo in ciclos:
            with st.expander(f"Ciclo {ciclo['numero_ciclo']} - {ciclo['fecha_cierre'].strftime('%d/%m/%Y')}"):
                col_det1, col_det2 = st.columns(2)
                
                with col_det1:
                    st.write(f"**Ahorros:** ${ciclo['total_ahorros']:,.2f}")
                    st.write(f"**Multas:** ${ciclo['total_multas']:,.2f}")
                    st.write(f"**Préstamos:** ${ciclo['total_prestamos']:,.2f}")
                
                with col_det2:
                    st.write(f"**Intereses:** ${ciclo['total_intereses']:,.2f}")
                    st.write(f"**Miembros Activos:** {ciclo['miembros_activos']}")
                    st.write(f"**Distribución:** ${ciclo['distribucion_por_miembro']:,.2f}")
    
    else:
        st.info("ℹ️ No se ha finalizado ningún ciclo todavía. Ve a la pestaña 'Generar Cierre' para crear el primer ciclo.")

# ======================================================
# FUNCIÓN PRINCIPAL CON TABS
# ======================================================

def mostrar_informacion_ciclo():
    """
    Función principal con estructura de tabs
    """
    st.header("🔒 Cierre de Ciclo - Resumen Financiero")
    
    # Crear tabs - SIEMPRE VISIBLES
    tab1, tab2 = st.tabs(["📋 Generar Cierre de Ciclo", "📊 Ciclos Finalizados"])
    
    with tab1:
        mostrar_tab_generar_cierre()
    
    with tab2:
        mostrar_tab_ciclos_finalizados()

# 🔥 FUNCIÓN QUE APP.PY ESTÁ BUSCANDO
def mostrar_ciclo():
    """Función que llama app.py"""
    verificar_modulos()
    mostrar_informacion_ciclo()

if __name__ == "__main__":
    mostrar_ciclo()
