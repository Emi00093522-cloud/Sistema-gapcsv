import streamlit as st
from modulos.registro_usuario import registrar_usuario
from modulos.login import login
from modulos.promotora import mostrar_promotora
from modulos.distrito import mostrar_distrito
from modulos.grupos import mostrar_grupos
from modulos.miembros import mostrar_miembro

from modulos.asistencia import mostrar_asistencia
from modulos.reglamentos import mostrar_reglamentos
from modulos.integrada import mostrar_gestion_integrada


# ---------------------------------------------------------
# ESTILO AZUL CLARO PREMIUM
# ---------------------------------------------------------
def estilo_azul_claro_premium():
    st.markdown("""
    <style>

    .stApp {
        background: linear-gradient(135deg, #eaf3ff 0%, #dcecff 50%, #cfe5ff 100%);
        font-family: 'Segoe UI', sans-serif;
    }

    h1 {
        color: #1B4F72 !important;
        font-weight: 800 !important;
        text-shadow: 0px 1px 3px rgba(0,0,0,0.1);
    }

    h2, h3 {
        color: #21618C !important;
        font-weight: 700 !important;
    }

    .stTabs [data-baseweb="tab"] {
        color: #1b4f72 !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: #2874a6 !important;
    }

    .stTabs [aria-selected="true"] {
        color: white !important;
        background: #2874a6 !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, #2874a6 0%, #1b4f72 100%) !important;
        color: white !important;
        border: none !important;
        padding: 12px 24px !important;
        border-radius: 10px !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        box-shadow: 0 3px 10px rgba(40,116,166,0.25) !important;
        transition: 0.3s ease-in-out;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #3598db 0%, #21618c 100%) !important;
        box-shadow: 0 4px 14px rgba(40,116,166,0.35) !important;
        transform: translateY(-2px);
    }

    .stTextInput > div > div > input,
    .stSelectbox > div > div,
    .stNumberInput > div > div > input {
        border-radius: 8px !important;
        border: 1px solid #aed6f1 !important;
        padding: 10px !important;
    }

    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div:focus,
    .stNumberInput > div > div > input:focus {
        border: 1px solid #3498db !important;
        box-shadow: 0 0 6px rgba(52,152,219,0.4) !important;
    }

    .banner-container {
        background: white;
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border: 1px solid #d6eaf8;
        margin-bottom: 25px;
    }

    .banner-img {
        width: 100%;
        border-radius: 12px;
    }

    </style>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------
st.set_page_config(page_title="Sistema GAPCSV", page_icon="💙", layout="wide")
estilo_azul_claro_premium()

if "sesion_iniciada" not in st.session_state:
    st.session_state["sesion_iniciada"] = False
if "pagina_actual" not in st.session_state:
    st.session_state["pagina_actual"] = "inicio"


# ---------------------------------------------------------
# PANEL SECRETARIA
# ---------------------------------------------------------
def panel_secretaria():
    st.title("💼 Panel de Secretaria")

    tabs = st.tabs([
        "👥 Registrar Grupo",
        "👥 Miembros",
        "📜 Reglamentos",
        "📅 Reuniones",
        "🚪 Cerrar sesión"
    ])

    with tabs[0]: mostrar_grupos()
    with tabs[1]: mostrar_miembro()
    with tabs[2]: mostrar_reglamentos()
    with tabs[3]: mostrar_gestion_integrada()

    with tabs[4]:
        if st.button("Cerrar sesión"):
            st.session_state.clear()
            st.session_state["pagina_actual"] = "sesion_cerrada"
            st.rerun()


# ---------------------------------------------------------
# PANEL PRESIDENTE
# ---------------------------------------------------------
def panel_presidente():
    st.title("👑 Panel de Presidente")

    tabs = st.tabs([
        "👥 Registrar Grupo",
        "👥 Miembros",
        "📜 Reglamentos",
        "💰 Préstamos",
        "🚪 Cerrar sesión"
    ])

    with tabs[0]: mostrar_grupos()
    with tabs[1]: mostrar_reglamentos()
    with tabs[2]: mostrar_miembro()
    with tabs[3]: mostrar_prestamo()

    with tabs[4]:
        if st.button("Cerrar sesión"):
            st.session_state.clear()
            st.session_state["pagina_actual"] = "sesion_cerrada"
            st.rerun()


# ---------------------------------------------------------
# PANEL PROMOTORA
# ---------------------------------------------------------
def panel_promotora(usuario):
    st.title("🤝 Panel de Promotora")

    tabs = st.tabs([
        "📈 Dashboard",
        "👩‍💼 Registro Promotora",
        "🏛️ Distrito",
        "🚪 Cerrar sesión"
    ])

    with tabs[0]:
        st.success(f"Bienvenida, {usuario} 🌟")
        st.info("📊 Dashboard general de promotoras en desarrollo...")

    with tabs[1]: mostrar_promotora()
    with tabs[2]: mostrar_distrito()

    with tabs[3]:
        if st.button("Cerrar sesión"):
            st.session_state.clear()
            st.session_state["pagina_actual"] = "sesion_cerrada"
            st.rerun()


# ---------------------------------------------------------
# PANEL ADMINISTRADORA
# ---------------------------------------------------------
def panel_admin():
    st.title("🛡️ Panel de Administradora")

    tabs = st.tabs([
        "📊 Consolidado Distritos",
        "🧑‍💻 Registrar Usuario",
        "🚪 Cerrar sesión"
    ])

    with tabs[0]:
        st.info("📊 Aquí irá el consolidado general por distrito.")

    with tabs[1]: registrar_usuario()

    with tabs[2]:
        if st.button("Cerrar sesión"):
            st.session_state.clear()
            st.session_state["pagina_actual"] = "sesion_cerrada"
            st.rerun()


# ---------------------------------------------------------
# FLUJO PRINCIPAL
# ---------------------------------------------------------
if st.session_state["sesion_iniciada"]:

    usuario = st.session_state.get("usuario", "Usuario")
    tipo = (st.session_state.get("tipo_usuario", "") or "").lower()
    cargo = (st.session_state.get("cargo_de_usuario", "") or "").upper()

    if cargo == "SECRETARIA":
        panel_secretaria()

    elif cargo == "PRESIDENTE":
        panel_presidente()

    elif tipo == "promotora" or cargo == "PROMOTORA":
        panel_promotora(usuario)

    elif tipo == "administradora":
        panel_admin()

    else:
        st.error("⚠️ Tipo de usuario no reconocido.")

else:

    # CIERRE DE SESIÓN
    if st.session_state["pagina_actual"] == "sesion_cerrada":
        st.success("Sesión finalizada.")
        if st.button("Volver al inicio"):
            st.session_state["pagina_actual"] = "inicio"
            st.rerun()

    # -----------------------------------------------------
    # PANTALLA DE INICIO CON IMAGEN + ESTILO PREMIUM
    # -----------------------------------------------------
    elif st.session_state["pagina_actual"] == "inicio":
        st.markdown("""
        <div class="banner-container">
            <img src="AQUÍ_TU_IMAGEN.png" class="banner-img" alt="Banner de ahorro y préstamos comunitarios">
        </div>
        """, unsafe_allow_html=True)

        st.title("Bienvenida al Sistema GAPCSV")
        st.subheader("Grupos de  Ahorro y Préstamos Comunitarios 🤝🌱💰")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔑 Iniciar sesión"):
                st.session_state["pagina_actual"] = "login"
                st.rerun()

        with col2:
            if st.button("📝 Registrarme"):
                st.session_state["pagina_actual"] = "registro"
                st.rerun()

    elif st.session_state["pagina_actual"] == "login":
        login()

    elif st.session_state["pagina_actual"] == "registro":
        registrar_usuario()
