import streamlit as st
from modulos.config.conexion import obtener_conexion

def mostrar_reglamento():
    st.header("📜 Gestión de Reglamentos por Grupo")

    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)

        # Cargar grupos existentes
        cursor.execute("SELECT ID_Grupo, nombre FROM Grupo ORDER BY nombre")
        grupos = cursor.fetchall()
            
        if not grupos:
            st.error("❌ No se encontraron grupos en la base de datos.")
            return

        # Verificar qué grupos ya tienen reglamento
        cursor.execute("SELECT DISTINCT ID_Grupo FROM Reglamento")
        grupos_con_reglamento = [row['ID_Grupo'] for row in cursor.fetchall()]

        grupo_opciones = {f"{g['nombre']}": g['ID_Grupo'] for g in grupos}
        grupos_sin_reglamento = {nombre: id_grupo for nombre, id_grupo in grupo_opciones.items() 
                               if id_grupo not in grupos_con_reglamento}

        # Pestañas para Registrar y Editar
        tab1, tab2 = st.tabs(["📝 Registrar Nuevo Reglamento", "✏️ Editar Reglamentos Existentes"])

        with tab1:
            st.subheader("Registrar Nuevo Reglamento")
            
            if not grupos_sin_reglamento:
                st.info("🎉 Todos los grupos ya tienen su reglamento registrado.")
                st.info("Usa la pestaña 'Editar Reglamentos Existentes' para modificar los reglamentos.")
                return

            # Seleccionar grupo para NUEVO reglamento (solo grupos sin reglamento)
            grupo_seleccionado = st.selectbox(
                "Selecciona el grupo para el NUEVO reglamento:",
                options=list(grupos_sin_reglamento.keys()),
                key="nuevo_grupo"
            )
            id_grupo = grupos_sin_reglamento[grupo_seleccionado]

            # Inicializar session_state para las filas del NUEVO reglamento
            if 'filas_nuevo_reglamento' not in st.session_state:
                st.session_state.filas_nuevo_reglamento = [{
                    'numero': 1,
                    'nombre_regla': '',
                    'descripcion': '',
                    'monto_multa': 0.00,
                    'estado': 1
                }]

            st.info("Puedes agregar hasta 50 reglas. Completa al menos el nombre de la regla para cada fila.")

            # Mostrar todas las filas existentes del NUEVO reglamento
            filas_a_eliminar = []
            
            for i, fila in enumerate(st.session_state.filas_nuevo_reglamento):
                st.markdown(f"**Regla {fila['numero']}**")
                
                col1, col2, col3, col4, col5 = st.columns([3, 3, 2, 2, 1])
                
                with col1:
                    nombre_regla = st.text_input(
                        "Nombre regla",
                        value=fila['nombre_regla'],
                        key=f"nuevo_nombre_{i}",
                        placeholder="Ej: Puntualidad en reuniones",
                        label_visibility="collapsed"
                    )
                
                with col2:
                    descripcion = st.text_area(
                        "Descripción",
                        value=fila['descripcion'],
                        key=f"nuevo_desc_{i}",
                        placeholder="Describe la regla...",
                        height=60,
                        label_visibility="collapsed"
                    )
                
                with col3:
                    monto_multa = st.number_input(
                        "Monto Multa (USD)",
                        min_value=0.00,
                        value=float(fila['monto_multa']),
                        step=0.50,
                        format="%.2f",
                        key=f"nuevo_monto_{i}",
                        label_visibility="collapsed"
                    )
                
                with col4:
                    estado = st.selectbox(
                        "Estado",
                        options=[1, 2],
                        format_func=lambda x: "✅ Activo" if x == 1 else "❌ Inactivo",
                        index=0 if fila['estado'] == 1 else 1,
                        key=f"nuevo_estado_{i}",
                        label_visibility="collapsed"
                    )
                
                with col5:
                    st.write("")  # Espacio vertical
                    st.write("")  # Espacio vertical
                    if len(st.session_state.filas_nuevo_reglamento) > 1:
                        if st.button("🗑️", key=f"nuevo_eliminar_{i}"):
                            filas_a_eliminar.append(i)
                
                # Actualizar datos en session_state
                st.session_state.filas_nuevo_reglamento[i] = {
                    'numero': fila['numero'],
                    'nombre_regla': nombre_regla,
                    'descripcion': descripcion,
                    'monto_multa': monto_multa,
                    'estado': estado
                }
                
                st.markdown("---")

            # Eliminar filas marcadas para eliminar
            for indice in sorted(filas_a_eliminar, reverse=True):
                if 0 <= indice < len(st.session_state.filas_nuevo_reglamento):
                    st.session_state.filas_nuevo_reglamento.pop(indice)
            
            # Renumerar filas después de eliminar
            if filas_a_eliminar:
                for i, fila in enumerate(st.session_state.filas_nuevo_reglamento):
                    fila['numero'] = i + 1
                st.rerun()

            # Botones de control para NUEVO
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                if st.button("➕ Agregar fila", use_container_width=True, key="nuevo_agregar"):
                    if len(st.session_state.filas_nuevo_reglamento) < 50:
                        nuevo_numero = len(st.session_state.filas_nuevo_reglamento) + 1
                        st.session_state.filas_nuevo_reglamento.append({
                            'numero': nuevo_numero,
                            'nombre_regla': '',
                            'descripcion': '',
                            'monto_multa': 0.00,
                            'estado': 1
                        })
                        st.rerun()
                    else:
                        st.warning("⚠️ Has alcanzado el límite máximo de 50 reglas.")
            
            with col_btn2:
                if st.button("🔄 Limpiar todo", use_container_width=True, key="nuevo_limpiar"):
                    st.session_state.filas_nuevo_reglamento = [{
                        'numero': 1,
                        'nombre_regla': '',
                        'descripcion': '',
                        'monto_multa': 0.00,
                        'estado': 1
                    }]
                    st.rerun()

            # Formulario para guardar NUEVO reglamento
            with st.form("form_nuevo_reglamento"):
                confirmar_otro = st.checkbox(
                    "📝 Registrar otro reglamento después de guardar",
                    key="nuevo_confirmar"
                )
                
                guardar = st.form_submit_button("✅ Guardar Reglamento", use_container_width=True)
                
                if guardar:
                    # Validar que haya al menos una regla con nombre
                    reglas_validas = [f for f in st.session_state.filas_nuevo_reglamento if f['nombre_regla'].strip()]
                    
                    if not reglas_validas:
                        st.error("❌ Debes ingresar al menos una regla con nombre.")
                        return
                    
                    # Insertar cada regla en la base de datos
                    reglas_guardadas = 0
                    errores = []
                    
                    for fila in st.session_state.filas_nuevo_reglamento:
                        # Solo guardar reglas que tengan nombre
                        if fila['nombre_regla'].strip():
                            try:
                                cursor.execute(
                                    """INSERT INTO Reglamento 
                                       (ID_Grupo, nombre_regla, descripcion, monto_multa, ID_Estado) 
                                       VALUES (%s, %s, %s, %s, %s)""",
                                    (
                                        id_grupo,
                                        fila['nombre_regla'].strip(),
                                        fila['descripcion'].strip() if fila['descripcion'] else None,
                                        fila['monto_multa'],
                                        fila['estado']
                                    )
                                )
                                reglas_guardadas += 1
                                
                            except Exception as e:
                                errores.append(f"Error en regla '{fila['nombre_regla']}': {e}")
                    
                    if errores:
                        con.rollback()
                        st.error("❌ Errores al guardar:")
                        for error in errores:
                            st.write(f"- {error}")
                    else:
                        con.commit()
                        st.success(f"✅ Reglamento guardado exitosamente para el grupo {grupo_seleccionado}! Se registraron {reglas_guardadas} regla(s).")
                        
                        if confirmar_otro:
                            # Limpiar y preparar para nuevo reglamento
                            st.session_state.filas_nuevo_reglamento = [{
                                'numero': 1,
                                'nombre_regla': '',
                                'descripcion': '',
                                'monto_multa': 0.00,
                                'estado': 1
                            }]
                            st.rerun()
                        else:
                            st.balloons()
                            st.info("🎉 Reglamento registrado correctamente. Para seguir navegando usa el menú de la izquierda.")

        with tab2:
            st.subheader("Editar Reglamentos Existentes")
            
            if not grupos_con_reglamento:
                st.info("📝 No hay reglamentos registrados aún. Usa la pestaña 'Registrar Nuevo Reglamento' para crear el primer reglamento.")
                return

            # Cargar reglamentos existentes con información del grupo
            cursor.execute("""
                SELECT r.ID_Grupo, g.nombre as nombre_grupo, 
                       COUNT(r.ID_Reglamento) as total_reglas
                FROM Reglamento r
                JOIN Grupo g ON r.ID_Grupo = g.ID_Grupo
                GROUP BY r.ID_Grupo, g.nombre
                ORDER BY g.nombre
            """)
            reglamentos_existentes = cursor.fetchall()

            st.write("### 📋 Reglamentos Guardados")
            
            for reglamento in reglamentos_existentes:
                with st.expander(f"📜 Reglamento - {reglamento['nombre_grupo']} ({reglamento['total_reglas']} reglas)"):
                    # Botón para editar este reglamento
                    if st.button(f"✏️ Editar Reglamento del Grupo {reglamento['nombre_grupo']}", 
                                key=f"editar_{reglamento['ID_Grupo']}"):
                        st.session_state.grupo_a_editar = reglamento['ID_Grupo']
                        st.session_state.nombre_grupo_editar = reglamento['nombre_grupo']
                        st.rerun()

            # Editar reglamento específico
            if 'grupo_a_editar' in st.session_state:
                st.write("---")
                st.subheader(f"✏️ Editando Reglamento del Grupo: {st.session_state.nombre_grupo_editar}")
                
                # Cargar reglas existentes de este grupo
                cursor.execute("""
                    SELECT ID_Reglamento, nombre_regla, descripcion, monto_multa, ID_Estado
                    FROM Reglamento 
                    WHERE ID_Grupo = %s
                    ORDER BY ID_Reglamento
                """, (st.session_state.grupo_a_editar,))
                reglas_existentes = cursor.fetchall()

                # Inicializar session_state para edición
                if 'filas_edicion_reglamento' not in st.session_state:
                    st.session_state.filas_edicion_reglamento = []
                    for i, regla in enumerate(reglas_existentes):
                        st.session_state.filas_edicion_reglamento.append({
                            'id_reglamento': regla['ID_Reglamento'],
                            'numero': i + 1,
                            'nombre_regla': regla['nombre_regla'],
                            'descripcion': regla['descripcion'] or '',
                            'monto_multa': float(regla['monto_multa']) if regla['monto_multa'] else 0.00,
                            'estado': regla['ID_Estado']
                        })

                # Mostrar filas para edición
                filas_edicion_eliminar = []
                
                for i, fila in enumerate(st.session_state.filas_edicion_reglamento):
                    st.markdown(f"**Regla {fila['numero']}**")
                    
                    col1, col2, col3, col4, col5 = st.columns([3, 3, 2, 2, 1])
                    
                    with col1:
                        nombre_regla = st.text_input(
                            "Nombre regla",
                            value=fila['nombre_regla'],
                            key=f"editar_nombre_{i}",
                            placeholder="Ej: Puntualidad en reuniones",
                            label_visibility="collapsed"
                        )
                    
                    with col2:
                        descripcion = st.text_area(
                            "Descripción",
                            value=fila['descripcion'],
                            key=f"editar_desc_{i}",
                            placeholder="Describe la regla...",
                            height=60,
                            label_visibility="collapsed"
                        )
                    
                    with col3:
                        monto_multa = st.number_input(
                            "Monto Multa (USD)",
                            min_value=0.00,
                            value=float(fila['monto_multa']),
                            step=0.50,
                            format="%.2f",
                            key=f"editar_monto_{i}",
                            label_visibility="collapsed"
                        )
                    
                    with col4:
                        estado = st.selectbox(
                            "Estado",
                            options=[1, 2],
                            format_func=lambda x: "✅ Activo" if x == 1 else "❌ Inactivo",
                            index=0 if fila['estado'] == 1 else 1,
                            key=f"editar_estado_{i}",
                            label_visibility="collapsed"
                        )
                    
                    with col5:
                        st.write("")  # Espacio vertical
                        st.write("")  # Espacio vertical
                        if st.button("🗑️", key=f"editar_eliminar_{i}"):
                            filas_edicion_eliminar.append(i)
                    
                    # Actualizar datos en session_state
                    st.session_state.filas_edicion_reglamento[i] = {
                        'id_reglamento': fila['id_reglamento'],
                        'numero': fila['numero'],
                        'nombre_regla': nombre_regla,
                        'descripcion': descripcion,
                        'monto_multa': monto_multa,
                        'estado': estado
                    }
                    
                    st.markdown("---")

                # Botones para edición
                col_edit1, col_edit2, col_edit3 = st.columns([1, 1, 1])
                
                with col_edit1:
                    if st.button("➕ Agregar regla", use_container_width=True, key="editar_agregar"):
                        if len(st.session_state.filas_edicion_reglamento) < 50:
                            nuevo_numero = len(st.session_state.filas_edicion_reglamento) + 1
                            st.session_state.filas_edicion_reglamento.append({
                                'id_reglamento': None,  # Nuevo registro
                                'numero': nuevo_numero,
                                'nombre_regla': '',
                                'descripcion': '',
                                'monto_multa': 0.00,
                                'estado': 1
                            })
                            st.rerun()
                
                with col_edit2:
                    if st.button("💾 Guardar Cambios", use_container_width=True, key="editar_guardar"):
                        # Procesar cambios
                        cambios_realizados = 0
                        errores_edicion = []
                        
                        for fila in st.session_state.filas_edicion_reglamento:
                            try:
                                if fila['id_reglamento']:  # UPDATE existente
                                    cursor.execute("""
                                        UPDATE Reglamento 
                                        SET nombre_regla=%s, descripcion=%s, monto_multa=%s, ID_Estado=%s
                                        WHERE ID_Reglamento=%s
                                    """, (
                                        fila['nombre_regla'].strip(),
                                        fila['descripcion'].strip() if fila['descripcion'] else None,
                                        fila['monto_multa'],
                                        fila['estado'],
                                        fila['id_reglamento']
                                    ))
                                else:  # INSERT nuevo
                                    cursor.execute("""
                                        INSERT INTO Reglamento 
                                        (ID_Grupo, nombre_regla, descripcion, monto_multa, ID_Estado) 
                                        VALUES (%s, %s, %s, %s, %s)
                                    """, (
                                        st.session_state.grupo_a_editar,
                                        fila['nombre_regla'].strip(),
                                        fila['descripcion'].strip() if fila['descripcion'] else None,
                                        fila['monto_multa'],
                                        fila['estado']
                                    ))
                                cambios_realizados += 1
                            except Exception as e:
                                errores_edicion.append(f"Error en regla '{fila['nombre_regla']}': {e}")
                        
                        if errores_edicion:
                            con.rollback()
                            st.error("❌ Errores al guardar cambios:")
                            for error in errores_edicion:
                                st.write(f"- {error}")
                        else:
                            con.commit()
                            st.success(f"✅ Cambios guardados exitosamente! {cambios_realizados} regla(s) actualizadas.")
                            # Limpiar estado de edición
                            if 'grupo_a_editar' in st.session_state:
                                del st.session_state.grupo_a_editar
                            if 'filas_edicion_reglamento' in st.session_state:
                                del st.session_state.filas_edicion_reglamento
                            st.rerun()
                
                with col_edit3:
                    if st.button("❌ Cancelar Edición", use_container_width=True, key="editar_cancelar"):
                        if 'grupo_a_editar' in st.session_state:
                            del st.session_state.grupo_a_editar
                        if 'filas_edicion_reglamento' in st.session_state:
                            del st.session_state.filas_edicion_reglamento
                        st.rerun()

    except Exception as e:
        st.error(f"❌ Error general: {e}")

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'con' in locals():
            con.close()
