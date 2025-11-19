import streamlit as st
from modulos.config.conexion import obtener_conexion
from datetime import datetime

def mostrar_miembros():   # ← CAMBIO HECHO AQUÍ
    st.header("👥 Registrar Miembro")

    # Estado para controlar el mensaje de éxito
    if 'miembro_registrado' not in st.session_state:
        st.session_state.miembro_registrado = False

    if st.session_state.miembro_registrado:
        st.success("🎉 ¡Miembro registrado con éxito!")

        if st.button("🆕 Registrar otro miembro"):
            st.session_state.miembro_registrado = False
            st.rerun()

        st.info("💡 Para seguir navegando, selecciona una opción en el menú de la izquierda")
        return

    try:
        con = obtener_conexion()
        cursor = con.cursor()

        # Obtener datos para los menús desplegables
        cursor.execute("SELECT ID_Grupo, nombre FROM Grupo")
        grupos = cursor.fetchall()

        # Formulario para registrar el miembro
        with st.form("form_miembro"):
            st.subheader("Datos del Miembro")

            # Grupo
            if grupos:
                grupo_options = {f"{grupo[1]} (ID: {grupo[0]})": grupo[0] for grupo in grupos}
                grupo_seleccionado = st.selectbox("Grupo *", options=list(grupo_options.keys()))
                ID_Grupo = grupo_options[grupo_seleccionado]
            else:
                st.error("No hay grupos disponibles en la base de datos")
                ID_Grupo = None

            # Nombre y apellido
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre *", placeholder="Ingrese el nombre", max_chars=100)
            with col2:
                apellido = st.text_input("Apellido *", placeholder="Ingrese el apellido", max_chars=100)

            DUI = st.text_input("DUI *", placeholder="Ingrese el número de DUI", max_chars=20)
            email = st.text_input("Email (opcional)", placeholder="Ingrese el email", max_chars=100)
            telefono = st.text_input("Teléfono *", placeholder="Ingrese el teléfono", max_chars=20)

            # Rol
            st.markdown("<h4 style='color:#2E4053; margin-top:18px;'>Rol en el grupo</h4>", unsafe_allow_html=True)

            roles = {
                1: "PRESIDENTE",
                2: "SECRETARIA",
                3: "TESORERA",
                4: "ENCARGADA_LLAVE",
                5: "ASOCIADA"
            }

            roles_directiva = {k: v for k, v in roles.items() if k in [1, 2, 3, 4]}
            roles_no_directiva = {k: v for k, v in roles.items() if k == 5}

            st.write("**🏛️ Miembros de Directiva:**")
            st.info("Los roles de directiva son: Presidente, Secretaria, Tesorera, Encargada de Llave")

            opciones_directiva = {f"🎯 {v} (ID: {k})": k for k, v in roles_directiva.items()}

            st.write("**👥 Asociadas:** (no forman parte de la directiva)")
            opciones_no_directiva = {f"{v} (ID: {k})": k for k, v in roles_no_directiva.items()}

            todas_opciones = {**opciones_directiva, **opciones_no_directiva}

            rol_seleccionado = st.selectbox("Seleccione el rol *", options=list(todas_opciones.keys()))
            ID_Rol = todas_opciones[rol_seleccionado]

            if ID_Rol in [1, 2, 3, 4]:
                st.success("🎯 Este miembro forma parte de la DIRECTIVA")
            else:
                st.info("👥 Este miembro es ASOCIADA")

            ID_Estado = st.selectbox("Estado", options=[1, 2],
                                     format_func=lambda x: "Activo" if x == 1 else "Inactivo", index=0)

            fecha_inscripcion = st.date_input("Fecha de inscripción *", value=datetime.now().date())

            enviar = st.form_submit_button("✅ Guardar Miembro")

            if enviar:
                if nombre.strip() == "":
                    st.warning("⚠ Debes ingresar el nombre del miembro.")
                elif apellido.strip() == "":
                    st.warning("⚠ Debes ingresar el apellido del miembro.")
                elif ID_Grupo is None:
                    st.warning("⚠ Debes seleccionar un grupo.")
                elif DUI.strip() == "":
                    st.warning("⚠ Debes ingresar el DUI (campo obligatorio).")
                elif telefono.strip() == "":
                    st.warning("⚠ Debes ingresar el teléfono (campo obligatorio).")
                else:
                    try:
                        DUI_val = DUI.strip()
                        email_val = email.strip() if email.strip() != "" else None
                        telefono_val = telefono.strip()

                        cursor.execute(
                            "SELECT ID_Miembro FROM Miembro WHERE nombre = %s AND apellido = %s",
                            (nombre.strip(), apellido.strip())
                        )
                        miembro_existente = cursor.fetchone()

                        if miembro_existente:
                            st.error("❌ Este miembro ya está registrado en el sistema. No puede pertenecer a más de un grupo.")
                        else:
                            cursor.execute(
                                """INSERT INTO Miembro 
                                (ID_Grupo, nombre, apellido, DUI, email, telefono, 
                                 ID_Rol, ID_Estado, fecha_inscripcion) 
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                                (ID_Grupo, nombre.strip(), apellido.strip(), DUI_val,
                                 email_val, telefono_val, ID_Rol, ID_Estado,
                                 fecha_inscripcion)
                            )

                            con.commit()

                            cursor.execute("SELECT LAST_INSERT_ID()")
                            id_miembro = cursor.fetchone()[0]

                            st.session_state.miembro_registrado = True
                            st.session_state.id_miembro_creado = id_miembro
                            st.session_state.nombre_miembro_creado = f"{nombre.strip()} {apellido.strip()}"

                            st.rerun()

                    except Exception as e:
                        con.rollback()
                        st.error(f"❌ Error al registrar el miembro: {e}")

    except Exception as e:
        st.error(f"❌ Error de conexión: {e}")

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'con' in locals():
            con.close()
