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
st.set_page_config(page_title="Sistema GAPCSV", page_icon="💜", layout="wide")

# ------------ ESTILOS ---------------
st.markdown("""
    <style>

    /* Tipografías */
    h1, h2, h3, h4, h5 {
        font-family: 'Segoe UI', sans-serif !important;
        color: #3A3A3A;
    }

    /* Color corporativo */
    .titulo-principal {
        color: #5A2D82 !important;
        font-size: 48px !important;
        font-weight: 800;
        text-align: center;
        margin-bottom: -10px;
    }

    .subtitulo-principal {
        color: #6A4C93 !important;
        font-size: 22px !important;
        font-weight: 500;
        text-align: center;
        margin-top: -10px;
    }

    .texto-objetivo {
        color: #4B4B4B !important;
        font-size: 17px !important;
        text-align: center;
        margin-top: 10px;
        padding: 0 80px;
    }

    /* Tabs más elegantes */
    .stTabs [role="tab"] {
        font-weight: 600;
        padding: 10px 16px;
        border-radius: 8px;
    }

    .stTabs [aria-selected="true"] {
        background-color: #E9D8FD !important;
        color: #4B0082 !important;
        border-bottom: 3px solid #5A2D82 !important;
    }

    </style>
""", unsafe_allow_html=True)

# --------- VARIABLES DE SESIÓN ----------
if "sesion_iniciada" not in st.session_state:
    st.session_state["sesion_iniciada"] = False
if "pagina_actual" not in st.session_state:
    st.session_state["pagina_actual"] = "inicio"

# ---------------- PANELS ----------------
def panel_secretaria():
    st.title("📋 Panel de Secretaria")
    st.caption("Gestión general de grupos y actividades")

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
        if st.button("Cerrar sesión", type="primary"):
            st.session_state.clear()
            st.session_state["sesion_iniciada"] = False
            st.session_state["pagina_actual"] = "sesion_cerrada"
            st.rerun()


def panel_presidente():
    st.title("🏛️ Panel de Presidente")
    st.caption("Supervisión de grupos y actividades principales")

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
        if st.button("Cerrar sesión", type="primary"):
            st.session_state.clear()
            st.session_state["sesion_iniciada"] = False
            st.session_state["pagina_actual"] = "sesion_cerrada"
            st.rerun()


def panel_promotora(usuario):
    st.title("👩‍💼 Panel de Promotora")
    st.caption("Supervisión y registro administrativo")

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
        if st.button("Cerrar sesión", type="primary"):
            st.session_state.clear()
            st.session_state["sesion_iniciada"] = False
            st.session_state["pagina_actual"] = "sesion_cerrada"
            st.rerun()


def panel_admin():
    st.title("🧑‍💻 Panel de Administradora")
    st.caption("Control total del sistema GAPCSV")

    tabs = st.tabs([
        "📊 Consolidado Distritos",
        "🧑‍💻 Registrar Usuario",
        "🚪 Cerrar sesión"
    ])

    with tabs[0]:
        st.info("Aquí irá el consolidado general por distrito")

    with tabs[1]:
        registrar_usuario()

    with tabs[2]:
        if st.button("Cerrar sesión", type="primary"):
            st.session_state.clear()
            st.session_state["sesion_iniciada"] = False
            st.session_state["pagina_actual"] = "sesion_cerrada"
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
    # --- PANTALLA SIN SESIÓN ---
    if st.session_state["pagina_actual"] == "sesion_cerrada":
        st.success("Sesión finalizada.")
        if st.button("Volver al inicio"):
            st.session_state["pagina_actual"] = "inicio"
            st.rerun()

    elif st.session_state["pagina_actual"] == "inicio":

        st.markdown("<h1 class='titulo-principal'>Sistema GAPCSV</h1>", unsafe_allow_html=True)
        st.markdown("<h3 class='subtitulo-principal'>Grupos de Ahorro y Préstamo Comunitario</h3>", unsafe_allow_html=True)

        st.markdown(
            "<p class='texto-objetivo'>Este sistema tiene como objetivo facilitar la gestión, "
            "organización y seguimiento administrativo de los grupos de ahorro, "
            "promoviendo la transparencia, participación y desarrollo comunitario.</p>",
            unsafe_allow_html=True
        )

        st.write("")
        st.write("")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔑 Iniciar sesión", use_container_width=True):
                st.session_state["pagina_actual"] = "login"
                st.rerun()
        with col2:
            if st.button("📝 Registrarme", use_container_width=True):
                st.session_state["pagina_actual"] = "registro"
                st.rerun()

    elif st.session_state["pagina_actual"] == "login":
        login()

    elif st.session_state["pagina_actual"] == "registro":
        registrar_usuario()
