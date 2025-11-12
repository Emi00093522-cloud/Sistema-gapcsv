import streamlit as st
from modulos.registro_usuario import registrar_usuario
from modulos.login import login
from modulos.ahorros import mostrar_ahorros  # Luego puedes reemplazarlo por tus dashboards reales

# 🌼 Configuración general
st.set_page_config(
    page_title="Sistema GAPCSV",
    page_icon="🧁",
    layout="centered"
)

# 🧠 Inicialización del estado
if "sesion_iniciada" not in st.session_state:
    st.session_state["sesion_iniciada"] = False
if "pagina_actual" not in st.session_state:
    st.session_state["pagina_actual"] = "inicio"

# --- SIDEBAR ---
st.sidebar.title("📋 Menú principal")

# 🟢 Si hay sesión iniciada
if st.session_state["sesion_iniciada"]:
    usuario = st.session_state.get("usuario", "Usuario")
    tipo = st.session_state.get("tipo_usuario", "Desconocido")

    st.sidebar.markdown(f"👤 **{usuario}** ({tipo})")

    if tipo.lower() == "administradora":
        opciones = ["🏢 Consolidado por distrito", "👥 Registrar usuario", "🚪 Cerrar sesión"]
    elif tipo.lower() == "promotora":
        opciones = ["📊 Consolidado por grupos", "🚪 Cerrar sesión"]
    else:
        opciones = ["🏠 Dashboard", "🚪 Cerrar sesión"]

    opcion = st.sidebar.selectbox("Selecciona una opción:", opciones)

    # --- Administradora ---
    if tipo.lower() == "administradora":
        if opcion == "🏢 Consolidado por distrito":
            st.title("📊 Consolidado general por distrito")
            mostrar_ahorros()
        elif opcion == "👥 Registrar usuario":
            registrar_usuario()
        elif opcion == "🚪 Cerrar sesión":
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("👋 Sesión cerrada correctamente.")
            st.rerun()

    # --- Promotora ---
    elif tipo.lower() == "promotora":
        if opcion == "📊 Consolidado por grupos":
            st.title("📈 Consolidado por grupos del distrito asignado")
            mostrar_ahorros()
        elif opcion == "🚪 Cerrar sesión":
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("👋 Sesión cerrada correctamente.")
            st.rerun()

# 🔴 Si NO hay sesión iniciada
else:
    # 💜 Estilo visual con HTML y CSS
    st.markdown(
    """
    <style>
    /* --- Fondo general de la página --- */
    .stApp {
        background: linear-gradient(135deg, #E6E6FA 0%, #F8E1F4 100%) !important;
        color: #4A4A4A;
    }

    /* --- Contenedor del mensaje de bienvenida --- */
    .fondo {
        background: rgba(255, 255, 255, 0.4); /* más transparente */
        padding: 50px;
        border-radius: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        text-align: center;
        backdrop-filter: blur(10px); /* da efecto cristal elegante */
    }

    /* --- Título y textos --- */
    .titulo {
        color: #5E3C77;
        font-size: 38px;
        font-weight: bold;
        margin-bottom: 0px;
    }
    .subtitulo {
        color: #7A4D96;
        font-size: 20px;
        margin-top: 5px;
        margin-bottom: 25px;
    }
    .texto {
        color: #4A4A4A;
        font-size: 18px;
        margin-bottom: 30px;
    }

    /* --- Botones personalizados --- */
    button[kind="primary"] {
        background-color: #7A4D96 !important;
        color: white !important;
        border-radius: 10px !important;
        font-size: 18px !important;
        border: none !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.15);
    }
    button[kind="primary"]:hover {
        background-color: #5E3C77 !important;
    }

    /* --- Ocultar el borde gris del contenedor Streamlit --- */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: transparent !important;
        box-shadow: none !important;
        padding: 0 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)


    # 💜 Contenido de bienvenida
    st.markdown("<div class='fondo'>", unsafe_allow_html=True)

    st.markdown("<p class='titulo'>💜 Sistema GAPCSV</p>", unsafe_allow_html=True)
    st.markdown("<p class='subtitulo'>Grupos de Ahorro y Prestamo Comunitario</p>", unsafe_allow_html=True)
    st.image("https://cdn-icons-png.flaticon.com/512/706/706830.png", width=130)
    st.markdown(
        "<p class='texto'>Bienvenid@ al sistema digital de apoyo para los grupos de ahorro comunitario. "
        "Aquí puedes administrar tus grupos, registrar participantes y consultar información relevante "
        "según tu rol como <b>Promotora</b> o <b>Administradora</b>.</p>",
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔑 Iniciar sesión", use_container_width=True):
            st.session_state["pagina_actual"] = "login"
    with col2:
        if st.button("📝 Registrarme", use_container_width=True):
            st.session_state["pagina_actual"] = "registro"

    st.markdown("</div>", unsafe_allow_html=True)

    # Mostrar pantallas según elección
    if st.session_state["pagina_actual"] == "login":
        login()
    elif st.session_state["pagina_actual"] == "registro":
        registrar_usuario()
