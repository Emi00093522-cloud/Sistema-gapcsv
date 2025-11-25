import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(__file__))

def obtener_id_promotora_actual():
    """Obtiene el ID de promotora de la tabla Promotora basado en el usuario logueado"""
    try:
        from modulos.config.conexion import obtener_conexion
        
        usuario_actual = st.session_state.get("usuario", "")
        if not usuario_actual:
            return None
        
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        # Buscar el ID en la tabla Promotora usando el nombre de usuario
        cursor.execute("""
            SELECT ID_Promotora 
            FROM Promotora 
            WHERE nombre = %s AND ID_Estado = 1
        """, (usuario_actual,))
        
        resultado = cursor.fetchone()
        cursor.close()
        con.close()
        
        if resultado:
            return resultado["ID_Promotora"]
        else:
            return None
            
    except Exception as e:
        st.error(f"Error buscando ID de promotora: {e}")
        return None

def mostrar_consolidado_promotora():
    st.title("📊 Consolidado de Promotora")
    
    # =============================================
    # 1. OBTENER ID PROMOTORA DESDE LA TABLA
    # =============================================
    st.write("### 🔍 Verificando permisos de promotora...")
    
    # Obtener ID de promotora desde la tabla
    id_promotora = obtener_id_promotora_actual()
    
    if id_promotora is None:
        st.error("""
        🚫 **No estás registrada como promotora**
        
        **Para usar este módulo necesitas:**
        1. Ir a la pestaña **"Registro Promotora"** 
        2. Registrarte como promotora
        3. Una vez registrada, podrás ver el consolidado aquí
        
        **Tu usuario actual:** """ + st.session_state.get("usuario", "No identificado"))
        return
    
    st.success(f"✅ **Promotora autorizada** - ID: {id_promotora}")
    
    # =============================================
    # 2. OBTENER GRUPOS DE ESTA PROMOTORA
    # =============================================
    def obtener_grupos_promotora():
        try:
            from modulos.config.conexion import obtener_conexion
            
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
            st.error(f"❌ Error obteniendo grupos: {e}")
            return []
    
    grupos = obtener_grupos_promotora()
    
    if not grupos:
        st.warning("""
        ℹ️ **No tienes grupos asignados**
        
        Una vez que crees grupos en el sistema, aparecerán aquí para el consolidado.
        """)
        return
    
    st.info(f"👥 **Grupos asignados:** {len(grupos)} grupo(s)")
    
    # =============================================
    # 3. FILTROS DE FECHAS
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
    # 4. FUNCIONES PARA OBTENER DATOS
    # =============================================
    
    def obtener_ahorros_grupo(id_grupo, fecha_inicio, fecha_fin):
        try:
            from modulos.config.conexion import obtener_conexion
            
            con = obtener_conexion()
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
            st.error(f"Error en ahorros: {e}")
            return 0.0
    
    def obtener_prestamos_grupo(id_grupo, fecha_inicio, fecha_fin):
        try:
            from modulos.config.conexion import obtener_conexion
            
            con = obtener_conexion()
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
            st.error(f"Error en préstamos: {e}")
            return 0.0, 0.0
    
    def obtener_multas_grupo(id_grupo, fecha_inicio, fecha_fin):
        try:
            from modulos.config.conexion import obtener_conexion
            
            con = obtener_conexion()
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
            st.error(f"Error en multas: {e}")
            return 0.0
    
    def obtener_miembros_grupo(id_grupo):
        try:
            from modulos.config.conexion import obtener_conexion
            
            con = obtener_conexion()
            cursor = con.cursor(dictionary=True)
            
            cursor.execute("SELECT COUNT(*) as total FROM Miembro WHERE ID_Grupo = %s AND ID_Estado = 1", (id_grupo,))
            resultado = cursor.fetchone()
            cursor.close()
            con.close()
            
            return resultado["total"]
            
        except Exception as e:
            st.error(f"Error contando miembros: {e}")
            return 0
    
    # =============================================
    # 5. GENERAR REPORTE
    # =============================================
    
    if st.button("🚀 GENERAR REPORTE CONSOLIDADO", type="primary", use_container_width=True):
        
        with st.spinner("Calculando consolidado..."):
            
            datos_consolidado = []
            
            for grupo in grupos:
                grupo_id = grupo["ID_Grupo"]
                grupo_nombre = grupo["nombre_grupo"]
                
                # Obtener datos
                ahorros = obtener_ahorros_grupo(grupo_id, fecha_inicio, fecha_fin)
                prestamos, intereses = obtener_prestamos_grupo(grupo_id, fecha_inicio, fecha_fin)
                multas = obtener_multas_grupo(grupo_id, fecha_inicio, fecha_fin)
                miembros = obtener_miembros_grupo(grupo_id)
                
                total_general = ahorros + prestamos + intereses + multas
                
                datos_consolidado.append({
                    "nombre_grupo": grupo_nombre,
                    "total_miembros": miembros,
                    "total_ahorros": ahorros,
                    "total_prestamos": prestamos,
                    "total_intereses": intereses,
                    "total_multas": multas,
                    "total_general": total_general
                })
            
            # MOSTRAR RESULTADOS
            st.subheader("📋 Tabla de Consolidado")
            
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
            st.subheader("📈 Métricas Totales")
            
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
            st.success("🎉 Consolidado generado exitosamente")

if __name__ == "__main__":
    mostrar_consolidado_promotora()
