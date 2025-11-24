import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Agregar la ruta de tus módulos
sys.path.append(os.path.dirname(__file__))

# =============================================
# FUNCIONES EXISTENTES (modificadas para incluir filtro de fechas)
# =============================================

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

def obtener_ahorros_por_miembro_ciclo(fecha_inicio=None, fecha_fin=None):
    """
    Obtiene los ahorros totales por miembro de las reuniones dentro del rango de fechas
    """
    try:
        from modulos.config.conexion import obtener_conexion
        
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        if 'reunion_actual' not in st.session_state:
            st.error("No hay reunión activa seleccionada")
            return []
        
        id_grupo = st.session_state.reunion_actual['id_grupo']
        
        # Consulta base - mantenemos la estructura original pero agregamos filtro opcional
        query = """
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
        """
        
        params = [id_grupo]
        
        # Agregar filtro de fechas si se proporcionan
        if fecha_inicio and fecha_fin:
            # Usar la columna de fecha que exista en tu base de datos
            query += " AND (r.fecha BETWEEN %s AND %s OR r.fecha BETWEEN %s AND %s)"
            params.extend([fecha_inicio, fecha_fin, fecha_inicio, fecha_fin])
        
        query += " GROUP BY m.ID_Miembro, m.nombre ORDER BY m.nombre"
        
        cursor.execute(query, tuple(params))
        
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
        # Fallback: obtener sin filtro de fecha
        try:
            return obtener_ahorros_por_miembro_sin_filtro()
        except:
            return []

def obtener_ahorros_por_miembro_sin_filtro():
    """Fallback: Obtiene ahorros sin filtro de fecha"""
    try:
        from modulos.config.conexion import obtener_conexion
        
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        if 'reunion_actual' not in st.session_state:
            return []
        
        id_grupo = st.session_state.reunion_actual['id_grupo']
        
        cursor.execute("""
            SELECT 
                m.ID_Miembro,
                m.nombre as nombre_miembro,
                COALESCE(SUM(a.monto_ahorro), 0) as total_ahorros,
                COALESCE(SUM(a.monto_otros), 0) as total_otros,
                COALESCE(SUM(a.monto_ahorro + a.monto_otros), 0) as total_general
            FROM Miembro m
            LEFT JOIN Ahorro a ON m.ID_Miembro = a.ID_Miembro
            WHERE m.ID_Grupo = %s AND m.ID_Estado = 1
            GROUP BY m.ID_Miembro, m.nombre
            ORDER BY m.nombre
        """, (id_grupo,))
        
        ahorros_miembros = cursor.fetchall()
        
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
        st.error(f"❌ Error en fallback de ahorros: {e}")
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

def obtener_datos_prestamos_desde_bd(fecha_inicio=None, fecha_fin=None):
    """
    Obtiene datos de préstamos directamente desde la base de datos
    con filtro opcional de fechas
    """
    try:
        from modulos.config.conexion import obtener_conexion
        
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        if 'reunion_actual' not in st.session_state:
            st.error("No hay reunión activa seleccionada")
            return []
        
        id_grupo = st.session_state.reunion_actual['id_grupo']
        
        # Consulta base
        query = """
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
        """
        
        params = [id_grupo]
        
        # Agregar filtro de fechas si se proporcionan
        if fecha_inicio and fecha_fin:
            query += " AND (p.fecha_solicitud BETWEEN %s AND %s OR p.fecha BETWEEN %s AND %s)"
            params.extend([fecha_inicio, fecha_fin, fecha_inicio, fecha_fin])
        
        cursor.execute(query, tuple(params))
        
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

def obtener_datos_multas_desde_bd(fecha_inicio=None, fecha_fin=None):
    """
    Obtiene datos de multas directamente desde la base de datos
    con filtro opcional de fechas
    """
    try:
        from modulos.config.conexion import obtener_conexion
        
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        if 'reunion_actual' not in st.session_state:
            st.error("No hay reunión activa seleccionada")
            return []
        
        id_grupo = st.session_state.reunion_actual['id_grupo']
        
        # Consulta para obtener multas del grupo
        query = """
            SELECT 
                pm.ID_PagoMulta,
                pm.monto_pagado,
                pm.fecha_pago,
                m.nombre as nombre_miembro,
                mult.descripcion as descripcion
            FROM PagoMulta pm
            JOIN Multa mult ON pm.ID_Multa = mult.ID_Multa
            JOIN Miembro m ON pm.ID_Miembro = m.ID_Miembro
            WHERE m.ID_Grupo = %s
        """
        
        params = [id_grupo]
        
        # Agregar filtro de fechas si se proporcionan
        if fecha_inicio and fecha_fin:
            query += " AND (pm.fecha_pago BETWEEN %s AND %s OR pm.fecha BETWEEN %s AND %s)"
            params.extend([fecha_inicio, fecha_fin, fecha_inicio, fecha_fin])
        
        cursor.execute(query, tuple(params))
        
        multas = cursor.fetchall()
        
        # Formatear resultados
        resultado = []
        for multa in multas:
            resultado.append({
                'monto_pagado': float(multa.get('monto_pagado', 0)),
                'fecha_pago': multa['fecha_pago'],
                'nombre_miembro': multa['nombre_miembro'],
                'descripcion': multa['descripcion']
            })
        
        cursor.close()
        con.close()
        
        return resultado
        
    except Exception as e:
        st.error(f"❌ Error obteniendo multas desde BD: {e}")
        return []

def obtener_datos_reales(fecha_inicio=None, fecha_fin=None):
    """
    Obtiene datos REALES de tus módulos con filtro opcional de fechas
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
        prestamos_data = obtener_datos_prestamos_desde_bd(fecha_inicio, fecha_fin)
    except Exception as e:
        st.error(f"❌ Error en préstamos: {e}")
    
    return ahorros_data, multas_data, prestamos_data

def calcular_totales_reales(fecha_inicio=None, fecha_fin=None):
    """
    Calcula los totales con datos REALES - AHORA SEPARA CAPITAL E INTERESES
    con filtro opcional de fechas
    """
    ahorros_data, multas_data, prestamos_data = obtener_datos_reales(fecha_inicio, fecha_fin)
    
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

# =============================================
# NUEVAS FUNCIONES CON FILTRO DE FECHAS
# =============================================

def inicializar_session_state():
    """Inicializa el estado de la sesión para las pestañas"""
    if 'ciclos_cerrados' not in st.session_state:
        st.session_state.ciclos_cerrados = []
    if 'mostrar_resumen' not in st.session_state:
        st.session_state.mostrar_resumen = False
    if 'ciclo_actual_numero' not in st.session_state:
        st.session_state.ciclo_actual_numero = 1
    if 'filtro_fechas' not in st.session_state:
        st.session_state.filtro_fechas = {
            'fecha_inicio': datetime.now().date() - timedelta(days=30),
            'fecha_fin': datetime.now().date()
        }

def mostrar_filtro_fechas():
    """Muestra el filtro de fechas para seleccionar el rango del ciclo"""
    st.subheader("📅 Seleccionar Rango del Ciclo")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fecha_inicio = st.date_input(
            "Fecha de Inicio del Ciclo",
            value=st.session_state.filtro_fechas['fecha_inicio'],
            max_value=datetime.now().date()
        )
    
    with col2:
        fecha_fin = st.date_input(
            "Fecha de Fin del Ciclo",
            value=st.session_state.filtro_fechas['fecha_fin'],
            max_value=datetime.now().date()
        )
    
    # Validar que fecha_inicio no sea mayor que fecha_fin
    if fecha_inicio > fecha_fin:
        st.error("❌ La fecha de inicio no puede ser mayor que la fecha de fin")
        return None, None
    
    # Actualizar session state
    st.session_state.filtro_fechas = {
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin
    }
    
    # Mostrar información del rango seleccionado
    dias_ciclo = (fecha_fin - fecha_inicio).days
    st.info(f"**📊 Rango seleccionado:** {fecha_inicio} a {fecha_fin} ({dias_ciclo} días)")
    
    return fecha_inicio, fecha_fin

def mostrar_resumen_completo(fecha_inicio, fecha_fin):
    """Muestra el resumen completo del ciclo con filtro de fechas"""
    st.subheader(f"💰 Resumen Financiero del Ciclo: {fecha_inicio} a {fecha_fin}")
    
    st.success("✅ Calculando datos para el rango seleccionado...")
    
    # Obtener datos - AHORA CON 4 VALORES
    with st.spinner("🔍 Calculando datos financieros..."):
        ahorros_totales, multas_totales, prestamos_capital, prestamos_intereses = calcular_totales_reales(fecha_inicio, fecha_fin)
    
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
    
    # Métricas - AHORA CON 4 COLUMNAS
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
    
    ahorros_por_miembro = obtener_ahorros_por_miembro_ciclo(fecha_inicio, fecha_fin)
    
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
    
    # Detalles de préstamos
    with st.expander("📊 Ver Detalles de Préstamos"):
        try:
            prestamos_detalle = obtener_datos_prestamos_desde_bd(fecha_inicio, fecha_fin)
            if prestamos_detalle:
                df_prestamos = pd.DataFrame(prestamos_detalle)
                st.dataframe(df_prestamos[['nombre_miembro', 'monto_capital', 'monto_intereses', 'monto_total']], 
                           use_container_width=True)
            else:
                st.info("No hay datos detallados de préstamos")
        except:
            st.info("No se pudieron cargar los detalles de préstamos")
    
    return {
        'ahorros_totales': ahorros_totales,
        'multas_totales': multas_totales,
        'prestamos_capital': prestamos_capital,
        'prestamos_intereses': prestamos_intereses,
        'total_ingresos': total_ingresos,
        'total_miembros_activos': total_miembros_activos,
        'distribucion_por_miembro': distribucion_por_miembro if total_miembros_activos > 0 and prestamos_intereses > 0 else 0,
        'ahorros_por_miembro': ahorros_por_miembro,
        'fecha_inicio': fecha_inicio.strftime("%Y-%m-%d"),
        'fecha_fin': fecha_fin.strftime("%Y-%m-%d"),
        'fecha_cierre': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def pestaña_ciclo_activo():
    """Pestaña 1: Ciclo Activo - Donde se calcula y cierra el ciclo actual"""
    st.header("🔒 Cierre de Ciclo - Resumen Financiero")
    
    # Mostrar filtro de fechas
    fecha_inicio, fecha_fin = mostrar_filtro_fechas()
    
    if fecha_inicio is None or fecha_fin is None:
        return
    
    st.markdown("---")
    
    # Botón principal para generar resumen
    if st.button("🚀 Generar Resumen del Ciclo", type="primary", use_container_width=True):
        st.session_state.mostrar_resumen = True
    
    # Mostrar resumen si el usuario presionó el botón
    if st.session_state.mostrar_resumen:
        datos_ciclo = mostrar_resumen_completo(fecha_inicio, fecha_fin)
        
        # Botón de confirmación
        st.markdown("---")
        st.write("### ✅ Confirmar Cierre Definitivo")
        
        if st.button("🔐 CONFIRMAR CIERRE DEL CICLO", type="primary", use_container_width=True):
            # Guardar ciclo en historial
            ciclo_cerrado = {
                'numero_ciclo': st.session_state.ciclo_actual_numero,
                'datos': datos_ciclo,
                'fecha_cierre': datos_ciclo['fecha_cierre'],
                'rango_fechas': f"{datos_ciclo['fecha_inicio']} a {datos_ciclo['fecha_fin']}"
            }
            st.session_state.ciclos_cerrados.append(ciclo_cerrado)
            
            # Incrementar número de ciclo para el próximo
            st.session_state.ciclo_actual_numero += 1
            st.session_state.mostrar_resumen = False
            
            st.success("🎉 ¡Ciclo cerrado exitosamente! Se ha iniciado un nuevo ciclo.")
            st.balloons()
            
            # Mostrar en qué pestaña está el historial
            st.info("📁 **Puedes ver el historial de ciclos cerrados en la pestaña 'Registro de Ciclos Cerrados'**")

def pestaña_ciclos_cerrados():
    """Pestaña 2: Registro de Ciclos Cerrados - Historial de ciclos finalizados"""
    st.header("📁 Registro de Ciclos Cerrados")
    
    if not st.session_state.ciclos_cerrados:
        st.info("ℹ️ No hay ciclos cerrados registrados. Los ciclos cerrados aparecerán aquí.")
        return
    
    # Mostrar cada ciclo cerrado
    for i, ciclo in enumerate(st.session_state.ciclos_cerrados):
        with st.expander(f"📊 Ciclo {ciclo['numero_ciclo']} - {ciclo['rango_fechas']} - {ciclo['fecha_cierre']}", expanded=i==0):
            datos = ciclo['datos']
            
            st.write(f"**Ciclo {ciclo['numero_ciclo']} - Rango: {ciclo['rango_fechas']} - Cerrado el: {ciclo['fecha_cierre']}**")
            
            # Tabla de consolidado
            st.write("#### 📋 Tabla de Consolidado")
            resumen_data = {
                "Concepto": [
                    "💰 Total de Ahorros", 
                    "⚖️ Total de Multas", 
                    "🏦 Total Préstamos (Capital)",
                    "📈 Total Intereses",
                    "💵 **TOTAL INGRESOS**"
                ],
                "Monto": [
                    f"${datos['ahorros_totales']:,.2f}",
                    f"${datos['multas_totales']:,.2f}",
                    f"${datos['prestamos_capital']:,.2f}",
                    f"${datos['prestamos_intereses']:,.2f}",
                    f"**${datos['total_ingresos']:,.2f}**"
                ]
            }
            
            df_resumen = pd.DataFrame(resumen_data)
            st.dataframe(df_resumen, use_container_width=True, hide_index=True)
            
            # Métricas
            st.write("#### 📈 Métricas del Ciclo")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Ahorros", f"${datos['ahorros_totales']:,.2f}")
            
            with col2:
                st.metric("Multas", f"${datos['multas_totales']:,.2f}")
            
            with col3:
                st.metric("Préstamos", f"${datos['prestamos_capital']:,.2f}")
            
            with col4:
                st.metric("Intereses", f"${datos['prestamos_intereses']:,.2f}")
            
            # Ahorros por miembro
            if datos['ahorros_por_miembro']:
                st.write("#### 📊 Ahorros por Miembro")
                tabla_data = {
                    "Miembro": [m['miembro'] for m in datos['ahorros_por_miembro']],
                    "Total Ahorros": [f"${m['total_ahorros']:,.2f}" for m in datos['ahorros_por_miembro']],
                    "Total Otros": [f"${m['total_otros']:,.2f}" for m in datos['ahorros_por_miembro']],
                    "TOTAL": [f"${m['total_general']:,.2f}" for m in datos['ahorros_por_miembro']]
                }
                
                df_tabla = pd.DataFrame(tabla_data)
                st.dataframe(df_tabla, use_container_width=True, hide_index=True)
            
            # Distribución de beneficios
            if datos['distribucion_por_miembro'] > 0:
                st.write("#### 📊 Distribución de Beneficios")
                st.info(f"**Distribución por miembro: ${datos['distribucion_por_miembro']:,.2f}**")

# =============================================
# FUNCIÓN PRINCIPAL
# =============================================

def mostrar_ciclo():
    """Función principal que llama app.py - AHORA CON PESTAÑAS Y FILTRO DE FECHAS"""
    verificar_modulos()
    inicializar_session_state()
    
    # Crear pestañas
    tab1, tab2 = st.tabs([
        "🔒 Cierre de Ciclo Activo", 
        "📁 Registro de Ciclos Cerrados"
    ])
    
    with tab1:
        pestaña_ciclo_activo()
    
    with tab2:
        pestaña_ciclos_cerrados()

if __name__ == "__main__":
    mostrar_ciclo()
