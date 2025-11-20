def panel_secretaria():
    st.title("Panel de Secretaria - ✅ ORDEN NUEVO")
    
    # DEBUG - Verificar que se está ejecutando el código nuevo
    st.error("🔴 ESTE ES EL CÓDIGO NUEVO - ORDEN MODIFICADO")
    
    tabs = st.tabs([
        "👥 Registrar Grupo",
        "👥 Miembros",
        "📜 Reglamentos", 
        "📅 Reuniones",
        "💰 Préstamos",
        "📝 Asistencia",
        "🚪 Cerrar sesión"
    ])

    with tabs[0]:
        st.header("REGISTRAR GRUPO - PESTAÑA 1")
        mostrar_grupos()

    with tabs[1]:
        st.header("MIEMBROS - PESTAÑA 2")
        mostrar_miembro()

    with tabs[2]:
        st.header("REGLAMENTOS - PESTAÑA 3")
        mostrar_reglamentos()

    with tabs[3]:
        st.header("REUNIONES - PESTAÑA 4")
        mostrar_reuniones()

    with tabs[4]:
        st.header("PRÉSTAMOS - PESTAÑA 5")
        mostrar_prestamo()

    with tabs[5]:
        st.header("ASISTENCIA - PESTAÑA 6")
        mostrar_asistencia()

    with tabs[6]:
        st.header("CERRAR SESIÓN - PESTAÑA 7")
        if st.button("Cerrar sesión"):
            st.session_state.clear()
            st.session_state["sesion_iniciada"] = False
            st.session_state["pagina_actual"] = "sesion_cerrada"
            st.rerun()
