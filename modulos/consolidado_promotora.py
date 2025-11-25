import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
import traceback

# Configuración de la página
st.set_page_config(
    page_title="Consolidado Promotora",
    page_icon="📊",
    layout="wide"
)

def debug_info():
    """Muestra información de debug en el sidebar"""
    with st.sidebar:
        st.header("🔧 Información de Debug")
        st.write(f"**Usuario:** {st.session_state.get('usuario', 'No logueado')}")
        st.write(f"**Cargo:** {st.session_state.get('cargo_de_usuario', 'No definido')}")
        st.write(f"**Acceso total:** {st.session_state.get('acceso_total_promotora', False)}")
        
        if st.button("🔄 Forzar Recarga"):
            st.rerun()

def obtener_conexion_segura():
    """Obtiene conexión a la base de datos con manejo de errores"""
    try:
        from modulos.config.conexion import obtener_conexion
        return obtener_conexion()
    except Exception as e:
        st.error(f"❌ Error de conexión a la base de datos: {e}")
        st.code(traceback.format_exc())
        return None

def obtener_id_promotora_actual():
    """Obtiene el ID de promotora de la tabla Promotora basado en el usuario logueado"""
    try:
        usuario_actual = st.session_state.get("usuario", "")
        if not usuario_actual:
            return None
        
        con = obtener_conexion_segura()
        if not con:
            return None
            
        cursor = con.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT ID_Promotora 
            FROM Promotora 
            WHERE nombre = %s AND ID_Estado = 1
        """, (usuario_actual,))
        
        resultado = cursor.fetchone()
        cursor.close()
        con.close()
        
        return resultado["ID_Promotora"] if resultado else None
            
    except Exception as e:
        st.error(f"❌ Error buscando ID de promotora: {e}")
        return None

def mostrar_consolidado_promotora():
    """Función principal para mostrar el consolidado de promotora"""
    
    # Mostrar información de debug
    debug_info()
    
    st.title("📊 Consolidado de Promotora")
    
    # Verificar si el usuario está logueado
    if 'usuario' not in st.session_state:
        st.error("🚫 No hay sesión activa. Por favor, inicia sesión primero.")
        return
    
    # =============================================
    # 1. VERIFICAR PERMISOS
    # =============================================
    es_promotora_acceso_total = st.session_state.get("acceso_total_promotora", False)
    
    st.write(f"**Usuario actual:** {st.session_state.get('usuario')}")
    st.write(f"**Cargo:** {st.session_state.get('cargo_de_usuario')}")
    
    if es_promotora_acceso_total:
        st.info("🔓 **MODO PROMOTORA CON ACCESO TOTAL**: Puedes ver todos los grupos del sistema")
    
    # =============================================
    # 2. OBTENER ID PROMOTORA
    # =============================================
    st.write("### 🔍 Verificando permisos de promotora...")
    
    id_promotora = obtener_id_promotora_actual()
    
    if id_promotora is None and not es_promotora_acceso_total:
        st.error("""
        🚫 **No estás registrada como promotora activa**
        
        **Posibles soluciones:**
        1. Ir a **Registro Promotora** para registrarte
        2. Contactar al administrador
        3. Verificar que tu usuario esté activo
        """)
        return
    
    # =============================================
    # 3. OBTENER GRUPOS
    # =============================================
    def obtener_grupos_promotora():
        try:
            con = obtener_conexion_segura()
            if not con:
                return []
                
            cursor = con.cursor(dictionary=True)
            
            if es_promotora_acceso_total:
                # Todos los grupos del sistema
                cursor.execute("""
                    SELECT g.ID_Grupo, g.nombre as nombre_grupo, p.nombre as nombre_promotora
                    FROM Grupo g
                    LEFT JOIN Promotora p ON g.ID_Promotora = p.ID_Promotora
                    WHERE g.ID_Estado = 1
                    ORDER BY g.nombre
                """)
            else:
                # Solo grupos de esta promotora
                cursor.execute("""
                    SELECT ID_Grupo, nombre as nombre_grupo
                    FROM Grupo 
                    WHERE ID_Promotora = %s AND ID_Estado = 1
                    ORDER BY nombre
                """, (id_promotora,))
            
            grupos = cursor.fetchall()
            cursor.close()
            con.close()
            
            return grupos
            
        except Exception as e:
            st.error(f"❌ Error obteniendo grupos: {e}")
            return []
    
    grupos = obtener_grupos_promotora()
    
    if not grupos:
        st.warning("📭 **No se encontraron grupos activos**")
        return
    
    st.success(f"✅ **Grupos encontrados:** {len(grupos)} grupo(s)")
    
    # =============================================
    # 4. FILTROS DE FECHAS
    # =============================================
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
        return
    
    dias_rango = (fecha_fin - fecha_inicio).days
    st.info(f"**Rango seleccionado:** {fecha_inicio} a {fecha_fin} ({dias_rango} días)")
    
    # =============================================
    # 5. FUNCIONES PARA OBTENER DATOS
    # =============================================
    
    def obtener_ahorros_grupo(id_grupo, fecha_inicio, fecha_fin):
        """Obtiene el total de ahorros de un grupo en el rango de fechas"""
        try:
            con = obtener_conexion_segura()
            if not con:
                return 0.0
                
            cursor = con.cursor(dictionary=True)
            
            query = """
                SELECT COALESCE(SUM(a.monto_ahorro + a.monto_otros), 0) as total
                FROM Miembro m
                LEFT JOIN Ahorro a ON m.ID_Miembro = a.ID_Miembro
                LEFT JOIN Reunion r ON a.ID_Reunion = r.ID_Reunion
                WHERE m.ID_Grupo = %s AND r.fecha BETWEEN %s AND %s
            """
            cursor.execute(query, (id_grupo, fecha_inicio, fecha_fin))
            resultado = cursor.fetchone()
            cursor.close()
            con.close()
            
            return float(resultado["total"])
            
        except Exception as e:
            st.error(f"❌ Error obteniendo ahorros: {e}")
            return 0.0
    
    def obtener_prestamos_grupo(id_grupo, fecha_inicio, fecha_fin):
        """Obtiene préstamos e intereses de un grupo"""
        try:
            con = obtener_conexion_segura()
            if not con:
                return 0.0, 0.0
                
            cursor = con.cursor(dictionary=True)
            
            query = """
                SELECT 
                    COALESCE(SUM(p.monto), 0) as capital,
                    COALESCE(SUM(p.total_interes), 0) as intereses
                FROM Prestamo p
                JOIN Miembro m ON p.ID_Miembro = m.ID_Miembro
                WHERE m.ID_Grupo = %s AND p.fecha_desembolso BETWEEN %s AND %s
            """
            cursor.execute(query, (id_grupo, fecha_inicio, fecha_fin))
            resultado = cursor.fetchone()
            cursor.close()
            con.close()
            
            capital = float(resultado["capital"])
            intereses = float(resultado["intereses"])
            return capital, intereses
            
        except Exception as e:
            st.error(f"❌ Error obteniendo préstamos: {e}")
            return 0.0, 0.0
    
    def obtener_multas_grupo(id_grupo, fecha_inicio, fecha_fin):
        """Obtiene multas pagadas de un grupo"""
        try:
            con = obtener_conexion_segura()
            if not con:
                return 0.0
                
            cursor = con.cursor(dictionary=True)
            
            query = """
                SELECT COALESCE(SUM(pm.monto_pagado), 0) as multas
                FROM PagoMulta pm
                JOIN Miembro m ON pm.ID_Miembro = m.ID_Miembro
                WHERE m.ID_Grupo = %s AND pm.fecha_pago BETWEEN %s AND %s
            """
            cursor.execute(query, (id_grupo, fecha_inicio, fecha_fin))
            resultado = cursor.fetchone()
            cursor.close()
            con.close()
            
            return float(resultado["multas"])
            
        except Exception as e:
            st.error(f"❌ Error obteniendo multas: {e}")
            return 0.0
    
    def obtener_miembros_grupo(id_grupo):
        """Obtiene el número de miembros activos en un grupo"""
        try:
            con = obtener_conexion_segura()
            if not con:
                return 0
                
            cursor = con.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT COUNT(*) as total 
                FROM Miembro 
                WHERE ID_Grupo = %s AND ID_Estado = 1
            """, (id_grupo,))
            
            resultado = cursor.fetchone()
            cursor.close()
            con.close()
            
            return resultado["total"]
            
        except Exception as e:
            st.error(f"❌ Error contando miembros: {e}")
            return 0
    
    # =============================================
    # 6. GENERAR REPORTE
    # =============================================
    
    if st.button("🚀 GENERAR REPORTE CONSOLIDADO", type="primary", use_container_width=True):
        
        with st.spinner("Calculando consolidado..."):
            datos_consolidado = []
            
            for grupo in grupos:
                grupo_id = grupo["ID_Grupo"]
                grupo_nombre = grupo["nombre_grupo"]
                
                # Obtener datos del grupo
                ahorros = obtener_ahorros_grupo(grupo_id, fecha_inicio, fecha_fin)
                prestamos, intereses = obtener_prestamos_grupo(grupo_id, fecha_inicio, fecha_fin)
                multas = obtener_multas_grupo(grupo_id, fecha_inicio, fecha_fin)
                miembros = obtener_miembros_grupo(grupo_id)
                
                total_general = ahorros + prestamos + intereses + multas
                
                # Agregar datos al consolidado
                dato_grupo = {
                    "nombre_grupo": grupo_nombre,
                    "total_miembros": miembros,
                    "total_ahorros": ahorros,
                    "total_prestamos": prestamos,
                    "total_intereses": intereses,
                    "total_multas": multas,
                    "total_general": total_general
                }
                
                # Agregar información de promotora si es acceso total
                if es_promotora_acceso_total:
                    dato_grupo["promotora"] = grupo.get("nombre_promotora", "N/A")
                
                datos_consolidado.append(dato_grupo)
            
            # MOSTRAR RESULTADOS
            mostrar_resultados_sin_plotly(datos_consolidado, es_promotora_acceso_total)

def mostrar_resultados_sin_plotly(datos_consolidado, es_promotora_acceso_total):
    """Muestra los resultados del consolidado SIN usar Plotly"""
    
    # 1. TABLA DE CONSOLIDADO
    st.subheader("📋 Tabla de Consolidado")
    
    # Preparar datos para la tabla
    tabla_data = []
    for dato in datos_consolidado:
        fila = {
            "Grupo": dato["nombre_grupo"],
            "Miembros": dato["total_miembros"],
            "Ahorros": f"${dato['total_ahorros']:,.2f}",
            "Préstamos": f"${dato['total_prestamos']:,.2f}",
            "Intereses": f"${dato['total_intereses']:,.2f}",
            "Multas": f"${dato['total_multas']:,.2f}",
            "TOTAL": f"${dato['total_general']:,.2f}"
        }
        
        if es_promotora_acceso_total:
            fila["Promotora"] = dato.get("promotora", "N/A")
        
        tabla_data.append(fila)
    
    # Crear DataFrame y mostrar tabla
    df = pd.DataFrame(tabla_data)
    st.dataframe(df, use_container_width=True)
    
    # 2. MÉTRICAS
    st.subheader("📈 Métricas Totales")
    
    totales = {
        "ahorros": sum(d["total_ahorros"] for d in datos_consolidado),
        "prestamos": sum(d["total_prestamos"] for d in datos_consolidado),
        "intereses": sum(d["total_intereses"] for d in datos_consolidado),
        "multas": sum(d["total_multas"] for d in datos_consolidado),
        "general": sum(d["total_general"] for d in datos_consolidado),
        "miembros": sum(d["total_miembros"] for d in datos_consolidado),
        "grupos": len(datos_consolidado)
    }
    
    # Mostrar métricas según el tipo de acceso
    if es_promotora_acceso_total:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Grupos", totales["grupos"])
            st.metric("Total Miembros", totales["miembros"])
            
        with col2:
            st.metric("Ahorros", f"${totales['ahorros']:,.2f}")
            st.metric("Multas", f"${totales['multas']:,.2f}")
            
        with col3:
            st.metric("Préstamos", f"${totales['prestamos']:,.2f}")
            st.metric("Intereses", f"${totales['intereses']:,.2f}")
            
        with col4:
            st.metric("TOTAL GENERAL", f"${totales['general']:,.2f}")
    else:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Grupos", totales["grupos"])
            st.metric("Total Miembros", totales["miembros"])
            
        with col2:
            st.metric("Ahorros", f"${totales['ahorros']:,.2f}")
            st.metric("Préstamos", f"${totales['prestamos']:,.2f}")
            
        with col3:
            st.metric("Intereses", f"${totales['intereses']:,.2f}")
            st.metric("TOTAL GENERAL", f"${totales['general']:,.2f}")
    
    # 3. GRÁFICOS CON STREAMLIT NATIVO
    st.subheader("📊 Gráficos de Consolidado")
    
    # Preparar datos para gráficos
    df_graficos = pd.DataFrame(datos_consolidado)
    
    # Gráfico 1: Barras para total general por grupo
    st.markdown("#### 📈 Total General por Grupo")
    
    # Ordenar datos para mejor visualización
    df_ordenado = df_graficos.sort_values('total_general', ascending=True)
    
    # Crear gráfico de barras con Streamlit
    st.bar_chart(
        df_ordenado.set_index('nombre_grupo')['total_general'],
        color="#1f77b4"
    )
    
    # Gráfico 2: Métricas por categoría
    st.markdown("#### 💰 Distribución por Categorías")
    
    categorias_totales = pd.DataFrame({
        'Categoría': ['Ahorros', 'Préstamos', 'Intereses', 'Multas'],
        'Total': [
            totales['ahorros'],
            totales['prestamos'], 
            totales['intereses'],
            totales['multas']
        ]
    })
    
    st.bar_chart(
        categorias_totales.set_index('Categoría')['Total'],
        color="#ff6b6b"
    )
    
    # Gráfico 3: Datos detallados por grupo
    st.markdown("#### 📊 Detalle por Grupo")
    
    # Seleccionar columnas para el gráfico
    columnas_grafico = ['total_ahorros', 'total_prestamos', 'total_intereses', 'total_multas']
    df_detalle = df_graficos[['nombre_grupo'] + columnas_grafico].set_index('nombre_grupo')
    
    st.bar_chart(df_detalle)
    
    # 4. RESUMEN ESTADÍSTICO
    st.subheader("📋 Resumen Estadístico")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 📊 Estadísticas de Grupos")
        st.write(f"**Grupo con mayor total:** {df_graficos.loc[df_graficos['total_general'].idxmax(), 'nombre_grupo']}")
        st.write(f"**Grupo con más miembros:** {df_graficos.loc[df_graficos['total_miembros'].idxmax(), 'nombre_grupo']}")
        st.write(f"**Promedio por grupo:** ${(totales['general']/len(datos_consolidado)):,.2f}")
    
    with col2:
        st.markdown("##### 💵 Distribución Porcentual")
        st.write(f"**Ahorros:** {(totales['ahorros']/totales['general']*100):.1f}%")
        st.write(f"**Préstamos:** {(totales['prestamos']/totales['general']*100):.1f}%")
        st.write(f"**Intereses:** {(totales['intereses']/totales['general']*100):.1f}%")
        st.write(f"**Multas:** {(totales['multas']/totales['general']*100):.1f}%")
    
    st.balloons()
    st.success("🎉 Consolidado generado exitosamente")

# Ejecutar la aplicación
if __name__ == "__main__":
    mostrar_consolidado_promotora()
