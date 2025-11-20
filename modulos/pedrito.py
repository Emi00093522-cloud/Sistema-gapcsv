import streamlit as st

# Importar módulos de cada panel
from distrito import mostrar_distrito            # para PROMOTORA

from grupos import mostrar_grupos                # para SECRETARIA
from miembros import mostrar_miembros
from reglamentos import mostrar_reglamentos
from reuniones import mostrar_reuniones
from prestamo import mostrar_prestamos
from integrada import mostrar_gestion_integrada

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

    menu = st.tabs(["Crear Grupo", "Miembros", "Reglamentos","Reuniones", "Préstamos"])

    with menu[0]:
        st.header("Crear Grupo")
        mostrar_grupos()

    with menu[1]:
        st.header("Gestión de Miembros")
        mostrar_miembros()

    with menu[2]:
        st.header("Reglamentos del Grupo")
        mostrar_reglamentos()

    with menu[3]:
        st.header("Reuniones del Grupo")
        mostrar_reuniones()

    with menu[4]:
        st.header("Gestión de Préstamos")
        mostrar_prestamos()


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
