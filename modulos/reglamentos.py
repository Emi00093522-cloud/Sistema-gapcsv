import streamlit as st
from modulos.config.conexion import obtener_conexion
from datetime import datetime

def mostrar_reglamentos():
    st.header("📜 Gestión de Reglamentos del Grupo")

    # 🔥 1) Grupo del usuario logueado
    id_grupo = st.session_state.get("id_grupo")
    if id_grupo is None:
        st.error("⚠️ No tienes un grupo asociado. Crea primero un grupo en el módulo 'Grupos'.")
        return

    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)

        # Info del grupo del usuario
        cursor.execute("""
            SELECT g.ID_Grupo, g.nombre, g.fecha_inicio, d.nombre as distrito
            FROM Grupo g
            LEFT JOIN Distrito d ON g.ID_Distrito = d.ID_Distrito
            WHERE g.ID_Grupo = %s
        """, (id_grupo,))
        grupo_info = cursor.fetchone()
            
        if not grupo_info:
            st.error("❌ No se encontró información del grupo asociado a tu usuario.")
            return

        # ¿Ya tiene reglamento este grupo?
        cursor.execute("SELECT ID_Reglamento FROM Reglamento WHERE ID_Grupo = %s", (id_grupo,))
        registro_reg = cursor.fetchone()
        tiene_reglamento = registro_reg is not None

        # Tabs
        tab1, tab2 = st.tabs(["📝 Registrar / Ver Reglamento del Grupo", "✏️ Editar Reglamento del Grupo"])

        # ======================================================
        # TAB 1: REGISTRAR (solo si no existe)
        # ======================================================
        with tab1:
            st.subheader("Reglamento del grupo")

            if tiene_reglamento:
                st.info("✅ Este grupo ya tiene un reglamento registrado.")
                st.info("Si deseas modificarlo, ve a la pestaña **'Editar Reglamento del Grupo'**.")
            else:
                st.markdown("### 📋 Formulario de Reglamento Interno")

                # 1. Comunidad (solo lectura)
                st.markdown("#### 1. Nombre de la comunidad")
                st.info(f"**Distrito:** {grupo_info['distrito'] or 'No asignado'}")

                # 2. Fecha formación (solo lectura)
                st.markdown("#### 2. Fecha en que se formó el grupo de ahorro")
                fecha_formacion = grupo_info['fecha_inicio']
                if fecha_formacion:
                    st.info(f"**Fecha de formación:** {fecha_formacion.strftime('%d/%m/%Y')}")
                else:
                    st.info("**Fecha de formación:** No registrada")

                # 3. Reuniones
                st.markdown("#### 3. Reuniones")
                col_reun1, col_reun2, col_reun3 = st.columns(3)
                
                with col_reun1:
                    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
                    dia_reunion = st.selectbox(
                        "Día:",
                        options=dias_semana,
                        key="dia_reunion"
                    )
                
                with col_reun2:
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
                    lugar_reunion = st.text_input(
                        "Lugar:",
                        placeholder="Ej: Casa comunal",
                        key="lugar_reunion"
                    )

                st.markdown("**Frecuencia de reunión:**")
                frecuencia_reunion = st.selectbox(
                    "Seleccione la frecuencia:",
                    options=["QUINCENAL", "SEMANAL", "MENSUAL"],
                    key="frecuencia_reunion",
                    label_visibility="collapsed"
                )

                # 4. Comité de Dirección (SOLO cargos específicos de directiva)
                st.markdown("#### 4. Comité de Dirección")
                try:
                    cursor.execute("""
                        SELECT m.nombre, m.apellido, r.nombre_rol as cargo
                        FROM Miembro m
                        INNER JOIN Rol r ON m.ID_Rol = r.ID_Rol
                        WHERE m.ID_Grupo = %s
                          AND UPPER(r.nombre_rol) IN ('PRESIDENTE', 'SECRETARIA', 'TESORERA', 'ENCARGADA DE LLAVE')
                        ORDER BY 
                            CASE UPPER(r.nombre_rol)
                                WHEN 'PRESIDENTE' THEN 1
                                WHEN 'SECRETARIA' THEN 2
                                WHEN 'TESORERA' THEN 3
                                WHEN 'ENCARGADA DE LLAVE' THEN 4
                                ELSE 5
                            END
                    """, (id_grupo,))
                    directiva = cursor.fetchall()
                    
                    if directiva:
                        for miembro in directiva:
                            nombre_completo = f"{miembro['nombre']} {miembro['apellido']}"
                            st.markdown(f"| {miembro['cargo']} | {nombre_completo} |")
                    else:
                        st.info("ℹ️ No se han registrado miembros de directiva (Presidente, Secretaria, Tesorera, Encargada de llave).")
                        
                except Exception as e:
                    st.error(f"❌ Error al cargar el comité de dirección: {e}")

                # 5. Nombre del grupo
                st.markdown("#### 5. Nombre del grupo de ahorro")
                st.info(f"**Nuestro grupo se llama:** {grupo_info['nombre']}")

                # 6. Asistencia
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

                # 7. Ahorros
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

                # 8. Préstamos
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

                # 9. Ciclo
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
                    placeholder="Describa la meta social o propósito del grupo...",
                    height=100,
                    key="meta_social"
                )

                # 11. Otras reglas
                st.markdown("#### 11. Otras reglas")
                st.info("Agrega reglas adicionales específicas de tu grupo:")
                
                if 'reglas_adicionales' not in st.session_state:
                    st.session_state.reglas_adicionales = [{'id': 1, 'texto': ''}]

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
                        st.session_state.reglas_adicionales[i]['texto'] = texto_regla
                    
                    with col_regla2:
                        st.write("")
                        st.write("")
                        if len(st.session_state.reglas_adicionales) > 1:
                            if st.button("🗑️", key=f"eliminar_regla_{i}"):
                                reglas_a_eliminar.append(i)

                for indice in sorted(reglas_a_eliminar, reverse=True):
                    if 0 <= indice < len(st.session_state.reglas_adicionales):
                        st.session_state.reglas_adicionales.pop(indice)
                
                for i, regla in enumerate(st.session_state.reglas_adicionales):
                    regla['id'] = i + 1

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

                st.markdown("---")
                if st.button("💾 Guardar Reglamento Completo", use_container_width=True, type="primary"):
                    if not dia_reunion or not hora_reunion or not lugar_reunion:
                        st.error("❌ Los campos de reuniones (día, hora, lugar) son obligatorios.")
                        return

                    try:
                        if not hora_reunion or ':' not in hora_reunion:
                            st.error("❌ Formato de hora inválido. Use formato HH:MM")
                            return
                        hora_completa = f"{hora_reunion} {periodo_reunion}"
                    except:
                        st.error("❌ Error en el formato de hora. Use formato HH:MM")
                        return

                    try:
                        otras_reglas_texto = "\n".join([
                            f"{regla['id']}. {regla['texto']}" 
                            for regla in st.session_state.reglas_adicionales 
                            if regla['texto'].strip()
                        ])

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
                        
                        st.session_state.reglas_adicionales = [{'id': 1, 'texto': ''}]
                        st.rerun()
                            
                    except Exception as e:
                        con.rollback()
                        st.error(f"❌ Error al guardar el reglamento: {e}")

        # ======================================================
        # TAB 2: EDITAR (solo reglamento de este grupo)
        # ======================================================
        with tab2:
            st.subheader("Editar Reglamento del Grupo")

            if not tiene_reglamento:
                st.info("📝 Este grupo aún no tiene reglamento. Crea uno en la pestaña 'Registrar / Ver Reglamento del Grupo'.")
            else:
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
                    WHERE r.ID_Grupo = %s
                    LIMIT 1
                """, (id_grupo,))
                reglamento_editar = cursor.fetchone()

                if not reglamento_editar:
                    st.error("❌ No se pudo cargar el reglamento del grupo.")
                else:
                    mostrar_formulario_edicion(reglamento_editar, cursor, con)

    except Exception as e:
        st.error(f"❌ Error general: {e}")

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'con' in locals():
            con.close()


def mostrar_formulario_edicion(reglamento, cursor, con):
    """Formulario para editar el reglamento existente del grupo actual"""
    
    st.subheader(f"✏️ Editando Reglamento: {reglamento['nombre_grupo']}")
    
    col_info1, col_info2 = st.columns(2)
    with col_info1:
        st.info(f"**Distrito:** {reglamento['distrito']}")
    with col_info2:
        st.info(f"**Fecha formación:** {reglamento['fecha_inicio'].strftime('%d/%m/%Y') if reglamento['fecha_inicio'] else 'No registrada'}")
    
    st.markdown("---")
    
    # 3. Reuniones
    st.markdown("#### 3. Reuniones")
    col_reun1, col_reun2, col_reun3 = st.columns(3)
    
    hora_existente = reglamento['hora_reunion'] or ""
    periodo_existente = "AM"
    hora_sin_periodo = hora_existente
    
    if hora_existente:
        if "AM" in hora_existente.upper():
            periodo_existente = "AM"
            hora_sin_periodo = hora_existente.upper().replace("AM", "").strip()
        elif "PM" in hora_existente.upper():
            periodo_existente = "PM"
            hora_sin_periodo = hora_existente.upper().replace("PM", "").strip()
    
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

    # 4. Comité de Dirección (SOLO cargos específicos de directiva)
    st.markdown("#### 4. Comité de Dirección")
    try:
        cursor.execute("""
            SELECT m.nombre, m.apellido, r.nombre_rol as cargo
            FROM Miembro m
            INNER JOIN Rol r ON m.ID_Rol = r.ID_Rol
            WHERE m.ID_Grupo = %s
              AND UPPER(r.nombre_rol) IN ('PRESIDENTE', 'SECRETARIA', 'TESORERA', 'ENCARGADA DE LLAVE')
            ORDER BY 
                CASE UPPER(r.nombre_rol)
                    WHEN 'PRESIDENTE' THEN 1
                    WHEN 'SECRETARIA' THEN 2
                    WHEN 'TESORERA' THEN 3
                    WHEN 'ENCARGADA DE LLAVE' THEN 4
                    ELSE 5
                END
        """, (reglamento['ID_Grupo'],))
        directiva = cursor.fetchall()
        
        if directiva:
            for miembro in directiva:
                nombre_completo = f"{miembro['nombre']} {miembro['apellido']}"
                st.markdown(f"| {miembro['cargo']} | {nombre_completo} |")
        else:
            st.info("ℹ️ No se han registrado miembros de directiva (Presidente, Secretaria, Tesorera, Encargada de llave).")
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
    
    if 'reglas_adicionales_edicion' not in st.session_state:
        reglas_existentes = []
        if reglamento['otras_reglas']:
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
                    reglas_existentes.append({
                        'id': len(reglas_existentes) + 1,
                        'texto': linea.strip()
                    })
        
        if not reglas_existentes:
            reglas_existentes = [{'id': 1, 'texto': ''}]
            
        st.session_state.reglas_adicionales_edicion = reglas_existentes

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
            st.write("")
            st.write("")
            if len(st.session_state.reglas_adicionales_edicion) > 1:
                if st.button("🗑️", key=f"editar_eliminar_regla_{i}"):
                    reglas_a_eliminar.append(i)

    for indice in sorted(reglas_a_eliminar, reverse=True):
        if 0 <= indice < len(st.session_state.reglas_adicionales_edicion):
            st.session_state.reglas_adicionales_edicion.pop(indice)
    
    for i, regla in enumerate(st.session_state.reglas_adicionales_edicion):
        regla['id'] = i + 1

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

    st.markdown("---")
    col_guardar, col_cancelar = st.columns(2)
    
    with col_guardar:
        if st.button("💾 Guardar Cambios", use_container_width=True, type="primary"):
            if not dia_reunion or not hora_reunion or not lugar_reunion:
                st.error("❌ Los campos de reuniones (día, hora, lugar) son obligatorios.")
                return

            try:
                if not hora_reunion or ':' not in hora_reunion:
                    st.error("❌ Formato de hora inválido. Use formato HH:MM")
                    return
                hora_completa = f"{hora_reunion} {periodo_reunion}"
            except:
                st.error("❌ Error en el formato de hora. Use formato HH:MM")
                return

            try:
                otras_reglas_texto = "\n".join([
                    f"{regla['id']}. {regla['texto']}" 
                    for regla in st.session_state.reglas_adicionales_edicion 
                    if regla['texto'].strip()
                ])

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
                
                if 'reglas_adicionales_edicion' in st.session_state:
                    del st.session_state.reglas_adicionales_edicion
                st.rerun()
                    
            except Exception as e:
                con.rollback()
                st.error(f"❌ Error al actualizar el reglamento: {e}")
    
    with col_cancelar:
        if st.button("❌ Cancelar Edición", use_container_width=True):
            if 'reglas_adicionales_edicion' in st.session_state:
                del st.session_state.reglas_adicionales_edicion
            st.rerun()
