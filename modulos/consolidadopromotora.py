import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from modulos.config.conexion import obtener_conexion

def obtener_grupos_promotora():
    """Obtiene los grupos asignados a la promotora logueada"""
    try:
        # Verificar que la promotora esté en session_state
        if 'user_id' not in st.session_state:
            st.error("No hay usuario logueado")
            return []
            
        id_promotora = st.session_state.user_id
        
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT g.ID_Grupo, g.nombre_grupo, g.descripcion
            FROM Grupo g
            WHERE g.ID_Promotora = %s
            ORDER BY g.nombre_grupo
        """, (id_promotora,))
        
        grupos = cursor.fetchall()
        return grupos
        
    except Exception as e:
        st.error(f"❌ Error obteniendo grupos: {e}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'con' in locals():
            con.close()

def obtener_ahorros_por_mes(id_grupo, fecha_inicio, fecha_fin):
    """Obtiene los ahorros totales por mes para un grupo"""
    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                DATE_FORMAT(r.fecha, '%Y-%m') as mes,
                COALESCE(SUM(a.monto_ahorro), 0) as total_ahorros,
                COALESCE(SUM(a.monto_otros), 0) as total_otros,
                COALESCE(SUM(a.monto_ahorro + a.monto_otros), 0) as total_general
            FROM Ahorro a
            JOIN Reunion r ON a.ID_Reunion = r.ID_Reunion
            WHERE r.ID_Grupo = %s
              AND r.fecha BETWEEN %s AND %s
            GROUP BY DATE_FORMAT(r.fecha, '%Y-%m')
            ORDER BY mes
        """, (id_grupo, fecha_inicio, fecha_fin))
        
        return cursor.fetchall()
        
    except Exception as e:
        st.error(f"❌ Error obteniendo ahorros: {e}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'con' in locals():
            con.close()

def obtener_prestamos_por_mes(id_grupo, fecha_inicio, fecha_fin):
    """Obtiene los préstamos otorgados por mes"""
    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                DATE_FORMAT(p.fecha_desembolso, '%Y-%m') as mes,
                COUNT(*) as cantidad_prestamos,
                COALESCE(SUM(p.monto), 0) as total_capital,
                COALESCE(SUM(p.total_interes), 0) as total_intereses,
                COALESCE(SUM(p.monto_total_pagar), 0) as total_prestamos
            FROM Prestamo p
            JOIN Miembro m ON p.ID_Miembro = m.ID_Miembro
            WHERE m.ID_Grupo = %s
              AND p.fecha_desembolso BETWEEN %s AND %s
              AND p.ID_Estado_prestamo != 3  -- Excluir cancelados
            GROUP BY DATE_FORMAT(p.fecha_desembolso, '%Y-%m')
            ORDER BY mes
        """, (id_grupo, fecha_inicio, fecha_fin))
        
        return cursor.fetchall()
        
    except Exception as e:
        st.error(f"❌ Error obteniendo préstamos: {e}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'con' in locals():
            con.close()

def obtener_multas_por_mes(id_grupo, fecha_inicio, fecha_fin):
    """Obtiene las multas pagadas por mes"""
    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                DATE_FORMAT(pm.fecha_pago, '%Y-%m') as mes,
                COUNT(*) as cantidad_multas,
                COALESCE(SUM(pm.monto_pagado), 0) as total_multas
            FROM PagoMulta pm
            JOIN Miembro m ON pm.ID_Miembro = m.ID_Miembro
            WHERE m.ID_Grupo = %s
              AND pm.fecha_pago BETWEEN %s AND %s
            GROUP BY DATE_FORMAT(pm.fecha_pago, '%Y-%m')
            ORDER BY mes
        """, (id_grupo, fecha_inicio, fecha_fin))
        
        return cursor.fetchall()
        
    except Exception as e:
        st.error(f"❌ Error obteniendo multas: {e}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'con' in locals():
            con.close()

def obtener_pagos_prestamos_por_mes(id_grupo, fecha_inicio, fecha_fin):
    """Obtiene los pagos de préstamos realizados por mes (EGRESOS)"""
    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                DATE_FORMAT(cp.fecha_pago_real, '%Y-%m') as mes,
                COALESCE(SUM(cp.capital_pagado), 0) as total_capital_pagado,
                COALESCE(SUM(cp.interes_pagado), 0) as total_intereses_pagado,
                COALESCE(SUM(cp.total_pagado), 0) as total_pagado
            FROM CuotaPrestamo cp
            JOIN Prestamo p ON cp.ID_Prestamo = p.ID_Prestamo
            JOIN Miembro m ON p.ID_Miembro = m.ID_Miembro
            WHERE m.ID_Grupo = %s
              AND cp.fecha_pago_real IS NOT NULL
              AND cp.fecha_pago_real BETWEEN %s AND %s
              AND cp.estado = 'pagado'
            GROUP BY DATE_FORMAT(cp.fecha_pago_real, '%Y-%m')
            ORDER BY mes
        """, (id_grupo, fecha_inicio, fecha_fin))
        
        resultados = cursor.fetchall()
        return resultados
        
    except Exception as e:
        st.error(f"❌ Error obteniendo pagos de préstamos: {e}")
        return []
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'con' in locals():
            con.close()

def consolidar_datos_por_mes(grupos_seleccionados, fecha_inicio, fecha_fin):
    """Consolida todos los datos por mes para los grupos seleccionados"""
    datos_consolidados = []
    
    for id_grupo in grupos_seleccionados:
        # Obtener nombre del grupo
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        cursor.execute("SELECT nombre_grupo FROM Grupo WHERE ID_Grupo = %s", (id_grupo,))
        grupo_data = cursor.fetchone()
        
        if not grupo_data:
            continue
            
        grupo_nombre = grupo_data['nombre_grupo']
        cursor.close()
        con.close()
        
        st.info(f"📊 Procesando datos del grupo: {grupo_nombre}")
        
        # Obtener datos de cada módulo
        ahorros = obtener_ahorros_por_mes(id_grupo, fecha_inicio, fecha_fin)
        prestamos = obtener_prestamos_por_mes(id_grupo, fecha_inicio, fecha_fin)
        multas = obtener_multas_por_mes(id_grupo, fecha_inicio, fecha_fin)
        pagos_prestamos = obtener_pagos_prestamos_por_mes(id_grupo, fecha_inicio, fecha_fin)
        
        # Debug: mostrar cuántos registros se encontraron
        st.write(f"✅ {grupo_nombre}: {len(ahorros)} meses con ahorros, {len(prestamos)} meses con préstamos, {len(multas)} meses con multas, {len(pagos_prestamos)} meses con pagos")
        
        # Crear estructura unificada por mes
        meses_unicos = set()
        
        # Agregar meses de todas las fuentes
        for data in [ahorros, prestamos, multas, pagos_prestamos]:
            for item in data:
                if item['mes']:
                    meses_unicos.add(item['mes'])
        
        if not meses_unicos:
            st.warning(f"No hay datos para el grupo {grupo_nombre} en el período seleccionado")
            continue
            
        for mes in sorted(meses_unicos):
            # Buscar datos para este mes
            ahorro_mes = next((a for a in ahorros if a['mes'] == mes), {
                'total_ahorros': 0, 'total_otros': 0, 'total_general': 0
            })
            
            prestamo_mes = next((p for p in prestamos if p['mes'] == mes), {
                'total_capital': 0, 'total_intereses': 0, 'total_prestamos': 0
            })
            
            multa_mes = next((m for m in multas if m['mes'] == mes), {
                'total_multas': 0
            })
            
            pago_mes = next((pp for pp in pagos_prestamos if pp['mes'] == mes), {
                'total_capital_pagado': 0, 'total_intereses_pagado': 0, 'total_pagado': 0
            })
            
            # Calcular totales
            total_ingresos = (ahorro_mes['total_general'] + 
                            prestamo_mes['total_prestamos'] + 
                            multa_mes['total_multas'])
            
            total_egresos = pago_mes['total_pagado']
            
            balance = total_ingresos - total_egresos
            
            datos_consolidados.append({
                'grupo': grupo_nombre,
                'mes': mes,
                'ahorros': float(ahorro_mes['total_general']),
                'prestamos_otorgados': float(prestamo_mes['total_prestamos']),
                'multas': float(multa_mes['total_multas']),
                'pagos_prestamos': float(pago_mes['total_pagado']),
                'total_ingresos': float(total_ingresos),
                'total_egresos': float(total_egresos),
                'balance': float(balance)
            })
    
    return datos_consolidados

def mostrar_filtro_fechas():
    """Muestra el filtro de fechas"""
    st.subheader("📅 Seleccionar Rango del Período")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fecha_inicio = st.date_input(
            "Fecha de Inicio",
            value=datetime.now().date() - timedelta(days=90),
            max_value=datetime.now().date(),
            key="fecha_inicio_consolidado"
        )
    
    with col2:
        fecha_fin = st.date_input(
            "Fecha de Fin",
            value=datetime.now().date(),
            max_value=datetime.now().date(),
            key="fecha_fin_consolidado"
        )
    
    if fecha_inicio > fecha_fin:
        st.error("❌ La fecha de inicio no puede ser mayor que la fecha de fin")
        return None, None
    
    dias_periodo = (fecha_fin - fecha_inicio).days
    st.info(f"**📊 Rango seleccionado:** {fecha_inicio} a {fecha_fin} ({dias_periodo} días)")
    
    return fecha_inicio, fecha_fin

def mostrar_graficas_consolidadas(datos_consolidados):
    """Muestra gráficas de ingresos, egresos y balance"""
    if not datos_consolidados:
        st.warning("No hay datos para mostrar en el período seleccionado.")
        return
    
    df = pd.DataFrame(datos_consolidados)
    
    # Gráfica de INGRESOS por mes y grupo
    st.subheader("📈 Ingresos por Mes y Grupo")
    
    if len(df) > 0:
        fig_ingresos = px.bar(
            df,
            x='mes',
            y='total_ingresos',
            color='grupo',
            barmode='group',
            title='Evolución de Ingresos Mensuales por Grupo',
            labels={'mes': 'Mes', 'total_ingresos': 'Total Ingresos ($)', 'grupo': 'Grupo'}
        )
        st.plotly_chart(fig_ingresos, use_container_width=True)
        
        # Gráfica de EGRESOS por mes y grupo
        st.subheader("📉 Egresos por Mes y Grupo")
        
        fig_egresos = px.bar(
            df,
            x='mes',
            y='total_egresos',
            color='grupo',
            barmode='group',
            title='Evolución de Egresos Mensuales por Grupo',
            labels={'mes': 'Mes', 'total_egresos': 'Total Egresos ($)', 'grupo': 'Grupo'}
        )
        st.plotly_chart(fig_egresos, use_container_width=True)
        
        # Gráfica de BALANCE por mes y grupo
        st.subheader("⚖️ Balance por Mes y Grupo")
        
        fig_balance = px.bar(
            df,
            x='mes',
            y='balance',
            color='grupo',
            barmode='group',
            title='Balance Mensual por Grupo (Ingresos - Egresos)',
            labels={'mes': 'Mes', 'balance': 'Balance ($)', 'grupo': 'Grupo'}
        )
        fig_balance.add_hline(y=0, line_dash="dash", line_color="red")
        st.plotly_chart(fig_balance, use_container_width=True)
    else:
        st.info("No hay suficientes datos para generar gráficas")

def mostrar_tabla_resumen(datos_consolidados):
    """Muestra tabla resumen de los datos consolidados"""
    if not datos_consolidados:
        return
    
    df = pd.DataFrame(datos_consolidados)
    
    st.subheader("📊 Tabla Resumen Consolidada")
    
    # Mostrar tabla detallada
    st.dataframe(
        df.round(2),
        use_container_width=True,
        hide_index=True
    )
    
    # Resumen general por grupo
    st.subheader("🎯 Resumen General por Grupo")
    
    resumen_grupo = df.groupby('grupo').agg({
        'total_ingresos': 'sum',
        'total_egresos': 'sum',
        'balance': 'sum'
    }).round(2).reset_index()
    
    # Mostrar métricas en columnas
    cols = st.columns(len(resumen_grupo))
    
    for idx, (_, grupo) in enumerate(resumen_grupo.iterrows()):
        with cols[idx % len(cols)]:
            st.metric(
                f"📈 Ingresos - {grupo['grupo']}",
                f"${grupo['total_ingresos']:,.2f}"
            )
            
            st.metric(
                f"📉 Egresos - {grupo['grupo']}",
                f"${grupo['total_egresos']:,.2f}"
            )
            
            balance_color = "normal" if grupo['balance'] >= 0 else "off"
            st.metric(
                f"⚖️ Balance - {grupo['grupo']}",
                f"${grupo['balance']:,.2f}",
                delta_color=balance_color
            )

def mostrar_consolidado_promotora():
    """Función principal del módulo de consolidado"""
    st.title("🏦 Consolidado Promotora")
    
    # Verificar que el usuario esté logueado y sea promotora
    if 'user_id' not in st.session_state:
        st.warning("⚠️ Debes iniciar sesión para acceder a este módulo.")
        return
        
    if 'user_type' not in st.session_state or st.session_state.user_type != 'promotora':
        st.error("❌ Esta funcionalidad es exclusiva para promotoras.")
        return
    
    st.info("Este módulo te permite ver el consolidado financiero de todos tus grupos.")
    
    # Obtener grupos de la promotora
    grupos = obtener_grupos_promotora()
    
    if not grupos:
        st.warning("No tienes grupos asignados. Contacta al administrador.")
        return
    
    # Mostrar información de grupos
    st.subheader("👥 Grupos Asignados")
    grupos_df = pd.DataFrame(grupos)
    st.dataframe(grupos_df[['nombre_grupo', 'descripcion']], use_container_width=True, hide_index=True)
    
    # Selección de grupos
    st.subheader("🎯 Seleccionar Grupos para Consolidar")
    
    grupos_dict = {f"{g['nombre_grupo']} (ID: {g['ID_Grupo']})": g['ID_Grupo'] for g in grupos}
    grupos_seleccionados_nombres = st.multiselect(
        "Selecciona los grupos a consolidar:",
        options=list(grupos_dict.keys()),
        default=list(grupos_dict.keys())[:1] if grupos_dict else [],
        help="Puedes seleccionar uno o varios grupos para comparar"
    )
    
    grupos_seleccionados = [grupos_dict[nombre] for nombre in grupos_seleccionados_nombres]
    
    if not grupos_seleccionados:
        st.info("Selecciona al menos un grupo para ver el consolidado.")
        return
    
    # Filtro de fechas
    fecha_inicio, fecha_fin = mostrar_filtro_fechas()
    if fecha_inicio is None:
        return
    
    # Botón para generar reporte
    if st.button("🚀 Generar Reporte Consolidado", type="primary", use_container_width=True):
        with st.spinner("Calculando consolidado... Esto puede tomar unos segundos."):
            datos_consolidados = consolidar_datos_por_mes(grupos_seleccionados, fecha_inicio, fecha_fin)
        
        if datos_consolidados:
            st.success(f"✅ Reporte generado con éxito! Se encontraron datos para {len(datos_consolidados)} períodos.")
            
            # Mostrar gráficas
            mostrar_graficas_consolidadas(datos_consolidados)
            
            # Mostrar tabla resumen
            mostrar_tabla_resumen(datos_consolidados)
            
            # Botón para exportar
            csv = pd.DataFrame(datos_consolidados).to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar Reporte en CSV",
                data=csv,
                file_name=f"consolidado_promotora_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.error("""
            ❌ No se encontraron datos para los grupos y fechas seleccionados.
            
            **Posibles causas:**
            - No hay reuniones registradas en el período
            - No hay ahorros, préstamos o multas en las fechas seleccionadas
            - Los grupos no tienen actividad financiera en este período
            """)

# Si el archivo se ejecuta directamente
if __name__ == "__main__":
    mostrar_consolidado_promotora()
