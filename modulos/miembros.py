import streamlit as st
from modulos.config.conexion import obtener_conexion
from datetime import datetime

def mostrar_miembro():
    st.header("👥 Gestión de Miembros del Grupo")

    # 🔥 1) Grupo del usuario logueado
    id_grupo = st.session_state.get("id_grupo")
    if id_grupo is None:
        st.error("⚠️ No tienes un grupo asociado. Crea primero un grupo en el módulo 'Grupos'.")
        return

    try:
        con = obtener_conexion()
        if not con:
            st.error("❌ No se pudo conectar a la base de datos.")
            return

        cursor = con.cursor(dictionary=True)

        # 🔥 2) Obtener información del grupo
        cursor.execute("SELECT nombre FROM Grupo WHERE ID_Grupo = %s", (id_grupo,))
        grupo_info = cursor.fetchone()
        
        if not grupo_info:
            st.error("❌ No se encontró información del grupo asociado a tu usuario.")
            return

        nombre_grupo = grupo_info['nombre']

        # Verificar si hay miembros registrados
        cursor.execute("SELECT COUNT(*) as total FROM Miembro WHERE ID_Grupo = %s", (id_grupo,))
        total_miembros = cursor.fetchone()['total']
        tiene_miembros = total_miembros > 0

        # Crear las dos tabs
        tab1, tab2 = st.tabs(["📝 Registrar Nuevo Miembro", "📋 Gestionar Todos los Miembros"])

        # ======================================================
        # TAB 1: REGISTRAR NUEVO MIEMBRO
        # ======================================================
        with tab1:
            st.subheader("Registrar Nuevo Miembro")

            # Estado para controlar el mensaje de éxito
            if "miembro_registrado" not in st.session_state:
                st.session_state.miembro_registrado = False

            if st.session_state.miembro_registrado:
                st.success("🎉 ¡Miembro registrado con éxito!")

                if st.button("🆕 Registrar otro miembro"):
                    st.session_state.miembro_registrado = False
                    st.rerun()
                return

            # Formulario para registrar el miembro
            with st.form("form_miembro"):
                st.markdown(f"**Grupo actual:** {nombre_grupo}")

                # Campos del formulario
                col1, col2 = st.columns(2)
                with col1:
                    nombre = st.text_input(
                        "Nombre *",
                        placeholder="Ingrese el nombre",
                        max_chars=100
                    )
                with col2:
                    apellido = st.text_input(
                        "Apellido *",
                        placeholder="Ingrese el apellido",
                        max_chars=100
                    )

                # Campo DUI y Teléfono
                col3, col4 = st.columns(2)
                with col3:
                    DUI = st.text_input(
                        "DUI *",
                        placeholder="Ingrese el número de DUI",
                        max_chars=20
                    )
                with col4:
                    telefono = st.text_input(
                        "Teléfono *",
                        placeholder="Ingrese el teléfono",
                        max_chars=20
                    )

                # -------------------------------------------------------
                # Rol en el grupo
                # -------------------------------------------------------
                st.markdown("#### 🏛️ Rol en el grupo")

                roles = {
                    1: "PRESIDENTE",
                    2: "SECRETARIA", 
                    3: "TESORERA",
                    4: "ENCARGADA_LLAVE",
                    5: "ASOCIADA"
                }

                roles_directiva = {k: v for k, v in roles.items() if k in [1, 2, 3, 4]}
                roles_no_directiva = {k: v for k, v in roles.items() if k == 5}

                st.info("**Miembros de Directiva:** Presidente, Secretaria, Tesorera, Encargada de Llave")

                opciones_directiva = {f"🎯 {v} (ID: {k})": k for k, v in roles_directiva.items()}
                opciones_no_directiva = {f"👥 {v} (ID: {k})": k for k, v in roles_no_directiva.items()}
                todas_opciones = {**opciones_directiva, **opciones_no_directiva}

                rol_seleccionado = st.selectbox("Seleccione el rol *", options=list(todas_opciones.keys()))
                ID_Rol = todas_opciones[rol_seleccionado]

                if ID_Rol in [1, 2, 3, 4]:
                    st.success("🎯 Este miembro formará parte de la DIRECTIVA")
                else:
                    st.info("👥 Este miembro será ASOCIADA")

                # Estado y fecha
                col5, col6 = st.columns(2)
                with col5:
                    ID_Estado = st.selectbox(
                        "Estado *",
                        options=[1, 2],
                        format_func=lambda x: "Activo" if x == 1 else "Inactivo",
                        index=0
                    )
                with col6:
                    fecha_inscripcion = st.date_input(
                        "Fecha de inscripción *",
                        value=datetime.now().date()
                    )

                enviar = st.form_submit_button("✅ Guardar Miembro", use_container_width=True)

                if enviar:
                    # Validaciones obligatorias
                    if not nombre.strip():
                        st.warning("⚠ Debes ingresar el nombre del miembro.")
                    elif not apellido.strip():
                        st.warning("⚠ Debes ingresar el apellido del miembro.")
                    elif not DUI.strip():
                        st.warning("⚠ Debes ingresar el DUI (campo obligatorio).")
                    elif not telefono.strip():
                        st.warning("⚠ Debes ingresar el teléfono (campo obligatorio).")
                    else:
                        try:
                            # Verificar duplicado SOLO dentro del mismo grupo
                            cursor.execute(
                                """
                                SELECT ID_Miembro 
                                FROM Miembro 
                                WHERE nombre = %s 
                                  AND apellido = %s 
                                  AND ID_Grupo = %s
                                """,
                                (nombre.strip(), apellido.strip(), id_grupo)
                            )
                            miembro_existente = cursor.fetchone()

                            if miembro_existente:
                                st.error(
                                    "❌ Este miembro ya está registrado en tu grupo. "
                                    "No puede pertenecer dos veces al mismo grupo."
                                )
                            else:
                                # INSERT en la tabla Miembro
                                cursor.execute(
                                    """
                                    INSERT INTO Miembro 
                                        (ID_Grupo, nombre, apellido, DUI, telefono, 
                                         ID_Rol, ID_Estado, fecha_inscripcion) 
                                    VALUES 
                                        (%s, %s, %s, %s, %s, %s, %s, %s)
                                    """,
                                    (
                                        id_grupo,
                                        nombre.strip(),
                                        apellido.strip(),
                                        DUI.strip(),
                                        telefono.strip(),
                                        ID_Rol,
                                        ID_Estado,
                                        fecha_inscripcion,
                                    )
                                )

                                con.commit()
                                st.session_state.miembro_registrado = True
                                st.rerun()

                        except Exception as e:
                            con.rollback()
                            st.error(f"❌ Error al registrar el miembro: {e}")

        # ======================================================
        # TAB 2: GESTIONAR TODOS LOS MIEMBROS
        # ======================================================
        with tab2:
            st.subheader("Gestionar Todos los Miembros")
            st.markdown(f"**Grupo:** {nombre_grupo}")

            if not tiene_miembros:
                st.info("📝 Este grupo aún no tiene miembros registrados. Agrega el primero en la pestaña 'Registrar Nuevo Miembro'.")
            else:
                # Cargar todos los miembros del grupo
                cursor.execute("""
                    SELECT m.ID_Miembro, m.nombre, m.apellido, m.DUI, m.telefono,
                           r.nombre_rol as rol, m.ID_Estado, m.fecha_inscripcion
                    FROM Miembro m
                    JOIN Rol r ON m.ID_Rol = r.ID_Rol
                    WHERE m.ID_Grupo = %s
                    ORDER BY m.nombre, m.apellido
                """, (id_grupo,))
                miembros = cursor.fetchall()

                st.info(f"📊 Total de miembros registrados: **{len(miembros)}**")
                
                # Inicializar session state para los estados si no existe
                if 'estados_miembros' not in st.session_state:
                    st.session_state.estados_miembros = {}
                    for miembro in miembros:
                        st.session_state.estados_miembros[miembro['ID_Miembro']] = miembro['ID_Estado']

                # Mostrar lista de miembros con selectbox de estado
                st.markdown("---")
                st.markdown("### 🎯 Lista de Miembros - Cambiar Estados")
                
                for i, miembro in enumerate(miembros):
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                    
                    with col1:
                        estado_color = "🟢" if miembro['ID_Estado'] == 1 else "🔴"
                        st.write(f"**{miembro['nombre']} {miembro['apellido']}**")
                        st.caption(f"{miembro['rol']} | DUI: {miembro['DUI']}")
                    
                    with col2:
                        st.write("**Teléfono:**")
                        st.write(miembro['telefono'])
                    
                    with col3:
                        st.write("**Fecha inscripción:**")
                        fecha = miembro['fecha_inscripcion']
                        if isinstance(fecha, str):
                            st.write(fecha)
                        else:
                            st.write(fecha.strftime('%d/%m/%Y') if fecha else "N/A")
                    
                    with col4:
                        # Selectbox para estado - usa session_state para mantener cambios
                        nuevo_estado = st.selectbox(
                            f"Estado {i}",
                            options=[1, 2],
                            format_func=lambda x: "✅ ACTIVO" if x == 1 else "❌ INACTIVO",
                            index=0 if st.session_state.estados_miembros[miembro['ID_Miembro']] == 1 else 1,
                            key=f"estado_{miembro['ID_Miembro']}"
                        )
                        st.session_state.estados_miembros[miembro['ID_Miembro']] = nuevo_estado
                        
                        # Mostrar badge del estado actual
                        if nuevo_estado == 1:
                            st.success("ACTIVO")
                        else:
                            st.error("INACTIVO")

                    st.markdown("---")

                # BOTÓN PARA GUARDAR CAMBIOS MASIVOS - AL FINAL DE TODO
                st.markdown("---")
                col_guardar, col_limpiar = st.columns([2, 1])
                
                with col_guardar:
                    if st.button("💾 GUARDAR TODOS LOS CAMBIOS", use_container_width=True, type="primary"):
                        try:
                            cambios_realizados = 0
                            for miembro in miembros:
                                id_miembro = miembro['ID_Miembro']
                                nuevo_estado = st.session_state.estados_miembros.get(id_miembro)
                                estado_original = miembro['ID_Estado']
                                
                                if nuevo_estado is not None and nuevo_estado != estado_original:
                                    cursor.execute(
                                        "UPDATE Miembro SET ID_Estado = %s WHERE ID_Miembro = %s",
                                        (nuevo_estado, id_miembro)
                                    )
                                    cambios_realizados += 1
                            
                            if cambios_realizados > 0:
                                con.commit()
                                st.success(f"✅ Se actualizaron {cambios_realizados} miembros correctamente!")
                                st.balloons()
                                
                                # Limpiar session state para recargar datos frescos
                                if 'estados_miembros' in st.session_state:
                                    del st.session_state.estados_miembros
                                st.rerun()
                            else:
                                st.info("ℹ️ No se realizaron cambios en los estados.")
                                
                        except Exception as e:
                            con.rollback()
                            st.error(f"❌ Error al guardar los cambios: {e}")
                
                with col_limpiar:
                    if st.button("🔄 Cancelar Cambios", use_container_width=True):
                        if 'estados_miembros' in st.session_state:
                            del st.session_state.estados_miembros
                        st.rerun()

                # Información sobre estados
                st.markdown("---")
                st.markdown("### 💡 Información sobre Estados")
                col_info1, col_info2 = st.columns(2)
                with col_info1:
                    st.success("**✅ ACTIVO:**")
                    st.write("- Aparece en asistencia")
                    st.write("- Puede realizar pagos")
                    st.write("- Puede solicitar préstamos")
                    st.write("- Aparece en módulo de ahorros")
                
                with col_info2:
                    st.error("**❌ INACTIVO:**")
                    st.write("- NO aparece en asistencia")
                    st.write("- NO puede realizar pagos")
                    st.write("- NO puede solicitar préstamos")
                    st.write("- NO aparece en módulo de ahorros")
                    st.write("- Solo vuelve con estado ACTIVO")

    except Exception as e:
        st.error(f"❌ Error general: {e}")

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'con' in locals():
            con.close()
