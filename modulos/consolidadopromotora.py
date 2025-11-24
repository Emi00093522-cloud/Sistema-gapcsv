# consolidados.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

def obtener_usuario_actual():
    """
    Obtiene información del usuario actual desde session_state
    MODIFICA ESTA FUNCIÓN según tu sistema de autenticación
    """
    # Ejemplo - ajusta según tu implementación real
    return {
        'id_usuario': st.session_state.get('id_usuario', 1),
        'rol': st.session_state.get('rol', 'promotora'),  # 'promotora' o 'administrador'
        'nombre': st.session_state.get('nombre_usuario', 'Usuario Demo'),
        'id_promotora': st.session_state.get('id_promotora', 1)  # Si el usuario es promotora
    }

def tiene_permiso_consolidado():
    """Verifica permisos para ver consolidados"""
    usuario = obtener_usuario_actual()
    return usuario['rol'] in ['promotora', 'administrador']

def obtener_grupos_por_promotora(id_promotora):
    """Obtiene todos los grupos asignados a una promotora"""
    try:
        from modulos.config.conexion import obtener_conexion
        
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                g.ID_Grupo,
                g.nombre as nombre_grupo,
                d.nombre as distrito
            FROM Grupo g
            LEFT JOIN Distrito d ON g.ID_Distrito = d.ID_Distrito
            WHERE g.ID_Promotora = %s AND g.estado = 'Activo'
        """, (id_promotora,))
        
        grupos = cursor.fetchall()
        cursor.close()
        con.close()
        
        return grupos
    except Exception as e:
        st.error(f"❌ Error obteniendo grupos: {e}")
        return []

def obtener_distritos_consolidado():
    """Obtiene todos los distritos para administradores"""
    try:
        from modulos.config.conexion import obtener_conexion
        
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                ID_Distrito,
                nombre as nombre_distrito
            FROM Distrito 
            WHERE estado = 'Activo'
            ORDER BY nombre
        """)
        
        distritos = cursor.fetchall()
        cursor.close()
        con.close()
        
        return distritos
    except Exception as e:
        st.error(f"❌ Error obteniendo distritos: {e}")
        return []

def obtener_grupos_por_distrito(id_distrito):
    """Obtiene grupos por distrito"""
    try:
        from modulos.config.conexion import obtener_conexion
        
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                ID_Grupo,
                nombre as nombre_grupo
            FROM Grupo 
            WHERE ID_Distrito = %s AND estado = 'Activo'
        """, (id_distrito,))
        
        grupos = cursor.fetchall()
        cursor.close()
        con.close()
        
        return grupos
    except Exception as e:
        st.error(f"❌ Error obteniendo grupos del distrito: {e}")
        return []

def calcular_totales_grupo(id_grupo, fecha_inicio, fecha_fin):
    """Calcula los totales para un grupo específico"""
    try:
        # Guardar el grupo actual si existe
        grupo_original = st.session_state.get('reunion_actual')
        
        # Establecer el grupo temporal para los cálculos
        st.session_state['reunion_actual'] = {
            'id_grupo': id_grupo,
            'nombre_grupo': 'Temporal'
        }
        
        # Importar y usar tu función existente de cierre_ciclo
        # Asegúrate de que esta función acepte los parámetros de fecha
        from cierre_ciclo import calcular_totales_reales
        ahorros, multas, prestamos_cap, prestamos_int = calcular_totales_reales(fecha_inicio, fecha_fin)
        total_ingresos = ahorros + multas + prestamos_cap + prestamos_int
        
        # Restaurar grupo original si existía
        if grupo_original:
            st.session_state['reunion_actual'] = grupo_original
        else:
            # Limpiar el grupo temporal si no existía uno original
            if 'reunion_actual' in st.session_state and st.session_state['reunion_actual']['id_grupo'] == id_grupo:
                del st.session_state['reunion_actual']
        
        return {
            'ahorros_totales': ahorros,
            'multas_totales': multas,
            'prestamos_capital': prestamos_cap,
            'prestamos_intereses': prestamos_int,
            'total_ingresos': total_ingresos
        }
    except Exception as e:
        st.error(f"❌ Error calculando grupo {id_grupo}: {e}")
        # Restaurar grupo original en caso de error
        if 'grupo_original' in locals() and grupo_original:
            st.session_state['reunion_actual'] = grupo_original
        
        return {
            'ahorros_totales': 0,
            'multas_totales': 0,
            'prestamos_capital': 0,
            'prestamos_intereses': 0,
            'total_ingresos': 0
        }

def calcular_consolidado_promotora(id_promotora, fecha_inicio, fecha_fin):
    """Calcula consolidado para todos los grupos de una promotora"""
    grupos = obtener_grupos_por_promotora(id_promotora)
    
    if not grupos:
        st.warning("⚠️ No se encontraron grupos asignados a esta promotora")
        return None
    
    consolidado = {
        'total_grupos': len(grupos),
        'fecha_inicio': fecha_inicio.strftime("%Y-%m-%d"),
        'fecha_fin': fecha_fin.strftime("%Y-%m-%d"),
        'grupos_detalle': [],
        'totales_consolidados': {
            'ahorros_totales': 0,
            'multas_totales': 0,
            'prestamos_capital': 0,
            'prestamos_intereses': 0,
            'total_ingresos': 0
        }
    }
    
    # Barra de progreso
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, grupo in enumerate(grupos):
        status_text.text(f"Calculando grupo: {grupo['nombre_grupo']}...")
        
        # Calcular datos del grupo
        datos_grupo = calcular_totales_grupo(grupo['ID_Grupo'], fecha_inicio, fecha_fin)
        
        # Agregar información del grupo al detalle
        grupo_detalle = {
            'id_grupo': grupo['ID_Grupo'],
            'nombre_grupo': grupo['nombre_grupo'],
            'distrito': grupo.get('distrito', 'No asignado'),
            **datos_grupo
        }
        
        consolidado['grupos_detalle'].append(grupo_detalle)
        
        # Sumar a totales consolidados
        consolidado['totales_consolidados']['ahorros_totales'] += datos_grupo['ahorros_totales']
        consolidado['totales_consolidados']['multas_totales'] += datos_grupo['multas_totales']
        consolidado['totales_consolidados']['prestamos_capital'] += datos_grupo['prestamos_capital']
        consolidado['totales_consolidados']['prestamos_intereses'] += datos_grupo['prestamos_intereses']
        consolidado['totales_consolidados']['total_ingresos'] += datos_grupo['total_ingresos']
        
        # Actualizar progreso
        progress_bar.progress((i + 1) / len(grupos))
    
    status_text.text("✅ Cálculo completado")
    progress_bar.empty()  # Limpiar barra de progreso
    
    return consolidado

def calcular_consolidado_administrador(fecha_inicio, fecha_fin):
    """Calcula consolidado general por distrito para administradores"""
    distritos = obtener_distritos_consolidado()
    
    if not distritos:
        st.warning("⚠️ No se encontraron distritos")
        return None
    
    consolidado = {
        'total_distritos': len(distritos),
        'fecha_inicio': fecha_inicio.strftime("%Y-%m-%d"),
        'fecha_fin': fecha_fin.strftime("%Y-%m-%d"),
        'distritos_detalle': [],
        'totales_generales': {
            'ahorros_totales': 0,
            'multas_totales': 0,
            'prestamos_capital': 0,
            'prestamos_intereses': 0,
            'total_ingresos': 0,
            'total_grupos': 0
        }
    }
    
    # Barra de progreso
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, distrito in enumerate(distritos):
        status_text.text(f"Procesando distrito: {distrito['nombre_distrito']}...")
        
        grupos_distrito = obtener_grupos_por_distrito(distrito['ID_Distrito'])
        total_distrito = {
            'ahorros_totales': 0,
            'multas_totales': 0,
            'prestamos_capital': 0,
            'prestamos_intereses': 0,
            'total_ingresos': 0
        }
        
        grupos_detalle = []
        
        for grupo in grupos_distrito:
            # Calcular datos del grupo
            datos_grupo = calcular_totales_grupo(grupo['ID_Grupo'], fecha_inicio, fecha_fin)
            
            # Agregar detalle del grupo
            grupos_detalle.append({
                'nombre_grupo': grupo['nombre_grupo'],
                **datos_grupo
            })
            
            # Sumar a totales del distrito
            total_distrito['ahorros_totales'] += datos_grupo['ahorros_totales']
            total_distrito['multas_totales'] += datos_grupo['multas_totales']
            total_distrito['prestamos_capital'] += datos_grupo['prestamos_capital']
            total_distrito['prestamos_intereses'] += datos_grupo['prestamos_intereses']
            total_distrito['total_ingresos'] += datos_grupo['total_ingresos']
        
        # Agregar distrito al consolidado
        consolidado['distritos_detalle'].append({
            'id_distrito': distrito['ID_Distrito'],
            'nombre_distrito': distrito['nombre_distrito'],
            'total_grupos': len(grupos_distrito),
            'totales_distrito': total_distrito,
            'grupos_detalle': grupos_detalle
        })
        
        # Sumar a totales generales
        consolidado['totales_generales']['ahorros_totales'] += total_distrito['ahorros_totales']
        consolidado['totales_generales']['multas_totales'] += total_distrito['multas_totales']
        consolidado['totales_generales']['prestamos_capital'] += total_distrito['prestamos_capital']
        consolidado['totales_generales']['prestamos_intereses'] += total_distrito['prestamos_intereses']
        consolidado['totales_generales']['total_ingresos'] += total_distrito['total_ingresos']
        consolidado['totales_generales']['total_grupos'] += len(grupos_distrito)
        
        # Actualizar progreso
        progress_bar.progress((i + 1) / len(distritos))
    
    status_text.text("✅ Cálculo completado")
    progress_bar.empty()  # Limpiar barra de progreso
    
    return consolidado

def mostrar_graficas_consolidado(totales, titulo):
    """Muestra gráficas de ingresos para el consolidado"""
    st.subheader(f"📊 Gráficas - {titulo}")
    
    # Preparar datos para gráficas
    labels = ['Ahorros', 'Multas', 'Préstamos (Capital)', 'Intereses']
    valores = [
        totales['ahorros_totales'],
        totales['multas_totales'], 
        totales['prestamos_capital'],
        totales['prestamos_intereses']
    ]
    
    # Verificar si hay datos para mostrar
    if sum(valores) == 0:
        st.info("ℹ️ No hay datos suficientes para mostrar gráficas")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfica de torta - Composición de ingresos
        try:
            fig_pie = px.pie(
                names=labels, 
                values=valores,
                title="Composición de Ingresos",
                color=labels,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
        except Exception as e:
            st.error(f"Error generando gráfica de torta: {e}")
    
    with col2:
        # Gráfica de barras
        try:
            fig_bar = px.bar(
                x=labels,
                y=valores,
                title="Ingresos por Concepto",
                labels={'x': 'Concepto', 'y': 'Monto ($)'},
                color=labels,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_bar.update_layout(showlegend=False)
            fig_bar.update_traces(texttemplate='$%{y:,.2f}', textposition='outside')
            st.plotly_chart(fig_bar, use_container_width=True)
        except Exception as e:
            st.error(f"Error generando gráfica de barras: {e}")
    
    # Gráfica adicional: Evolución (simulada)
    st.write("#### 📈 Distribución de Ingresos")
    df_distribucion = pd.DataFrame({
        'Concepto': labels,
        'Monto': valores,
        'Porcentaje': [f"{(val/totales['total_ingresos'])*100:.1f}%" if totales['total_ingresos'] > 0 else "0%" for val in valores]
    })
    
    st.dataframe(df_distribucion, use_container_width=True, hide_index=True)

def mostrar_resumen_promotora(consolidado):
    """Muestra el resumen consolidado para promotoras"""
    usuario = obtener_usuario_actual()
    
    st.header(f"👩‍💼 Consolidado de Promotora: {usuario['nombre']}")
    st.write(f"**📅 Período:** {consolidado['fecha_inicio']} a {consolidado['fecha_fin']}")
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Grupos", consolidado['total_grupos'])
    with col2:
        st.metric(
            "Total Ahorros", 
            f"${consolidado['totales_consolidados']['ahorros_totales']:,.2f}"
        )
    with col3:
        st.metric(
            "Total Ingresos", 
            f"${consolidado['totales_consolidados']['total_ingresos']:,.2f}"
        )
    with col4:
        st.metric(
            "Total Intereses", 
            f"${consolidado['totales_consolidados']['prestamos_intereses']:,.2f}"
        )
    
    # Gráficas
    mostrar_graficas_consolidado(consolidado['totales_consolidados'], "Consolidado Promotora")
    
    # Tabla detallada por grupo
    st.subheader("📋 Detalle por Grupo")
    if consolidado['grupos_detalle']:
        # Crear datos para la tabla
        datos_tabla = []
        for grupo in consolidado['grupos_detalle']:
            datos_tabla.append({
                'Grupo': grupo['nombre_grupo'],
                'Distrito': grupo['distrito'],
                'Ahorros': f"${grupo['ahorros_totales']:,.2f}",
                'Multas': f"${grupo['multas_totales']:,.2f}",
                'Préstamos Capital': f"${grupo['prestamos_capital']:,.2f}",
                'Intereses': f"${grupo['prestamos_intereses']:,.2f}",
                'Total Grupo': f"${grupo['total_ingresos']:,.2f}"
            })
        
        df = pd.DataFrame(datos_tabla)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Resumen final
        st.success(f"**🎯 Resumen Final: {consolidado['total_grupos']} grupos - Total Consolidado: ${consolidado['totales_consolidados']['total_ingresos']:,.2f}**")
    else:
        st.info("ℹ️ No hay datos detallados de grupos para mostrar")

def mostrar_resumen_administrador(consolidado):
    """Muestra el resumen consolidado para administradores"""
    st.header("👨‍💼 Consolidado Administrativo")
    st.write(f"**📅 Período:** {consolidado['fecha_inicio']} a {consolidado['fecha_fin']}")
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Distritos", consolidado['total_distritos'])
    with col2:
        st.metric("Total Grupos", consolidado['totales_generales']['total_grupos'])
    with col3:
        st.metric(
            "Total Ingresos", 
            f"${consolidado['totales_generales']['total_ingresos']:,.2f}"
        )
    with col4:
        st.metric(
            "Total Intereses", 
            f"${consolidado['totales_generales']['prestamos_intereses']:,.2f}"
        )
    
    # Gráficas generales
    mostrar_graficas_consolidado(consolidado['totales_generales'], "Consolidado General")
    
    # Acordeón por distrito
    st.subheader("🏢 Consolidado por Distrito")
    
    for distrito in consolidado['distritos_detalle']:
        with st.expander(
            f"📁 {distrito['nombre_distrito']} - "
            f"{distrito['total_grupos']} grupos - "
            f"Total: ${distrito['totales_distrito']['total_ingresos']:,.2f}"
        ):
            
            # Métricas del distrito
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Ahorros", f"${distrito['totales_distrito']['ahorros_totales']:,.2f}")
            with col2:
                st.metric("Multas", f"${distrito['totales_distrito']['multas_totales']:,.2f}")
            with col3:
                st.metric("Préstamos", f"${distrito['totales_distrito']['prestamos_capital']:,.2f}")
            with col4:
                st.metric("Intereses", f"${distrito['totales_distrito']['prestamos_intereses']:,.2f}")
            
            # Gráficas del distrito
            mostrar_graficas_consolidado(
                distrito['totales_distrito'], 
                f"Distrito {distrito['nombre_distrito']}"
            )
            
            # Tabla de grupos del distrito
            st.write(f"**📋 Grupos del Distrito {distrito['nombre_distrito']}:**")
            if distrito['grupos_detalle']:
                datos_grupos = []
                for grupo in distrito['grupos_detalle']:
                    datos_grupos.append({
                        'Grupo': grupo['nombre_grupo'],
                        'Ahorros': f"${grupo['ahorros_totales']:,.2f}",
                        'Multas': f"${grupo['multas_totales']:,.2f}",
                        'Préstamos': f"${grupo['prestamos_capital']:,.2f}",
                        'Intereses': f"${grupo['prestamos_intereses']:,.2f}",
                        'Total': f"${grupo['total_ingresos']:,.2f}"
                    })
                
                df_grupos = pd.DataFrame(datos_grupos)
                st.dataframe(df_grupos, use_container_width=True, hide_index=True)
            else:
                st.info("No hay grupos con datos en este distrito")
    
    # Resumen final
    st.success(
        f"**🎯 Resumen General: {consolidado['total_distritos']} distritos, "
        f"{consolidado['totales_generales']['total_grupos']} grupos - "
        f"Total General: ${consolidado['totales_generales']['total_ingresos']:,.2f}**"
    )

def mostrar_consolidados():
    """Función principal para mostrar consolidados según el rol del usuario"""
    st.header("🏢 Consolidados Gerenciales")
    
    # Verificar permisos
    if not tiene_permiso_consolidado():
        st.warning("⚠️ No tienes permisos para ver consolidados gerenciales")
        st.info("ℹ️ Solo usuarios con rol 'promotora' o 'administrador' pueden acceder a esta sección")
        return
    
    usuario = obtener_usuario_actual()
    st.write(f"**Usuario:** {usuario['nombre']} | **Rol:** {usuario['rol'].title()}")
    
    # Filtro de fechas para el consolidado
    st.subheader("📅 Seleccionar Rango del Consolidado")
    col1, col2 = st.columns(2)
    
    with col1:
        fecha_inicio = st.date_input(
            "Fecha de Inicio",
            value=datetime.now().date() - timedelta(days=30),
            key="consol_inicio",
            help="Selecciona la fecha inicial del período a consolidar"
        )
    
    with col2:
        fecha_fin = st.date_input(
            "Fecha de Fin", 
            value=datetime.now().date(),
            key="consol_fin",
            help="Selecciona la fecha final del período a consolidar"
        )
    
    # Validar fechas
    if fecha_inicio > fecha_fin:
        st.error("❌ Error: La fecha de inicio no puede ser mayor que la fecha de fin")
        return
    
    dias_periodo = (fecha_fin - fecha_inicio).days
    st.info(f"**📊 Período seleccionado:** {fecha_inicio} a {fecha_fin} ({dias_periodo} días)")
    
    # Botón para generar consolidado
    st.markdown("---")
    if st.button("🚀 Generar Consolidado", type="primary", use_container_width=True):
        with st.spinner("🔄 Calculando consolidado. Esto puede tomar unos momentos..."):
            try:
                if usuario['rol'] == 'promotora':
                    st.write(f"### 👩‍💼 Consolidado para Promotora: {usuario['nombre']}")
                    consolidado = calcular_consolidado_promotora(
                        usuario['id_promotora'],  # Ajusta según tu campo real
                        fecha_inicio, 
                        fecha_fin
                    )
                    if consolidado:
                        mostrar_resumen_promotora(consolidado)
                    else:
                        st.error("No se pudo generar el consolidado para la promotora")
                
                elif usuario['rol'] == 'administrador':
                    st.write("### 👨‍💼 Consolidado Administrativo General")
                    consolidado = calcular_consolidado_administrador(
                        fecha_inicio, 
                        fecha_fin
                    )
                    if consolidado:
                        mostrar_resumen_administrador(consolidado)
                    else:
                        st.error("No se pudo generar el consolidado administrativo")
                
                else:
                    st.error("Rol de usuario no reconocido para consolidados")
                    
            except Exception as e:
                st.error(f"❌ Error generando consolidado: {str(e)}")
                st.info("ℹ️ Verifica que los módulos de base de datos estén configurados correctamente")

# Función para verificación de módulo
def verificar_modulo_consolidados():
    """Verifica que el módulo de consolidados esté funcionando"""
    try:
        from modulos.config.conexion import obtener_conexion
        st.sidebar.success("✅ consolidados.py - CONECTADO")
        return True
    except ImportError as e:
        st.sidebar.error(f"❌ consolidados.py - ERROR: {e}")
        return False

if __name__ == "__main__":
    # Para probar el módulo independientemente
    st.set_page_config(page_title="Consolidados", layout="wide")
    mostrar_consolidados()
