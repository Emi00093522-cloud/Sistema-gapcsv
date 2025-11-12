import streamlit as st
from modulos.registro_usuario import registrar_usuario
from modulos.login import login
from modulos.ahorros import mostrar_ahorros  # Puedes reemplazar luego por tus dashboards reales

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
    </style>
""", unsafe_allow_html=True)

# 🟢 Si ya hay sesión iniciada
if st.session_state["sesion_iniciada"]:
    usuario = st.session_state.get("usuario", "Usuario")
    tipo = st.session_state.get("tipo_usuario", "Desconocido")

    st.sidebar.write(f"👤 **{usuario}** ({tipo})")

    # Menú dinámico según tipo
    if tipo.lower() == "administradora":
        opciones = ["Consolidado por distrito", "Registrar usuario", "Cerrar sesión"]
    elif tipo.lower() == "promotora":
        opciones = ["Consolidado por grupos", "Cerrar sesión"]
    else:
        opciones = ["Dashboard", "Cerrar sesión"]

    opcion = st.sidebar.selectbox("Ir a:", opciones)

    # --- Administradora ---
    if tipo.lower() == "administradora":
        if opcion == "Consolidado por distrito":
            st.title("📊 Consolidado general por distrito 💲")
            mostrar_ahorros()  # Aquí irá tu función real
        elif opcion == "Registrar usuario":
            registrar_usuario()
        elif opcion == "Cerrar sesión":
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.session_state["pagina_actual"] = "inicio"
            st.success("👋 Sesión cerrada correctamente.")
            st.rerun()

    # --- Promotora ---
    elif tipo.lower() == "promotora":
        if opcion == "Consolidado por grupos":
            st.title("📈 Consolidado por grupos del distrito asignado 💰")
            mostrar_ahorros()  # Aquí irá tu función real
        elif opcion == "Cerrar sesión":
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.session_state["pagina_actual"] = "inicio"
            st.success("👋 Sesión cerrada correctamente.")
            st.rerun()

# 🔴 Si no hay sesión iniciada, mostrar página de bienvenida
else:
    if st.session_state["pagina_actual"] == "inicio":
        st.markdown("<h1 class='titulo'>💜 Bienvenida al Sistema GAPCSV 💲</h1>", unsafe_allow_html=True)
        st.markdown("<h3 class='subtitulo'>Grupos de Ahorro Comunitario Solidario y Visionario</h3>", unsafe_allow_html=True)

        st.markdown("""
        <div class='descripcion'>
            <p class='emoji'>💰 Este sistema te ayuda a registrar, monitorear y consolidar los ahorros de los grupos comunitarios.</p>
            <p class='emoji'>🤝 Promueve la colaboración, la transparencia y el crecimiento económico local.</p>
            <p>Si ya tienes una cuenta, inicia sesión para ver tus reportes.<br>
            Si aún no tienes usuario, puedes registrarte fácilmente para comenzar a formar parte de esta comunidad de ahorro. 🌱</p>
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
