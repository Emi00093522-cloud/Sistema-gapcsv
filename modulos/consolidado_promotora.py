import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# =============================================
# DEBUG SUPER DETALLADO
# =============================================

def debug_inicial():
    """DEBUG para saber qué está pasando"""
    st.sidebar.title("🐛 DEBUG CONSOLIDADO")
    st.sidebar.write("### Session State:")
    for key, value in st.session_state.items():
        st.sidebar.write(f"- **{key}:** {value}")
    
    # Verificar específicamente id_promotora
    if "id_promotora" in st.session_state:
        st.sidebar.success(f"✅ id_promotora: {st.session_state.id_promotora}")
    else:
        st.sidebar.error("❌ NO HAY id_promotora EN SESSION_STATE")

def mostrar_consolidado_promotora():
    """Función principal CON DEBUG EN CADA PASO"""
    
    st.title("📊 Consolidado de Promotora - DEBUG MODE")
    
    # =============================================
    # PASO 1: VERIFICAR SESIÓN
    # =============================================
    st.write("### 🔍 PASO 1: Verificando sesión...")
    
    if "id_promotora" not in st.session_state:
        st.error("""
        🚫 ERROR CRÍTICO: No hay id_promotora en session_state
        
        ¿QUÉ PASÓ?
        - El login no guardó el id_promotora
        - O no iniciaste sesión como promotora
        
        ¿QUÉ HACER?
        1. Ve al módulo de login
        2. Inicia sesión como PROMOTORA
        3. Verifica que el login guarde st.session_state.id_promotora
        """)
        return
    
    id_promotora = st.session_state.id_promotora
    st.success(f"✅ PASO 1 COMPLETADO - id_promotora: {id_promotora}")
    
    # =============================================
    # PASO 2: OBTENER GRUPOS CON DEBUG
    # =============================================
    st.write("### 🔍 PASO 2: Obteniendo grupos...")
    
    def obtener_grupos_con_debug():
        try:
            st.write("📝 Intentando importar conexión...")
            from modulos.config.conexion import obtener_conexion
            st.success("✅ Conexión importada")
            
            st.write("🔌 Conectando a BD...")
            con = obtener_conexion()
            st.success("✅ Conexión BD establecida")
            
            cursor = con.cursor(dictionary=True)
            
            query = """
                SELECT ID_Grupo, nombre_grupo 
                FROM Grupo 
                WHERE ID_Promotora = %s
                ORDER BY nombre_grupo
            """
            
            st.write(f"📊 Ejecutando query: {query}")
            st.write(f"📋 Con parámetros: [{id_promotora}]")
            
            cursor.execute(query, (id_promotora,))
            grupos = cursor.fetchall()
            
            st.write(f"📦 Grupos obtenidos: {len(grupos)}")
            
            cursor.close()
            con.close()
            st.success("✅ Conexión BD cerrada")
            
            return grupos
            
        except Exception as e:
            st.error(f"""
            ❌ ERROR EN PASO 2: {e}
            
            POSIBLES CAUSAS:
            1. No hay conexión a la base de datos
            2. La tabla 'Grupo' no existe
            3. La columna 'ID_Promotora' no existe
            4. Error de red o servidor
            """)
            return []
    
    grupos = obtener_grupos_con_debug()
    
    if not grupos:
        st.error("""
        🚫 NO SE PUEDE CONTINUAR
        
        No se encontraron grupos para esta promotora. Razones:
        1. La promotora no tiene grupos asignados
        2. El ID de promotora no existe en la BD
        3. Hay error en la consulta SQL
        """)
        return
    
    st.success(f"✅ PASO 2 COMPLETADO - {len(grupos)} grupos encontrados")
    
    # Mostrar grupos encontrados
    st.write("### 👥 Grupos Encontrados:")
    for i, grupo in enumerate(grupos, 1):
        st.write(f"{i}. **{grupo['nombre_grupo']}** (ID: {grupo['ID_Grupo']})")
    
    # =============================================
    # PASO 3: FILTROS DE FECHA
    # =============================================
    st.write("### 🔍 PASO 3: Configurando fechas...")
    
    st.subheader("📅 Seleccionar Rango de Fechas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fecha_inicio = st.date_input(
            "Fecha de Inicio",
            value=datetime.now().date() - timedelta(days=30),
            max_value=datetime.now().date(),
            key="fecha_inicio_debug"
        )
    
    with col2:
        fecha_fin = st.date_input(
            "Fecha de Fin",
            value=datetime.now().date(),
            max_value=datetime.now().date(),
            key="fecha_fin_debug"
        )
    
    st.write(f"📆 Fechas seleccionadas: {fecha_inicio} a {fecha_fin}")
    
    if fecha_inicio > fecha_fin:
        st.error("❌ La fecha de inicio no puede ser mayor que la fecha de fin")
        return
    
    dias_rango = (fecha_fin - fecha_inicio).days
    st.info(f"**Rango:** {fecha_inicio} a {fecha_fin} ({dias_rango} días)")
    
    st.success("✅ PASO 3 COMPLETADO")
    
    # =============================================
    # PASO 4: FUNCIONES DE DATOS CON DEBUG
    # =============================================
    
    def obtener_datos_grupo_con_debug(grupo_id, grupo_nombre):
        """Obtiene datos de un grupo con debug paso a paso"""
        st.write(f"---")
        st.write(f"**📊 Procesando grupo: {grupo_nombre} (ID: {grupo_id})**")
        
        try:
            from modulos.config.conexion import obtener_conexion
            
            # AHORROS
            st.write("💰 Calculando ahorros...")
            con = obtener_conexion()
            cursor = con.cursor(dictionary=True)
            
            query_ahorros = """
                SELECT COALESCE(SUM(a.monto_ahorro + a.monto_otros), 0) as total
                FROM Miembro m
                LEFT JOIN Ahorro a ON m.ID_Miembro = a.ID_Miembro
                LEFT JOIN Reunion r ON a.ID_Reunion = r.ID_Reunion
                WHERE m.ID_Grupo = %s AND r.fecha BETWEEN %s AND %s
            """
            cursor.execute(query_ahorros, (grupo_id, fecha_inicio, fecha_fin))
            ahorros = cursor.fetchone()["total"] or 0
            
            # PRÉSTAMOS
            st.write("🏦 Calculando préstamos...")
            query_prestamos = """
                SELECT 
                    COALESCE(SUM(p.monto), 0) as capital,
                    COALESCE(SUM(p.total_interes), 0) as intereses
                FROM Prestamo p
                JOIN Miembro m ON p.ID_Miembro = m.ID_Miembro
                WHERE m.ID_Grupo = %s AND p.fecha_desembolso BETWEEN %s AND %s
            """
            cursor.execute(query_prestamos, (grupo_id, fecha_inicio, fecha_fin))
            prestamos_data = cursor.fetchone()
            prestamos = prestamos_data["capital"] or 0
            intereses = prestamos_data["intereses"] or 0
            
            # MULTAS
            st.write("⚖️ Calculando multas...")
            query_multas = """
                SELECT COALESCE(SUM(pm.monto_pagado), 0) as multas
                FROM PagoMulta pm
                JOIN Miembro m ON pm.ID_Miembro = m.ID_Miembro
                WHERE m.ID_Grupo = %s AND pm.fecha_pago BETWEEN %s AND %s
            """
            cursor.execute(query_multas, (grupo_id, fecha_inicio, fecha_fin))
            multas = cursor.fetchone()["multas"] or 0
            
            # MIEMBROS
            st.write("👥 Contando miembros...")
            query_miembros = "SELECT COUNT(*) as total FROM Miembro WHERE ID_Grupo = %s AND ID_Estado = 1"
            cursor.execute(query_miembros, (grupo_id,))
            miembros = cursor.fetchone()["total"] or 0
            
            cursor.close()
            con.close()
            
            total_general = ahorros + prestamos + intereses + multas
            
            st.success(f"✅ {grupo_nombre}: A${ahorros:.2f} P${prestamos:.2f} M${multas:.2f}")
            
            return {
                "nombre_grupo": grupo_nombre,
                "total_miembros": miembros,
                "total_ahorros": float(ahorros),
                "total_prestamos": float(prestamos),
                "total_intereses": float(intereses),
                "total_multas": float(multas),
                "total_general": float(total_general)
            }
            
        except Exception as e:
            st.error(f"❌ Error en grupo {grupo_nombre}: {e}")
            return {
                "nombre_grupo": grupo_nombre,
                "total_miembros": 0,
                "total_ahorros": 0.0,
                "total_prestamos": 0.0,
                "total_intereses": 0.0,
                "total_multas": 0.0,
                "total_general": 0.0
            }
    
    # =============================================
    # PASO 5: BOTÓN PARA GENERAR
    # =============================================
    st.write("### 🔍 PASO 4: Generando reporte...")
    
    if st.button("🚀 GENERAR REPORTE CON DEBUG", type="primary", use_container_width=True):
        
        st.write("### 🔄 INICIANDO CÁLCULO...")
        
        datos_consolidado = []
        
        # Procesar cada grupo
        for i, grupo in enumerate(grupos, 1):
            st.write(f"**🔄 Procesando grupo {i}/{len(grupos)}**")
            
            datos = obtener_datos_grupo_con_debug(
                grupo["ID_Grupo"], 
                grupo["nombre_grupo"]
            )
            datos_consolidado.append(datos)
        
        st.success("✅ TODOS LOS GRUPOS PROCESADOS")
        
        # =============================================
        # PASO 6: MOSTRAR RESULTADOS
        # =============================================
        st.write("### 🔍 PASO 5: Mostrando resultados...")
        
        # TABLA
        st.subheader("📋 TABLA DE CONSOLIDADO")
        
        if not datos_consolidado:
            st.error("❌ No hay datos para mostrar")
            return
        
        tabla_data = []
        for dato in datos_consolidado:
            tabla_data.append({
                "Grupo": dato["nombre_grupo"],
                "Miembros": dato["total_miembros"],
                "Ahorros": f"${dato['total_ahorros']:,.2f}",
                "Préstamos": f"${dato['total_prestamos']:,.2f}", 
                "Intereses": f"${dato['total_intereses']:,.2f}",
                "Multas": f"${dato['total_multas']:,.2f}",
                "TOTAL": f"${dato['total_general']:,.2f}"
            })
        
        df = pd.DataFrame(tabla_data)
        st.dataframe(df, use_container_width=True)
        
        # MÉTRICAS
        st.subheader("📈 MÉTRICAS TOTALES")
        
        totales = {
            "ahorros": sum(d["total_ahorros"] for d in datos_consolidado),
            "prestamos": sum(d["total_prestamos"] for d in datos_consolidado),
            "intereses": sum(d["total_intereses"] for d in datos_consolidado),
            "multas": sum(d["total_multas"] for d in datos_consolidado),
            "general": sum(d["total_general"] for d in datos_consolidado),
            "miembros": sum(d["total_miembros"] for d in datos_consolidado)
        }
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Grupos", len(grupos))
            st.metric("Total Miembros", totales["miembros"])
            
        with col2:
            st.metric("Ahorros", f"${totales['ahorros']:,.2f}")
            st.metric("Multas", f"${totales['multas']:,.2f}")
            
        with col3:
            st.metric("Préstamos", f"${totales['prestamos']:,.2f}")
            st.metric("Intereses", f"${totales['intereses']:,.2f}")
            
        with col4:
            st.metric("TOTAL GENERAL", f"${totales['general']:,.2f}")
        
        st.balloons()
        st.success("🎉 **REPORTE GENERADO EXITOSAMENTE**")

# =============================================
# EJECUCIÓN PRINCIPAL
# =============================================
if __name__ == "__main__":
    # DEBUG INICIAL EN SIDEBAR
    debug_inicial()
    
    # Si no hay sesión, simular una para pruebas
    if "id_promotora" not in st.session_state:
        st.warning("🔧 MODO PRUEBA - Sesión simulada")
        st.session_state.id_promotora = 1
    
    mostrar_consolidado_promotora()
