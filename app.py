import streamlit as st
from modulos.registro_usuario import registrar_usuario
from modulos.login import login
from modulos.grupos import mostrar_grupo

# ⚙️ Configuración de la app
st.set_page_config(page_title="Sistema GAPCSV", page_icon="💜", layout="centered")

# 🧠 Inicialización del estado
if "sesion_iniciada" not in st.session_state:
    st.session_state["sesion_iniciada"] = False
if "pagina_actual" not in st.session_state:
    st.session_state["pagina_actual"] = "inicio"

# --- NAVEGACIÓN LATERAL ---
st.sidebar.title("📋 Menú principal")

# 💅 Estilo visual personalizado
st.markdown("""
    <style>
        .titulo {
            text-align: center;
            color: #6C3483;
            font-size: 2.2em;
            font-weight: bold;
        }
        .subtitulo {
            text-align: center;
            color: #2E4053;
            font-size: 1.3em;
        }
        .descripcion {
            background-color: #F8F9F9;
            border-radius: 12px;
            padding: 20px;
            margin-top: 10px;
            box-shadow: 0 0 10px rgba(108, 52, 131, 0.2);
        }
        .emoji {
            font-size: 1.4em;
        }
        .sesion-cerrada {
            text-align: center;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 10px;
            margin: 20px 0;
        }
    </style>
""", unsafe_allow_html=True)

# =====================================================
# 🟢 Si ya hay sesión iniciada
# =====================================================
if st.session_state["sesion_iniciada"]:
    usuario = st.session_state.get("usuario", "Usuario")
    tipo = st.session_state.get("tipo_usuario", "Desconocido")

    st.sidebar.write(f"👤 **{usuario}** ({tipo})")

    # --- Menú dinámico según tipo de usuario ---
    if tipo.lower() == "administradora":
        opciones = ["Consolidado por distrito", "Cerrar sesión"]
        opcion = st.sidebar.selectbox("Ir a:", opciones)

        if opcion == "Consolidado por distrito":
            st.title("📊 Consolidado general por distrito 💲")
            st.info("Aquí se mostrará el consolidado de todos los grupos por distrito.")
        elif opcion == "Cerrar sesión":
            usuario_temp = st.session_state.get("usuario", "")
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.session_state["sesion_iniciada"] = False
            st.session_state["pagina_actual"] = "sesion_cerrada"
            st.rerun()

    elif tipo.lower() == "promotora":
        opciones = ["Consolidado por grupos", "Cerrar sesión"]
        opcion = st.sidebar.selectbox("Ir a:", opciones)

        if opcion == "Consolidado por grupos":
            st.title("📈 Consolidado por grupos del distrito asignado 💰")
            st.info("Aquí se mostrará el consolidado de los grupos bajo tu distrito.")
        elif opcion == "Cerrar sesión":
            usuario_temp = st.session_state.get("usuario", "")
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.session_state["sesion_iniciada"] = False
            st.session_state["pagina_actual"] = "sesion_cerrada"
            st.rerun()

    elif tipo.lower() in ["presidenta", "secretaria"]:
        opciones = ["Registrar grupo", "Ver grupos", "Cerrar sesión"]
        opcion = st.sidebar.selectbox("Ir a:", opciones)

        if opcion == "Registrar grupo":
            st.title("👥 Registro y edición de grupos")
            mostrar_grupo()
        elif opcion == "Ver grupos":
            st.title("📋 Listado de grupos existentes")
            st.info("Aquí podrás consultar los grupos ya registrados.")
        elif opcion == "Cerrar sesión":
            usuario_temp = st.session_state.get("usuario", "")
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.session_state["sesion_iniciada"] = False
            st.session_state["pagina_actual"] = "sesion_cerrada"
            st.rerun()

    else:
        st.warning("⚠️ Tipo de usuario no reconocido. Contacte al administrador.")

# =====================================================
# 🔴 Si NO hay sesión iniciada
# =====================================================
else:
    # --- Página de sesión cerrada ---
    if st.session_state["pagina_actual"] == "sesion_cerrada":
        st.markdown("<div class='sesion-cerrada'>", unsafe_allow_html=True)
        st.markdown("### ✅ Sesión finalizada")
        st.markdown("<p>Has cerrado sesión exitosamente.</p>", unsafe_allow_html=True)
        
        if st.button("🏠 Volver al inicio"):
            st.session_state["pagina_actual"] = "inicio"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # --- Página de inicio normal ---
    elif st.session_state["pagina_actual"] == "inicio":
        st.markdown("<h1 class='titulo'> Bienvenido al Sistema GAPCSV </h1>", unsafe_allow_html=True)
        st.markdown("<h3 class='subtitulo'>Grupos de Ahorro y Préstamo Comunitario </h3>", unsafe_allow_html=True)

        st.markdown("""
        <div class='descripcion'>
            <p class='emoji'>💰 Este sistema te ayuda a registrar, monitorear y consolidar los ahorros de los grupos comunitarios.</p>
            <p class='emoji'>🤝 Promueve la colaboración, la transparencia y el crecimiento económico local.</p>
            <p>Si ya tienes una cuenta, inicia sesión.<br>
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

    # --- Pantalla de login ---
    elif st.session_state["pagina_actual"] == "login":
        login()

    # --- Pantalla de registro ---
    elif st.session_state["pagina_actual"] == "registro":
        registrar_usuario()

