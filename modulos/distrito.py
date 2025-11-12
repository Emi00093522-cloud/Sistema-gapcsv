import streamlit as st
from modulos.config.conexion import obtener_conexion

def mostrar_distrito():
    st.header("🏛️ Registrar Distrito")
    st.success("👋 ¡Hola, promotor!")
    
    # Variable para controlar el estado de éxito
    if 'distrito_creado' not in st.session_state:
        st.session_state.distrito_creado = False
    if 'id_distrito_creado' not in st.session_state:
        st.session_state.id_distrito_creado = None
    if 'nombre_distrito_creado' not in st.session_state:
        st.session_state.nombre_distrito_creado = ""

    # Si ya se creó un distrito, mostrar mensaje de éxito
    if st.session_state.distrito_creado:
        st.success("🎉 ¡Distrito creado con éxito!")
        st.info(f"**ID del distrito:** {st.session_state.id_distrito_creado}")
        st.info(f"**Nombre del distrito:** {st.session_state.nombre_distrito_creado}")
        
        # Botón para regresar a la pantalla de inicio
        if st.button("🏠 Regresar a Inicio"):
            st.session_state.distrito_creado = False
            st.session_state.id_distrito_creado = None
            st.session_state.nombre_distrito_creado = ""
            st.rerun()
        return

    try:
        con = obtener_conexion()
        cursor = con.cursor()

        # **DIAGNÓSTICO: Mostrar todas las tablas disponibles**
        cursor.execute("SHOW TABLES")
        tablas = cursor.fetchall()
        st.info(f"📊 **Tablas disponibles en tu base de datos:**")
        for tabla in tablas:
            st.write(f"- `{tabla[0]}`")

        # **ENCONTRAR EL NOMBRE CORRECTO DE LA TABLA**
        nombres_posibles = ['distritos', 'Distritos', 'distrito', 'Distrito', 'tb_distritos', 'tbl_distritos']
        tabla_correcta = None
        
        for nombre_tabla in nombres_posibles:
            try:
                cursor.execute(f"SELECT 1 FROM {nombre_tabla} LIMIT 1")
                tabla_correcta = nombre_tabla
                st.success(f"✅ **Tabla encontrada:** `{tabla_correcta}`")
                break
            except:
                continue
        
        if not tabla_correcta:
            st.error("❌ No se encontró ninguna tabla de distritos. Verifica el nombre en PHPMyAdmin.")
            cursor.close()
            con.close()
            return

        # Formulario para registrar el distrito
        with st.form("form_distrito"):
            nombre = st.text_input("Nombre del distrito", 
                                 placeholder="Ingrese el nombre completo del distrito")
            codigo = st.text_input("Código del distrito (opcional)", 
                                 placeholder="Ingrese el código (máx. 10 caracteres)",
                                 max_chars=10)
            enviar = st.form_submit_button("💾 Guardar distrito")

            if enviar:
                if nombre.strip() == "":
                    st.warning("⚠ Debes ingresar el nombre del distrito.")
                else:
                    try:
                        # Si el código está vacío, lo convertimos a None (NULL en la BD)
                        codigo_valor = codigo.strip() if codigo.strip() != "" else None
                        
                        # Insertar en la tabla usando el nombre CORRECTO
                        cursor.execute(
                            f"INSERT INTO {tabla_correcta} (nombre, codigo) VALUES (%s, %s)",
                            (nombre.strip(), codigo_valor)
                        )
                        con.commit()
                        
                        # Obtener el ID del distrito recién insertado
                        cursor.execute("SELECT LAST_INSERT_ID()")
                        id_distrito = cursor.fetchone()[0]
                        
                        # Guardar en session_state para mostrar en el mensaje de éxito
                        st.session_state.distrito_creado = True
                        st.session_state.id_distrito_creado = id_distrito
                        st.session_state.nombre_distrito_creado = nombre.strip()
                        
                        st.rerun()
                        
                    except Exception as e:
                        con.rollback()
                        st.error(f"❌ Error al registrar el distrito: {e}")

    except Exception as e:
        st.error(f"❌ Error de conexión: {e}")

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'con' in locals():
            con.close()

# Función principal
def gestionar_distritos():
    mostrar_distrito()
