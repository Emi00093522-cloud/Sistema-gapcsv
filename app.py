import streamlit as st
from modulos.registro_usuario import registrar_usuario
from modulos.login import login
from modulos.promotora import mostrar_promotora
from modulos.distrito import mostrar_distrito
from modulos.asistencia import mostrar_asistencia
from modulos.integrada import mostrar_gestion_integrada
from modulos.grupos import mostrar_grupos
from modulos.reglamentos import mostrar_reglamentos
from modulos.miembros import mostrar_miembro

# ---------------------------------------------------------
# 🔧 DEBUG MEJORADO PARA DETECTAR ERRORES DE IMPORTACIÓN
# ---------------------------------------------------------

# Importación del módulo ciclo
try:
    from modulos.ciclo import mostrar_ciclo
    CICLO_CARGADO = True
except ImportError as e:
    st.sidebar.error(f"❌ Error cargando ciclo: {e}")
    def mostrar_ciclo():
        st.warning("Módulo de Cierre de Ciclo en desarrollo")
    CICLO_CARGADO = False

# Importación del módulo préstamo  
try:
    from modulos.prestamo import mostrar_prestamo
    PRESTAMO_CARGADO = True
except ImportError:
    def mostrar_prestamo():
        st.warning("Módulo de Préstamos en desarrollo")
    PRESTAMO_CARGADO = False

# 🔥🔥🔥 NUEVO IMPORT CON DEBUG SUPER DETALLADO PARA CONSOLIDADO_PROMOTORA
try:
    st.sidebar.write("🔄 **DEBUG:** Intentando importar consolidado_promotora...")
    
    # Intento 1: Import normal
    from modulos.consolidado_promotora import mostrar_consolidado_promotora
    CONSOLIDADO_CARGADO = True
    st.sidebar.success("✅ **DEBUG:** consolidado_promotora IMPORTADO EXITOSAMENTE")
    
except ImportError as e:
    st.sidebar.error(f"❌ **DEBUG ERROR:** No se pudo importar consolidado_promotora")
    st.sidebar.error(f"🔍 **Error detallado:** {e}")
    CONSOLIDADO_CARGADO = False
    
    # Función de emergencia con DEBUG COMPLETO
    def mostrar_consolidado_promotora():
        st.error("🚫 **Módulo Consolidado Promotora - ERROR DE CARGA**")
        
        st.write("### 🔍 DEBUG DETALLADO DEL ERROR:")
        
        # Información del sistema
        st.write("#### 📁 Información del Sistema:")
        import os
        import sys
        st.write(f"**Directorio actual:** {os.getcwd()}")
        st.write(f"**Ruta de Python:** {sys.path}")
        
        # Verificar si el archivo existe
        archivo_path = os.path.join("modulos", "consolidado_promotora.py")
        st.write(f"**Buscando archivo en:** {archivo_path}")
        st.write(f"**¿Existe el archivo?:** {os.path.exists(archivo_path)}")
        
        # Intentar leer el archivo
        if os.path.exists(archivo_path):
            try:
                with open(archivo_path, 'r', encoding='utf-8') as f:
                    primeras_lineas = [next(f) for _ in range(10)]
                st.write("**Primeras 10 líneas del archivo:**")
                for i, linea in enumerate(primeras_lineas, 1):
                    st.write(f"{i}: {linea.strip()}")
            except Exception as file_error:
                st.error(f"Error leyendo archivo: {file_error}")
        
        # Soluciones
        st.write("#### 🔧 SOLUCIONES:")
        st.write("""
        1. **Verifica que el archivo existe** en `modulos/consolidado_promotora.py`
        2. **Verifica que no tenga errores de sintaxis** - ejecuta: `python modulos/consolidado_promotora.py`
        3. **Verifica los imports internos** del módulo
        4. **Reinicia Streamlit** completamente
        """)
        
        # Botón para diagnóstico automático
        if st.button("🔄 EJECUTAR DIAGNÓSTICO AUTOMÁTICO"):
            try:
                # Intentar diagnóstico
                import subprocess
                result = subprocess.run([
                    'python', '-c', 
                    'from modulos.consolidado_promotora import mostrar_consolidado_promotora; print("✅ Módulo carga correctamente")'
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    st.success("✅ Diagnóstico: El módulo debería funcionar")
                    st.write("**Output:**", result.stdout)
                else:
                    st.error("❌ Diagnóstico: Error en el módulo")
                    st.write("**Error:**", result.stderr)
                    
            except Exception as diag_error:
                st.error(f"Error en diagnóstico: {diag_error}")

except Exception as e:
    st.sidebar.error(f"❌ **ERROR INESPERADO:** {e}")
    def mostrar_consolidado_promotora():
        st.error(f"Error crítico: {e}")
    CONSOLIDADO_CARGADO = False

# 🔥🔥🔥 NUEVO IMPORT PARA CONSOLIDADO_ADMINISTRADOR
try:
    st.sidebar.write("🔄 **DEBUG:** Intentando importar consolidado_administrador...")
    
    from modulos.consolidado_administrador import mostrar_consolidado_administrador
    CONSOLIDADO_ADMIN_CARGADO = True
    st.sidebar.success("✅ **DEBUG:** consolidado_administrador IMPORTADO EXITOSAMENTE")
    
except ImportError as e:
    st.sidebar.error(f"❌ **DEBUG ERROR:** No se pudo importar consolidado_administrador")
    st.sidebar.error(f"🔍 **Error detallado:** {e}")
    CONSOLIDADO_ADMIN_CARGADO = False
    
    # Función de emergencia para consolidado administrador
    def mostrar_consolidado_administrador():
        st.error("🚫 **Módulo Consolidado Administrador - ERROR DE CARGA**")
        
        st.write("### 🔍 DEBUG DETALLADO DEL ERROR:")
        
        # Información del sistema
        import os
        import sys
        st.write(f"**Directorio actual:** {os.getcwd()}")
        
        # Verificar si el archivo existe
        archivo_path = os.path.join("modulos", "consolidado_administrador.py")
        st.write(f"**Buscando archivo en:** {archivo_path}")
        st.write(f"**¿Existe el archivo?:** {os.path.exists(archivo_path)}")
        
        # Soluciones
        st.write("#### 🔧 SOLUCIONES:")
        st.write("""
        1. **Crea el archivo** `modulos/consolidado_administrador.py`
        2. **Verifica que tenga el código correcto**
        3. **Reinicia Streamlit** completamente
        """)
        
        # Botón para crear archivo de ejemplo
        if st.button("📝 CREAR ARCHIVO DE EJEMPLO"):
            try:
                codigo_ejemplo = '''
import streamlit as st
import pandas as pd

def mostrar_consolidado_administrador():
    """Módulo de consolidado para administradora - mostrará datos de TODOS los grupos"""
    st.title("👑 Consolidado General - Administradora")
    st.info("📊 Este módulo mostrará el consolidado de TODOS los grupos del sistema")
    
    # Aquí irá el código completo del consolidado para administradora
    st.warning("🔧 Módulo en desarrollo - Próximamente mostrará datos completos del sistema")
    
    # Placeholder para demostración
    st.subheader("📈 Métricas del Sistema (Ejemplo)")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Grupos", "25")
    with col2:
        st.metric("Total Miembros", "380")
    with col3:
        st.metric("Total Ahorros", "$45,230.00")
    with col4:
        st.metric("Total Préstamos", "$28,150.00")
'''
                
                with open(archivo_path, 'w', encoding='utf-8') as f:
                    f.write(codigo_ejemplo)
                
                st.success(f"✅ Archivo creado en: {archivo_path}")
                st.info("🔄 Recarga la página para cargar el módulo")
                
            except Exception as file_error:
                st.error(f"Error creando archivo: {file_error}")

except Exception as e:
    st.sidebar.error(f"❌ **ERROR INESPERADO en consolidado_administrador:** {e}")
    def mostrar_consolidado_administrador():
        st.error(f"Error crítico en módulo administrador: {e}")
    CONSOLIDADO_ADMIN_CARGADO = False

# ---------------------------------------------------------
# 🔧 FIX SOLO PARA VISIBILIDAD DE TEXTO EN SELECT / INPUTS
# ---------------------------------------------------------
st.markdown("""
<style>
/* Texto dentro de inputs */
input, textarea { color: #000 !important; }

/* Texto visible en select actual */
.stSelectbox div[data-baseweb="select"] * { color: #000 !important; }

/* Texto visible en opciones desplegadas */
ul[role="listbox"] li { color: #000 !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------
st.set_page_config(page_title="Sistema GAPCSV", page_icon="💙", layout="wide")

if "sesion_iniciada" not in st.session_state:
    st.session_state["sesion_iniciada"] = False
if "pagina_actual" not in st.session_state:
    st.session_state["pagina_actual"] = "inicio"

# ---------------------------------------------------------
# PANEL SECRETARIA
# ---------------------------------------------------------
def panel_secretaria():
    st.title("💼 Panel de Secretaria")

    tabs = st.tabs([
        "👥 Registrar Grupo",
        "👥 Miembros",
        "📜 Reglamentos",
        "📅 Reuniones",
        "🔄 Cierre de Ciclo",
        "🚪 Cerrar sesión"
    ])

    with tabs[0]: mostrar_grupos()
    with tabs[1]: mostrar_miembro()
    with tabs[2]: mostrar_reglamentos()
    with tabs[3]: mostrar_gestion_integrada()
    with tabs[4]: mostrar_ciclo()

    with tabs[5]:
        if st.button("Cerrar sesión"):
            st.session_state.clear()
            st.session_state["pagina_actual"] = "sesion_cerrada"
            st.rerun()

# ---------------------------------------------------------
# PANEL PRESIDENTE
# ---------------------------------------------------------
def panel_presidente():
    st.title("👑 Panel de Presidente")

    tabs = st.tabs([
        "👥 Registrar Grupo",
        "👥 Miembros",
        "📜 Reglamentos",
        "💰 Préstamos",
        "🔄 Cierre de Ciclo",
        "🚪 Cerrar sesión"
    ])

    with tabs[0]: mostrar_grupos()
    with tabs[1]: mostrar_miembro()
    with tabs[2]: mostrar_reglamentos()
    with tabs[3]: mostrar_prestamo()
    with tabs[4]: mostrar_ciclo()

    with tabs[5]:
        if st.button("Cerrar sesión"):
            st.session_state.clear()
            st.session_state["pagina_actual"] = "sesion_cerrada"
            st.rerun()

# ---------------------------------------------------------
# PANEL PROMOTORA - CON DEBUG MEJORADO
# ---------------------------------------------------------
def panel_promotora(usuario):
    st.title("🤝 Panel de Promotora")

    # DEBUG INFO EN EL PANEL PRINCIPAL
    if not CONSOLIDADO_CARGADO:
        st.error("🚫 **ADVERTENCIA:** El módulo Consolidado Promotora no se cargó correctamente")
    
    tabs = st.tabs([
        "📈 Dashboard",
        "👩‍💼 Registro Promotora", 
        "🏛️ Distrito",
        "📊 Consolidado Promotora",
        "🚪 Cerrar sesión"
    ])

    with tabs[0]:
        st.success(f"Bienvenida, {usuario} 🌟")
        st.info("📊 Dashboard general de promotoras en desarrollo...")
        
        # Estado de módulos
        st.write("### 🔧 Estado de Módulos:")
        col1, col2, col3 = st.columns(3)
        with col1:
            status = "✅ Cargado" if CICLO_CARGADO else "❌ Error"
            st.metric("Módulo Ciclo", status)
        with col2:
            status = "✅ Cargado" if PRESTAMO_CARGADO else "⚠️ Desarrollo"
            st.metric("Módulo Préstamos", status)
        with col3:
            status = "✅ Cargado" if CONSOLIDADO_CARGADO else "❌ ERROR"
            st.metric("Módulo Consolidado", status)

    with tabs[1]: mostrar_promotora()
    with tabs[2]: mostrar_distrito()
    
    with tabs[3]: 
        if CONSOLIDADO_CARGADO:
            st.success("✅ Módulo Consolidado Promotora - CARGADO")
            mostrar_consolidado_promotora()
        else:
            st.error("❌ **ERROR CRÍTICO:** El módulo no se pudo cargar")
            st.info("Revisa la información de debug en el sidebar para más detalles")
            
            # Forzar recarga
            if st.button("🔄 FORZAR RECARGA DEL MÓDULO"):
                st.rerun()

    with tabs[4]:
        if st.button("Cerrar sesión"):
            st.session_state.clear()
            st.session_state["pagina_actual"] = "sesion_cerrada"
            st.rerun()

# ---------------------------------------------------------
# PANEL ADMINISTRADORA - ACTUALIZADO CON CONSOLIDADO
# ---------------------------------------------------------
def panel_admin():
    st.title("🛡️ Panel de Administradora")

    tabs = st.tabs([
        "📊 Consolidado Distritos",
        "🧑‍💻 Registrar Usuario", 
        "🚪 Cerrar sesión"
    ])

    with tabs[0]:
        if CONSOLIDADO_ADMIN_CARGADO:
            st.success("✅ Módulo Consolidado Administrador - CARGADO")
            mostrar_consolidado_administrador()
        else:
            st.error("❌ **ERROR:** El módulo Consolidado Administrador no se pudo cargar")
            st.info("""
            **Para solucionar este problema:**
            
            1. **Crea el archivo** `modulos/consolidado_administrador.py`
            2. **Copia el código** del módulo de consolidado para administradora
            3. **Reinicia Streamlit** completamente
            
            **El módulo mostrará:**
            - 📊 Consolidado de TODOS los grupos
            - 📈 Gráficos generales del sistema  
            - 🏢 Distribución por distritos
            - 💰 Totales de ahorros, préstamos, multas
            """)
            
            # Mostrar información básica como placeholder
            st.subheader("📋 Información del Sistema (Placeholder)")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Grupos Activos", "15")
            with col2:
                st.metric("Total Miembros", "245")
            with col3:
                st.metric("Ahorros Totales", "$32,580.00")
            with col4:
                st.metric("Préstamos Activos", "$18,750.00")

    with tabs[1]: 
        registrar_usuario()

    with tabs[2]:
        if st.button("Cerrar sesión"):
            st.session_state.clear()
            st.session_state["pagina_actual"] = "sesion_cerrada"
            st.rerun()

# ---------------------------------------------------------
# FLUJO PRINCIPAL
# ---------------------------------------------------------
if st.session_state["sesion_iniciada"]:

    usuario = st.session_state.get("usuario", "Usuario")
    tipo = (st.session_state.get("tipo_usuario", "") or "").lower()
    cargo = (st.session_state.get("cargo_de_usuario", "") or "").upper()

    # DEBUG INFO EN SIDEBAR
    st.sidebar.write("### 👤 Información de Sesión")
    st.sidebar.write(f"**Usuario:** {usuario}")
    st.sidebar.write(f"**Tipo:** {tipo}")
    st.sidebar.write(f"**Cargo:** {cargo}")
    
    # Estado de módulos en sidebar
    st.sidebar.write("### 🔧 Estado de Módulos")
    st.sidebar.write(f"**Consolidado Promotora:** {'✅' if CONSOLIDADO_CARGADO else '❌'}")
    st.sidebar.write(f"**Consolidado Admin:** {'✅' if CONSOLIDADO_ADMIN_CARGADO else '❌'}")
    
    if "id_promotora" in st.session_state:
        st.sidebar.success(f"**ID Promotora:** {st.session_state.id_promotora}")
    else:
        st.sidebar.warning("⚠️ No hay id_promotora en session_state")

    if cargo == "SECRETARIA":
        panel_secretaria()
    elif cargo == "PRESIDENTE":
        panel_presidente()
    elif tipo == "promotora" or cargo == "PROMOTORA":
        panel_promotora(usuario)
    elif cargo == "ADMINISTRADOR":
        panel_admin()
    else:
        st.error("⚠️ Tipo de usuario no reconocido.")

else:
    if st.session_state["pagina_actual"] == "sesion_cerrada":
        st.success("Sesión finalizada.")
        if st.button("Volver al inicio"):
            st.session_state["pagina_actual"] = "inicio"
            st.rerun()

    elif st.session_state["pagina_actual"] == "inicio":
        st.title("Bienvenida al Sistema GAPCSV")
        st.subheader("Grupos de Ahorro y Préstamos Comunitarios 🤝🌱💰")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔑 Iniciar sesión"):
                st.session_state["pagina_actual"] = "login"
                st.rerun()

        with col2:
            if st.button("📝 Registrarme"):
                st.session_state["pagina_actual"] = "registro"
                st.rerun()

    elif st.session_state["pagina_actual"] == "login":
        login()
    
    elif st.session_state["pagina_actual"] == "registro":
        registrar_usuario()
