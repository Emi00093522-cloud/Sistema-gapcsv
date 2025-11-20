import streamlit as st

# Inicializar estados de sesión SI NO EXISTEN
if 'opcion_secreta_activa' not in st.session_state:
    st.session_state.opcion_secreta_activa = "Registrar Grupo"

# Importar módulos de cada panel
from distrito import mostrar_distrito            # para PROMOTORA

from grupos import mostrar_grupos                # para SECRETARIA
from miembros import mostrar_miembros
from reuniones import mostrar_reuniones
from reglamentos import mostrar_reglamentos
from prestamo import mostrar_prestamos
from asistencia import mostrar_asistencia

# -----------------------------
# PANEL DE PROMOTORA
# -----------------------------
def panel_promotora(usuario, dui):
    st.title("Panel de Promotora")

    st.write(f"Promotora: **{usuario}** — DUI: **{dui}**")

    menu = st.tabs(["Distritos"])

    with menu[0]:
        st.header("Gestión de Distritos")
        mostrar_distrito()


# -----------------------------
# PANEL DE SECRETARÍA
# -----------------------------
def panel_secretaria(usuario, dui):
    st.title("Panel de Secretaría")
    st.write(f"Secretaria: **{usuario}** — DUI: **{dui}**")

    # Lista de opciones en el sidebar
    st.sidebar.title("📋 Menú de Gestión")
    
    opciones = [
        "Registrar Grupo",
        "Reglamentos", 
        "Miembros",
        "Préstamos",
        "Reuniones",
        "Asistencia"
    ]
    
    # Usar st.sidebar.radio y guardar en session_state
    opcion_seleccionada = st.sidebar.radio(
        "Selecciona una opción:",
        options=opciones,
        key="opcion_secreta_activa"  # IMPORTANTE: usar key para session_state
    )

    # Mostrar el contenido según la opción seleccionada
    st.header(opcion_seleccionada)
    
    if opcion_seleccionada == "Registrar Grupo":
        mostrar_grupos()
        
    elif opcion_seleccionada == "Reglamentos":
        mostrar_reglamentos()
        
    elif opcion_seleccionada == "Miembros":
        mostrar_miembros()
        
    elif opcion_seleccionada == "Préstamos":
        mostrar_prestamos()
        
    elif opcion_seleccionada == "Reuniones":
        mostrar_reuniones()
        
    elif opcion_seleccionada == "Asistencia":
        mostrar_asistencia()


# -----------------------------
# PANEL DE ADMINISTRADOR
# -----------------------------
def panel_admin(usuario, dui):
    st.title("Panel de Administrador")

    st.write(f"Administrador: **{usuario}** — DUI: **{dui}**")

    st.info("Aquí irá toda la gestión del sistema.")  # temporal


# -----------------------------
# FUNCIÓN PRINCIPAL PARA ELECCIÓN DE PANEL
# -----------------------------
def cargar_panel(tipo_usuario, usuario, dui):

    tipo_usuario = tipo_usuario.lower().strip()

    if tipo_usuario == "promotora":
        panel_promotora(usuario, dui)

    elif tipo_usuario == "secretaria":
        panel_secretaria(usuario, dui)

    elif tipo_usuario == "administrador":
        panel_admin(usuario, dui)

    else:
        st.error("⚠️ Tipo de usuario no reconocido. Contacte al administrador.")
