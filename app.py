import streamlit as st
from modulos.registro_usuario import registrar_usuario
from modulos.login import login
from modulos.promotora import mostrar_promotora
from modulos.distrito import mostrar_distrito
from modulos.grupos import mostrar_grupos
from modulos.reglamentos import mostrar_reglamentos  # <-- import agregado
from modulos.miembros import mostrar_miembro

# ⚙️ Configuración: SIEMPRE al inicio
st.set_page_config(page_title="Sistema GAPCSV", page_icon="💜", layout="centered")

# 🧠 Estado
if "sesion_iniciada" not in st.session_state:
    st.session_state["sesion_iniciada"] = False
if "pagina_actual" not in st.session_state:
    st.session_state["pagina_actual"] = "inicio"

# --- NAVEGACIÓN LATERAL ---
st.sidebar.title("📋 Menú principal")

# 💅 Estilos
st.markdown("""
    <style>
        .titulo { text-align:center; color:#6C3483; font-size:2.2em; font-weight:bold; }
        .subtitulo { text-align:center; color:#2E4053; font-size:1.3em; }
        .descripcion { background:#F8F9F9; border-radius:12px; padding:20px; margin-top:10px; box-shadow:0 0 10px rgba(108,52,131,.2); }
        .emoji { font-size:1.4em; }
        .sesion-cerrada { text-align:center; padding:20px; background:#f8f9fa; border-radius:10px; margin:20px 0; }
    </style>
""", unsafe_allow_html=True)

def dashboard_promotora(usuario):
    st.title("👩‍💼 Dashboard de Promotora")
    st.success(f"¡Bienvenida, {usuario}!")
    st.info("Desde aquí puedes gestionar promotoras, distritos y grupos.")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Tu Cargo", "PROMOTORA")
    with col2:
        st.metric("Acciones Disponibles", "3")
    with col3:
        st.metric("Módulos", "Promotora, Distrito, Grupos")

# Utilidad: mapea etiquetas (lo que ve el usuario) a claves internas
def make_menu(options_dict, default_label=None, key="menu_principal"):
    labels = list(options_dict.keys())
    if default_label and default_label in labels:
        index = labels.index(default_label)
    else:
        index = 0
    chosen = st.sidebar.selectbox("Ir a:", labels, index=index, key=key)
    return options_dict[chosen]

# Si hay sesión iniciada
if st.session_state["sesion_iniciada"]:
    usuario = st.session_state.get("usuario", "Usuario")
    tipo = (st.session_state.get("tipo_usuario", "Desconocido") or "").strip().lower()
    cargo = st.session_state.get("cargo_usuario").strip().upper()

    st.sidebar.write(f"👤 **{usuario}** ({cargo})")

    # --- Si es SECRETARIA o PRESIDENTE: MENÚ REDUCIDO SOLO CON 3 OPCIONES ---
    if cargo in ("SECRETARIA", "PRESIDENTE"):
        options = {
            "👥 Registro de grupos": "grupos_registrar",
            "📜 Registro de reglamentos": "reglamentos_registrar",
            "🚪 Cerrar sesión": "logout"
        }
        route = make_menu(options, default_label="👥 Registro de grupos", key="menu_secret_pres_reducido")

        if route == "grupos_registrar":
            st.title("👥 Registrar Grupo")
            mostrar_grupos()
        elif route == "reglamentos_registrar":
            st.title("📜 Registrar Reglamento")
            mostrar_reglamentos()
        elif route == "logout":
            st.session_state.clear()
            st.session_state["sesion_iniciada"] = False
            st.session_state["pagina_actual"] = "sesion_cerrada"
            st.rerun()

    else:
        # Usuario no SECRETARIA/PRESIDENTE: menú normal por tipo
        if tipo == "administradora":
            options = {
                "📊 Consolidado por distrito": "admin_consolidado",
                "🧑‍💻 Registrar usuario": "admin_registrar_usuario",
                "🚪 Cerrar sesión": "logout"
            }
            route = make_menu(options, default_label="📊 Consolidado por distrito")

            if route == "admin_consolidado":
                st.title("📊 Consolidado general por distrito 💲")
                # mostrar_ahorros()
            elif route == "admin_registrar_usuario":
                registrar_usuario()
            elif route == "logout":
                st.session_state.clear()
                st.session_state["sesion_iniciada"] = False
                st.session_state["pagina_actual"] = "sesion_cerrada"
                st.rerun()

        elif (tipo == "promotora") or (cargo == "PROMOTORA"):
            options = {
                "📈 Dashboard promotora": "prom_dashboard",
                "👩‍💼 Registro de promotora": "prom_registrar",
                "🏛️ Registro de distrito": "dist_registrar",
                "🚪 Cerrar sesión": "logout"
            }
            route = make_menu(options, default_label="📈 Dashboard promotora")

            if route == "prom_dashboard":
                dashboard_promotora(usuario)
            elif route == "prom_registrar":
                st.title("👩‍💼 Registrar Nueva Promotora")
                mostrar_promotora()
            elif route == "dist_registrar":
                st.title("🏛️ Registrar Nuevo Distrito")
                mostrar_distrito()
           
            elif route == "logout":
                st.session_state.clear()
                st.session_state["sesion_iniciada"] = False
                st.session_state["pagina_actual"] = "sesion_cerrada"
                st.rerun()

        else:
            # Otros tipos
            options = {
                "👥 Registro de grupos": "grupos_registrar",
                "📜 Registro de reglamentos": "reglamentos_registrar",
                "👥 Registro de miembro": "miembro_registrar",
                "🚪 Cerrar sesión": "logout"
            }
            route = make_menu(options, default_label="📊 Dashboard")

            if route == "otros_dashboard":
                st.title("📊 Dashboard")
            
            elif route == "grupos_registrar":
                st.title("👥 Registrar Nuevo Grupo")
                mostrar_grupos()
                
            elif route == "reglamentos_registrar":
                st.title("📜 Registrar Reglamento")
                mostrar_reglamentos()

            elif route == "miembro_registrar": 
                st.title("👥 Registro de miembros") 
                mostrar_miembro()
            
            elif route == "logout":
                st.session_state.clear()
                st.session_state["sesion_iniciada"] = False
                st.session_state["pagina_actual"] = "sesion_cerrada"
                st.rerun()

# Sin sesión
else:
    if st.session_state["pagina_actual"] == "sesion_cerrada":
        st.markdown("<div class='sesion-cerrada'>", unsafe_allow_html=True)
        st.markdown("### ✅ Sesión finalizada")
        st.markdown("<p>Has cerrado sesión exitosamente.</p>", unsafe_allow_html=True)
        if st.button("🏠 Volver al inicio"):
            st.session_state["pagina_actual"] = "inicio"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    elif st.session_state["pagina_actual"] == "inicio":
        st.markdown("<h1 class='titulo'> Bienvenido al Sistema GAPCSV </h1>", unsafe_allow_html=True)
        st.markdown("<h3 class='subtitulo'>Grupos de Ahorro y Prestamo Comunitario </h3>", unsafe_allow_html=True)
        st.markdown("""
        <div class='descripcion'>
            <p class='emoji'>Este sistema te ayuda a registrar, monitorear y consolidar los ahorros de los grupos comunitarios.</p>
            <p class='emoji'>Promueve la colaboración, la transparencia y el crecimiento económico local 🤝.</p>
            <p>Si tienes cuenta, inicia sesión.<br>
            Si aún no tienes usuario, puedes registrarte fácilmente. 🌱</p>
        </div>
        """, unsafe_allow_html=True)

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


