import streamlit as st
from modulos.registro_usuario import registrar_usuario
from modulos.login import login
from modulos.promotora import mostrar_promotora
from modulos.distrito import mostrar_distrito
from modulos.grupos import mostrar_grupos
from modulos.miembros import mostrar_miembro
from modulos.prestamo import mostrar_prestamo
from modulos.reuniones import mostrar_reuniones
from modulos.asistencia import mostrar_asistencia
from modulos.reglamentos import mostrar_reglamentos


# ---------------------------------------------------------
# ESTILO MORADO PREMIUM
# ---------------------------------------------------------
def estilo_morado_premium():
    st.markdown("""
    <style>

    .stApp {
        background: linear-gradient(135deg, #f5f0ff 0%, #ece4ff 50%, #e6dbff 100%);
        font-family: 'Segoe UI', sans-serif;
    }

    h1 {
        color: #5423A7 !important;
        font-weight: 800 !important;
        text-shadow: 0px 1px 3px rgba(0,0,0,0.1);
    }

    h2, h3 {
        color: #6A32C9 !important;
        font-weight: 700 !important;
    }

    .stTabs [data-baseweb="tab"] {
        color: #5a21a6 !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: #7d2fe3 !important;
    }

    .stTabs [aria-selected="true"] {
        color: white !important;
        background: #7d2fe3 !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, #7d2fe3 0%, #6424b8 100%) !important;
        color: white !important;
        border: none !important;
        padding: 12px 24px !important;
        border-radius: 10px !important;
        font-size: 1rem !important;
        font-weight: 600 !important;
        box-shadow: 0 3px 10px rgba(125,47,227,0.25) !important;
        transition: 0.3s ease-in-out;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #8e47f0 0%, #6a2ac9 100%) !important;
        box-shadow: 0 4px 14px rgba(125,47,227,0.35) !important;
        transform: translateY(-2px);
    }

    .stTextInput > div > div > input,
    .stSelectbox > div > div,
    .stNumberInput > div > div > input {
        border-radius: 8px !important;
        border: 1px solid #c8b6ff !important;
        padding: 10px !important;
    }

    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div:focus,
    .stNumberInput > div > div > input:focus {
        border: 1px solid #7d2fe3 !important;
        box-shadow: 0 0 6px rgba(125,47,227,0.4) !important;
    }

    </style>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------
st.set_page_config(page_title="Sistema GAPCSV", page_icon="💜", layout="wide")
estilo_morado_premium()

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
        "📜 Reglamentos",
        "👥 Miembros",
        "💰 Préstamos",
        "📅 Reuniones",
        "📝 Asistencia",
        "🚪 Cerrar sesión"
    ])

    with tabs[0]: mostrar_grupos()
    with tabs[1]: mostrar_reglamentos()
    with tabs[2]: mostrar_miembro()
    with tabs[3]: mostrar_prestamo()
    with tabs[4]: mostrar_reuniones()
    with tabs[5]: mostrar_asistencia()

    with tabs[6]:
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
        "📜 Reglamentos",
        "👥 Miembros",
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

    if st.session_state["pagina_actual"] == "sesion_cerrada":
        st.success("Sesión finalizada.")
        if st.button("Volver al inicio"):
            st.session_state["pagina_actual"] = "inicio"
            st.rerun()

    elif st.session_state["pagina_actual"] == "inicio":
        st.title("Bienvenida al Sistema GAPCSV")
        st.subheader(" Grupos comunitarios fortaleciendo el ahorro y los préstamos solidarios🤝🌱💰")

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
