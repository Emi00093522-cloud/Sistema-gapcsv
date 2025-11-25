import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
    # 1. VERIFICAR SI ES USUARIO PROMOTORA CON ACCESO TOTAL
    # =============================================
    es_promotora_acceso_total = st.session_state.get("acceso_total_promotora", False)
    cargo_usuario = st.session_state.get("cargo_de_usuario", "")
    
    if es_promotora_acceso_total:
        st.info("🔓 **MODO PROMOTORA CON ACCESO TOTAL**: Puedes ver todos los grupos del sistema")
    
    # =============================================
    # 2. OBTENER ID PROMOTORA DESDE LA TABLA
    # =============================================
    st.write("### 🔍 Verificando permisos de promotora...")
    
    # Obtener ID de promotora desde la tabla
    id_promotora = obtener_id_promotora_actual()
    
    if id_promotora is None and not es_promotora_acceso_total:
        st.error("""
        🚫 **No estás registrada como promotora**
        
        **Para usar este módulo necesitas:**
        1. Ir a la pestaña **"Registro Promotora"** 
        2. Registrarte como promotora
        3. Una vez registrada, podrás ver el consolidado aquí
        
        **Tu usuario actual:** """ + st.session_state.get("usuario", "No identificado"))
        return
    
    if es_promotora_acceso_total:
        st.success(f"✅ **Promotora con acceso total** - Puedes ver todos los grupos del sistema")
    else:
        st.success(f"✅ **Promotora autorizada** - ID: {id_promotora}")
    
    # =============================================
    # 3. OBTENER GRUPOS (TODOS SI ES PROMOTORA CON ACCESO TOTAL)
    # =============================================
    def obtener_grupos_promotora():
        try:
            from modulos.config.conexion import obtener_conexion
            
            con = obtener_conexion()
            cursor = con.cursor(dictionary=True)
            
            if es_promotora_acceso_total:
                # 👉 PROMOTORA CON ACCESO TOTAL: TODOS LOS GRUPOS
                cursor.execute("""
                    SELECT g.ID_Grupo, g.nombre as nombre_grupo, p.nombre as nombre_promotora
                    FROM Grupo g
                    LEFT JOIN Promotora p ON g.ID_Promotora = p.ID_Promotora
                    ORDER BY g.nombre
                """)
                st.info("📋 **Vista de todos los grupos del sistema**")
            else:
                # 👉 PROMOTORA NORMAL: SOLO SUS GRUPOS
                cursor.execute("""
                    SELECT ID_Grupo, nombre as nombre_grupo
                    FROM Grupo 
                    WHERE ID_Promotora = %s
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
        st.warning("""
        ℹ️ **No hay grupos en el sistema**
        
        Una vez que se creen grupos, aparecerán aquí para el consolidado.
        """)
        return
    
    if es_promotora_acceso_total:
        st.info(f"👥 **Total de grupos en el sistema:** {len(grupos)} grupo(s)")
    else:
        st.info(f"👥 **Grupos asignados:** {len(grupos)} grupo(s)")
    
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
    # 5. FUNCIONES PARA OBTENER DATOS (SIN CAMBIOS, FUNCIONAN PARA CUALQUIER GRUPO)
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
    # 6. GENERAR REPORTE CON GRÁFICOS
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
                
                # Agregar información de promotora si es acceso total
                if es_promotora_acceso_total:
                    datos_consolidado.append({
                        "nombre_grupo": grupo_nombre,
                        "promotora": grupo.get("nombre_promotora", "N/A"),
                        "total_miembros": miembros,
                        "total_ahorros": ahorros,
                        "total_prestamos": prestamos,
                        "total_intereses": intereses,
                        "total_multas": multas,
                        "total_general": total_general
                    })
                else:
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
                if es_promotora_acceso_total:
                    tabla_data.append({
                        "Grupo": dato["nombre_grupo"],
                        "Promotora": dato["promotora"],
                        "Miembros": dato["total_miembros"],
                        "Ahorros": f"${dato['total_ahorros']:,.2f}",
                        "Préstamos": f"${dato['total_prestamos']:,.2f}",
                        "Intereses": f"${dato['total_intereses']:,.2f}",
                        "Multas": f"${dato['total_multas']:,.2f}",
                        "TOTAL": f"${dato['total_general']:,.2f}"
                    })
                else:
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
            
            if es_promotora_acceso_total:
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
            else:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Grupos", len(grupos))
                    st.metric("Total Miembros", totales["miembros"])
                    
                with col2:
                    st.metric("Ahorros", f"${totales['ahorros']:,.2f}")
                    st.metric("Préstamos", f"${totales['prestamos']:,.2f}")
                    
                with col3:
                    st.metric("Intereses", f"${totales['intereses']:,.2f}")
                    st.metric("TOTAL GENERAL", f"${totales['general']:,.2f}")
            
            # =============================================
            # 7. GRÁFICOS INTERACTIVOS
            # =============================================
            st.subheader("📊 Gráficos de Consolidado")
            
            # Preparar datos para gráficos
            df_graficos = pd.DataFrame(datos_consolidado)
            
            # Gráfico 1: Distribución por categorías (Barras apiladas)
            st.markdown("#### 💰 Distribución Financiera por Grupo")
            
            fig_barras = go.Figure(data=[
                go.Bar(name='Ahorros', x=df_graficos['nombre_grupo'], y=df_graficos['total_ahorros'], 
                       marker_color='#2E86AB'),
                go.Bar(name='Préstamos', x=df_graficos['nombre_grupo'], y=df_graficos['total_prestamos'], 
                       marker_color='#A23B72'),
                go.Bar(name='Intereses', x=df_graficos['nombre_grupo'], y=df_graficos['total_intereses'], 
                       marker_color='#F18F01'),
                go.Bar(name='Multas', x=df_graficos['nombre_grupo'], y=df_graficos['total_multas'], 
                       marker_color='#C73E1D')
            ])
            
            fig_barras.update_layout(
                title="Distribución Financiera por Grupo",
                xaxis_title="Grupos",
                yaxis_title="Monto ($)",
                barmode='stack',
                height=500,
                showlegend=True
            )
            
            st.plotly_chart(fig_barras, use_container_width=True)
            
            # Gráfico 2: Comparación de totales por grupo
            st.markdown("#### 📈 Comparación de Totales por Grupo")
            
            fig_totales = px.bar(
                df_graficos, 
                x='nombre_grupo', 
                y='total_general',
                title="Total General por Grupo",
                color='total_general',
                color_continuous_scale='Viridis'
            )
            
            fig_totales.update_layout(
                xaxis_title="Grupos",
                yaxis_title="Total General ($)",
                height=400
            )
            
            st.plotly_chart(fig_totales, use_container_width=True)
            
            # Gráfico 3: Pie chart de distribución general
            st.markdown("#### 🥧 Distribución General de Ingresos")
            
            categorias_totales = {
                'Ahorros': totales['ahorros'],
                'Préstamos': totales['prestamos'],
                'Intereses': totales['intereses'],
                'Multas': totales['multas']
            }
            
            # Filtrar categorías con valores mayores a 0
            categorias_filtradas = {k: v for k, v in categorias_totales.items() if v > 0}
            
            if categorias_filtradas:
                fig_pie = px.pie(
                    names=list(categorias_filtradas.keys()),
                    values=list(categorias_filtradas.values()),
                    title="Distribución Porcentual de Ingresos",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                fig_pie.update_layout(height=500)
                
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No hay datos suficientes para mostrar el gráfico circular")
            
            # Gráfico 4: Relación Miembros vs Ahorros
            st.markdown("#### 👥 Relación Miembros vs Ahorros")
            
            fig_scatter = px.scatter(
                df_graficos,
                x='total_miembros',
                y='total_ahorros',
                size='total_ahorros',
                color='nombre_grupo',
                title="Relación entre Número de Miembros y Total de Ahorros",
                hover_name='nombre_grupo',
                size_max=60
            )
            
            fig_scatter.update_layout(
                xaxis_title="Número de Miembros",
                yaxis_title="Total Ahorros ($)",
                height=500
            )
            
            st.plotly_chart(fig_scatter, use_container_width=True)
            
            # Gráfico 5: Barras horizontales para comparación
            st.markdown("#### 📊 Comparación Horizontal de Grupos")
            
            # Ordenar por total general
            df_ordenado = df_graficos.sort_values('total_general', ascending=True)
            
            fig_horizontal = go.Figure()
            
            fig_horizontal.add_trace(go.Bar(
                y=df_ordenado['nombre_grupo'],
                x=df_ordenado['total_general'],
                orientation='h',
                marker_color='#1f77b4',
                text=df_ordenado['total_general'].apply(lambda x: f"${x:,.2f}"),
                textposition='auto',
            ))
            
            fig_horizontal.update_layout(
                title="Total General por Grupo (Ordenado)",
                xaxis_title="Total General ($)",
                yaxis_title="Grupos",
                height=400
            )
            
            st.plotly_chart(fig_horizontal, use_container_width=True)
            
            st.balloons()
            st.success("🎉 Consolidado generado exitosamente")

if __name__ == "__main__":
    mostrar_consolidado_promotora()
