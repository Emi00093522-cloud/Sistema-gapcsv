import streamlit as st
from modulos.registro_usuario import registrar_usuario
from modulos.login import login
from modulos.promotora import mostrar_promotora
from modulos.distrito import mostrar_distrito

from modulos.asistencia import mostrar_asistencia
from modulos.integrada import mostrar_gestion_integrada
from modulos.grupos import mostrar_grupos
from modulos.reglamentos import mostrar_reglamentos
from modulos.miembros import mostrar_miembro

# Agregar importación del módulo ciclo (si existe)
try:
    from modulos.ciclo import mostrar_ciclo
except ImportError:
    # Si el módulo no existe, creamos una función temporal
    def mostrar_ciclo():
        st.warning("Módulo de Cierre de Ciclo en desarrollo")


# ---------------------------------------------------------
# 🔧 FIX SOLO PARA VISIBILIDAD DE TEXTO EN SELECT / INPUTS
# ---------------------------------------------------------
st.markdown("""
<style>
/* Texto dentro de inputs */
input, textarea { color: #000 !important; }

/* Texto visible en select actual */
.stSelectbox div[data-baseweb="select"] * { color: #000 !important; }

/* Texto visible en opciones desplegadas */
ul[role="listbox"] li { color: #000 !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------------
st.set_page_config(page_title="Sistema GAPCSV", page_icon="💙", layout="wide")

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
        "🔄 Cierre de Ciclo",  # Nueva pestaña agregada
        "🚪 Cerrar sesión"
    ])

    with tabs[0]: mostrar_grupos()
    with tabs[1]: mostrar_miembro()
    with tabs[2]: mostrar_reglamentos()
    with tabs[3]: mostrar_gestion_integrada()
    with tabs[4]: mostrar_ciclo()  # Mostrar el módulo de cierre de ciclo

        
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
        "🔄 Cierre de Ciclo",  # También para presidente si es necesario
        "🚪 Cerrar sesión"
    ])

    with tabs[0]: mostrar_grupos()
    with tabs[1]: mostrar_reglamentos()
    with tabs[2]: mostrar_miembro()
    with tabs[3]: mostrar_prestamo()
    with tabs[4]: mostrar_ciclo()  # Cierre de ciclo para presidente

    with tabs[5]:
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
        "🔄 Cierre de Ciclo",  # Para promotora si es necesario
        "🚪 Cerrar sesión"
    ])

    with tabs[0]:
        st.success(f"Bienvenida, {usuario} 🌟")
        st.info("📊 Dashboard general de promotoras en desarrollo...")

    with tabs[1]: mostrar_promotora()
    with tabs[2]: mostrar_distrito()
    with tabs[3]: mostrar_ciclo()  # Cierre de ciclo para promotora

    with tabs[4]:
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
        "🔄 Cierre de Ciclo",  # Para administradora
        "🚪 Cerrar sesión"
    ])

    with tabs[0]:
        st.info("📊 Aquí irá el consolidado general por distrito.")

    with tabs[1]: registrar_usuario()
    with tabs[2]: mostrar_ciclo()  # Cierre de ciclo para administradora

    with tabs[3]:
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
        st.subheader("Grupos de Ahorro y Préstamos Comunitarios 🤝🌱💰")

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
