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

# ----------------------- ESTÉTICA GLOBAL --------------------------
st.set_page_config(page_title="Sistema GAPCSV", page_icon="💜", layout="wide")

# CSS personalizado
def css_estilo():
    st.markdown(
        """
        <style>

        /* Fondo general suave */
        .stApp {
            background: #f8f5fc;
        }

        /* Títulos elegantes */
        h1, h2, h3, h4 {
            font-family: 'Segoe UI', sans-serif !important;
            font-weight: 650 !important;
            color: #4B2E83 !important;
        }

        /* Tarjetas estilo material */
        .css-1r6slb0, .css-12oz5g7 {
            padding: 20px;
            border-radius: 15px;
            background: white !important;
            box-shadow: 0px 4px 12px rgba(0,0,0,0.1);
        }

        /* Tabs personalizados */
        .stTabs [data-baseweb="tab"] {
            background-color: #e8d9ff !important;
            padding: 10px 20px;
            border-radius: 10px;
            margin-right: 5px;
            font-weight: 600;
            color: #4B2E83 !important;
        }
        .stTabs [aria-selected="true"] {
            background-color: #4B2E83 !important;
            color: white !important;
        }

        /* Botones estilizados */
        .stButton>button {
            background: linear-gradient(90deg, #7042b8, #9b59ff);
            color: white;
            padding: 10px 20px;
            border-radius: 10px;
            border: none;
            font-weight: 600;
            cursor: pointer;
        }
        .stButton>button:hover {
            background: linear-gradient(90deg, #59309b, #8443e8);
        }

        /* Inputs más elegantes */
        .stTextInput>div>div>input, .stSelectbox>div>div>select {
            border-radius: 10px !important;
            border: 1px solid #bfa8e5 !important;
            padding: 8px;
        }

        </style>
        """,
        unsafe_allow_html=True
    )

css_estilo()

# ----------------------- SESIÓN --------------------------
if "sesion_iniciada" not in st.session_state:
    st.session_state["sesion_iniciada"] = False
if "pagina_actual" not in st.session_state:
    st.session_state["pagina_actual"] = "inicio"

# ----------------------- PANELES --------------------------
def panel_secretaria():
    st.title("💼 Panel de Secretaria")
    st.write("---")

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
        if st.button("Cerrar sesión"): cerrar_sesion()


def panel_presidente():
    st.title("👑 Panel de Presidente")
    st.write("---")

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
        if st.button("Cerrar sesión"): cerrar_sesion()


def panel_promotora(usuario):
    st.title("🌸 Panel de Promotora")
    st.write(f"Bienvenida, **{usuario}** ✨")
    st.write("---")

    tabs = st.tabs([
        "📈 Dashboard",
        "👩‍💼 Registro Promotora",
        "🏛️ Distrito",
        "🚪 Cerrar sesión"
    ])

    with tabs[0]: st.info("Dashboard general de promotoras")
    with tabs[1]: mostrar_promotora()
    with tabs[2]: mostrar_distrito()

    with tabs[3]:
        if st.button("Cerrar sesión"): cerrar_sesion()


def panel_admin():
    st.title("🛠️ Panel de Administradora")
    st.write("---")

    tabs = st.tabs([
        "📊 Consolidado Distritos",
        "🧑‍💻 Registrar Usuario",
        "🚪 Cerrar sesión"
    ])

    with tabs[0]: st.info("Aquí irá el consolidado general por distrito")
    with tabs[1]: registrar_usuario()

    with tabs[2]:
        if st.button("Cerrar sesión"): cerrar_sesion()


# ----------------------- FUNCIÓN CERRAR SESIÓN --------------------------
def cerrar_sesion():
    st.session_state.clear()
    st.session_state["sesion_iniciada"] = False
    st.session_state["pagina_actual"] = "sesion_cerrada"
    st.rerun()


# ----------------------- FLUJO APP --------------------------
if st.session_state["sesion_iniciada"]:
    usuario = st.session_state.get("usuario", "Usuario")
    tipo = (st.session_state.get("tipo_usuario", "") or "").lower()
    cargo = (st.session_state.get("cargo_de_usuario", "") or "").upper()

    if cargo == "SECRETARIA": panel_secretaria()
    elif cargo == "PRESIDENTE": panel_presidente()
    elif tipo == "promotora" or cargo == "PROMOTORA": panel_promotora(usuario)
    elif tipo == "administradora": panel_admin()
    else: st.error("⚠️ Tipo de usuario no reconocido.")

else:
    if st.session_state["pagina_actual"] == "sesion_cerrada":
        st.success("Sesión finalizada.")
        if st.button("Volver al inicio"):
            st.session_state["pagina_actual"] = "inicio"
            st.rerun()

    elif st.session_state["pagina_actual"] == "inicio":
        st.title("🟦 Sistema GAPCSV
Grupos de Ahorro y Préstamo Comunitario")
("Esta página servirá como plataforma para gestionar grupos, registrar miembros, administrar reuniones y llevar el control financiero de forma eficiente y organizada.")
        st.subheader("Grupos de Ahorro y Préstamo Comunitario")
        st.write("---")

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
