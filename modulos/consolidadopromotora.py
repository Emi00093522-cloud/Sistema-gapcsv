import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import calendar

# =============================================
#  VERSIÓN DEBUG - PARA IDENTIFICAR EL PROBLEMA
# =============================================

def debug_session_state():
    """Muestra el estado actual de session_state para debugging"""
    st.sidebar.write("### 🔍 DEBUG - Session State")
    for key, value in st.session_state.items():
        st.sidebar.write(f"**{key}:** {value}")

def obtener_id_promotora_desde_usuario():
    """
    Obtiene el ID de promotora basado en el usuario logueado.
    Versión debug que muestra qué está buscando.
    """
    st.write("### 🔍 PASO 1: Buscando ID de promotora")
    
    # Mostrar qué hay en session_state
    st.write("**Session State actual:**")
    st.json({k: v for k, v in st.session_state.items()})
    
    # Obtener el ID del usuario logueado
    id_usuario = st.session_state.get("id_usuario")
    st.write(f"**ID Usuario encontrado:** {id_usuario}")
    
    if not id_usuario:
        st.error("❌ No hay 'id_usuario' en session_state")
        return None
    
    try:
        from modulos.config.conexion import obtener_conexion
        
        st.write("### 🔍 PASO 2: Consultando base de datos")
        
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        # PRIMERO: Verificar si existe la tabla Promotora
        cursor.execute("SHOW TABLES LIKE 'Promotora'")
        tabla_existe = cursor.fetchone()
        st.write(f"**¿Tabla Promotora existe?:** {bool(tabla_existe)}")
        
        if tabla_existe:
            # Buscar la promotora asociada a este usuario
            query = "SELECT * FROM Promotora WHERE ID_Usuario = %s"
            st.write(f"**Query ejecutado:** {query % id_usuario}")
            
            cursor.execute(query, (id_usuario,))
            resultado = cursor.fetchone()
            
            st.write("**Resultado de la consulta:**")
            st.json(resultado if resultado else "NO HAY RESULTADOS")
            
            if resultado:
                st.success(f"✅ Promotora encontrada: ID {resultado['ID_Promotora']}")
                return resultado['ID_Promotora']
            else:
                st.error("❌ No se encontró promotora para este usuario")
                st.info("""
                **Posibles soluciones:**
                1. El usuario no está registrado como promotora
                2. El campo en la tabla se llama diferente (ej: id_usuario vs ID_Usuario)
                3. No hay relación entre usuario y promotora
                """)
        else:
            st.error("❌ La tabla 'Promotora' no existe en la base de datos")
            
        cursor.close()
        con.close()
        
        return None
        
    except Exception as e:
        st.error(f"❌ Error en la consulta: {e}")
        import traceback
        st.code(traceback.format_exc())
        return None

def obtener_grupos_promotora_debug(id_promotora):
    """Versión debug para obtener grupos"""
    st.write("### 🔍 PASO 3: Buscando grupos de la promotora")
    st.write(f"**ID Promotora:** {id_promotora}")
    
    try:
        from modulos.config.conexion import obtener_conexion
        
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        # Verificar estructura de la tabla Grupo
        cursor.execute("DESCRIBE Grupo")
        estructura_grupo = cursor.fetchall()
        
        st.write("**Estructura de la tabla Grupo:**")
        st.dataframe(estructura_grupo)
        
        # Buscar grupos
        query = "SELECT * FROM Grupo WHERE ID_Promotora = %s"
        st.write(f"**Query ejecutado:** {query % id_promotora}")
        
        cursor.execute(query, (id_promotora,))
        grupos = cursor.fetchall()
        
        st.write(f"**Grupos encontrados:** {len(grupos)}")
        if grupos:
            st.dataframe(grupos)
        else:
            st.warning("⚠️ No se encontraron grupos para esta promotora")
            
        cursor.close()
        con.close()
        
        return grupos
        
    except Exception as e:
        st.error(f"❌ Error obteniendo grupos: {e}")
        return []

def mostrar_consolidado_promotora_debug():
    """Versión debug del consolidado"""
    
    st.title("🔍 Módulo de Consolidado - MODO DEBUG")
    
    # Mostrar estado de session_state
    debug_session_state()
    
    st.write("---")
    st.write("## 🚀 Iniciando proceso de consolidado...")
    
    # PASO 1: Obtener ID de promotora
    id_promotora = obtener_id_promotora_desde_usuario()
    
    if not id_promotora:
        st.error("""
        ❌ **NO SE PUEDE CONTINUAR**
        
        **Problemas identificados:**
        1. Usuario no tiene ID en session_state
        2. Usuario no está registrado como promotora  
        3. La tabla Promotora no existe o tiene diferente estructura
        
        **Solución temporal para pruebas:**
        """)
        
        # Input manual para testing
        id_promotora_manual = st.number_input(
            "Ingresa manualmente un ID de promotora para testing:", 
            min_value=1, value=1
        )
        
        if st.button("Usar este ID para testing"):
            st.session_state.debug_promotora_id = id_promotora_manual
            st.rerun()
            
        if "debug_promotora_id" in st.session_state:
            id_promotora = st.session_state.debug_promotora_id
            st.info(f"🔧 Usando ID de promotora manual: {id_promotora}")
        else:
            return
    
    # PASO 2: Obtener grupos
    grupos = obtener_grupos_promotora_debug(id_promotora)
    
    if not grupos:
        st.error("❌ No hay grupos para mostrar")
        return
    
    # PASO 3: Mostrar interfaz normal
    st.success("✅ ¡Todo listo! Mostrando consolidado...")
    st.write("---")
    
    # Aquí continuaría tu interfaz normal...
    mostrar_interfaz_normal(grupos)

def mostrar_interfaz_normal(grupos):
    """Interfaz normal una vez que tenemos los datos"""
    
    st.title("📊 Consolidado de Grupos - Promotora")
    
    # Selector de año
    año_actual = datetime.now().year
    año_seleccionado = st.sidebar.selectbox(
        "Seleccionar Año",
        [año_actual - 1, año_actual, año_actual + 1],
        index=1
    )
    
    # Resumen simple
    st.subheader("📈 Resumen de Grupos")
    
    # Crear datos de ejemplo para demostración
    datos_ejemplo = []
    for grupo in grupos:
        datos_ejemplo.append({
            'Grupo': grupo.get('nombre_grupo', f"Grupo {grupo.get('ID_Grupo', 'N/A')}"),
            'Miembros': grupo.get('total_miembros', 0),
            'Ingresos Ejemplo': f"${len(grupo) * 1000:,.2f}",
            'Estado': '🟢 Activo'
        })
    
    df_resumen = pd.DataFrame(datos_ejemplo)
    st.dataframe(df_resumen, use_container_width=True)
    
    # Gráfica de ejemplo
    st.subheader("📊 Gráfica de Ejemplo")
    
    if len(grupos) > 0:
        # Datos para gráfica
        nombres_grupos = [g.get('nombre_grupo', f"Grupo {g.get('ID_Grupo')}") for g in grupos]
        ingresos_ejemplo = [len(g) * 1000 for g in grupos]  # Datos de ejemplo
        
        fig = px.bar(
            x=nombres_grupos,
            y=ingresos_ejemplo,
            title="Ingresos por Grupo (Ejemplo)",
            labels={'x': 'Grupos', 'y': 'Ingresos ($)'},
            color=ingresos_ejemplo,
            color_continuous_scale='Viridis'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay suficientes datos para mostrar gráficas")
    
    # Información para el usuario
    st.info("""
    **💡 Esta es una vista de demostración.**
    Para ver datos reales, necesitamos:
    1. Que tu usuario esté correctamente asociado a una promotora
    2. Que la promotora tenga grupos asignados
    3. Que existan datos financieros en las tablas correspondientes
    """)

# =============================================
#  FUNCIÓN PRINCIPAL
# =============================================

def main():
    """Función principal"""
    
    # Verificar si estamos en modo debug
    if st.sidebar.checkbox("🔍 Modo Debug", value=True):
        mostrar_consolidado_promotora_debug()
    else:
        # Intentar modo normal
        try:
            from consolidados_original import mostrar_consolidado_promotora
            mostrar_consolidado_promotora()
        except:
            st.error("No se pudo cargar el módulo normal. Usando modo debug.")
            mostrar_consolidado_promotora_debug()

if __name__ == "__main__":
    main()
