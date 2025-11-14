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

# 📌 NUEVO MÓDULO ASISTENCIA
from modulos.asistencia import mostrar_asistencia

# ⚙️ Configuración
st.set_page_config(page_title="Sistema GAPCSV", page_icon="💜", layout="centered")

# 🧠 Estado
if "sesion_iniciada" not in st.session_state:
    st.session_state["sesion_iniciada"] = False
if "pagina_actual" not in st.session_state:
    st.session_state["pagina_actual"] = "inicio"

# --- ESTILOS ---
st.markdown("""
    <style>
        .titulo { text-align:center; color:#6C3483; font-size:2.2em; font-weight:bold; }
        .subtitulo { text-align:center; color:#2E4053; font-size:1.3em; }
        .descripcion { background:#F8F9F9; border-radius:12px; padding:20px; 
                       margin-top:10px; box-shadow:0 0 10px rgba(108,52,131,.2); }
        .emoji { font-size:1.4em; }
        .sesion-cerrada { text-align:center; padding:20px; background:#f8f9fa; 
                          border-radius:10px; margin:20px 0; }
    </style>
""", unsafe_allow_html=True)

# 🔧 Utilidad de menú
def make_menu(options_dict, default_label=None, key="menu"):
    labels = list(options_dict.keys())
    index = labels.index(default_label) if default_label in labels else 0
    return options_dict[st.sidebar.selectbox("Ir a:", labels, index=index, key=key)]

# --- APLICACIÓN ---
if st.session_state["sesion_iniciada"]:

    usuario = st.session_state.get("usuario", "Usuario")
    tipo = (st.session_state.get("tipo_usuario", "Desconocido") or "").strip().lower()
    cargo = st.session_state.get("cargo_de_usuario", "").strip().upper()

    st.sidebar.title("📋 Menú principal")
    st.sidebar.write(f"👤 *{usuario}* ({cargo})")

    # ------------------------------ SECRETARIA / PRESIDENTE ------------------------------
    if cargo in ("SECRETARIA", "PRESIDENTE"):

        if cargo == "SECRETARIA":
            options = {
                "👥 Registro de grupos": "grupos_registrar",
                "📜 Registro de reglamentos": "reglamentos_registrar",
                "👥 Registro de miembro": "miembro_registrar",
                "💰 Registro de préstamo": "prestamo_registrar",
                "📅 Registro de reuniones": "reuniones_registrar",
                "📝 Control de asistencia": "asistencia_registrar",  # <-- AGREGADO
                "🚪 Cerrar sesión": "logout"
            }
        else:
            options = {
                "👥 Registro de grupos": "grupos_registrar",
                "📜 Registro de reglamentos": "reglamentos_registrar",
                "👥 Registro de miembro": "miembro_registrar",
                "💰 Registro de préstamo": "prestamo_registrar",
                "🚪 Cerrar sesión": "logout"
            }

        route = make_menu(options, "👥 Registro de grupos", "menu_secret_pres")

        if route == "grupos_registrar":
            st.title("👥 Registrar Grupo")
            mostrar_grupos()

        elif route == "reglamentos_registrar":
            st.title("📜 Registrar Reglamento")
            mostrar_reglamentos()

        elif route == "miembro_registrar":
            st.title("👥 Registro de miembros")
            mostrar_miembro()

        elif route == "prestamo_registrar":
            st.title("💰 Registrar Préstamo")
            mostrar_prestamo()

        elif route == "reuniones_registrar":
            st.title("📅 Registro de Reuniones")
            mostrar_reuniones()

        # ⭐ NUEVO MÓDULO DE ASISTENCIA
        elif route == "asistencia_registrar":
            st.title("📝 Control de Asistencia")
            mostrar_asistencia()

        elif route == "logout":
            st.session_state.clear()
            st.session_state["sesion_iniciada"] = False
            st.session_state["pagina_actual"] = "sesion_cerrada"
            st.rerun()

    # ------------------------------ ADMINISTRADORA ------------------------------
    elif tipo == "administradora":
        options = {
            "📊 Consolidado por distrito": "admin_consolidado",
            "🧑‍💻 Registrar usuario": "admin_registrar_usuario",
            "🚪 Cerrar sesión": "logout"
        }

        route = make_menu(options, "📊 Consolidado por distrito")

        if route == "admin_consolidado":
            st.title("📊 Consolidado general por distrito 💲")

        elif route == "admin_registrar_usuario":
            registrar_usuario()

        elif route == "logout":
            st.session_state.clear()
            st.session_state["sesion_iniciada"] = False
            st.session_state["pagina_actual"] = "sesion_cerrada"
            st.rerun()

    # ------------------------------ PROMOTORA ------------------------------
    elif tipo == "promotora" or cargo == "PROMOTORA":

        options = {
            "📈 Dashboard promotora": "prom_dashboard",
            "👩‍💼 Registro de promotora": "prom_registrar",
            "🏛️ Registro de distrito": "dist_registrar",
            "🚪 Cerrar sesión": "logout"
        }

        route = make_menu(options, "📈 Dashboard promotora")

        if route == "prom_dashboard":
            st.title("👩‍💼 Dashboard Promotora")
            st.success(f"¡Bienvenida, {usuario}!")

        elif route == "prom_registrar":
            mostrar_promotora()

        elif route == "dist_registrar":
            mostrar_distrito()

        elif route == "logout":
            st.session_state.clear()
            st.session_state["sesion_iniciada"] = False
            st.session_state["pagina_actual"] = "sesion_cerrada"
            st.rerun()

    # ------------------------------ OTROS TIPOS ------------------------------
    else:
        options = {
            "👥 Registro de grupos": "grupos_registrar",
            "📜 Registro de reglamentos": "reglamentos_registrar",
            "👥 Registro de miembro": "miembro_registrar",
            "🚪 Cerrar sesión": "logout"
        }

        route = make_menu(options, "👥 Registro de grupos")

        if route == "grupos_registrar":
            mostrar_grupos()

        elif route == "reglamentos_registrar":
            mostrar_reglamentos()

        elif route == "miembro_registrar":
            mostrar_miembro()

        elif route == "logout":
            st.session_state.clear()
            st.session_state["sesion_iniciada"] = False
            st.session_state["pagina_actual"] = "sesion_cerrada"
            st.rerun()

# ------------------------------ LOGIN / REGISTRO ------------------------------
else:

    if st.session_state["pagina_actual"] == "sesion_cerrada":
        st.markdown("<div class='sesion-cerrada'>", unsafe_allow_html=True)
        st.markdown("### ✅ Sesión cerrada")
        if st.button("🏠 Volver al inicio"):
            st.session_state["pagina_actual"] = "inicio"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    elif st.session_state["pagina_actual"] == "inicio":
        st.markdown("<h1 class='titulo'> Bienvenido al Sistema GAPCSV </h1>", unsafe_allow_html=True)
        st.markdown("<h3 class='subtitulo'>Grupos de Ahorro y Préstamo Comunitario </h3>", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        if col1.button("🔑 Iniciar sesión"):
            st.session_state["pagina_actual"] = "login"
            st.rerun()
        if col2.button("📝 Registrarme"):
            st.session_state["pagina_actual"] = "registro"
            st.rerun()

    elif st.session_state["pagina_actual"] == "login":
        login()

    elif st.session_state["pagina_actual"] == "registro":
        registrar_usuario()
