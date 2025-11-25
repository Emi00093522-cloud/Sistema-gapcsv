import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Agregar la ruta de tus módulos
sys.path.append(os.path.dirname(__file__))

def mostrar_consolidado_promotora():
    """Función principal del consolidado de promotora"""
    
    st.title("📊 Consolidado de Promotora")
    
    # =============================================
    # 1. VERIFICAR SESIÓN DE PROMOTORA
    # =============================================
    if "id_promotora" not in st.session_state:
        st.error("🚫 No hay sesión de promotora activa. Debes iniciar sesión como promotora.")
        return
    
    id_promotora = st.session_state.id_promotora
    st.success(f"✅ Sesión activa - Promotora ID: {id_promotora}")
    
    # =============================================
    # 2. OBTENER GRUPOS DE LA PROMOTORA
    # =============================================
    def obtener_grupos_promotora():
        """Obtiene los grupos que maneja la promotora"""
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
        st.warning("ℹ️ No tienes grupos asignados como promotora.")
        return
    
    st.info(f"👥 Tienes {len(grupos)} grupo(s) asignado(s)")
    
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
    st.info(f"**📊 Rango seleccionado:** {fecha_inicio} a {fecha_fin} ({dias_rango} días)")
    
    # =============================================
    # 4. FUNCIONES PARA OBTENER DATOS
    # =============================================
    
    def obtener_ahorros_grupo(id_grupo, fecha_inicio, fecha_fin):
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
            
            return float(resultado["total_general"])
            
        except Exception as e:
            st.error(f"❌ Error en ahorros grupo {id_grupo}: {e}")
            return 0.0
    
    def obtener_prestamos_grupo(id_grupo, fecha_inicio, fecha_fin):
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
            
            capital = float(resultado["total_capital"])
            intereses = float(resultado["total_intereses"])
            
            return capital, intereses
            
        except Exception as e:
            st.error(f"❌ Error en préstamos grupo {id_grupo}: {e}")
            return 0.0, 0.0
    
    def obtener_multas_grupo(id_grupo, fecha_inicio, fecha_fin):
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
            
            return float(resultado["total_multas"])
            
        except Exception as e:
            st.error(f"❌ Error en multas grupo {id_grupo}: {e}")
            return 0.0
    
    def obtener_miembros_grupo(id_grupo):
        """Obtiene número de miembros activos de un grupo"""
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
            cursor.close()
            con.close()
            
            return resultado["total_miembros"] if resultado else 0
            
        except Exception as e:
            st.error(f"❌ Error obteniendo miembros grupo {id_grupo}: {e}")
            return 0
    
    # =============================================
    # 5. BOTÓN PARA GENERAR REPORTE
    # =============================================
    
    if st.button("🚀 GENERAR REPORTE CONSOLIDADO", type="primary", use_container_width=True):
        
        with st.spinner("🔍 Calculando consolidado de todos los grupos..."):
            
            datos_consolidado = []
            
            # Procesar cada grupo
            for grupo in grupos:
                grupo_id = grupo["ID_Grupo"]
                grupo_nombre = grupo["nombre_grupo"]
                
                # Obtener datos del grupo
                total_ahorros = obtener_ahorros_grupo(grupo_id, fecha_inicio, fecha_fin)
                total_prestamos, total_intereses = obtener_prestamos_grupo(grupo_id, fecha_inicio, fecha_fin)
                total_multas = obtener_multas_grupo(grupo_id, fecha_inicio, fecha_fin)
                total_miembros = obtener_miembros_grupo(grupo_id)
                
                # Calcular total general
                total_general = total_ahorros + total_prestamos + total_intereses + total_multas
                
                datos_consolidado.append({
                    "id_grupo": grupo_id,
                    "nombre_grupo": grupo_nombre,
                    "total_miembros": total_miembros,
                    "total_ahorros": total_ahorros,
                    "total_prestamos": total_prestamos,
                    "total_intereses": total_intereses,
                    "total_multas": total_multas,
                    "total_general": total_general
                })
            
            # =============================================
            # 6. MOSTRAR TABLA DE CONSOLIDADO
            # =============================================
            st.subheader("📋 Tabla de Consolidado por Grupo")
            
            # Crear tabla
            tabla_data = []
            for dato in datos_consolidado:
                tabla_data.append({
                    "Grupo": dato["nombre_grupo"],
                    "Miembros": f"{dato['total_miembros']}",
                    "💰 Ahorros": f"${dato['total_ahorros']:,.2f}",
                    "🏦 Préstamos": f"${dato['total_prestamos']:,.2f}",
                    "📈 Intereses": f"${dato['total_intereses']:,.2f}",
                    "⚖️ Multas": f"${dato['total_multas']:,.2f}",
                    "💵 TOTAL": f"${dato['total_general']:,.2f}"
                })
            
            df_tabla = pd.DataFrame(tabla_data)
            st.dataframe(df_tabla, use_container_width=True, hide_index=True)
            
            # =============================================
            # 7. MOSTRAR MÉTRICAS Y TOTALES
            # =============================================
            st.subheader("📈 Métricas del Consolidado")
            
            # Calcular totales generales
            totales = {
                "ahorros": sum(d["total_ahorros"] for d in datos_consolidado),
                "prestamos": sum(d["total_prestamos"] for d in datos_consolidado),
                "intereses": sum(d["total_intereses"] for d in datos_consolidado),
                "multas": sum(d["total_multas"] for d in datos_consolidado),
                "general": sum(d["total_general"] for d in datos_consolidado),
                "miembros": sum(d["total_miembros"] for d in datos_consolidado)
            }
            
            # Mostrar métricas en columnas
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Grupos", len(grupos))
                st.metric("Total Miembros", totales["miembros"])
                
            with col2:
                st.metric("Total Ahorros", f"${totales['ahorros']:,.2f}")
                st.metric("Total Multas", f"${totales['multas']:,.2f}")
                
            with col3:
                st.metric("Total Préstamos", f"${totales['prestamos']:,.2f}")
                st.metric("Total Intereses", f"${totales['intereses']:,.2f}")
                
            with col4:
                st.metric("TOTAL GENERAL", f"${totales['general']:,.2f}")
                st.metric("Promedio x Grupo", f"${totales['general']/len(grupos):,.2f}")
            
            # =============================================
            # 8. GRÁFICO DE BARRAS SIMPLE
            # =============================================
            st.subheader("📊 Gráfico de Barras - Comparativa por Grupo")
            
            # Usar la tabla de Streamlit como "gráfico" simple
            st.info("📈 **Comparativa Visual de Totales por Grupo:**")
            
            for dato in datos_consolidado:
                # Crear una barra visual simple con texto
                porcentaje = (dato['total_general'] / totales['general']) * 100 if totales['general'] > 0 else 0
                st.write(f"**{dato['nombre_grupo']}:** ${dato['total_general']:,.2f} ({porcentaje:.1f}%)")
            
            # =============================================
            # 9. DETALLES POR GRUPO
            # =============================================
            st.subheader("👥 Detalles por Grupo")
            
            for dato in datos_consolidado:
                with st.expander(f"📊 {dato['nombre_grupo']} - {dato['total_miembros']} miembros"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Ahorros:** ${dato['total_ahorros']:,.2f}")
                        st.write(f"**Préstamos:** ${dato['total_prestamos']:,.2f}")
                        
                    with col2:
                        st.write(f"**Intereses:** ${dato['total_intereses']:,.2f}")
                        st.write(f"**Multas:** ${dato['total_multas']:,.2f}")
                    
                    st.success(f"**TOTAL DEL GRUPO:** ${dato['total_general']:,.2f}")
            
            st.balloons()
            st.success("🎉 **CONSOLIDADO GENERADO EXITOSAMENTE**")

# Para pruebas directas
if __name__ == "__main__":
    # Simular sesión para pruebas
    if "id_promotora" not in st.session_state:
        st.session_state.id_promotora = 1
    mostrar_consolidado_promotora()
