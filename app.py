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

# ================================
# CONFIGURACIÓN GENERAL
# ================================
st.set_page_config(
    page_title="Sistema GAPCSV",
    page_icon="💙",
    layout="wide"
)

# ================================
# ESTILOS (CSS CORPORATIVO AZUL SUAVE)
# ================================
st.markdown("""
<style>

:root {
    --azul-suave: #4A90E2;
    --azul-claro: #E7F0FA;
    --gris-texto: #3A3A3A;
    --gris-suave: #F7F9FB;
    --borde-suave: #D9E4F1;
}

/* Fondo general */
body {
    background-color: var(--gris-suave) !important;
}

/* TITULOS PRINCIPALES */
h1, h2, h3 {
    color: var(--gris-texto) !important;
    font-weight: 700 !important;
}

/* Tarjetas elegantes */
.card {
    background: white;
    padding: 25px;
    border-radius: 12px;
    border: 1px solid var(--borde-suave);
    box-shadow: 0px 4px 10px rgba(0,0,0,0.05);
    margin-bottom: 25px;
}

/* Botones */
div.stButton > button {
    background-color: var(--azul-suave);
    color: white;
    padding: 10px 18px;
    border-radius: 8px;
    border: none;
    font-weight: 600;
}

div.stButton > button:hover {
    background-color: #357ABD;
    color: white;
}

/* Tabs */
div[data-baseweb="tab-list"] {
    background-color: var(--azul-claro);
    padding: 10px;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# ======================================
# SESIÓN
# ======================================
if "sesion_iniciada" not in st.session_state:
    st.session_state["sesion_iniciada"] = False
if "pagina_actual" not in st.session_state:
    st.session_state["pagina_actual"] = "inicio"


# ================================
# PANEL DE SECRETARIA
# ================================
def panel_secretaria():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.title("📘 Panel de Secretaría")
    st.markdown('</div>', unsafe_allow_html=True)

    tabs = st.tabs([
        "📁 Registrar Grupo",
        "📜 Reglamentos",
        "👥 Miembros",
        "💰 Préstamos",
        "📅 Reuniones",
        "📝 Asistencia",
        "🚪 Cerrar sesión"
    ])

    with tabs[0]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        mostrar_grupos()
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[1]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        mostrar_reglamentos()
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[2]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        mostrar_miembro()
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[3]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        mostrar_prestamo()
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[4]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        mostrar_reuniones()
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[5]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        mostrar_asistencia()
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[6]:
        if st.button("Cerrar sesión"):
            st.session_state.clear()
            st.session_state["sesion_iniciada"] = False
            st.session_state["pagina_actual"] = "sesion_cerrada"
            st.rerun()


# ================================
# PANEL DE PRESIDENTE
# ================================
def panel_presidente():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.title("📘 Panel de Presidente")
    st.markdown('</div>', unsafe_allow_html=True)

    tabs = st.tabs([
        "📁 Registrar Grupo",
        "📜 Reglamentos",
        "👥 Miembros",
        "💰 Préstamos",
        "🚪 Cerrar sesión"
    ])

    with tabs[0]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        mostrar_grupos()
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[1]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        mostrar_reglamentos()
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[2]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        mostrar_miembro()
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[3]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        mostrar_prestamo()
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[4]:
        if st.button("Cerrar sesión"):
            st.session_state.clear()
            st.session_state["sesion_iniciada"] = False
            st.session_state["pagina_actual"] = "sesion_cerrada"
            st.rerun()


# ================================
# PANEL DE PROMOTORA
# ================================
def panel_promotora(usuario):
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.title("📊 Panel de Promotora")
    st.markdown('</div>', unsafe_allow_html=True)

    tabs = st.tabs([
        "📈 Dashboard",
        "👩‍💼 Registro Promotora",
        "🏛️ Distrito",
        "🚪 Cerrar sesión"
    ])

    with tabs[0]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.success(f"Bienvenida, {usuario}")
        st.info("Dashboard general de promotoras")
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[1]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        mostrar_promotora()
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[2]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        mostrar_distrito()
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[3]:
        if st.button("Cerrar sesión"):
            st.session_state.clear()
            st.session_state["sesion_iniciada"] = False
            st.session_state["pagina_actual"] = "sesion_cerrada"
            st.rerun()


# ================================
# PANEL DE ADMINISTRADORA
# ================================
def panel_admin():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.title("🧑‍💻 Panel de Administradora")
    st.markdown('</div>', unsafe_allow_html=True)

    tabs = st.tabs([
        "📊 Consolidado Distritos",
        "🧑‍💻 Registrar Usuario",
        "🚪 Cerrar sesión"
    ])

    with tabs[0]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.info("Aquí irá el consolidado general por distrito")
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[1]:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        registrar_usuario()
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[2]:
        if st.button("Cerrar sesión"):
            st.session_state.clear()
            st.session_state["sesion_iniciada"] = False
            st.session_state["pagina_actual"] = "sesion_cerrada"
            st.rerun()


# ================================
# FLUJO DE LA APLICACIÓN
# ================================
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
    # ================
    # PANTALLA SIN SESIÓN (BIENVENIDA)
    # ================
    if st.session_state["pagina_actual"] == "sesion_cerrada":
        st.success("Sesión finalizada.")
        if st.button("Volver al inicio"):
            st.session_state["pagina_actual"] = "inicio"
            st.rerun()

    elif st.session_state["pagina_actual"] == "inicio":

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.title("💙 Sistema GAPCSV")
        st.subheader("Plataforma oficial de Grupos de Ahorro y Préstamo Comunitario")
        st.markdown('</div>', unsafe_allow_html=True)

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
        st.markdown('<div class="card">', unsafe_allow_html=True)
        login()
        st.markdown('</div>', unsafe_allow_html=True)

    elif st.session_state["pagina_actual"] == "registro":
        st.markdown('<div class="card">', unsafe_allow_html=True)
        registrar_usuario()
        st.markdown('</div>', unsafe_allow_html=True)
