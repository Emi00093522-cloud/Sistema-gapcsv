import streamlit as st

# Importar tus módulos
from grupos import mostrar_grupos
from miembros import mostrar_miembros
from reuniones import mostrar_reuniones
from reglamentos import mostrar_reglamentos
from prestamo import mostrar_prestamos

def panel_secretaria(usuario, dui):
    st.title("Panel de Secretaría")

    # información del usuario
    st.write(f"Secretaria: **{usuario}**   —   DUI: **{dui}**")

    # Barra de navegación
    menu = st.tabs(["Crear Grupo", "Miembros", "Reuniones", "Reglamentos", "Préstamos"])

    # --- Crear Grupo ---
    with menu[0]:
        st.header("Crear Grupo")
        mostrar_grupos()

    # --- Miembros ---
    with menu[1]:
        st.header("Gestión de Miembros")
        mostrar_miembros()

    # --- Reuniones ---
    with menu[2]:
        st.header("Reuniones del Grupo")
        mostrar_reuniones()

    # --- Reglamentos ---
    with menu[3]:
        st.header("Reglamentos del Grupo")
        mostrar_reglamentos()

    # --- Préstamos ---
    with menu[4]:
        st.header("Gestión de Préstamos")
        mostrar_prestamos()


# Si deseas probar este módulo solo:
if __name__ == "__main__":
    panel_secretaria("secretaria_demo", "00000000-0")

