import streamlit as st
from modulos.registro_usuario import registrar_usuario
from modulos.login import login
from modulos.promotora import mostrar_promotora
from modulos.distrito import mostrar_distrito

# ⚙️ Configuración: SIEMPRE al inicio
st.set_page_config(page_title="Sistema GAPCSV", page_icon="💜", layout="centered")

# 🧠 Estado
if "sesion_iniciada" not in st.session_state:
    st.session_state["sesion_iniciada"] = False
if "pagina_actual" not in st.session_state:
    st.session_state["pagina_actual"] = "inicio"

# --- NAVEGACIÓN LATERAL ---
st.sidebar.title("📋 Menú principal")

# 💅 Estilos (igual que los tuyos)
st.markdown("""
    <style>
        .titulo { text-align:center; color:#6C3483; font-size:2.2em; font-weight:bold; }
        .subtitulo { text-align:center; color:#2E4053; font-size:1.3em; }
        .descripcion { background:#F8F9F9; border-radius:12px; padding:20px; margin-top:10px; box-shadow:0 0 10px rgba(108,52,131,.2); }
        .emoji { font-size:1.4em; }
        .sesion-cerrada { text-align:center; padding:20px; background:#f8f9fa; border-radius:10px; margin:20px 0; }
    </style>
""", unsafe_allow_html=True)

def dashboard_promotora(usuario):
    st.title("👩‍💼 Dashboard de Promotora")
    st.success(f"¡Bienvenida, {usuario}!")
    st.info("Desde aquí puedes gestionar promotoras y distritos.")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Tu Cargo", "PROMOTORA")
    with col2:
        st.metric("Acciones Disponibles", "2")

# 🔵 Utilidad: mapea etiquetas (lo que ve el usuario) a claves internas
def make_menu(options_dict, default_label=None):
    labels = list(options_dict.keys())
    if default_label and default_label in labels:
        index = labels.index(default_label)
    else:
        index = 0
    chosen = st.sidebar.selectbox("Ir a:", labels, index=index, key="menu_principal")
    return options_dict[chosen]  # devuelve la clave interna

# 🟢 Si hay sesión iniciada
if st.session_state["sesion_iniciada"]:
    usuario = st.session_state.get("usuario", "Usuario")
    tipo = (st.session_state.get("tipo_usuario", "Desconocido") or "").strip().lower()
    cargo = (st.session_state.get("cargo_usuario", "") or "").strip().upper()

    st.sidebar.write(f"👤 **{usuario}** ({tipo or 'desconocido'})")

    # 🔐 Rutas por perfil (evita depender de mayúsculas/acentos)
    if tipo == "administradora":
        options = {
            "📊 Consolidado por distrito": "admin_consolidado",

