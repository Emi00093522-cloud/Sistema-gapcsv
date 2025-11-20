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

    menu = st.tabs(["Registrar Grupo", "Miembros", "Reglamentos", "Reuniones"])

    with menu[0]:
        st.header("Registrar Grupo")
        mostrar_grupos()

    with menu[1]:
        st.header("Gestión de Miembros")
        mostrar_miembros()

    with menu[2]:
        st.header("Reglamentos del Grupo")
        mostrar_reglamentos()

    with menu[3]:
        st.header("Reuniones del Grupo")
        
        # Botones para las opciones dentro de Reuniones
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📅 Gestión de Reuniones", use_container_width=True):
                st.session_state.mostrar_reuniones = True
                st.session_state.mostrar_prestamos = False
                st.session_state.mostrar_asistencia = False
                
        with col2:
            if st.button("💰 Préstamos", use_container_width=True):
                st.session_state.mostrar_reuniones = False
                st.session_state.mostrar_prestamos = True
                st.session_state.mostrar_asistencia = False
        
        # Botón para Asistencia en una nueva fila
        col3, col4 = st.columns(2)
        with col3:
            if st.button("✅ Asistencia", use_container_width=True):
                st.session_state.mostrar_reuniones = False
                st.session_state.mostrar_prestamos = False
                st.session_state.mostrar_asistencia = True
        
        # Mostrar el contenido según la selección
        if st.session_state.get('mostrar_reuniones', True):
            mostrar_reuniones()
        elif st.session_state.get('mostrar_prestamos', False):
            mostrar_prestamos()
        elif st.session_state.get('mostrar_asistencia', False):
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
