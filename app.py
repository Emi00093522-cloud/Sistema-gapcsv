# Nuevo diseño corporativo con estilo formal para Sistema GAPCSV
# Este archivo contiene el código completo estilizado.

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

# --------------------------------------------------
# CONFIGURACIÓN GENERAL
# --------------------------------------------------
st.set_page_config(page_title="Sistema GAPCSV", page_icon="💼", layout="wide")

# --------------------------------------------------
# ESTILOS CORPORATIVOS
# --------------------------------------------------
st.markdown(
    """
    <style>
        /* FUENTE GENERAL */
        * {
            font-family: 'Segoe UI', sans-serif;
        }

        /* TITULOS */
        .titulo-principal {
            font-size: 48px !important;
            font-weight: 700 !important;
            color: #2A2A2A !important;
            text-align: center;
            margin-bottom: -10px;
        }

        .subtitulo-principal {
            font-size: 22px !important;
            color: #555 !important;
            text-align: center;
            margin-top: -5px;
        }

        /* TARJETAS */
        .stMarkdown, .stText, .stButton > button {
            border-radius: 8px !important;
        }

        /* BOTONES */
        .stButton > button {
            background-color: #4C4C4C !important;
            color: white !important;
            border: none !important;
            padding: 10px 20px !important;
            border-radius: 6px !important;
            font-size: 16px;
        }
        .stButton > button:hover {
            background-color: #2E2E2E !important;
        }

        /* TABS CORPORATIVOS */
        .stTabs [role="tab"] {
            background-color: #F2F2F2 !important;
            padding: 10px 18px !important;
            border-radius: 6px 6px 0 0 !important;
            font-weight: 600 !important;
            color: #333 !important;
        }
        .stTabs [aria-selected="true"] {
            background-color: #D9D9D9 !important;
            border-bottom: 3px solid #4C4C4C !important;
            color: #000 !important;
        }

        /* CONTENEDOR PANEL */
        .panel {
            background-color: #FFFFFF;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.12);
            margin-bottom: 20px;
        }

    </style>
    """,
    unsafe_allow_html=True
)

# --------------------------------------------------
# VARIABLES DE SESIÓN
# --------------------------------------------------
if "sesion_iniciada" not in st.session_state:
    st.session_state["sesion_iniciada"] = False
if "pagina_actual" not in st.session_state:
    st.session_state["pagina_actual"] = "inicio"

# --------------------------------------------------
# PANEL SECRETARIA
# --------------------------------------------------
def panel_secretaria():
    st.markdown("<h1 class='panel'>Panel de Secretaria</h1>", unsafe_allow_html=True)

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
            st.session_state["sesion_iniciada"] = False
            st.session_state["pagina_actual"] = "sesion_cerrada"
            st.rerun()

# --------------------------------------------------
# PANEL PRESIDENTE
# --------------------------------------------------
def panel_presidente():
    st.markdown("<h1 class='panel'>Panel de Presidente</h1>", unsafe_allow_html=True)

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
            st.session_state["sesion_iniciada"] = False
            st.session_state["pagina_actual"] = "sesion_cerrada"
            st.rerun()

# --------------------------------------------------
# PANEL PROMOTORA
# --------------------------------------------------
def panel_promotora(usuario):
    st.markdown("<h1 class='panel'>Panel de Promotora</h1>", unsafe_allow_html=True)

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
            st.session_state["sesion_iniciada"] = False
            st.session_state["pagina_actual"] = "sesion_cerrada"
            st.rerun()

# --------------------------------------------------
# PANEL ADMINISTRADORA
# --------------------------------------------------
def panel_admin():
    st.markdown("<h1 class='panel'>Panel de Administradora</h1>", unsafe_allow_html=True)

    tabs = st.tabs([
        "📊 Consolidado Distritos",
        "🧑‍💻 Registrar Usuario",
        "🚪 Cerrar sesión"
    ])

    with tabs[0]:
        st.info("Aquí irá el consolidado general por distrito")

    with tabs[1]: registrar_usuario()

    with tabs[2]:
        if st.button("Cerrar sesión"):
            st.session_state.clear()
            st.session_state["sesion_iniciada"] = False
            st.session_state["pagina_actual"] = "sesion_cerrada"
            st.rerun()

# --------------------------------------------------
# FLUJO GENERAL DE LA APLICACIÓN
# --------------------------------------------------
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
        if st.button("Volver al inicio"): st.session_state["pagina_actual"] = "inicio"; st.rerun()

    elif st.session_state["pagina_actual"] == "inicio":
        st.markdown("<h1 class='titulo-principal'>Sistema GAPCSV</h1>", unsafe_allow_html=True)
        st.markdown("<h3 class='subtitulo-principal'>Grupos de Ahorro y Préstamo Comunitario</h3>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔑 Iniciar sesión"): st.session_state["pagina_actual"] = "login"; st.rerun()
        with col2:
            if st.button("📝 Registr
