import streamlit as st
from modulos.config.conexion import obtener_conexion
from datetime import datetime, date

def mostrar_reglamentos():
    st.header("📋 Reglamentos de Grupos")
    
    try:
        con = obtener_conexion()
        cursor = con.cursor()
        
        # Obtener grupos que ya tienen reglamento
        cursor.execute("""
            SELECT DISTINCT g.ID_Grupo, g.nombre 
            FROM Grupo g 
            JOIN Reglamento r ON g.ID_Grupo = r.ID_Grupo
        """)
        grupos_con_reglamento = cursor.fetchall()
        
        # Obtener todos los grupos para el selector
        cursor.execute("SELECT ID_Grupo, nombre FROM Grupo ORDER BY nombre")
        todos_grupos = cursor.fetchall()
        
        tab1, tab2 = st.tabs(["📝 Registrar Nuevo Reglamento", "✏️ Editar Reglamentos Existentes"])
        
        with tab1:
            st.subheader("Registrar Nuevo Reglamento")
            
            if not todos_grupos:
                st.info("📝 No hay grupos registrados. Primero registra un grupo en la sección 'Grupos'.")
                return
            
            # Selector de grupo
            grupo_options = {f"{grupo[1]} (ID: {grupo[0]})": grupo[0] for grupo in todos_grupos}
            grupo_seleccionado = st.selectbox(
                "Seleccione el grupo para el reglamento:",
                options=list(grupo_options.keys())
            )
            id_grupo = grupo_options[grupo_seleccionado]
            
            st.markdown("---")
            st.markdown("### ✍️ Complete el Reglamento del Grupo")
            
            # 1. Título del reglamento
            st.markdown("#### 1. Título del Reglamento")
            titulo_reglamento = st.text_input(
                "Título del reglamento:",
                value=f"Reglamento del Grupo {grupo_seleccionado.split(' (ID:')[0]}",
                placeholder="Ingrese el título del reglamento...",
                key="titulo_reglamento"
            )
            
            # 2. Introducción
            st.markdown("#### 2. Introducción")
            introduccion = st.text_area(
                "Introducción del reglamento:",
                value="Nosotras, las socias del grupo, nos comprometemos a cumplir con las siguientes normas establecidas para el buen funcionamiento de nuestra organización...",
                height=100,
                key="introduccion"
            )
            
            # 3. Reuniones - MODIFICADO: Frecuencia como menú desplegable
            st.markdown("#### 3. Reuniones")

            col_reun1, col_reun2, col_reun3, col_reun4 = st.columns(4)

            with col_reun1:
                st.markdown("**Día:**")
                dia_reunion = st.selectbox(
                    "Día de reunión:",
                    options=["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"],
                    key="dia_reunion",
                    label_visibility="collapsed"
                )

            with col_reun2:
                st.markdown("**Hora:**")
                hora_reunion = st.text_input(
                    "Hora:",
                    placeholder="HH:MM",
                    key="hora_reunion",
                    label_visibility="collapsed"
                )

            with col_reun3:
                st.markdown("**Período:**")
                periodo_reunion = st.selectbox(
                    "Período:",
                    options=["AM", "PM"],
                    key="periodo_reunion",
                    label_visibility="collapsed"
                )

            with col_reun4:
                st.markdown("**Lugar:**")
                lugar_reunion = st.text_input(
                    "Lugar:",
                    placeholder="Ej: UCA, Escuela, etc.",
                    key="lugar_reunion",
                    label_visibility="collapsed"
                )

            # Frecuencia de reunión - MODIFICADO: Solo menú desplegable
            st.markdown("**Frecuencia de reunión:**")
            frecuencia_reunion = st.selectbox(
                "Seleccione la frecuencia:",
                options=["SEMANAL", "QUINCENAL", "MENSUAL"],
                key="frecuencia_reunion",
                label_visibility="collapsed"
            )
            
            # 4. Asistencia - CAMPOS EDITABLES
            st.markdown("#### 4. Asistencia")
            
            col_asist1, col_asist2 = st.columns(2)
            
            with col_asist1:
                st.markdown("**Multa por llegar tarde:**")
                monto_multa_tarde = st.number_input(
                    "Multa por tardanza (USD):",
                    min_value=0.00,
                    value=0.25,
                    step=0.05,
                    format="%.2f",
                    key="monto_multa_tarde"
                )
                
                st.markdown("**Multa por faltar a reunión:**")
                monto_multa_asistencia = st.number_input(
                    "Multa por falta (USD):",
                    min_value=0.00,
                    value=0.50,
                    step=0.05,
                    format="%.2f",
                    key="monto_multa_asistencia"
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

            # 5. Ahorros - CAMPO EDITABLE
            st.markdown("#### 5. Ahorros")
            st.markdown("**Depositamos una cantidad mínima de ahorros de:**")
            ahorro_minimo = st.number_input(
                "Cantidad mínima de ahorros (USD):",
                min_value=0.00,
                value=1.00,
                step=0.50,
                format="%.2f",
                key="ahorro_minimo"
            )

            # 6. Préstamos - CAMPOS EDITABLES
            st.markdown("#### 6. Préstamos")
            
            st.markdown("**Pagamos interés cuando se cumple el mes.**")
            
            col_prest1, col_prest2, col_prest3 = st.columns(3)
            
            with col_prest1:
                st.markdown("**Interés por cada $10.00 prestados:**")
                interes_por_diez = st.number_input(
                    "Interés ($):",
                    min_value=0.00,
                    value=0.50,
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
                    value=100.00,
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
                    value=6,
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

            # 7. Ciclo - CAMPOS EDITABLES
            st.markdown("#### 7. Ciclo")
            
            col_ciclo1, col_ciclo2 = st.columns(2)
            
            with col_ciclo1:
                st.markdown("**Fecha inicio de ciclo:**")
                fecha_inicio_ciclo = st.date_input(
                    "Fecha inicio:",
                    value=datetime.now().date(),
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

            # 8. Meta social - CAMPO EDITABLE
            st.markdown("#### 8. Meta social")
            meta_social = st.text_area(
                "Meta social del grupo:",
                placeholder="Describa la meta social o propósito del grupo...",
                height=100,
                key="meta_social"
            )

            # 9+. Otras reglas - SISTEMA DE REGLONES
            st.markdown("#### 9. Otras reglas")
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
                       d.nombre as distrito, g.fecha_inicio
                FROM Reglamento r
                JOIN Grupo g ON r.ID_Grupo = g.ID_Grupo
                LEFT JOIN Distrito d ON g.ID_Distrito = d.ID_Distrito
                ORDER BY g.nombre
            """)
            reglamentos_existentes = cursor.fetchall()

            st.write("### 📋 Reglamentos Guardados")
            
            for reglamento in reglamentos_existentes:
                with st.expander(f"📜 {reglamento['nombre_grupo']} - Distrito: {reglamento['distrito']}"):
                    # Botón para editar este reglamento
                    if st.button(f"✏️ Editar Reglamento", key=f"editar_{reglamento['ID_Reglamento']}"):
                        st.session_state.reglamento_a_editar = reglamento['ID_Reglamento']
                        st.rerun()

            # TODO: Implementar la funcionalidad de edición completa
            if 'reglamento_a_editar' in st.session_state:
                st.write("---")
                st.subheader("✏️ Editando Reglamento")
                st.info("🔧 Funcionalidad de edición en desarrollo...")
                
                if st.button("❌ Cancelar Edición"):
                    del st.session_state.reglamento_a_editar
                    st.rerun()

    except Exception as e:
        st.error(f"❌ Error general: {e}")

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'con' in locals():
            con.close()
