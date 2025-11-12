# 🟢 Si ya hay sesión iniciada
if st.session_state["sesion_iniciada"]:
    usuario = st.session_state.get("usuario", "Usuario")
    tipo = st.session_state.get("tipo_usuario", "Desconocido")

    st.sidebar.write(f"👤 **{usuario}** ({tipo})")

    # Menú dinámico según tipo
    if tipo.lower() == "administradora":
        opciones = ["Consolidado por distrito", "Registrar usuario", "Registrar grupo", "Cerrar sesión"]  # ← AGREGADO AQUÍ
    elif tipo.lower() == "promotora":
        opciones = ["Consolidado por grupos", "Registrar grupo", "Cerrar sesión"]  # ← AGREGADO AQUÍ
    else:
        opciones = ["Dashboard", "Registrar grupo", "Cerrar sesión"]  # ← AGREGADO AQUÍ

    opcion = st.sidebar.selectbox("Ir a:", opciones)

    # --- Administradora ---
    if tipo.lower() == "administradora":
        if opcion == "Consolidado por distrito":
            st.title("📊 Consolidado general por distrito 💲")
            mostrar_ahorros()  # Aquí irá tu función real
        elif opcion == "Registrar usuario":
            registrar_usuario()
        elif opcion == "Registrar grupo":  # ← NUEVA OPCIÓN AQUÍ
            mostrar_grupo()
        elif opcion == "Cerrar sesión":
            # ... (código existente)

    # --- Promotora ---
    elif tipo.lower() == "promotora":
        if opcion == "Consolidado por grupos":
            st.title("📈 Consolidado por grupos del distrito asignado 💰")
            mostrar_ahorros()  # Aquí irá tu función real
        elif opcion == "Registrar grupo":  # ← NUEVA OPCIÓN AQUÍ
            mostrar_grupo()
        elif opcion == "Cerrar sesión":
            # ... (código existente)

    # --- Otros tipos de usuario ---
    else:
        if opcion == "Dashboard":
            st.title("📊 Dashboard")
            # Aquí irá tu función real del dashboard
        elif opcion == "Registrar grupo":  # ← NUEVA OPCIÓN AQUÍ
            mostrar_grupo()
        elif opcion == "Cerrar sesión":
            # ... (código existente)
