import streamlit as st
from modulos.registro_usuario import registrar_usuario
from modulos.login import login
from modulos.ahorros import mostrar_ahorros  # Puedes reemplazar luego por tus dashboards reales

# ⚙️ Configuración de la app
st.set_page_config(page_title="Sistema GAPCSV", page_icon="🧁", layout="centered")

# 🎨 --- ESTILOS VISUALES ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');

    html, body, [class*="st-"] {
        font-family: 'Poppins', sans-serif;
    }

    .stApp {
        background: linear-gradient(135deg, #E6E6FA 0%, #F8E1F4 100%) !important;
        color: #4A4A4A;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: transparent !important;
        box-shadow: none !important;
        padding: 0 !important;
    }

    .fondo {
        background: rgba(255, 255, 255, 0.4);
        padding: 50px;
        border-radius: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        text-align: center;
        backdrop-filter: blur(10px);
    }

    .titulo {
        color: #5E3C77;
        font-size: 38px;
        font-weight: 700;
        margin-bottom: 10px;
    }
    .subtitulo {
        color: #7A4D96;
        font-size: 22px;
        font-weight: 600;
        margin-bottom: 25px;
    }
    .texto {
        color: #4A4A4A;
        font-size: 18px;
        margin-bottom: 30px;
    }

    button[kind="primary"] {
        background-color: #7A4D96 !important;
        color: white !important;
        border-radius: 12px !important;
        font-size: 18px !important;
        font-weight: 600 !important;
        border: none !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.15);
        transition: all 0.2s ease-in-out;
    }
    button[kind="primary"]:hover {
        background-color: #5E3C77 !important;
        transform: scale(1.02);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 🧠 Inicialización del estado
if "sesion_iniciada" not in st.session_state:
    st.session_state["sesion_iniciada"] = False
if "pagina_actual" not in st.session_state:
    st.session_state["pagina_actual"] = "inicio"

# --- NAVEGACIÓN LATERAL ---
st.sidebar.title("📋 Menú principal")

# 🟢 Si ya hay sesión iniciada
if st.session_state["sesion_iniciada"]:
    usuario = st.session_state.get("usuario", "Usuario")
    tipo = st.session_state.get("tipo_usuario", "Desconocido")

    st.sidebar.write(f"👤 **{usuario}** ({tipo})")

    if tipo.lower() == "administradora":
        opciones = ["Consolidado por distrito", "Registrar usuario", "Cerrar sesión"]
    elif tipo.lower() == "promotora":
        opciones = ["Consolidado por grupos", "Cerrar sesión"]
    else:
        opciones = ["Dashboard", "Cerrar sesión"]

    opcion = st.sidebar.selectbox("Ir a:", opciones)

    if tipo.lower() == "administradora":
        if opcion == "Consolidado por distrito":
            st.title("📊 Consolidado general por distrito")
            mostrar_ahorros()
        elif opcion == "Registrar usuario":
            registrar_usuario()
        elif opcion == "Cerrar sesión":
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("👋 Sesión cerrada correctamente.")
            st.rerun()

    elif tipo.lower() == "promotora":
        if opcion == "Consolidado por grupos":
            st.title("📈 Consolidado por grupos del distrito asignado")
            mostrar_ahorros()
        elif opcion == "Cerrar sesión":
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("👋 Sesión cerrada correctamente.")
            st.rerun()

# 🔴 Si no hay sesión iniciada, mostrar página de bienvenida
else:
    st.markdown("<div class='fondo'>", unsafe_allow_html=True)
    st.markdown("<h1 class='titulo'>💜 Bienvenida al Sistema GAPCSV</h1>", unsafe_allow_html=True)
    st.markdown("<h3 class='subtitulo'>Grupos de Ahorro Comunitario Solidario y Visionario</h3>", unsafe_allow_html=True)
    st.markdown(
        "<p class='texto'>Este sistema permite gestionar la información de los grupos de ahorro comunitario.<br>"
        "Si ya tienes una cuenta, <b>inicia sesión</b> para acceder a tus datos.<br>"
        "Si aún no tienes usuario, <b>regístrate</b> fácilmente aquí.</p>",
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔑 Iniciar sesión"):
            st.session_state["pagina_actual"] = "login"
    with col2:
        if st.button("📝 Registrarme"):
            st.session_state["pagina_actual"] = "registro"

    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state["pagina_actual"] == "login":
        login()
    elif st.session_state["pagina_actual"] == "registro":
        registrar_usuario()
