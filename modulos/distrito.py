import streamlit as st
from modulos.config.conexion import obtener_conexion

def mostrar_distrito():
    st.header("🏛️ Registrar Distrito")
    
    # Mensaje de bienvenida personalizado
    st.success("👋 ¡Hola, promotor!")
    
    try:
        con = obtener_conexion()
        cursor = con.cursor()

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
                        
                        cursor.execute(
                            "INSERT INTO Distritos (nombre, codigo) VALUES (%s, %s)",
                            (nombre.strip(), codigo_valor)
                        )
                        con.commit()
                        
                        # Obtener el ID del distrito recién insertado
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

# Función adicional para mostrar los distritos existentes (opcional)
def mostrar_distritos_existentes():
    try:
        con = obtener_conexion()
        cursor = con.cursor()
        
        cursor.execute("SELECT ID_Distrito, nombre, codigo FROM Distritos ORDER BY ID_Distrito DESC LIMIT 10")
        distritos = cursor.fetchall()
        
        if distritos:
            st.subheader("📋 Últimos distritos registrados")
            for distrito in distritos:
                id_dist, nombre, codigo = distrito
                codigo_display = codigo if codigo else "No asignado"
                st.write(f"**ID {id_dist}:** {nombre} - Código: {codigo_display}")
                
    except Exception as e:
        st.error(f"Error al cargar distritos: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'con' in locals():
            con.close()

# Función principal que puedes llamar desde tu app
def gestionar_distritos():
    mostrar_distrito()
    st.divider()
    mostrar_distritos_existentes()
