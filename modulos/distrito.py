import streamlit as st
from modulos.config.conexion import obtener_conexion

def mostrar_distrito():
    st.header("🏛️ Registrar Distrito")
    st.success("👋 ¡Hola, promotor!")
    
    try:
        con = obtener_conexion()
        cursor = con.cursor()

        # **NUEVO: Mostrar tablas disponibles para diagnóstico**
        cursor.execute("SHOW TABLES")
        tablas = cursor.fetchall()
        st.info(f"📊 Tablas disponibles en la base de datos: {[tabla[0] for tabla in tablas]}")

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
                        codigo_valor = codigo.strip() if codigo.strip() != "" else None
                        
                        # **POSIBLES NOMBRES DE TABLA - prueba uno por uno**
                        # Intenta con diferentes nombres comunes de tabla:
                        nombres_tablas = ['distritos', 'Distritos', 'distrito', 'Distrito', 'tb_distritos']
                        
                        for nombre_tabla in nombres_tablas:
                            try:
                                cursor.execute(f"SELECT 1 FROM {nombre_tabla} LIMIT 1")
                                st.success(f"✅ Tabla encontrada: {nombre_tabla}")
                                tabla_correcta = nombre_tabla
                                break
                            except:
                                continue
                        else:
                            st.error("❌ No se encontró ninguna tabla de distritos")
                            return
                        
                        cursor.execute(
                            f"INSERT INTO {tabla_correcta} (nombre, codigo) VALUES (%s, %s)",
                            (nombre.strip(), codigo_valor)
                        )
                        con.commit()
                        
                        cursor.execute("SELECT LAST_INSERT_ID()")
                        id_distrito = cursor.fetchone()[0]
                        
                        st.success(f"✅ Distrito registrado correctamente!")
                        st.info(f"**ID del distrito:** {id_distrito}")
                        st.info(f"**Nombre:** {nombre.strip()}")
                        if codigo_valor:
                            st.info(f"**Código:** {codigo_valor}")
                        
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
