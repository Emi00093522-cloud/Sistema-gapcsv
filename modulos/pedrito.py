import streamlit as st

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

    # Lista de opciones en lugar de pestañas
    st.sidebar.title("📋 Menú de Gestión")
    
    opciones = [
        "Registrar Grupo",
        "Reglamentos", 
        "Miembros",
        "Préstamos",
        "Reuniones",
        "Asistencia"
    ]
    
    opcion_seleccionada = st.sidebar.radio(
        "Selecciona una opción:",
        options=opciones,
        index=0
    )

    # Mostrar el contenido según la opción seleccionada
    if opcion_seleccionada == "Registrar Grupo":
        st.header("Registrar Grupo")
        mostrar_grupos()
        
    elif opcion_seleccionada == "Reglamentos":
        st.header("Reglamentos del Grupo")
        mostrar_reglamentos()
        
    elif opcion_seleccionada == "Miembros":
        st.header("Gestión de Miembros")
        mostrar_miembros()
        
    elif opcion_seleccionada == "Préstamos":
        st.header("Gestión de Préstamos")
        mostrar_prestamos()
        
    elif opcion_seleccionada == "Reuniones":
        st.header("Reuniones del Grupo")
        mostrar_reuniones()
        
    elif opcion_seleccionada == "Asistencia":
        st.header("Gestión de Asistencia")
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
