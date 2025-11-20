import streamlit as st
from modulos.reuniones import mostrar_reuniones
from modulos.prestamo import mostrar_prestamo
from modulos.asistencia import mostrar_asistencia

def mostrar_gestion_integrada():
    """
    Módulo integrado que contiene 3 pestañas con los módulos existentes:
    1. Reuniones
    2. Préstamos  
    3. Asistencia
    """
    
    st.header("📊 Gestión Integrada de Grupo")
    
    # Verificación de permisos
    cargo = st.session_state.get("cargo_de_usuario", "").strip().upper()
    if cargo != "SECRETARIA":
        st.warning("🔒 Acceso restringido: Solo la SECRETARIA puede acceder a esta función.")
        return

    # Crear pestañas principales
    tab1, tab2, tab3 = st.tabs(["📅 Reuniones", "💰 Préstamos", "🧍‍♂️ Asistencia"])

    # ======================================================
    # PESTAÑA 1: REUNIONES
    # ======================================================
    with tab1:
        st.subheader("📅 Gestión de Reuniones")
        mostrar_reuniones()

    # ======================================================
    # PESTAÑA 2: PRÉSTAMOS
    # ======================================================
    with tab2:
        st.subheader("💰 Gestión de Préstamos")
        mostrar_prestamo()

    # ======================================================
    # PESTAÑA 3: ASISTENCIA
    # ======================================================
    with tab3:
        st.subheader("🧍‍♂️ Registro de Asistencia")
        mostrar_asistencia()
