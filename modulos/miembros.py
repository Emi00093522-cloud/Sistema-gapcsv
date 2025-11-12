import streamlit as st
from datetime import date
from modulos.config.conexion import obtener_conexion

def mostrar_miembro():
    st.header("👥 Registrar nuevo miembro")

    try:
        con = obtener_conexion()
        cursor = con.cursor()

        # Cargar listas de grupos, roles y estados (si existen las tablas)
        try:
            cursor.execute("SELECT ID_Grupo FROM Grupo")
            grupos = [str(row[0]) for row in cursor.fetchall()]
        except:
            grupos = []

        try:
            cursor.execute("SELECT ID_Rol FROM Rol")
            roles = [str(row[0]) for row in cursor.fetchall()]
        except:
            roles = []

        try:
            cursor.execute("SELECT ID_Estado FROM Estado")
            estados = [str(row[0]) for row in cursor.fetchall()]
        except:
            estados = ["1"]

        # Formulario
        with st.form("form_miembro"):
            st.subheader("Datos personales")
            nombre = st.text_input("🧾 Nombre")
            apellido = st.text_input("🧾 Apellido")
            dui = st.text_input("🪪 DUI (opcional)")
            email = st.text_input("📧 Correo electrónico (opcional)")
            telefono = st.text_input("📞 Teléfono (opcional)")

            st.subheader("Datos del grupo")
            id_grupo = st.selectbox("🏠 ID del Grupo", opciones := grupos if grupos else ["Sin grupos disponibles"])
            id_rol = st.selectbox("🎯 ID del Rol", opciones2 := roles if roles else ["Sin roles disponibles"])
            id_estado = st.selectbox("⚙️ Estado", estados)

            fecha_inscripcion = st.date_input("📆 Fecha de inscripción", value=date.today())
            ausencias = st.number_input("🚫 Ausencias", min_value=0, step=1, value=0)

            enviar = st.form_submit_button("✅ Guardar miembro")

            if enviar:
                if nombre.strip() == "" or apellido.strip() == "":
                    st.warning("⚠️ Debes ingresar al menos el nombre y apellido del miembro.")
                else:
                    try:
                        cursor.execute("""
                            INSERT INTO Miembro 
                            (ID_Grupo, nombre, apellido, DUI, email, telefono, ID_Rol, ID_Estado, fecha_inscripcion, ausencias)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            id_grupo if id_grupo.isdigit() else None,
                            nombre,
                            apellido,
                            dui if dui.strip() != "" else None,
                            email if email.strip() != "" else None,
                            telefono if telefono.strip() != "" else None,
                            id_rol if id_rol.isdigit() else None,
                            id_estado if id_estado.isdigit() else 1,
                            fecha_inscripcion,
                            ausencias
                        ))
                        con.commit()
                        st.success(f"✅ Miembro registrado correctamente: {nombre} {apellido}")
                        st.rerun()
                    except Exception as e:
                        con.rollback()
                        st.error(f"❌ Error al registrar el miembro: {e}")

    except Exception as e:
        st.error(f"❌ Error general: {e}")

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'con' in locals():
            con.close()
