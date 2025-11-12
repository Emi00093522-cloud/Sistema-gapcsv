import streamlit as st
from modulos.registro_usuario import registrar_usuario
from modulos.login import login
from modulos.ahorros import mostrar_ahorros  # Puedes renombrar esta como quieras
# 👉 Importa tus funciones reales de dashboard si las tienes
# from modulos.dashboard import mostrar_consolidado_distritos, mostrar_consolidado_grupos

# Configuración de la app
st.set_page_config(page_title="Sistema GAPCSV", page_icon="🧁", layout="centered")

# Estado inicial
if "sesion_iniciada" not in st.session_state:
    st.session_state["sesion_iniciada"] = False
if "pagina_actual" not in st.session_state:
    st.session_state["pagina_actual"] = "login"

st.sidebar.title("📋 Menú principal")

# 🟢 Si ya hay sesión iniciada
if st.session_state["sesion_iniciada"]:
    usuario = st.session_state.get("usuario", "Usuario")
    tipo = st.session_state.get("tipo_usuario", "Desconocido")

    st.sidebar.write(f"👤 **{usuario}** ({tipo})")

    # Menú distinto según el tipo de usuario
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
            # Aquí irá tu función real de consolidado:
            mostrar_ahorros()
            # mostrar_consolidado_distritos()

        elif opcion == "Registrar usuario":
            st.title("🆕 Registro de nuevo usuario")
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
            # Aquí irá tu función real de consolidado de grupos:
            mostrar_ahorros()
            # mostrar_consolidado_grupos()

        elif opcion == "Cerrar sesión":
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("👋 Sesión cerrada correctamente.")
            st.rerun()

# 🔴 Si no hay sesión iniciada: mostrar login o registro
else:
    menu = st.sidebar.selectbox("Selecciona una opción", ["Iniciar sesión", "Registrar usuario"])

    if menu == "Iniciar sesión":
        login()
    elif menu == "Registrar usuario":
        registrar_usuario()
