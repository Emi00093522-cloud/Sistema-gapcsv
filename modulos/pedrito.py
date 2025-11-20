def panel_secretaria():
    st.title("Panel de Secretaria - 🚨 VERSIÓN NUEVA")
    
    # DEBUG VISIBLE
    st.error("🚨 ¡ESTA ES LA VERSIÓN NUEVA CON ORDEN CORREGIDO!")
    st.warning("Si ves este mensaje, el código SÍ se está ejecutando")
    
    tabs = st.tabs([
        "👥 Registrar Grupo - 1",
        "👥 Miembros - 2", 
        "📜 Reglamentos - 3",
        "📅 Reuniones - 4",
        "💰 Préstamos - 5",
        "📝 Asistencia - 6",
        "🚪 Cerrar sesión - 7"
    ])

    with tabs[0]:
        st.header("📍 PESTAÑA 1 - REGISTRAR GRUPO")
        mostrar_grupos()

    with tabs[1]:
        st.header("📍 PESTAÑA 2 - MIEMBROS")
        mostrar_miembro()

    with tabs[2]:
        st.header("📍 PESTAÑA 3 - REGLAMENTOS")
        mostrar_reglamentos()

    with tabs[3]:
        st.header("📍 PESTAÑA 4 - REUNIONES")
        mostrar_reuniones()

    with tabs[4]:
        st.header("📍 PESTAÑA 5 - PRÉSTAMOS")
        mostrar_prestamo()

    with tabs[5]:
        st.header("📍 PESTAÑA 6 - ASISTENCIA")
        mostrar_asistencia()

    with tabs[6]:
        st.header("📍 PESTAÑA 7 - CERRAR SESIÓN")
        if st.button("Cerrar sesión"):
            st.session_state.clear()
            st.session_state["sesion_iniciada"] = False
            st.session_state["pagina_actual"] = "sesion_cerrada"
            st.rerun()
