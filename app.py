import streamlit as st
from modulos.registro_usuario import registrar_usuario
from modulos.login import login
# from modulos.grupos import mostrar_grupo
# mostrar_grupo()
from modulos.promotora import mostrar_promotora
from modulos.distrito import mostrar_distrito
# ⚙️ Configuración de la app
st.set_page_config(page_title="Sistema GAPCSV", page_icon="💜", layout="centered")

# 🧠 Inicialización del estado
if "sesion_iniciada" not in st.session_state:
    st.session_state["sesion_iniciada"] = False
if "pagina_actual" not in st.session_state:
    st.session_state["pagina_actual"] = "inicio"

# --- NAVEGACIÓN LATERAL ---
st.sidebar.title("📋 Menú principal")

# 💅 Estilo visual personalizado
st.markdown("""
    <style>
        .titulo {
            text-align: center;
            color: #6C3483;
            font-size: 2.2em;
            font-weight: bold;
        }
        .subtitulo {
            text-align: center;
            color: #2E4053;
            font-size: 1.3em;
        }
        .descripcion {
            background-color: #F8F9F9;
            border-radius: 12px;
            padding: 20px;
            margin-top: 10px;
            box-shadow: 0 0 10px rgba(108, 52, 131, 0.2);
        }
        .emoji {
            font-size: 1.4em;
        }
        .sesion-cerrada {
            text-align: center;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 10px;
            margin: 20px 0;
        }
    </style>
""", unsafe_allow_html=True)

# 🟢 Si ya hay sesión iniciada
if st.session_state["sesion_iniciada"]:
    usuario = st.session_state.get("usuario", "Usuario")
    tipo = st.session_state.get("tipo_usuario", "Desconocido")
    cargo = st.session_state.get("cargo_usuario", "")

    st.sidebar.write(f"👤 **{usuario}** ({tipo})")

    # Menú dinámico según tipo y cargo
    if tipo.lower() == "administradora":
        opciones = ["Consolidado por distrito", "Registrar usuario", "Cerrar sesión"]
    elif tipo.lower() == "promotora" or cargo.upper() == "PROMOTORA":
        # Menú especial para PROMOTORAS
        opciones = ["Dashboard Promotora", "Registrar Promotora", "Registrar Distrito", "Cerrar sesión"]
    else:
        opciones = ["Dashboard","Registrar Promotora","Registrar Distritos" "Cerrar sesión"]

    opcion = st.sidebar.selectbox("Ir a:", opciones)

    # --- Administradora ---
    if tipo.lower() == "administradora":
        if opcion == "Consolidado por distrito":
            st.title("📊 Consolidado general por distrito 💲")
            # mostrar_ahorros()  # Aquí irá tu función real
        elif opcion == "Registrar usuario":
            registrar_usuario()
        elif opcion == "Cerrar sesión":
            # Guardar el nombre del usuario para el mensaje de despedida
            usuario_temp = st.session_state.get("usuario", "")
            
            # Limpiar toda la sesión
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            
            # Restablecer estado básico
            st.session_state["sesion_iniciada"] = False
            st.session_state["pagina_actual"] = "sesion_cerrada"
            
            st.rerun()

    # --- PROMOTORA --- (tipo PROMOTORA o cargo PROMOTORA)
    elif tipo.lower() == "promotora" or cargo.upper() == "PROMOTORA":
        if opcion == "Dashboard Promotora":
            st.title("👩‍💼 Dashboard de Promotora")
            st.success(f"¡Bienvenida, {usuario}!")
            st.info("Desde aquí puedes gestionar promotoras y distritos.")
            
            # Mostrar estadísticas rápidas o información relevante
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Tu Cargo", "PROMOTORA")
            with col2:
                st.metric("Acciones Disponibles", "2")
                
        elif opcion == "Registrar Promotora":
            st.title("👩‍💼 Registrar Nueva Promotora")
            mostrar_promotora()
            
        elif opcion == "Registrar Distrito":
            st.title("🏛️ Registrar Nuevo Distrito")
            mostrar_distrito()
            
        elif opcion == "Cerrar sesión":
            # Guardar el nombre del usuario para el mensaje de despedida
            usuario_temp = st.session_state.get("usuario", "")
            
            # Limpiar toda la sesión
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            
            # Restablecer estado básico
            st.session_state["sesion_iniciada"] = False
            st.session_state["pagina_actual"] = "sesion_cerrada"
            
            st.rerun()

    # --- Otros tipos de usuario ---
    else:
        if opcion == "Dashboard":
            st.title("📊 Dashboard")
            # Aquí irá tu función real del dashboard
        elif opcion == "Cerrar sesión":
            # Guardar el nombre del usuario para el mensaje de despedida
            usuario_temp = st.session_state.get("usuario", "")
            
            # Limpiar toda la sesión
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            
            # Restablecer estado básico
            st.session_state["sesion_iniciada"] = False
            st.session_state["pagina_actual"] = "sesion_cerrada"
            
            st.rerun()

# 🔴 Si no hay sesión iniciada, mostrar página de bienvenida o sesión cerrada
else:
    # --- Página de sesión cerrada ---
    if st.session_state["pagina_actual"] == "sesion_cerrada":
        st.markdown("<div class='sesion-cerrada'>", unsafe_allow_html=True)
        st.markdown("### ✅ Sesión finalizada")
        st.markdown("<p>Has cerrado sesión exitosamente.</p>", unsafe_allow_html=True)
        
        if st.button("🏠 Volver al inicio"):
            st.session_state["pagina_actual"] = "inicio"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # --- Página de inicio normal ---
    elif st.session_state["pagina_actual"] == "inicio":
        st.markdown("<h1 class='titulo'> Bienvenido al Sistema GAPCSV </h1>", unsafe_allow_html=True)
        st.markdown("<h3 class='subtitulo'>Grupos de Ahorro y Prestamo Comunitario </h3>", unsafe_allow_html=True)

        st.markdown("""
        <div class='descripcion'>
            <p class='emoji'> Este sistema te ayuda a registrar, monitorear y consolidar los ahorros de los grupos comunitarios.</p>
            <p class='emoji'>Promueve la colaboración, la transparencia y el crecimiento económico local🤝.</p>
            <p>Si ya tienes una cuenta, inicia sesión .<br>
            Si aún no tienes usuario, puedes registrarte fácilmente. 🌱</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔑 Iniciar sesión"):
                st.session_state["pagina_actual"] = "login"
                st.rerun()

        with col2:
            if st.button("📝 Registrarme"):
                st.session_state["pagina_actual"] = "registro"
                st.rerun()

    # --- Pantalla de login ---
    elif st.session_state["pagina_actual"] == "login":
        login()

    # --- Pantalla de registro ---
    elif st.session_state["pagina_actual"] == "registro":
        registrar_usuario()
