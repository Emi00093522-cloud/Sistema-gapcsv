import streamlit as st

# DEBUG: Verificar si se está ejecutando el código nuevo
st.sidebar.info("🔍 Código nuevo cargado")

# Inicializar estados de sesión
if 'opcion_secreta_activa' not in st.session_state:
    st.session_state.opcion_secreta_activa = "Registrar Grupo"

# Importar módulos de cada panel
try:
    from distrito import mostrar_distrito
    from grupos import mostrar_grupos
    from miembros import mostrar_miembros
    from reuniones import mostrar_reuniones
    from reglamentos import mostrar_reglamentos
    from prestamo import mostrar_prestamos
    from asistencia import mostrar_asistencia
    st.sidebar.success("✅ Módulos importados")
except ImportError as e:
    st.sidebar.error(f"❌ Error importando: {e}")

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
# PANEL DE SECRETARÍA - VERSIÓN NUEVA
# -----------------------------
def panel_secretaria(usuario, dui):
    st.title("Panel de Secretaría - NUEVA VERSIÓN")
    st.write(f"Secretaria: **{usuario}** — DUI: **{dui}**")
    
    # Mostrar debug info
    st.sidebar.write(f"Opción activa: {st.session_state.opcion_secreta_activa}")

    # Lista de opciones en el sidebar
    st.sidebar.markdown("---")
    st.sidebar.title("📋 Menú de Gestión")
    
    opciones = [
        "Registrar Grupo",
        "Reglamentos", 
        "Miembros",
        "Préstamos",
        "Reuniones",
        "Asistencia"
    ]
    
    # Radio button en el sidebar
    opcion = st.sidebar.radio(
        "Selecciona una opción:",
        options=opciones,
        key="opcion_secreta_activa"
    )

    # Mostrar el contenido según la opción seleccionada
    st.header(f"📌 {opcion}")
    
    if opcion == "Registrar Grupo":
        mostrar_grupos()
        
    elif opcion == "Reglamentos":
        mostrar_reglamentos()
        
    elif opcion == "Miembros":
        mostrar_miembros()
        
    elif opcion == "Préstamos":
        mostrar_prestamos()
        
    elif opcion == "Reuniones":
        mostrar_reuniones()
        
    elif opcion == "Asistencia":
        mostrar_asistencia()

# -----------------------------
# PANEL DE ADMINISTRADOR
# -----------------------------
def panel_admin(usuario, dui):
    st.title("Panel de Administrador")
    st.write(f"Administrador: **{usuario}** — DUI: **{dui}**")
    st.info("Aquí irá toda la gestión del sistema.")

# -----------------------------
# FUNCIÓN PRINCIPAL PARA ELECCIÓN DE PANEL
# -----------------------------
def cargar_panel(tipo_usuario, usuario, dui):
    tipo_usuario = tipo_usuario.lower().strip()
    
    st.sidebar.write(f"Tipo usuario: {tipo_usuario}")

    if tipo_usuario == "promotora":
        panel_promotora(usuario, dui)

    elif tipo_usuario == "secretaria":
        panel_secretaria(usuario, dui)

    elif tipo_usuario == "administrador":
        panel_admin(usuario, dui)

    else:
        st.error("⚠️ Tipo de usuario no reconocido. Contacte al administrador.")
