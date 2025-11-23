def login():
    """Interfaz del login."""
    st.title("Inicio de sesión 👩‍💼")
    
    # 🔥 BOTÓN VOLVER AL MENÚ PRINCIPAL
    if st.button("🏠 Volver al menú principal"):
        st.session_state["pagina_actual"] = "inicio"
        st.rerun()
    
    st.markdown("---")
    
    # Mostrar opción de restablecer contraseña si se solicita
    if st.session_state.get("mostrar_restablecer", False):
        restablecer_contrasena()
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⬅️ Volver al login", use_container_width=True):
                st.session_state["mostrar_restablecer"] = False
                st.rerun()
        with col2:
            if st.button("🏠 Volver al menú principal", use_container_width=True):
                st.session_state["pagina_actual"] = "inicio"
                st.session_state["mostrar_restablecer"] = False
                st.rerun()
        return

    usuario = st.text_input("Usuario", key="usuario_input")
    contrasena = st.text_input("Contraseña", type="password", key="contrasena_input")

    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Iniciar sesión", use_container_width=True):
            datos_usuario = verificar_usuario(usuario, contrasena)

            if datos_usuario:
                # 🔥 GUARDAMOS TODO EN SESIÓN + PERMISOS
                st.session_state["sesion_iniciada"] = True
                st.session_state["usuario"] = datos_usuario["Usuario"]
                st.session_state["tipo_usuario"] = datos_usuario["tipo_usuario"]
                st.session_state["cargo_de_usuario"] = datos_usuario["cargo"]
                st.session_state["id_usuario"] = datos_usuario["ID_Usuario"]
                
                # 🔥 OBTENER Y GUARDAR PERMISOS (IMPORTANTE)
                from modulos.permisos import obtener_permisos_usuario
                permisos = obtener_permisos_usuario(
                    datos_usuario["ID_Usuario"],
                    datos_usuario["tipo_usuario"],
                    datos_usuario["cargo"]
                )
                st.session_state["permisos_usuario"] = permisos

                st.success(
                    f"Bienvenido, {datos_usuario['Usuario']} 👋 "
                    f"(Cargo: {datos_usuario['cargo']})"
                )

                st.rerun()
            else:
                st.error("❌ Usuario o contraseña incorrectos.")
    
    with col2:
        if st.button("¿Olvidaste tu contraseña?", use_container_width=True):
            st.session_state["mostrar_restablecer"] = True
            st.rerun()
