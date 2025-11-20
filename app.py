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
st.set_page_config(page_title="Sistema GAPCSV", page_icon="💼", layout="wide")

# ------------ ESTILO CORPORATIVO ---------------
st.markdown("""
    <style>
    body { background-color: #F5F6FA !important; }
    h1, h2, h3, h4, h5, label { font-family: 'Roboto', sans-serif !important; color: #5A2D82 !important; }
    p, div, span { font-family: 'Roboto', sans-serif !important; color: #1A1A1A !important; }
    .titulo-principal { color: #5A2D82 !important; font-size: 50px !important; font-weight: 900; text-align: center; }
    .subtitulo-principal { color: #7D5BA6 !important; font-size: 22px; text-align: center; }
    .texto-objetivo { color: #2C3E50 !important; font-size: 17px; text-align: center; padding: 0 90px; }
    .card { padding: 25px; background: white; border-radius: 10px; box-shadow: 0px 2px 6px rgba(0,0,0,0.12); margin-bottom: 20px; }
    .stTabs [role="tab"] { font-weight: 600; padding: 12px 18px; border-radius: 6px; border: 1px solid #5A2D82 !important; background-color: #F3E8FF; color: #5A2D82 !important; }
    .stTabs [aria-selected="true"] { background-color: #5A2D82 !important; color: white !important; }
    .stButton>button { background-color: #5A2D82 !important; color: white !important; border-radius: 6px !important; padding: 8px 20px !important; font-weight: 600 !important; }
    .stButton>button:hover { background-color: #7D5BA6 !important; transform: scale(1.02); }
    </style>
""", unsafe_allow_html=True)

# --------- VARIABLES DE SESIÓN ----------
if "sesion_iniciada" not in st.session_state:
    st.session_state["sesion_iniciada"] = False
if "pagina_actual" not in st.session_state:
    st.session_state["pagina_actual"] = "inicio"

# ---------------- PANEL SECRETARIA ----------------
def panel_secretaria():
    st.markdown("<div class='card'><h1>📋 Panel de Secretaria</h1><p>Gestión general de grupos y actividades</p></div>", unsafe_allow_html=True)
    tabs = st.tabs(["👥 Registrar Grupo", "📜 Reglamentos", "👥 Miembros", "💰 Préstamos", "📅 Reuniones", "📝 Asistencia", "🚪 Cerrar sesión"])
    with tabs[0]: mostrar_grupos()
    with tabs[1]: mostrar_reglamentos()
    with tabs[2]: mostrar_miembro()
    with tabs[3]: mostrar_prestamo()
    with tabs[4]: mostrar_reuniones()
    with tabs[5]: mostrar_asistencia()
    with tabs[6]:
        if st.button("Cerrar sesión"):
            st.session_state.clear(); st.session_state["sesion_iniciada"] = False; st.session_state["pagina_actual"] = "sesion_cerrada"; st.rerun()

# ---------------- PANEL PRESIDENTE ----------------
def panel_presidente():
    st.markdown("<div class='card'><h1>🏛️ Panel de Presidente</h1><p>Supervisión de grupos y actividades</p></div>", unsafe_allow_html=True)
    tabs = st.tabs(["👥 Registrar Grupo", "📜 Reglamentos", "👥 Miembros", "💰 Préstamos", "🚪 Cerrar sesión"])
    with tabs[0]: mostrar_grupos()
    with tabs[1]: mostrar_reglamentos()
    with tabs[2]: mostrar_miembro()
    with tabs[3]: mostrar_prestamo()
    with tabs[4]:
        if st.button("Cerrar sesión"):
            st.session_state.clear(); st.session_state["sesion_iniciada"] = False; st.session_state["pagina_actual"] = "sesion_cerrada"; st.rerun()

# ---------------- PANEL PROMOTORA ----------------
def panel_promotora(usuario):
    st.markdown("<div class='card'><h1>👩‍💼 Panel de Promotora</h1><p>Supervisión y administración territorial</p></div>", unsafe_allow_html=True)
    tabs = st.tabs(["📈 Dashboard", "👩‍💼 Registro Promotora", "🏛️ Distrito", "🚪 Cerrar sesión"])
    with tabs[0]: st.success(f"Bienvenida, {usuario}"); st.info("Dashboard general de promotoras")
    with tabs[1]: mostrar_promotora()
    with tabs[2]: mostrar_distrito()
    with tabs[3]:
        if st.button("Cerrar sesión"):
            st.session_state.clear(); st.session_state["sesion_iniciada"] = False; st.session_state["pagina_actual"] = "sesion_cerrada"; st.rerun()

# ---------------- PANEL ADMINISTRADORA ----------------
def panel_admin():
    st.markdown("<div class='card'><h1>🧑‍💻 Panel de Administradora</h1><p>Gestión integral del sistema</p></div>", unsafe_allow_html=True)
    tabs = st.tabs(["📊 Consolidado Distritos", "🧑‍💻 Registrar Usuario", "🚪 Cerrar sesión"])
    with tabs[0]: st.info("Aquí irá el consolidado general por distrito")
    with tabs[1]: registrar_usuario()
    with tabs[2]:
        if st.button("Cerrar sesión"):
            st.session_state.clear(); st.session_state["sesion_iniciada"] = False; st.session_state["pagina_actual"] = "sesion_cerrada"; st.rerun()

# ----------- APP FLOW ----------
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
        st.markdown("<p class='texto-objetivo'>Plataforma institucional para la gestión, administración y control operativo...</p>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔑 Iniciar sesión", use_container_width=True): st.session_state["pagina_actual"] = "login"; st.rerun()
        with col2:
            if st.button("📝 Registrarme", use_container_width=True): st
