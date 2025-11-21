import streamlit as st
from modulos.reuniones import mostrar_reuniones
from modulos.prestamo import mostrar_prestamo
from modulos.asistencia import mostrar_asistencia
from modulos.ahorros import mostrar_ahorros

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

    # Inicializar session_state para el contexto de reunión
    if 'reunion_contexto' not in st.session_state:
        st.session_state.reunion_contexto = None

    # Crear pestañas principales - ahora con 4 pestañas
    tab1, tab2, tab3, tab4 = st.tabs([
        "📅 Reuniones", 
        "🧍‍♂️ Asistencia", 
        "💰 Préstamos",
        "💵 Ahorros"
    ])

    with tab1:
        st.subheader("📅 Gestión de Reuniones")
        
        # Mostrar reuniones y capturar la selección
        mostrar_reuniones()
        
        # Información del contexto actual
        if st.session_state.reunion_contexto:
            ctx = st.session_state.reunion_contexto
            st.success(f"✅ Reunión activa: {ctx['reunion_label']}")
            st.info(f"📋 Esta reunión está disponible en las otras pestañas")

    with tab2:
        st.subheader("🧍‍♂️ Registro de Asistencia")
        
        if st.session_state.reunion_contexto:
            ctx = st.session_state.reunion_contexto
            st.success(f"📅 Reunión activa: {ctx['reunion_label']}")
            try:
                # Pasar el contexto a asistencia
                mostrar_asistencia(
                    id_reunion=ctx['id_reunion'],
                    id_grupo=ctx['id_grupo']
                )
            except Exception as e:
                st.error(f"Error en asistencia: {e}")
                mostrar_asistencia()  # Fallback al modo normal
        else:
            st.warning("⚠️ Primero selecciona una reunión en la pestaña 'Reuniones'")
            mostrar_asistencia()

    with tab3:
        st.subheader("💰 Gestión de Préstamos")
        
        if st.session_state.reunion_contexto:
            ctx = st.session_state.reunion_contexto
            st.success(f"📅 Reunión activa: {ctx['reunion_label']}")
            try:
                # Pasar el contexto a préstamos
                mostrar_prestamo(
                    id_reunion=ctx['id_reunion'],
                    id_grupo=ctx['id_grupo'],
                    reunion_info=ctx['reunion_label'],
                    grupo_info=ctx['grupo_label']
                )
            except Exception as e:
                st.error(f"Error en préstamos: {e}")
                mostrar_prestamo()  # Fallback al modo normal
        else:
            st.warning("⚠️ Primero selecciona una reunión en la pestaña 'Reuniones'")
            mostrar_prestamo()

    with tab4:
        st.subheader("💵 Gestión de Ahorros")
        
        if st.session_state.reunion_contexto:
            ctx = st.session_state.reunion_contexto
            st.success(f"📅 Reunión activa: {ctx['reunion_label']}")
            try:
                # Pasar el contexto a ahorros (necesitarás adaptar mostrar_ahorros)
                mostrar_ahorros(
                    id_reunion=ctx['id_reunion'],
                    id_grupo=ctx['id_grupo'],
                    reunion_info=ctx['reunion_label'],
                    grupo_info=ctx['grupo_label']
                )
            except Exception as e:
                st.error(f"Error en ahorros: {e}")
                mostrar_ahorros()  # Fallback al modo normal
        else:
            st.warning("⚠️ Primero selecciona una reunión en la pestaña 'Reuniones'")
            mostrar_ahorros()
