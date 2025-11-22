import streamlit as st
from modulos.reuniones import mostrar_reuniones
from modulos.prestamo import mostrar_prestamo
from modulos.asistencia import mostrar_asistencia
from modulos.ahorros import mostrar_ahorros  # ✅ Nuevo módulo agregado

def mostrar_gestion_integrada():
    """
    Módulo integrado que contiene 4 pestañas con los módulos existentes
    """
    
    st.header("📊 Gestión Integrada de Grupo")
    
    # Verificación de permisos
    cargo = st.session_state.get("cargo_de_usuario", "").strip().upper()
    if cargo != "SECRETARIA":
        st.warning("🔒 Acceso restringido: Solo la SECRETARIA puede acceder a esta función.")
        return

    # Crear pestañas principales - ahora con 4 pestañas
    tab1, tab2, tab3, tab4 = st.tabs([
        "📅 Reuniones", 
        "🧍‍♂️ Asistencia", 
        "💰 Préstamos",
        "💵 Ahorros"  # ✅ Nueva pestaña agregada
    ])

    with tab1:
        st.subheader("📅 Gestión de Reuniones")
        mostrar_reuniones()

    with tab2:
        st.subheader("🧍‍♂️ Registro de Asistencia")
        mostrar_asistencia()

    with tab3:
        st.subheader("💰 Gestión de Préstamos")
        try:
            mostrar_prestamo()
        except Exception as e:
            st.error("Error temporal en préstamos - trabajando en la solución")
            st.info("Por ahora, usa el módulo individual de préstamos")

    with tab4:  # ✅ Nueva pestaña para ahorros
        st.subheader("💵 Gestión de Ahorros")
        try:
            mostrar_ahorros()
        except Exception as e:
            st.error(f"Error al cargar módulo de ahorros: {e}")
            st.info("Por favor, usa el módulo individual de ahorros")
