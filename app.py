import streamlit as st
from modulos.registro_usuario import registrar_usuario
from modulos.login import login
from modulos.promotora import mostrar_promotora
from modulos.distrito import mostrar_distrito
from modulos.grupos import mostrar_grupos
from modulos.reglamentos import mostrar_reglamentos
from modulos.miembros import mostrar_miembro
from modulos.prestamo import mostrar_prestamo
from modulos.reuniones import mostrar_reuniones
from modulos.asistencia import mostrar_asistencia

# ⚙️ Configuración
st.set_page_config(page_title="Sistema GAPCSV", page_icon="💜", layout="centered")

# Estado
if "sesion_iniciada" not in st.session_state:
    st.session_state["sesion_iniciada"] = False
if "pagina_actual" not in st.session_state:
    st.session_state["pagina_actual"] = "inicio"

# Estilos globales
st.markdown("""
<style>
.btn-opcion {
    width: 100%;
    background:#E8DAEF;
    padding:15px;
    border-radius:12px;
    text-align:center;
    margin:8px 0;
    font-size:1.2em;
    border:2px solid #BB8FCE;
}
.btn-opcion:hover {
    background:#D2B4DE;
    cursor:pointer;
}
.titulo-panel {
    text-align:center;
    color:#6C3483;
    font-size:2em;
    font-weight:bold;
    margin-bottom:10px;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------

# PANEL PARA ADMINISTRADORA
def panel_admin():
    st.markdown("<h2 class='titulo-panel'>Panel de Administradora</h2>", unsafe_allow_html=True)
    
    if st.button("📊 Consolidado general por distrito", key="admin_cons"):
        st.session_state["pagina_actual"] = "admin_consolidado"
        st.rerun()

    if st.button("🧑‍💼 Registrar usuario", key="admin_reg"):
        st.session_state["pagina_actual"] = "admin_registrar_usuario"
        st.rerun()

    if st.button("🚪 Cerrar sesión"):
        st.session_state.clear()
        st.session_state["sesion_iniciada"] = False
        st.session_state["pagina_actual"] = "inicio"
        st.rerun()

# PANEL DE SECRETARIA
def panel_secretaria():
    st.markdown("<h2 class='titulo-panel'>Panel de Secretaria</h2>", unsafe_allow_html=True)

    if st.button("👥 Registrar Grupo"):
        st.session_state["pagina_actual"] = "grupos_registrar"
        st.rerun()

    if st.button("📜 Registrar Reglamentos"):
        st.session_state["pagina_actual"] = "reglamentos_registrar"
        st.rerun()

    if st.button("👥 Registrar Miembros"):
        st.session_state["pagina_actual"] = "miembro_registrar"
        st.rerun()

    if st.button("💰 Registrar Préstamo"):
        st.session_state["pagina_actual"] = "prestamo_registrar"
        st.rerun()

    if st.button("📅 Registrar Reuniones"):
        st.session_state["pagina_actual"] = "reuniones_registrar"
        st.rerun()

    if st.button("📝 Control de asistencia"):
        st.session_state["pagina_actual"] = "asistencia_registrar"
        st.rerun()

    if st.button("🚪 Cerrar sesión"):
        st.session_state.clear()
        st.session_state["sesion_iniciada"] = False
        st.session_state["pagina_actual"] = "inicio"
        st.rerun()

# PANEL DE PRESIDENTE
def panel_presidente():
    st.markdown("<h2 class='titulo-panel'>Panel de Presidente</h2>", unsafe_allow_html=True)

    if st.button("👥 Registrar Grupo"):
        st.session_state["pagina_actual"] = "grupos_registrar"
        st.rerun()

    if st.button("📜 Registrar Reglamentos"):
        st.session_state["pagina_actual"] = "reglamentos_registrar"
        st.rerun()

    if st.button("👥 Registrar Miembros"):
        st.session_state["pagina_actual"] = "miembro_registrar"
        st.rerun()

    if st.button("💰 Registrar Préstamo"):
        st.session_state["pagina_actual"] = "prestamo_registrar"
        st.rerun()

    if st.button("🚪 Cerrar sesión"):
        st.session_state.clear()
        st.session_state["sesion_iniciada"] = False
        st.session_state["pagina_actual"] = "inicio"
        st.rerun()

# PANEL DE PROMOTORA
def panel_promotora():
    st.markdown("<h2 class='titulo-panel'>Panel de Promotora</h2>", unsafe_allow_html=True)

    if st.button("📈 Dashboard promotora"):
        st.session_state["pagina_actual"] = "prom_dashboard"
        st.rerun()

    if st.button("👩‍💼 Registrar promotora"):
        st.session_state["pagina_actual"] = "prom_registrar"
        st.rerun()

    if st.button("🏛️ Registrar distrito"):
        st.session_state["pagina_actual"] = "dist_registrar"
        st.rerun()

    if st.button("🚪 Cerrar sesión"):
        st.session_state.clear()
        st.session_state["sesion_iniciada"] = False
        st.session_state["pagina_actual"] = "inicio"
        st.rerun()

# ------------------------------------------------------------------

# RENDER DEL SISTEMA
if st.session_state["sesion_iniciada"]:

    usuario = st.session_state.get("usuario", "Usuario")
    cargo = st.session_state.get("cargo_de_usuario", "").strip().upper()
    tipo = st.session_state.get("tipo_usuario", "").strip().lower()

    # Mostrar el panel correspondiente
    if cargo == "SECRETARIA":
        panel_secretaria()
    elif cargo == "PRESIDENTE":
        panel_presidente()
    elif cargo == "PROMOTORA" or tipo == "promotora":
        panel_promotora()
    elif tipo == "administradora":
        panel_admin()
    else:
        st.write("Usuario sin rol definido.")

    # ----------- RUTAS A LOS MÓDULOS -------------
    if st.session_state["pagina_actual"] == "grupos_registrar":
        mostrar_grupos()

    elif st.session_state["pagina_actual"] == "reglamentos_registrar":
        mostrar_reglamentos()

    elif st.session_state["pagina_actual"] == "miembro_registrar":
        mostrar_miembro()

    elif st.session_state["pagina_actual"] == "prestamo_registrar":
        mostrar_prestamo()

    elif st.session_state["pagina_actual"] == "reuniones_registrar":
        mostrar_reuniones()

    elif st.session_state["pagina_actual"] == "asistencia_registrar":
        mostrar_asistencia()

    elif st.session_state["pagina_actual"] == "prom_registrar":
        mostrar_promotora()

    elif st.session_state["pagina_actual"] == "dist_registrar":
        mostrar_distrito()

    elif st.session_state["pagina_actual"] == "prom_dashboard":
        st.title("📈 Dashboard de Promotora")

    elif st.session_state["pagina_actual"] == "admin_consolidado":
        st.title("📊 Consolidado general por distrito")

    elif st.session_state["pagina_actual"] == "admin_registrar_usuario":
        registrar_usuario()

else:
    # Pantallas sin sesión
    if st.session_state["pagina_actual"] == "login":
        login()
    elif st.session_state["pagina_actual"] == "registro":
        registrar_usuario()
    else:
        st.title("Bienvenido al Sistema GAPCSV")
        if st.button("🔑 Iniciar sesión"):
            st.session_state["pagina_actual"] = "login"
            st.rerun()
        if st.button("📝 Registrarme"):
            st.session_state["pagina_actual"] = "registro"
            st.rerun()
