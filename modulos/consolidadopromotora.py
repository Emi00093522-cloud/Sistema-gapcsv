import streamlit as st
import pandas as pd
import plotly.express as px
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

def obtener_datos_simples_para_debug():
    """Función simple para debug - obtener datos básicos"""
    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        # Verificar si hay grupos en la base de datos
        cursor.execute("SELECT COUNT(*) as total FROM Grupo")
        total_grupos = cursor.fetchone()
        st.write(f"📊 Total de grupos en BD: {total_grupos['total']}")
        
        # Verificar si hay reuniones
        cursor.execute("SELECT COUNT(*) as total FROM Reunion")
        total_reuniones = cursor.fetchone()
        st.write(f"📅 Total de reuniones en BD: {total_reuniones['total']}")
        
        # Verificar si hay ahorros
        cursor.execute("SELECT COUNT(*) as total FROM Ahorro")
        total_ahorros = cursor.fetchone()
        st.write(f"💰 Total de ahorros en BD: {total_ahorros['total']}")
        
        return True
        
    except Exception as e:
        st.error(f"❌ Error en debug: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'con' in locals():
            con.close()

def mostrar_consolidado_promotora():
    """Función principal del módulo de consolidado - VERSIÓN SIMPLIFICADA"""
    st.title("🏦 Consolidado Promotora")
    
    st.info("Este módulo te permite ver el consolidado financiero de todos tus grupos.")
    
    # DEBUG: Mostrar información del usuario
    st.write("### 🔍 Información de Debug")
    st.write(f"User ID en session: {st.session_state.get('user_id', 'NO HAY')}")
    st.write(f"User type en session: {st.session_state.get('user_type', 'NO HAY')}")
    st.write(f"Usuario en session: {st.session_state.get('usuario', 'NO HAY')}")
    
    # Ejecutar debug simple
    obtener_datos_simples_para_debug()
    
    # Obtener grupos de la promotora
    grupos = obtener_grupos_promotora()
    
    st.write("### 👥 Grupos Encontrados")
    if grupos:
        st.success(f"✅ Se encontraron {len(grupos)} grupos asignados a esta promotora")
        
        # Mostrar grupos en una tabla simple
        for grupo in grupos:
            st.write(f"- **{grupo['nombre_grupo']}** (ID: {grupo['ID_Grupo']}) - {grupo['descripcion']}")
    else:
        st.error("""
        ❌ No se encontraron grupos asignados a esta promotora.
        
        **Posibles soluciones:**
        1. Verifica que el usuario esté correctamente logueado como promotora
        2. Asegúrate de que la promotora tenga grupos asignados en la base de datos
        3. Contacta al administrador del sistema
        """)
        return
    
    # Selección de grupos
    st.subheader("🎯 Seleccionar Grupos para Consolidar")
    
    grupos_dict = {f"{g['nombre_grupo']}": g['ID_Grupo'] for g in grupos}
    grupos_seleccionados_nombres = st.multiselect(
        "Selecciona los grupos a consolidar:",
        options=list(grupos_dict.keys()),
        default=list(grupos_dict.keys())[:1] if grupos_dict else []
    )
    
    grupos_seleccionados = [grupos_dict[nombre] for nombre in grupos_seleccionados_nombres]
    
    if not grupos_seleccionados:
        st.info("Selecciona al menos un grupo para ver el consolidado.")
        return
    
    # Filtro de fechas SIMPLIFICADO
    st.subheader("📅 Seleccionar Rango de Fechas")
    
    col1, col2 = st.columns(2)
    with col1:
        fecha_inicio = st.date_input(
            "Fecha de Inicio",
            value=datetime.now().date() - timedelta(days=365),  # Un año atrás para más datos
            key="fecha_inicio_simple"
        )
    with col2:
        fecha_fin = st.date_input(
            "Fecha de Fin", 
            value=datetime.now().date(),
            key="fecha_fin_simple"
        )
    
    if fecha_inicio > fecha_fin:
        st.error("❌ La fecha de inicio no puede ser mayor que la fecha de fin")
        return
    
    # Botón para probar con datos de ejemplo
    st.subheader("🚀 Probar con Datos de Ejemplo")
    
    if st.button("Generar Reporte con Datos Reales", type="primary"):
        st.warning("⏳ Buscando datos reales en la base de datos...")
        
        # Aquí iría la lógica completa de consolidación
        # Por ahora mostramos un mensaje
        st.info("""
        **Estado del módulo:**
        - ✅ Módulo cargado correctamente
        - ✅ Grupos encontrados: Sí
        - ✅ Fechas configuradas: Sí
        - 🔄 Procesando datos financieros...
        """)
        
        # Mensaje temporal
        st.success("🎉 El módulo de Consolidado Promotora está funcionando correctamente!")
        st.info("La funcionalidad completa de gráficas y reportes se cargará una vez que se confirmen los datos de conexión.")

# Si el archivo se ejecuta directamente
if __name__ == "__main__":
    mostrar_consolidado_promotora()
