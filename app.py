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

# -------- CONFIG -----------
st.set_page_config(page_title="Sistema GAPCSV", page_icon="🏛️", layout="wide")

# ----------- ESTILO CORPORATIVO -----------
st.markdown("""
    <style>

    /* Paleta corporativa */
    :root {
        --vino: #7A1E48;
        --vino-oscuro: #5A0F32;
        --gris: #2E2E2E;
        --gris-claro: #f5f5f5;
        --blanco: #ffffff;
    }

    /* Fuente */
    h1, h2, h3, h4, h5 {
        font-family: 'Segoe UI', sans-serif !important;
    }

    p, div, span, label {
        font-family: 'Segoe UI', sans-serif !important;
    }

    /* Fondos */
    body {
        background-color: var(--gris-claro) !important;
    }

    /* Título */
    .titulo {
        text-align: center;
        font-size: 48px;
        font-weight: 800;
        color: var(--vino);
        margin-bottom: -10px;
    }

    .subtitulo {
        text-align: center;
        font-size: 20px;
        color: var(--gris);
        margin-bottom: 20px;
    }

    /* Tarjetas */
    .card {
        padding: 25px;
        background: var(--blanco);
        border-radius: 10px;
        box-shadow: 0px 3px 10px rgba(0,0,0,0.15);
        margin-bottom: 20px;
        border-left: 6px solid var(--vino);
    }

    /* Tabs */
    .stTabs [role="tab"] {
        padding: 10px 18px;
        font-weight: 600;
        border-radius: 6px;
        background-color: #f1e6eb;
        border: 1px solid var(--vino);
        color: var(--vino);
    }

    .stTabs [aria-selected="true"] {
        background-color: var(--vino) !important;
        color: white !important;
    }

    /* Botones */
    .stButton>button {
        background-color: var(--vino) !important;
        color: white !important;
        border-radius: 6px;
        border: none;
        font-weight: 600;
        padding: 10px 20px;
        transition: .2s;
    }

    .stButton>button:hover {
        background-color: var(--vino-oscuro) !important;
        transform: scale(1.02);
    }

    </style>
""", unsafe_allow_html=True)


# -------- SESIÓN ----------
if "sesion_iniciada" not in st.session_state:
    st.session_state["sesion_iniciada"] = False

if "pagina_actual" not in st.session_state:
    st.session_state["pagina_actual"] = "inicio"


# -------- PANELS ----------
def panel_secretaria():
    st.markdown("<div class='card'><h1>📋 Panel de Secretaria</h1></div>", unsafe_allow_html=True)

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
            st.session_state["pagina_actual"] = "inicio"
            st.rerun()


def panel_presidente():
    st.markdown("<div class='card'><h1>🏛️ Panel de Presidente</h1></div>", unsafe_allow_html=True)

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
            st.session_state["pagina_actual"] = "inicio"
            st.rerun()


def panel_promotora(usuario):
    st.markdown("<div class='card'><h1>👩‍💼 Panel de Promotora</h1></div>", unsafe_allow_html=True)

    tabs = st.tabs([
        "📈 Dashboard",
        "👩‍💼 Registro Promotora",
        "🏛️ Distrito",
        "🚪 Cerrar sesión"
    ])

    with tabs[0]:
        st.success(f"Bienvenida, {usuario}")
        st.info("Dashboard general de promotoras")

    with tabs[1]: mostrar_promotora()
    with tabs[2]: mostrar_distrito()

    with tabs[3]:
        if st.button("Cerrar sesión"):
            st.session_state.clear()
            st.session_state["pagina_actual"] = "inicio"
            st.rerun()


def panel_admin():
    st.markdown("<div class='card'><h1>🧑‍💻 Panel de Administradora</h1></div>", unsafe_allow_html=True)

    tabs = st.tabs([
        "📊 Consolidado Distritos",
        "🧑‍💻 Registrar Usuario",
        "🚪 Cerrar sesión"
    ])

    with tabs[0]: st.info("Aquí irá el consolidado general por distrito")
    with tabs[1]: registrar_usuario()

    with tabs[2]:
        if st.button("Cerrar sesión"):
            st.session_state.clear()
            st.session_state["pagina_actual"] = "inicio"
            st.rerun()



# ----------- APP FLOW ----------
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

        st.markdown("<h1 class='titulo'>Sistema GAPCSV</h1>", unsafe_allow_html=True)
        st.markdown("<h3 class='subtitulo'>Grupos de Ahorro y Préstamo Comunitario</h3>", unsafe_allow_html=True)

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
