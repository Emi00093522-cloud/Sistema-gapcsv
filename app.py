import streamlit as st
from modulos.registro_usuario import registrar_usuario
from modulos.login import login
from modulos.bienvenida import mostrar_bienvenida  # Puedes reemplazar luego por tus dashboards reales

# ⚙️ Configuración de la app
st.set_page_config(page_title="Sistema GAPCSV", page_icon="💜", layout="centered")

# 🧠 Inicialización del estado
if "sesion_iniciada" not in st.session_state:
    st.session_state["sesion_iniciada"] = False
if "pagina_actual" not in st.session_state:
    st.session_state["pagina_actual"] = "inicio"
if "usuario" not in st.session_state:
    st.session_state["usuario"] = ""
if "tipo_usuario" not in st.session_state:
    st.session_state["tipo_usuario"] = ""
if "cargo" not in st.session_state:
    st.session_state["cargo"] = ""

# --- NAVEGACIÓN LATERAL ---
st.sidebar.title("📋 Menú principal")

# 💅 Estilo visual personalizado
st.markdown("""
    <style>
        .titulo {
            text-align: center;
            color: #6C3483;
            font-size: 2.2em;
            font-weight: bold;
        }
        .subtitulo {
            text-align: center;
            color: #2E4053;
            font-size: 1.3em;
        }
        .descripcion {
            background-color: #F8F9F9;
            border-radius: 12px;
            padding: 20px;
            margin-top: 10px;
            box-shadow: 0 0 10px rgba(108, 52, 131, 0.2);
        }
        .emoji {
            font-size: 1.4em;
        }
    </style>
""", unsafe_allow_html=True)

# 🔴 Si no hay sesión iniciada, mostrar login automáticamente
if not st.session_state.get("sesion_iniciada", False):
    login()
    
# 🟢 Si hay sesión iniciada, mostrar la aplicación principal
else:
    usuario = st.session_state.get("usuario", "Usuario")
    tipo = st.session_state.get("tipo_usuario", "Desconocido")
    cargo = st.session_state.get("cargo", "")

    st.sidebar.write(f"👤 **{usuario}**")
    st.sidebar.write(f"🏷️ **Tipo:** {tipo}")
    st.sidebar.write(f"💼 **Cargo:** {cargo}")

    # Menú dinámico según tipo de usuario y cargo
    if tipo.upper() == "EDITOR":
        if cargo.upper() == "PRESIDENTE":
            opciones = ["Dashboard Presidente", "Reportes", "Cerrar sesión"]
        elif cargo.upper() == "SECRETARIA":
            opciones = ["Dashboard Secretaria", "Registros", "Cerrar sesión"]
        else:
            opciones = ["Dashboard", "Cerrar sesión"]
            
    elif tipo.upper() == "LECTOR":
        if cargo.upper() == "ADMINISTRADOR":
            opciones = ["Consolidado por distrito", "Registrar usuario", "Reportes", "Cerrar sesión"]
        elif cargo.upper() == "PROMOTORA":
            opciones = ["Consolidado por grupos", "Cerrar sesión"]
        elif cargo.upper() == "TESORERA":
            opciones = ["Control de tesorería", "Reportes financieros", "Cerrar sesión"]
        elif cargo.upper() == "SOCIA":
            opciones = ["Mi ahorro", "Mis préstamos", "Cerrar sesión"]
        else:
            opciones = ["Dashboard", "Cerrar sesión"]
    else:
        opciones = ["Dashboard", "Cerrar sesión"]

    opcion = st.sidebar.selectbox("Ir a:", opciones)

    # --- EDITORES ---
    if tipo.upper() == "EDITOR":
        if "Dashboard Presidente" in opcion:
            st.title("🎯 Dashboard Presidente")
            st.info("Funcionalidades específicas para el Presidente")
            # mostrar_dashboard_presidente()  # Tu función real aquí
            
        elif "Dashboard Secretaria" in opcion:
            st.title("📋 Dashboard Secretaria")
            st.info("Funcionalidades específicas para la Secretaria")
            # mostrar_dashboard_secretaria()  # Tu función real aquí
            
        elif "Reportes" in opcion:
            st.title("📊 Reportes")
            st.info("Módulo de reportes para editores")
            
        elif "Registros" in opcion:
            st.title("📝 Registros")
            st.info("Módulo de registros para secretaría")

    # --- LECTORES ---
    elif tipo.upper() == "LECTOR":
        if cargo.upper() == "ADMINISTRADOR":
            if opcion == "Consolidado por distrito":
                st.title("📊 Consolidado general por distrito 💲")
                # mostrar_ahorros()  # Tu función real aquí
                st.info("Módulo de consolidado por distrito - ADMINISTRADOR")
                
            elif opcion == "Registrar usuario":
                registrar_usuario()
                
            elif opcion == "Reportes":
                st.title("📈 Reportes Administrativos")
                st.info("Módulo de reportes para administradores")

        elif cargo.upper() == "PROMOTORA":
            if opcion == "Consolidado por grupos":
                st.title("📈 Consolidado por grupos del distrito asignado 💰")
                # mostrar_ahorros()  # Tu función real aquí
                st.info("Módulo de consolidado por grupos - PROMOTORA")

        elif cargo.upper() == "TESORERA":
            if opcion == "Control de tesorería":
                st.title("💰 Control de Tesorería")
                st.info("Módulo de control de tesorería")
                
            elif opcion == "Reportes financieros":
                st.title("📊 Reportes Financieros")
                st.info("Módulo de reportes financieros")

        elif cargo.upper() == "SOCIA":
            if opcion == "Mi ahorro":
                st.title("💵 Mi Ahorro Personal")
                st.info("Módulo de consulta de ahorro personal")
                
            elif opcion == "Mis préstamos":
                st.title("🏦 Mis Préstamos")
                st.info("Módulo de consulta de préstamos")

    # --- CERRAR SESIÓN (para todos) ---
    if opcion == "Cerrar sesión":
        # Guardar información temporal si es necesario
        usuario_temp = st.session_state.get("usuario", "")
        
        # Limpiar toda la sesión
        for key in list(st.session_state.keys()):
            del st.session_state[key]
            
        # Restablecer estado básico
        st.session_state["sesion_iniciada"] = False
        st.session_state["pagina_actual"] = "inicio"
        
        st.success(f"👋 Sesión cerrada correctamente. Hasta luego, {usuario_temp}!")
        st.rerun()

    # --- CONTENIDO PRINCIPAL ---
    st.markdown("---")
    st.markdown(f"### 🏠 Página principal - {cargo}")
    st.write(f"Bienvenido/a **{usuario}** - Tipo: **{tipo}** - Cargo: **{cargo}**")
    
    # Aquí puedes agregar el contenido principal de tu aplicación
    # mostrar_bienvenida()  # O tus dashboards reales
