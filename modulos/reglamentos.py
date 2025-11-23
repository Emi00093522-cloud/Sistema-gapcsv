import streamlit as st
from modulos.config.conexion import obtener_conexion
from datetime import datetime

def mostrar_reglamentos():
    st.header("📜 Gestión de Reglamentos por Grupo")

    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)

        # Cargar grupos existentes con información disponible
        cursor.execute("""
            SELECT g.ID_Grupo, g.nombre, g.fecha_inicio, d.nombre as distrito
            FROM Grupo g
            LEFT JOIN Distrito d ON g.ID_Distrito = d.ID_Distrito
            ORDER BY g.nombre
        """)
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

            # 1. Selección del grupo
            st.markdown("### 1. Nombre del grupo de ahorro")
            grupo_seleccionado = st.selectbox(
                "Selecciona el grupo para el NUEVO reglamento:",
                options=list(grupos_sin_reglamento.keys()),
                key="nuevo_grupo"
            )
            id_grupo = grupos_sin_reglamento[grupo_seleccionado]
            
            # Obtener información del grupo seleccionado
            grupo_info = next((g for g in grupos if g['ID_Grupo'] == id_grupo), None)
            
            if not grupo_info:
                st.error("❌ No se pudo obtener la información del grupo.")
                return

            st.markdown("---")
            st.markdown("### 📋 Formulario de Reglamento Interno")

            # 1. Nombre de la comunidad (Distrito) - SOLO LECTURA
            st.markdown("#### 1. Nombre de la comunidad")
            st.info(f"**Distrito:** {grupo_info['distrito'] or 'No asignado'}")

            # 2. Fecha en que se formó el grupo - SOLO LECTURA
            st.markdown("#### 2. Fecha en que se formó el grupo de ahorro")
            fecha_formacion = grupo_info['fecha_inicio']
            if fecha_formacion:
                st.info(f"**Fecha de formación:** {fecha_formacion.strftime('%d/%m/%Y')}")
            else:
                st.info("**Fecha de formación:** No registrada")

            # 3. Reuniones - CAMPOS EDITABLES (MODIFICADO CON FRECUENCIA SIMPLE)
            st.markdown("#### 3. Reuniones")
            col_reun1, col_reun2, col_reun3 = st.columns(3)
            
            with col_reun1:
                # Día de la semana - lista desplegable
                dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
                dia_reunion = st.selectbox(
                    "Día:",
                    options=dias_semana,
                    key="dia_reunion"
                )
            
            with col_reun2:
                # Hora con formato y AM/PM
                col_hora, col_ampm = st.columns([2, 1])
                with col_hora:
                    hora_reunion = st.text_input(
                        "Hora:",
                        placeholder="00:00",
                        key="hora_reunion",
                        max_chars=5
                    )
                with col_ampm:
                    periodo_reunion = st.selectbox(
                        "Periodo:",
                        options=["AM", "PM"],
                        key="periodo_reunion"
                    )
            
            with col_reun3:
                # Lugar - solo texto
                lugar_reunion = st.text_input(
                    "Lugar:",
                    placeholder="Ej: Casa comunal",
                    key="lugar_reunion"
                )

            # Frecuencia de reunión - MODIFICADO: Solo menú desplegable
            st.markdown("**Frecuencia de reunión:**")
            frecuencia_reunion = st.selectbox(
                "Seleccione la frecuencia:",
                options=["QUINCENAL", "SEMANAL", "MENSUAL"],
                key="frecuencia_reunion",
                label_visibility="collapsed"
            )

            # 4. Comité de Dirección - MOSTRAR TODOS LOS MIEMBROS CON ROL
            st.markdown("#### 4. Comité de Dirección")
            
            try:
                # Mostrar TODOS los miembros que tengan un rol asignado
                cursor.execute("""
                    SELECT m.nombre, m.apellido, r.nombre_rol as cargo
                    FROM Miembro m
                    INNER JOIN Rol r ON m.ID_Rol = r.ID_Rol
                    WHERE m.ID_Grupo = %s
                    ORDER BY r.nombre_rol
                """, (id_grupo,))
                directiva = cursor.fetchall()
                
                if directiva:
                    st.markdown("""
                    | Cargo | Nombre de la Socia |
                    |-------|-------------------|
                    """)
                    for miembro in directiva:
                        nombre_completo = f"{miembro['nombre']} {miembro['apellido']}"
                        st.markdown(f"| {miembro['cargo']} | {nombre_completo} |")
                else:
                    st.info("ℹ️ No se han registrado miembros con roles asignados para este grupo.")
                    
            except Exception as e:
                st.error(f"❌ Error al cargar el comité de dirección: {e}")

            # 5. Nombre del grupo de ahorro - SOLO LECTURA
            st.markdown("#### 5. Nombre del grupo de ahorro")
            st.info(f"**Nuestro grupo se llama:** {grupo_info['nombre']}")

            # 6. Asistencia y Reglas - REGLONES EDITABLES
            st.markdown("#### 6. Asistencia")
            
            st.markdown("**Nosotras asistimos a todas las reuniones.**")
            
            col_asist1, col_asist2 = st.columns(2)
            
            with col_asist1:
                st.markdown("**Si faltamos a una reunión pagamos una multa de:**")
                monto_multa_asistencia = st.number_input(
                    "Monto de multa por falta (USD):",
                    min_value=0.00,
                    value=0.00,
                    step=0.50,
                    format="%.2f",
                    key="monto_multa_asistencia",
                    label_visibility="collapsed"
                )
            
            with col_asist2:
                st.markdown("**No pagamos una multa si faltamos a una reunión y tenemos permiso por la siguiente razón (o razones):**")
                justificacion_ausencia = st.text_area(
                    "Justificación para ausencia sin multa:",
                    placeholder="Ej: Enfermedad certificada, emergencia familiar, etc.",
                    height=80,
                    key="justificacion_ausencia",
                    label_visibility="collapsed"
                )

            # 7. Ahorros - CAMPO EDITABLE
            st.markdown("#### 7. Ahorros")
            st.markdown("**Depositamos una cantidad mínima de ahorros de:**")
            ahorro_minimo = st.number_input(
                "Cantidad mínima de ahorros (USD):",
                min_value=0.00,
                value=0.00,
                step=0.50,
                format="%.2f",
                key="ahorro_minimo"
            )

            # 8. Préstamos - CAMPOS EDITABLES
            st.markdown("#### 8. Préstamos")
            
            st.markdown("**Pagamos interés cuando se cumple el mes.**")
            
            col_prest1, col_prest2, col_prest3 = st.columns(3)
            
            with col_prest1:
                st.markdown("**Interés por cada $10.00 prestados:**")
                interes_por_diez = st.number_input(
                    "Interés ($):",
                    min_value=0.00,
                    value=0.00,
                    step=0.10,
                    format="%.2f",
                    key="interes_por_diez",
                    label_visibility="collapsed"
                )
            
            with col_prest2:
                st.markdown("**Monto máximo de préstamo:**")
                monto_maximo_prestamo = st.number_input(
                    "Monto máximo (USD):",
                    min_value=0.00,
                    value=0.00,
                    step=10.00,
                    format="%.2f",
                    key="monto_maximo_prestamo",
                    label_visibility="collapsed"
                )
            
            with col_prest3:
                st.markdown("**Plazo máximo de préstamo:**")
                plazo_maximo_prestamo = st.number_input(
                    "Plazo máximo (meses):",
                    min_value=0,
                    value=0,
                    step=1,
                    key="plazo_maximo_prestamo",
                    label_visibility="collapsed"
                )
            
            st.markdown("**Solamente podemos tener un préstamo a la vez.**")
            un_prestamo_vez = st.selectbox(
                "¿Solo un préstamo a la vez?",
                options=["Sí", "No"],
                key="un_prestamo_vez"
            )

            # 9. Ciclo - CAMPOS EDITABLES
            st.markdown("#### 9. Ciclo")
            
            col_ciclo1, col_ciclo2 = st.columns(2)
            
            with col_ciclo1:
                st.markdown("**Fecha inicio de ciclo:**")
                fecha_inicio_ciclo = st.date_input(
                    "Fecha inicio:",
                    key="fecha_inicio_ciclo",
                    label_visibility="collapsed"
                )
            
            with col_ciclo2:
                st.markdown("**Duración del ciclo:**")
                duracion_ciclo = st.selectbox(
                    "Duración:",
                    options=[6, 12],
                    format_func=lambda x: f"{x} meses",
                    key="duracion_ciclo",
                    label_visibility="collapsed"
                )
            
            # Calcular fecha fin automáticamente
            if fecha_inicio_ciclo:
                try:
                    from dateutil.relativedelta import relativedelta
                    fecha_fin_ciclo = fecha_inicio_ciclo + relativedelta(months=duracion_ciclo)
                    st.info(f"**Fecha fin de ciclo:** {fecha_fin_ciclo.strftime('%d/%m/%Y')}")
                except:
                    # Fallback si no tiene dateutil
                    import datetime as dt
                    fecha_fin_ciclo = fecha_inicio_ciclo + dt.timedelta(days=duracion_ciclo * 30)
                    st.info(f"**Fecha fin de ciclo (aproximada):** {fecha_fin_ciclo.strftime('%d/%m/%Y')}")

            st.markdown("**Al cierre de ciclo, vamos a calcular los ahorros y ganancias de cada socia durante el ciclo, a retirar nuestros ahorros y ganancias y a decidir cuándo vamos a empezar un nuevo ciclo.**")

            # 10. Meta social - CAMPO EDITABLE
            st.markdown("#### 10. Meta social")
            meta_social = st.text_area(
                "Meta social del grupo:",
                placeholder="Describa la meta social o propósito del grupo...",
                height=100,
                key="meta_social"
            )

            # 11+. Otras reglas - SISTEMA DE REGLONES
            st.markdown("#### 11. Otras reglas")
            st.info("Agrega reglas adicionales específicas de tu grupo:")
            
            # Inicializar session_state para reglas adicionales
            if 'reglas_adicionales' not in st.session_state:
                st.session_state.reglas_adicionales = [{'id': 1, 'texto': ''}]

            # Mostrar reglas existentes
            reglas_a_eliminar = []
            for i, regla in enumerate(st.session_state.reglas_adicionales):
                col_regla1, col_regla2 = st.columns([5, 1])
                
                with col_regla1:
                    texto_regla = st.text_area(
                        f"Regla {regla['id']}:",
                        value=regla['texto'],
                        placeholder="Describe la regla adicional...",
                        height=60,
                        key=f"regla_adicional_{i}"
                    )
                    # Actualizar en session_state
                    st.session_state.reglas_adicionales[i]['texto'] = texto_regla
                
                with col_regla2:
                    st.write("")  # Espacio
                    st.write("")  # Espacio
                    if len(st.session_state.reglas_adicionales) > 1:
                        if st.button("🗑️", key=f"eliminar_regla_{i}"):
                            reglas_a_eliminar.append(i)

            # Eliminar reglas marcadas
            for indice in sorted(reglas_a_eliminar, reverse=True):
                if 0 <= indice < len(st.session_state.reglas_adicionales):
                    st.session_state.reglas_adicionales.pop(indice)
            
            # Renumerar reglas
            for i, regla in enumerate(st.session_state.reglas_adicionales):
                regla['id'] = i + 1

            # Botones para gestionar reglas adicionales
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                if st.button("➕ Agregar regla adicional", use_container_width=True):
                    nuevo_id = len(st.session_state.reglas_adicionales) + 1
                    st.session_state.reglas_adicionales.append({'id': nuevo_id, 'texto': ''})
                    st.rerun()
            
            with col_btn2:
                if st.button("🔄 Limpiar reglas adicionales", use_container_width=True):
                    st.session_state.reglas_adicionales = [{'id': 1, 'texto': ''}]
                    st.rerun()

            # Botón para guardar TODO el reglamento
            st.markdown("---")
            if st.button("💾 Guardar Reglamento Completo", use_container_width=True, type="primary"):
                # Validar campos obligatorios
                if not dia_reunion or not hora_reunion or not lugar_reunion:
                    st.error("❌ Los campos de reuniones (día, hora, lugar) son obligatorios.")
                    return

                # Validar formato de hora
                try:
                    # Combinar hora con AM/PM
                    hora_completa = f"{hora_reunion} {periodo_reunion}"
                    # Verificar formato básico
                    if not hora_reunion or ':' not in hora_reunion:
                        st.error("❌ Formato de hora inválido. Use formato HH:MM")
                        return
                except:
                    st.error("❌ Error en el formato de hora. Use formato HH:MM")
                    return

                try:
                    # Preparar reglas adicionales como texto
                    otras_reglas_texto = "\n".join([
                        f"{regla['id']}. {regla['texto']}" 
                        for regla in st.session_state.reglas_adicionales 
                        if regla['texto'].strip()
                    ])

                    # Guardar el reglamento completo
                    cursor.execute("""
                        INSERT INTO Reglamento 
                        (ID_Grupo, dia_reunion, hora_reunion, lugar_reunion, frecuencia_reunion,
                         monto_multa_asistencia, justificacion_ausencia, ahorro_minimo,
                         interes_por_diez, monto_maximo_prestamo, plazo_maximo_prestamo,
                         un_prestamo_vez, fecha_inicio_ciclo, duracion_ciclo,
                         meta_social, otras_reglas)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        id_grupo, dia_reunion, hora_completa, lugar_reunion, frecuencia_reunion,
                        monto_multa_asistencia, justificacion_ausencia, ahorro_minimo,
                        interes_por_diez, monto_maximo_prestamo, plazo_maximo_prestamo,
                        un_prestamo_vez, fecha_inicio_ciclo, duracion_ciclo,
                        meta_social, otras_reglas_texto
                    ))
                    
                    con.commit()
                    st.success("✅ Reglamento guardado exitosamente!")
                    st.balloons()
                    
                    # Limpiar formulario
                    st.session_state.reglas_adicionales = [{'id': 1, 'texto': ''}]
                    st.rerun()
                        
                except Exception as e:
                    con.rollback()
                    st.error(f"❌ Error al guardar el reglamento: {e}")

        with tab2:
            st.subheader("Editar Reglamentos Existentes")
            
            if not grupos_con_reglamento:
                st.info("📝 No hay reglamentos registrados aún. Usa la pestaña 'Registrar Nuevo Reglamento' para crear el primer reglamento.")
                return

            # Cargar reglamentos existentes con información del grupo
            cursor.execute("""
                SELECT r.ID_Reglamento, r.ID_Grupo, g.nombre as nombre_grupo, 
                       d.nombre as distrito, g.fecha_inicio,
                       r.dia_reunion, r.hora_reunion, r.lugar_reunion, r.frecuencia_reunion,
                       r.monto_multa_asistencia, r.justificacion_ausencia, r.ahorro_minimo,
                       r.interes_por_diez, r.monto_maximo_prestamo, r.plazo_maximo_prestamo,
                       r.un_prestamo_vez, r.fecha_inicio_ciclo, r.duracion_ciclo,
                       r.meta_social, r.otras_reglas
                FROM Reglamento r
                JOIN Grupo g ON r.ID_Grupo = g.ID_Grupo
                LEFT JOIN Distrito d ON g.ID_Distrito = d.ID_Distrito
                ORDER BY g.nombre
            """)
            reglamentos_existentes = cursor.fetchall()

            st.write("### 📋 Reglamentos Guardados")
            
            # Si estamos en modo edición, mostrar el formulario de edición
            if 'reglamento_a_editar' in st.session_state:
                reglamento_id = st.session_state.reglamento_a_editar
                
                # Buscar el reglamento seleccionado
                reglamento_editar = next((r for r in reglamentos_existentes if r['ID_Reglamento'] == reglamento_id), None)
                
                if reglamento_editar:
                    mostrar_formulario_edicion(reglamento_editar, cursor, con)
                else:
                    st.error("❌ No se encontró el reglamento seleccionado.")
                    if st.button("🔙 Volver a la lista"):
                        del st.session_state.reglamento_a_editar
                        st.rerun()
            else:
                # Mostrar lista de reglamentos para editar
                for reglamento in reglamentos_existentes:
                    with st.expander(f"📜 {reglamento['nombre_grupo']} - Distrito: {reglamento['distrito']}"):
                        # Mostrar información resumida del reglamento
                        st.write(f"**Reuniones:** {reglamento['dia_reunion']} {reglamento['hora_reunion']} - {reglamento['lugar_reunion']}")
                        st.write(f"**Ahorro mínimo:** ${reglamento['ahorro_minimo']:.2f}")
                        st.write(f"**Multa por falta:** ${reglamento['monto_multa_asistencia']:.2f}")
                        
                        # Botón para editar este reglamento
                        if st.button(f"✏️ Editar Reglamento", key=f"editar_{reglamento['ID_Reglamento']}"):
                            st.session_state.reglamento_a_editar = reglamento['ID_Reglamento']
                            st.rerun()

    except Exception as e:
        st.error(f"❌ Error general: {e}")

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'con' in locals():
            con.close()


def mostrar_formulario_edicion(reglamento, cursor, con):
    """Muestra el formulario para editar un reglamento existente"""
    
    st.subheader(f"✏️ Editando Reglamento: {reglamento['nombre_grupo']}")
    
    # Información del grupo (solo lectura)
    col_info1, col_info2 = st.columns(2)
    with col_info1:
        st.info(f"**Distrito:** {reglamento['distrito']}")
    with col_info2:
        st.info(f"**Fecha formación:** {reglamento['fecha_inicio'].strftime('%d/%m/%Y') if reglamento['fecha_inicio'] else 'No registrada'}")
    
    st.markdown("---")
    
    # 3. Reuniones - CAMPOS EDITABLES
    st.markdown("#### 3. Reuniones")
    col_reun1, col_reun2, col_reun3 = st.columns(3)
    
    # Parsear hora existente si está disponible
    hora_existente = reglamento['hora_reunion'] or ""
    periodo_existente = "AM"
    hora_sin_periodo = hora_existente
    
    if hora_existente:
        if "AM" in hora_existente.upper():
            periodo_existente = "AM"
            hora_sin_periodo = hora_existente.replace("AM", "").replace("am", "").strip()
        elif "PM" in hora_existente.upper():
            periodo_existente = "PM"
            hora_sin_periodo = hora_existente.replace("PM", "").replace("pm", "").strip()
    
    with col_reun1:
        dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        dia_reunion = st.selectbox(
            "Día:",
            options=dias_semana,
            index=dias_semana.index(reglamento['dia_reunion']) if reglamento['dia_reunion'] in dias_semana else 0,
            key="editar_dia_reunion"
        )
    
    with col_reun2:
        col_hora, col_ampm = st.columns([2, 1])
        with col_hora:
            hora_reunion = st.text_input(
                "Hora:",
                value=hora_sin_periodo,
                placeholder="00:00",
                key="editar_hora_reunion",
                max_chars=5
            )
        with col_ampm:
            periodo_reunion = st.selectbox(
                "Periodo:",
                options=["AM", "PM"],
                index=0 if periodo_existente == "AM" else 1,
                key="editar_periodo_reunion"
            )
    
    with col_reun3:
        lugar_reunion = st.text_input(
            "Lugar:",
            value=reglamento['lugar_reunion'] or "",
            placeholder="Ej: Casa comunal",
            key="editar_lugar_reunion"
        )

    st.markdown("**Frecuencia de reunión:**")
    frecuencia_reunion = st.selectbox(
        "Seleccione la frecuencia:",
        options=["QUINCENAL", "SEMANAL", "MENSUAL"],
        index=["QUINCENAL", "SEMANAL", "MENSUAL"].index(reglamento['frecuencia_reunion']) if reglamento['frecuencia_reunion'] in ["QUINCENAL", "SEMANAL", "MENSUAL"] else 0,
        key="editar_frecuencia_reunion",
        label_visibility="collapsed"
    )

    # 4. Comité de Dirección - SOLO LECTURA
    st.markdown("#### 4. Comité de Dirección")
    try:
        cursor.execute("""
            SELECT m.nombre, m.apellido, r.nombre_rol as cargo
            FROM Miembro m
            INNER JOIN Rol r ON m.ID_Rol = r.ID_Rol
            WHERE m.ID_Grupo = %s
            ORDER BY r.nombre_rol
        """, (reglamento['ID_Grupo'],))
        directiva = cursor.fetchall()
        
        if directiva:
            st.markdown("""
            | Cargo | Nombre de la Socia |
            |-------|-------------------|
            """)
            for miembro in directiva:
                nombre_completo = f"{miembro['nombre']} {miembro['apellido']}"
                st.markdown(f"| {miembro['cargo']} | {nombre_completo} |")
        else:
            st.info("ℹ️ No se han registrado miembros con roles asignados para este grupo.")
    except Exception as e:
        st.error(f"❌ Error al cargar el comité de dirección: {e}")

    # 5. Nombre del grupo - SOLO LECTURA
    st.markdown("#### 5. Nombre del grupo de ahorro")
    st.info(f"**Nuestro grupo se llama:** {reglamento['nombre_grupo']}")

    # 6. Asistencia
    st.markdown("#### 6. Asistencia")
    st.markdown("**Nosotras asistimos a todas las reuniones.**")
    
    col_asist1, col_asist2 = st.columns(2)
    
    with col_asist1:
        st.markdown("**Si faltamos a una reunión pagamos una multa de:**")
        monto_multa_asistencia = st.number_input(
            "Monto de multa por falta (USD):",
            min_value=0.00,
            value=float(reglamento['monto_multa_asistencia'] or 0.00),
            step=0.50,
            format="%.2f",
            key="editar_monto_multa_asistencia",
            label_visibility="collapsed"
        )
    
    with col_asist2:
        st.markdown("**No pagamos una multa si faltamos a una reunión y tenemos permiso por la siguiente razón (o razones):**")
        justificacion_ausencia = st.text_area(
            "Justificación para ausencia sin multa:",
            value=reglamento['justificacion_ausencia'] or "",
            placeholder="Ej: Enfermedad certificada, emergencia familiar, etc.",
            height=80,
            key="editar_justificacion_ausencia",
            label_visibility="collapsed"
        )

    # 7. Ahorros
    st.markdown("#### 7. Ahorros")
    st.markdown("**Depositamos una cantidad mínima de ahorros de:**")
    ahorro_minimo = st.number_input(
        "Cantidad mínima de ahorros (USD):",
        min_value=0.00,
        value=float(reglamento['ahorro_minimo'] or 0.00),
        step=0.50,
        format="%.2f",
        key="editar_ahorro_minimo"
    )

    # 8. Préstamos
    st.markdown("#### 8. Préstamos")
    st.markdown("**Pagamos interés cuando se cumple el mes.**")
    
    col_prest1, col_prest2, col_prest3 = st.columns(3)
    
    with col_prest1:
        st.markdown("**Interés por cada $10.00 prestados:**")
        interes_por_diez = st.number_input(
            "Interés ($):",
            min_value=0.00,
            value=float(reglamento['interes_por_diez'] or 0.00),
            step=0.10,
            format="%.2f",
            key="editar_interes_por_diez",
            label_visibility="collapsed"
        )
    
    with col_prest2:
        st.markdown("**Monto máximo de préstamo:**")
        monto_maximo_prestamo = st.number_input(
            "Monto máximo (USD):",
            min_value=0.00,
            value=float(reglamento['monto_maximo_prestamo'] or 0.00),
            step=10.00,
            format="%.2f",
            key="editar_monto_maximo_prestamo",
            label_visibility="collapsed"
        )
    
    with col_prest3:
        st.markdown("**Plazo máximo de préstamo:**")
        plazo_maximo_prestamo = st.number_input(
            "Plazo máximo (meses):",
            min_value=0,
            value=int(reglamento['plazo_maximo_prestamo'] or 0),
            step=1,
            key="editar_plazo_maximo_prestamo",
            label_visibility="collapsed"
        )
    
    st.markdown("**Solamente podemos tener un préstamo a la vez.**")
    opciones_prestamo = ["Sí", "No"]
    index_prestamo = 0 if reglamento['un_prestamo_vez'] == "Sí" else 1
    un_prestamo_vez = st.selectbox(
        "¿Solo un préstamo a la vez?",
        options=opciones_prestamo,
        index=index_prestamo,
        key="editar_un_prestamo_vez"
    )

    # 9. Ciclo
    st.markdown("#### 9. Ciclo")
    
    col_ciclo1, col_ciclo2 = st.columns(2)
    
    with col_ciclo1:
        st.markdown("**Fecha inicio de ciclo:**")
        fecha_inicio_ciclo = st.date_input(
            "Fecha inicio:",
            value=reglamento['fecha_inicio_ciclo'],
            key="editar_fecha_inicio_ciclo",
            label_visibility="collapsed"
        )
    
    with col_ciclo2:
        st.markdown("**Duración del ciclo:**")
        duracion_ciclo = st.selectbox(
            "Duración:",
            options=[6, 12],
            index=0 if reglamento['duracion_ciclo'] == 6 else 1,
            format_func=lambda x: f"{x} meses",
            key="editar_duracion_ciclo",
            label_visibility="collapsed"
        )
    
    # Calcular fecha fin automáticamente
    if fecha_inicio_ciclo:
        try:
            from dateutil.relativedelta import relativedelta
            fecha_fin_ciclo = fecha_inicio_ciclo + relativedelta(months=duracion_ciclo)
            st.info(f"**Fecha fin de ciclo:** {fecha_fin_ciclo.strftime('%d/%m/%Y')}")
        except:
            import datetime as dt
            fecha_fin_ciclo = fecha_inicio_ciclo + dt.timedelta(days=duracion_ciclo * 30)
            st.info(f"**Fecha fin de ciclo (aproximada):** {fecha_fin_ciclo.strftime('%d/%m/%Y')}")

    st.markdown("**Al cierre de ciclo, vamos a calcular los ahorros y ganancias de cada socia durante el ciclo, a retirar nuestros ahorros y ganancias y a decidir cuándo vamos a empezar un nuevo ciclo.**")

    # 10. Meta social
    st.markdown("#### 10. Meta social")
    meta_social = st.text_area(
        "Meta social del grupo:",
        value=reglamento['meta_social'] or "",
        placeholder="Describa la meta social o propósito del grupo...",
        height=100,
        key="editar_meta_social"
    )

    # 11. Otras reglas
    st.markdown("#### 11. Otras reglas")
    st.info("Edita las reglas adicionales específicas de tu grupo:")
    
    # Inicializar reglas adicionales desde el reglamento existente
    if 'reglas_adicionales_edicion' not in st.session_state:
        reglas_existentes = []
        if reglamento['otras_reglas']:
            # Parsear reglas existentes (formato: "1. Texto regla\n2. Otra regla")
            lineas = reglamento['otras_reglas'].split('\n')
            for linea in lineas:
                if '.' in linea:
                    partes = linea.split('.', 1)
                    if len(partes) == 2:
                        reglas_existentes.append({
                            'id': int(partes[0].strip()),
                            'texto': partes[1].strip()
                        })
                elif linea.strip():
                    # Si no tiene número, agregar como nueva regla
                    reglas_existentes.append({
                        'id': len(reglas_existentes) + 1,
                        'texto': linea.strip()
                    })
        
        if not reglas_existentes:
            reglas_existentes = [{'id': 1, 'texto': ''}]
            
        st.session_state.reglas_adicionales_edicion = reglas_existentes

    # Mostrar reglas existentes para edición
    reglas_a_eliminar = []
    for i, regla in enumerate(st.session_state.reglas_adicionales_edicion):
        col_regla1, col_regla2 = st.columns([5, 1])
        
        with col_regla1:
            texto_regla = st.text_area(
                f"Regla {regla['id']}:",
                value=regla['texto'],
                placeholder="Describe la regla adicional...",
                height=60,
                key=f"editar_regla_adicional_{i}"
            )
            st.session_state.reglas_adicionales_edicion[i]['texto'] = texto_regla
        
        with col_regla2:
            st.write("")  # Espacio
            st.write("")  # Espacio
            if len(st.session_state.reglas_adicionales_edicion) > 1:
                if st.button("🗑️", key=f"editar_eliminar_regla_{i}"):
                    reglas_a_eliminar.append(i)

    # Eliminar reglas marcadas
    for indice in sorted(reglas_a_eliminar, reverse=True):
        if 0 <= indice < len(st.session_state.reglas_adicionales_edicion):
            st.session_state.reglas_adicionales_edicion.pop(indice)
    
    # Renumerar reglas
    for i, regla in enumerate(st.session_state.reglas_adicionales_edicion):
        regla['id'] = i + 1

    # Botones para gestionar reglas adicionales
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("➕ Agregar regla adicional", use_container_width=True, key="editar_agregar_regla"):
            nuevo_id = len(st.session_state.reglas_adicionales_edicion) + 1
            st.session_state.reglas_adicionales_edicion.append({'id': nuevo_id, 'texto': ''})
            st.rerun()
    
    with col_btn2:
        if st.button("🔄 Limpiar reglas adicionales", use_container_width=True, key="editar_limpiar_reglas"):
            st.session_state.reglas_adicionales_edicion = [{'id': 1, 'texto': ''}]
            st.rerun()

    # Botones de acción
    st.markdown("---")
    col_guardar, col_cancelar = st.columns(2)
    
    with col_guardar:
        if st.button("💾 Guardar Cambios", use_container_width=True, type="primary"):
            # Validar campos obligatorios
            if not dia_reunion or not hora_reunion or not lugar_reunion:
                st.error("❌ Los campos de reuniones (día, hora, lugar) son obligatorios.")
                return

            # Validar formato de hora
            try:
                hora_completa = f"{hora_reunion} {periodo_reunion}"
                if not hora_reunion or ':' not in hora_reunion:
                    st.error("❌ Formato de hora inválido. Use formato HH:MM")
                    return
            except:
                st.error("❌ Error en el formato de hora. Use formato HH:MM")
                return

            try:
                # Preparar reglas adicionales como texto
                otras_reglas_texto = "\n".join([
                    f"{regla['id']}. {regla['texto']}" 
                    for regla in st.session_state.reglas_adicionales_edicion 
                    if regla['texto'].strip()
                ])

                # ACTUALIZAR el reglamento existente (sin Fecha_Actualizacion)
                cursor.execute("""
                    UPDATE Reglamento 
                    SET dia_reunion = %s, hora_reunion = %s, lugar_reunion = %s, frecuencia_reunion = %s,
                        monto_multa_asistencia = %s, justificacion_ausencia = %s, ahorro_minimo = %s,
                        interes_por_diez = %s, monto_maximo_prestamo = %s, plazo_maximo_prestamo = %s,
                        un_prestamo_vez = %s, fecha_inicio_ciclo = %s, duracion_ciclo = %s,
                        meta_social = %s, otras_reglas = %s
                    WHERE ID_Reglamento = %s
                """, (
                    dia_reunion, hora_completa, lugar_reunion, frecuencia_reunion,
                    monto_multa_asistencia, justificacion_ausencia, ahorro_minimo,
                    interes_por_diez, monto_maximo_prestamo, plazo_maximo_prestamo,
                    un_prestamo_vez, fecha_inicio_ciclo, duracion_ciclo,
                    meta_social, otras_reglas_texto, reglamento['ID_Reglamento']
                ))
                
                con.commit()
                st.success("✅ Reglamento actualizado exitosamente!")
                st.balloons()
                
                # Limpiar session state y volver a la lista
                if 'reglas_adicionales_edicion' in st.session_state:
                    del st.session_state.reglas_adicionales_edicion
                if 'reglamento_a_editar' in st.session_state:
                    del st.session_state.reglamento_a_editar
                st.rerun()
                    
            except Exception as e:
                con.rollback()
                st.error(f"❌ Error al actualizar el reglamento: {e}")
    
    with col_cancelar:
        if st.button("❌ Cancelar Edición", use_container_width=True):
            # Limpiar session state
            if 'reglas_adicionales_edicion' in st.session_state:
                del st.session_state.reglas_adicionales_edicion
            if 'reglamento_a_editar' in st.session_state:
                del st.session_state.reglamento_a_editar
            st.rerun()
