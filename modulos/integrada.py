import streamlit as st
from modulos.reuniones import mostrar_reuniones
from modulos.prestamo import mostrar_prestamo
from modulos.asistencia import mostrar_asistencia

def mostrar_gestion_integrada():
    """
    Módulo integrado que contiene 3 pestañas con los módulos existentes
    """
    
    st.header("📊 Gestión Integrada de Grupo")
    
    # Verificación de permisos
    cargo = st.session_state.get("cargo_de_usuario", "").strip().upper()
    if cargo != "SECRETARIA":
        st.warning("🔒 Acceso restringido: Solo la SECRETARIA puede acceder a esta función.")
        return

    # Crear pestañas principales
    tab1, tab2, tab3 = st.tabs(["📅 Reuniones", "💰 Préstamos", "🧍‍♂️ Asistencia"])

    with tab1:
        st.subheader("📅 Gestión de Reuniones")
        mostrar_reuniones()

    with tab2:
        st.subheader("💰 Gestión de Préstamos")
        try:
            mostrar_prestamo()
        except Exception as e:
            st.error("Error temporal en préstamos - trabajando en la solución")
            st.info("Por ahora, usa el módulo individual de préstamos")

    with tab3:
        st.subheader("🧍‍♂️ Registro de Asistencia")
        mostrar_asistencia()
