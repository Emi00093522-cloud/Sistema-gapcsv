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
# 🔧 IMPORTS MEJORADOS CON MANEJO DE ERRORES DETALLADO
# ---------------------------------------------------------

# Importación del módulo ciclo
try:
    from modulos.ciclo import mostrar_ciclo
    CICLO_DISPONIBLE = True
except ImportError as e:
    st.sidebar.warning(f"⚠️ Módulo ciclo no disponible: {e}")
    def mostrar_ciclo():
        st.warning("Módulo de Cierre de Ciclo en desarrollo")
    CICLO_DISPONIBLE = False

# Importación del módulo préstamo
try:
    from modulos.prestamo import mostrar_prestamo
    PRESTAMO_DISPONIBLE = True
except ImportError as e:
    st.sidebar.warning(f"⚠️ Módulo préstamo no disponible: {e}")
    def mostrar_prestamo():
        st.warning("Módulo de Préstamos en desarrollo")
    PRESTAMO_DISPONIBLE = False

# Importación del módulo consolidado promotora - CON DEBUG DETALLADO
try:
    # Intento 1: Importar directamente
    from modulos.consolidado_promotora import mostrar_consolidado_promotora
    CONSOLIDADO_DISPONIBLE = True
    st.sidebar.success("✅ Módulo Consolidado Promotora cargado")
    
except ImportError as e:
    st.sidebar.error(f"❌ Error importando consolidado_promotora: {e}")
    CONSOLIDADO_DISPONIBLE = False
    
    # Función temporal con debug detallado
    def mostrar_consolidado_promotora():
        st.error("🚫 Módulo Consolidado Promotora - ERROR DE CARGA")
        
        with st.expander("🔍 Debug Detallado - Click para ver"):
            st.write("### 🐛 Información del Error")
            st.code(f"Error: {e}", language='python')
            
            st.write("### 📁 Estructura esperada:")
            st.code("""
tu_proyecto/
├── app.py
├── modulos/
│   ├── __init__.py
│   ├── consolidado_promotora.py  ← Debe existir este archivo
│   └── ...
            """)
            
            st.write("### 🔧 Soluciones:")
            st.write("""
            1. **Verifica que el archivo existe:**
               - Asegúrate de que `modulos/consolidado_promotora.py` existe
               
            2. **Verifica el contenido del archivo:**
               - El archivo debe tener una función llamada `mostrar_consolidado_promotora()`
               
            3. **Verifica que no tenga errores de sintaxis:**
               - Ejecuta el archivo directamente para ver si tiene errores
               
            4. **Verifica los imports internos:**
               - El módulo podría estar fallando en sus propios imports
            """)
            
            # Botón para probar carga manual
            if st.button("🔄 Intentar cargar módulo manualmente"):
                try:
                    import importlib
                    import sys
                    import os
                    
                    # Agregar ruta de módulos
                    sys.path.append(os.path.dirname(__file__))
                    
                    # Intentar importar manualmente
                    from modulos.consolidado_promotora import mostrar_consolidado_promotora
                    st.success("✅ ¡Módulo cargado manualmente!")
                    st.rerun()
                    
                except Exception as manual_error:
                    st.error(f"❌ Error en carga manual: {manual_error}")

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
    with tabs[3]: mostrar_prestamo() if PRESTAMO_DISPONIBLE else st.warning("Módulo préstamos no disponible")
    with tabs[4]: mostrar_ciclo()

    with tabs[5]:
        if st.button("Cerrar sesión"):
            st.session_state.clear()
            st.session_state["pagina_actual"] = "sesion_cerrada"
            st.rerun()

# ---------------------------------------------------------
# PANEL PROMOTORA - CON Consolidado Promotora
# ---------------------------------------------------------
def panel_promotora(usuario):
    st.title("🤝 Panel de Promotora")

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
        
        # Mostrar estado de módulos
        st.write("### 🔧 Estado de Módulos")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Ciclo", "✅" if CICLO_DISPONIBLE else "❌")
        with col2:
            st.metric("Préstamos", "✅" if PRESTAMO_DISPONIBLE else "❌")
        with col3:
            st.metric("Consolidado", "✅" if CONSOLIDADO_DISPONIBLE else "❌")

    with tabs[1]: mostrar_promotora()
    with tabs[2]: mostrar_distrito()
    
    with tabs[3]: 
        if CONSOLIDADO_DISPONIBLE:
            mostrar_consolidado_promotora()
        else:
            st.error("❌ El módulo de Consolidado Promotora no está disponible")
            if st.button("🔄 Reintentar carga de módulo"):
                st.rerun()

    with tabs[4]:
        if st.button("Cerrar sesión"):
            st.session_state.clear()
            st.session_state["pagina_actual"] = "sesion_cerrada"
            st.rerun()

# ---------------------------------------------------------
# PANEL ADMINISTRADORA - SIN Cierre de Ciclo
# ---------------------------------------------------------
def panel_admin():
    st.title("🛡️ Panel de Administradora")

    tabs = st.tabs([
        "📊 Consolidado Distritos",
        "🧑‍💻 Registrar Usuario",
        "🚪 Cerrar sesión"
    ])

    with tabs[0]:
        st.info("📊 Aquí irá el consolidado general por distrito.")
        
        # Mostrar estado de módulos para admin
        st.write("### 🔧 Estado de Módulos del Sistema")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Ciclo", "✅" if CICLO_DISPONIBLE else "❌")
        with col2:
            st.metric("Préstamos", "✅" if PRESTAMO_DISPONIBLE else "❌")
        with col3:
            st.metric("Consolidado", "✅" if CONSOLIDADO_DISPONIBLE else "❌")

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

    # DEBUG: Mostrar información de sesión en sidebar
    st.sidebar.write("### 👤 Información de Sesión")
    st.sidebar.write(f"Usuario: {usuario}")
    st.sidebar.write(f"Tipo: {tipo}")
    st.sidebar.write(f"Cargo: {cargo}")
    
    if "id_promotora" in st.session_state:
        st.sidebar.write(f"ID Promotora: {st.session_state.id_promotora}")

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
        st.write(f"Debug - Tipo: '{tipo}', Cargo: '{cargo}'")

else:
    if st.session_state["pagina_actual"] == "sesion_cerrada":
        st.success("Sesión finalizada.")
        if st.button("Volver al inicio"):
            st.session_state["pagina_actual"] = "inicio"
            st.rerun()

    elif st.session_state["pagina_actual"] == "inicio":
        st.title("Bienvenida al Sistema GAPCSV")
        st.subheader("Grupos de Ahorro y Préstamos Comunitarios 🤝🌱💰")

        # Mostrar estado de módulos en página de inicio
        with st.expander("🔧 Estado del Sistema"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write("**Ciclo:**", "✅ Disponible" if CICLO_DISPONIBLE else "❌ En desarrollo")
            with col2:
                st.write("**Préstamos:**", "✅ Disponible" if PRESTAMO_DISPONIBLE else "❌ En desarrollo")
            with col3:
                st.write("**Consolidado:**", "✅ Disponible" if CONSOLIDADO_DISPONIBLE else "❌ En desarrollo")

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
