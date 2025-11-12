import streamlit as st
from modulos.registro_usuario import registrar_usuario
from modulos.login import login
from modulos.ahorros import mostrar_ahorros  # Puedes reemplazar luego por tus dashboards reales

# ⚙️ Configuración de la app
st.set_page_config(page_title="Sistema GAPCSV", page_icon="🧁", layout="centered")

# 🧠 Inicialización del estado
if "sesion_iniciada" not in st.session_state:
    st.session_state["sesion_iniciada"] = False
if "pagina_actual" not in st.session_state:
    st.session_state["pagina_actual"] = "inicio"

# --- NAVEGACIÓN LATERAL ---
st.sidebar.title("📋 Menú principal")

# 🟢 Si ya hay sesión iniciada
if st.session_state["sesion_iniciada"]:
    usuario = st.session_state.get("usuario", "Usuario")
    tipo = st.session_state.get("tipo_usuario", "Desconocido")

    st.sidebar.write(f"👤 **{usuario}** ({tipo})")

    # Menú dinámico según tipo
    if tipo.lower() == "administradora":
        opciones = ["Consolidado por distrito", "Registrar usuario", "Cerrar sesión"]
    elif tipo.lower() == "promotora":
        opciones = ["Consolidado por grupos", "Cerrar sesión"]
    else:
        opciones = ["Dashboard", "Cerrar sesión"]

    opcion = st.sidebar.selectbox("Ir a:", opciones)

    # --- Administradora ---
    if tipo.lower() == "administradora":
        if opcion == "Consolidado por distrito":
            st.title("📊 Consolidado general por distrito")
            mostrar_ahorros()  # Aquí irá tu función real
        elif opcion == "Registrar usuario":
            registrar_usuario()
        elif opcion == "Cerrar sesión":
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("👋 Sesión cerrada correctamente.")
            st.rerun()

    # --- Promotora ---
    elif tipo.lower() == "promotora":
        if opcion == "Consolidado por grupos":
            st.title("📈 Consolidado por grupos del distrito asignado")
            mostrar_ahorros()  # Aquí irá tu función real
        elif opcion == "Cerrar sesión":
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("👋 Sesión cerrada correctamente.")
            st.rerun()

# 🔴 Si no hay sesión iniciada, mostrar página de bienvenida
else:
    st.title("💜 Bienvenida al Sistema GAPCSV")
    st.subheader("Grupos de Ahorro Comunitario Solidario y Visionario")
    st.markdown(
        """
        Este sistema permite gestionar la información de los grupos de ahorro comunitario.  
        Si ya tienes una cuenta, **inicia sesión** para acceder a tus datos.  
        Si aún no tienes usuario, **regístrate** fácilmente aquí.
        """
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔑 Iniciar sesión"):
            st.session_state["pagina_actual"] = "login"

    with col2:
        if st.button("📝 Registrarme"):
            st.session_state["pagina_actual"] = "registro"

    # --- Pantallas según elección ---
    if st.session_state["pagina_actual"] == "login":
        login()

    elif st.session_state["pagina_actual"] == "registro":
        registrar_usuario()
