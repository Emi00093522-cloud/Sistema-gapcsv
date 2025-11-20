```python
import streamlit as st
from streamlit_option_menu import option_menu

# ---------- CONFIGURACIÓN GENERAL ----------
st.set_page_config(page_title="Panel Administrativo", page_icon="📊", layout="wide")

# Paleta formal
PRIMARY = "#8B5E83"      # Acento elegante
BG_LIGHT = "#F7F5F2"      # Fondo claro profesional
CARD_BG = "#FFFFFF"       # Tarjetas blancas
TEXT_DARK = "#3A3A3A"     

# ---------- ESTILOS CSS ----------
st.markdown(f"""
<style>
    body {{ background-color: {BG_LIGHT}; }}

    .main > div {{ padding: 20px 40px; }}

    h1, h2, h3, h4, h5, h6 {{
        color: {TEXT_DARK};
        font-family: 'Segoe UI', sans-serif;
        font-weight: 600;
    }}

    .stButton>button {{
        background-color: {PRIMARY};
        color: white;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        border: none;
        font-size: 16px;
    }}
    .stButton>button:hover {{
        background-color: #6F4768;
    }}

    .card {{
        background-color: {CARD_BG};
        padding: 18px;
        border-radius: 12px;
        box-shadow: 0 3px 10px rgba(0,0,0,0.08);
        margin-bottom: 20px;
    }}
</style>
""", unsafe_allow_html=True)

# ---------- SIDEBAR ----------
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/1b/UN_logo.svg/1200px-UN_logo.svg.png", width=130)
    st.markdown("### **Panel Administrativo**")

    menu = option_menu(
        menu_title="Navegación",
        options=["Inicio", "Usuarios", "Grupos", "Reportes"],
        icons=["house", "people", "layers", "bar-chart"],
        default_index=0,
        styles={{
            "container": {{"background-color": BG_LIGHT}},
            "icon": {{"color": PRIMARY}},
            "nav-link": {{"font-size": "16px", "text-align": "left", "padding": "10px"}},
            "nav-link-selected": {{"background-color": PRIMARY}},
        }},
    )

# ---------- PÁGINA: INICIO ----------
if menu == "Inicio":
    st.markdown("<h1>📌 Dashboard General</h1>", unsafe_allow_html=True)
    st.write("Bienvenida al sistema administrativo. Aquí podrás gestionar usuarios, grupos y ver reportes consolidados.")

    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"<div class='card'><h3>👥 Total Usuarios</h3><h2 style='color:{PRIMARY}'>128</h2></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='card'><h3>🧩 Grupos Activos</h3><h2 style='color:{PRIMARY}'>34</h2></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='card'><h3>📊 Reportes</h3><h2 style='color:{PRIMARY}'>12</h2></div>", unsafe_allow_html=True)

# ---------- PÁGINA: USUARIOS ----------
if menu == "Usuarios":
    st.markdown("<h1>👤 Gestión de Usuarios</h1>", unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Registrar Nuevo Usuario")
        nombre = st.text_input("Nombre completo:")
        correo = st.text_input("Correo electrónico:")
        rol = st.selectbox("Rol", ["Administrador", "Promotora", "Invitado"])
        if st.button("Guardar Usuario"):
            st.success("Usuario registrado correctamente ✨")
        st.markdown("</div>", unsafe_allow_html=True)

# ---------- PÁGINA: GRUPOS ----------
if menu == "Grupos":
    st.markdown("<h1>🧩 Administración de Grupos</h1>", unsafe_allow_html=True)
    st.markdown("<div class='card'>", unsafe_allow_html=True)

    nombre_grupo = st.text_input("Nombre del grupo:")
    id_usuario = st.text_input("ID del usuario encargado:")
    
    if st.button("Crear Grupo"):
        st.success("Grupo creado exitosamente ✨")

    st.markdown("</div>", unsafe_allow_html=True)

# ---------- PÁGINA: REPORTES ----------
if menu == "Reportes":
    st.markdown("<h1>📈 Reportes Consolidado</h1>", unsafe_allow_html=True)
    st.write("Aquí se mostrarán gráficos de ingresos, egresos y consolidado general.")

    st.markdown(f"<div class='card'><h3>🔧 Módulo en desarrollo…</h3></div>", unsafe_allow_html=True)
```

