import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import sys
import os

# Agregar la ruta de tus módulos
sys.path.append(os.path.dirname(__file__))

# =============================================
#  DEBUG INICIAL - VER QUÉ ESTÁ PASANDO
# =============================================

def debug_inicial():
    """Función de debug para ver el estado de la aplicación"""
    st.sidebar.title("🔍 DEBUG CONSOLIDADO PROMOTORA")
    
    # 1. Verificar session_state
    st.sidebar.write("### 📋 Session State Keys:")
    session_keys = list(st.session_state.keys())
    for key in session_keys:
        value = st.session_state.get(key)
        st.sidebar.write(f"- **{key}:** {value}")
    
    # 2. Verificar específicamente id_promotora
    st.sidebar.write("### 👤 Estado Promotora:")
    if "id_promotora" in st.session_state:
        st.sidebar.success(f"✅ id_promotora encontrado: {st.session_state.id_promotora}")
    else:
        st.sidebar.error("❌ id_promotora NO encontrado en session_state")
    
    # 3. Verificar conexión a BD
    st.sidebar.write("### 🗄️ Estado Base de Datos:")
    try:
        from modulos.config.conexion import obtener_conexion
        con = obtener_conexion()
        cursor = con.cursor()
        cursor.execute("SELECT 1")
        st.sidebar.success("✅ Conexión BD: OK")
        cursor.close()
        con.close()
    except Exception as e:
        st.sidebar.error(f"❌ Conexión BD: ERROR - {e}")

# =============================================
#  VERIFICACIÓN DE SESIÓN ROBUSTA
# =============================================

def verificar_sesion_promotora():
    """Verifica que la promotora tenga sesión activa de manera robusta"""
    
    st.write("### 1. 🔐 Verificando Sesión...")
    
    # Opción 1: Verificar si existe la clave en session_state
    if "id_promotora" not in st.session_state:
        st.error("""
        🚫 **ERROR CRÍTICO:** No se encontró 'id_promotora' en session_state
        
        **Posibles soluciones:**
        1. Asegúrate de haber iniciado sesión como promotora
        2. Verifica que el login guarde correctamente en st.session_state
        3. Revisa el nombre de la variable (debe ser 'id_promotora')
        """)
        st.stop()
    
    # Opción 2: Verificar que no sea None
    id_promotora = st.session_state.id_promotora
    if id_promotora is None:
        st.error("""
        ⚠️ **id_promotora es None**
        
        El valor existe pero está vacío. Probablemente el login no se completó correctamente.
        """)
        st.stop()
    
    # Opción 3: Verificar que sea un número válido
    try:
        id_promotora_int = int(id_promotora)
        if id_promotora_int <= 0:
            st.error("❌ ID de promotora no válido (menor o igual a 0)")
            st.stop()
    except (ValueError, TypeError):
        st.error("❌ ID de promotora no es un número válido")
        st.stop()
    
    st.success(f"✅ Sesión verificada - ID Promotora: {id_promotora}")
    return id_promotora

# =============================================
#  OBTENER GRUPOS CON DEBUG
# =============================================

def obtener_grupos_promotora_con_debug(id_promotora):
    """Obtiene los grupos de la promotora con información de debug"""
    
    st.write("### 2. 📊 Buscando Grupos...")
    
    try:
        from modulos.config.conexion import obtener_conexion
        
        st.info(f"🔍 Buscando grupos para promotora ID: {id_promotora}")
        
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        # Query para obtener grupos
        query = """
            SELECT ID_Grupo, nombre_grupo 
            FROM Grupo 
            WHERE ID_Promotora = %s
            ORDER BY nombre_grupo
        """
        
        st.write(f"📝 Ejecutando query: `{query}` con parámetro: {id_promotora}")
        
        cursor.execute(query, (id_promotora,))
        grupos = cursor.fetchall()
        
        cursor.close()
        con.close()
        
        st.success(f"✅ Se encontraron {len(grupos)} grupo(s)")
        
        # Mostrar grupos encontrados
        if grupos:
            st.write("### 👥 Grupos Encontrados:")
            for i, grupo in enumerate(grupos, 1):
                st.write(f"{i}. **{grupo['nombre_grupo']}** (ID: {grupo['ID_Grupo']})")
        else:
            st.warning("""
            ⚠️ **No se encontraron grupos para esta promotora**
            
            **Posibles causas:**
            1. La promotora no tiene grupos asignados
            2. El ID de promotora no existe en la base de datos
            3. Los grupos están inactivos o eliminados
            """)
        
        return grupos
        
    except Exception as e:
        st.error(f"""
        ❌ **Error crítico al obtener grupos:**
        
        **Detalle del error:** {e}
        
        **Solución:**
        1. Verifica que la tabla 'Grupo' exista en la BD
        2. Verifica que la columna 'ID_Promotora' exista
        3. Revisa la conexión a la base de datos
        """)
        return []

# =============================================
#  FUNCIONES DE CÁLCULO (IGUAL QUE CICLO.PY)
# =============================================

def obtener_ahorros_grupo_rango(id_grupo, fecha_inicio, fecha_fin):
    """Obtiene ahorros de un grupo en rango de fechas"""
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
    """Obtiene préstamos de un grupo en rango de fechas"""
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
    """Obtiene multas de un grupo en rango de fechas"""
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
    """Obtiene miembros activos de un grupo"""
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
#  CÁLCULO DE CONSOLDADO
# =============================================

def calcular_consolidado_grupo(id_grupo, nombre_grupo, fecha_inicio, fecha_fin):
    """Calcula el consolidado completo para un grupo"""
    
    st.write(f"📈 Calculando consolidado para: {nombre_grupo}")
    
    # Obtener datos del grupo
    ahorros = obtener_ahorros_grupo_rango(id_grupo, fecha_inicio, fecha_fin)
    prestamos = obtener_prestamos_grupo_rango(id_grupo, fecha_inicio, fecha_fin)
    multas = obtener_multas_grupo_rango(id_grupo, fecha_inicio, fecha_fin)
    miembros = obtener_miembros_activos_grupo(id_grupo)
    
    # Calcular totales
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
#  VISUALIZACIONES
# =============================================

def crear_grafico_barras_consolidado(datos_consolidado):
    """Crea gráfico de barras con los datos consolidados"""
    if not datos_consolidado:
        st.warning("No hay datos para mostrar en el gráfico.")
        return None
    
    # Preparar datos para el gráfico
    grupos = [f"{d['nombre_grupo']}" for d in datos_consolidado]
    
    df_grafico = pd.DataFrame({
        'Grupo': grupos,
        'Ahorros': [d["total_ahorros"] for d in datos_consolidado],
        'Préstamos': [d["total_prestamos_capital"] for d in datos_consolidado],
        'Intereses': [d["total_intereses"] for d in datos_consolidado],
        'Multas': [d["total_multas"] for d in datos_consolidado]
    })
    
    # Crear gráfico de barras
    fig = px.bar(df_grafico, 
                 x='Grupo', 
                 y=['Ahorros', 'Préstamos', 'Intereses', 'Multas'],
                 title='📊 Consolidado Financiero por Grupo',
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
    """Muestra la tabla de consolidado"""
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
            "Préstamos": f"${dato['total_prestamos_capital']:,.2f}",
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
            "prestamos": sum(d["total_prestamos_capital"] for d in datos_consolidado),
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
#  INTERFAZ PRINCIPAL CON DEBUG
# =============================================

def mostrar_consolidado_promotora():
    """Función principal con debug integrado"""
    
    st.title("📊 Consolidado de Promotora")
    
    # =============================================
    # FASE 1: DEBUG INICIAL
    # =============================================
    debug_inicial()
    
    # =============================================
    # FASE 2: VERIFICAR SESIÓN
    # =============================================
    st.write("---")
    st.write("## 🔐 FASE 1: Verificación de Sesión")
    
    id_promotora = verificar_sesion_promotora()
    
    # =============================================
    # FASE 3: OBTENER GRUPOS
    # =============================================
    st.write("---")
    st.write("## 📊 FASE 2: Obtención de Grupos")
    
    grupos = obtener_grupos_promotora_con_debug(id_promotora)
    
    if not grupos:
        st.error("""
        🚫 **NO SE PUEDE CONTINUAR** 
        
        No se encontraron grupos para esta promotora. El consolidado no puede generarse.
        """)
        return
    
    # =============================================
    # FASE 4: FILTROS Y CÁLCULOS
    # =============================================
    st.write("---")
    st.write("## 📅 FASE 3: Configuración de Fechas")
    
    # Filtros de fecha
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
    
    dias_ciclo = (fecha_fin - fecha_inicio).days
    st.info(f"**📊 Rango seleccionado:** {fecha_inicio} a {fecha_fin} ({dias_ciclo} días)")
    
    # =============================================
    # FASE 5: GENERAR REPORTE
    # =============================================
    st.write("---")
    st.write("## 🚀 FASE 4: Generar Reporte Consolidado")
    
    if st.button("🎯 GENERAR REPORTE COMPLETO", type="primary", use_container_width=True):
        
        st.write("### 🔄 Procesando grupos...")
        progress_bar = st.progress(0)
        
        datos_consolidado = []
        total_grupos = len(grupos)
        
        for i, grupo in enumerate(grupos):
            st.write(f"**Procesando:** {grupo['nombre_grupo']} ({i+1}/{total_grupos})")
            
            consolidado = calcular_consolidado_grupo(
                grupo["ID_Grupo"],
                grupo["nombre_grupo"],
                fecha_inicio,
                fecha_fin
            )
            datos_consolidado.append(consolidado)
            
            # Actualizar progreso
            progress_bar.progress((i + 1) / total_grupos)
        
        # =============================================
        # FASE 6: MOSTRAR RESULTADOS
        # =============================================
        st.write("---")
        st.write("## 📈 FASE 5: Resultados del Consolidado")
        
        # 1. Tabla de Consolidado
        st.subheader("📋 Tabla de Consolidado")
        mostrar_tabla_consolidado(datos_consolidado)
        
        # 2. Gráfico de Barras
        st.subheader("📊 Gráfico de Barras")
        fig = crear_grafico_barras_consolidado(datos_consolidado)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        
        # 3. Métricas Resumen
        st.subheader("🎯 Métricas Resumen")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_ahorros = sum(d["total_ahorros"] for d in datos_consolidado)
            st.metric("Total Ahorros", f"${total_ahorros:,.2f}")
        with col2:
            total_prestamos = sum(d["total_prestamos_capital"] for d in datos_consolidado)
            st.metric("Total Préstamos", f"${total_prestamos:,.2f}")
        with col3:
            total_multas = sum(d["total_multas"] for d in datos_consolidado)
            st.metric("Total Multas", f"${total_multas:,.2f}")
        with col4:
            total_intereses = sum(d["total_intereses"] for d in datos_consolidado)
            st.metric("Total Intereses", f"${total_intereses:,.2f}")
        
        st.balloons()
        st.success("🎉 **CONSOLIDADO GENERADO EXITOSAMENTE**")

# =============================================
#  EJECUCIÓN DIRECTA (PARA PRUEBAS)
# =============================================

if __name__ == "__main__":
    # Si se ejecuta directamente, simular una sesión para pruebas
    if "id_promotora" not in st.session_state:
        st.warning("""
        🔧 **MODO PRUEBA - Sesión simulada**
        
        Para usar en producción, asegúrate de que el login guarde st.session_state.id_promotora
        """)
        # Simular una promotora para pruebas
        st.session_state.id_promotora = 1  # Cambia este valor según tu BD
    
    mostrar_consolidado_promotora()
