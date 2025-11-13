import streamlit as st
from modulos.config.conexion import obtener_conexion

def mostrar_reglamentos():
    st.header("📜 Registrar Reglamento")

    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)

        # Cargar grupos existentes
        cursor.execute("SELECT ID_Grupo, nombre FROM Grupo ORDER BY nombre")
        grupos = cursor.fetchall()
            
        if not grupos:
            st.error("❌ No se encontraron grupos en la base de datos.")
            return
            
        grupo_opciones = {f"{g['nombre']}": g['ID_Grupo'] for g in grupos}

        # Inicializar session_state para las filas
        if 'filas_reglamento' not in st.session_state:
            st.session_state.filas_reglamento = [{
                'numero': 1,
                'nombre_regla': '',
                'descripcion': '',
                'monto_multa': 0.00,
                'estado': 1
            }]

        # Seleccionar grupo
        grupo_seleccionado = st.selectbox(
            "Selecciona el grupo para el reglamento:",
            options=list(grupo_opciones.keys())
        )
        id_grupo = grupo_opciones[grupo_seleccionado]

        st.subheader("📋 Reglas del Reglamento")
        st.info("Puedes agregar hasta 50 reglas. Completa al menos el nombre de la regla para cada fila.")

        # Mostrar todas las filas existentes
        filas_a_eliminar = []
        
        for i, fila in enumerate(st.session_state.filas_reglamento):
            st.markdown(f"**Regla {fila['numero']}**")
            
            col1, col2, col3, col4, col5 = st.columns([3, 3, 2, 2, 1])
            
            with col1:
                nombre_regla = st.text_input(
                    "Nombre regla",
                    value=fila['nombre_regla'],
                    key=f"nombre_{i}",
                    placeholder="Ej: Puntualidad en reuniones",
                    label_visibility="collapsed"
                )
            
            with col2:
                descripcion = st.text_area(
                    "Descripción",
                    value=fila['descripcion'],
                    key=f"desc_{i}",
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
                    key=f"monto_{i}",
                    label_visibility="collapsed"
                )
            
            with col4:
                estado = st.selectbox(
                    "Estado",
                    options=[1, 2],
                    format_func=lambda x: "✅ Activo" if x == 1 else "❌ Inactivo",
                    index=0 if fila['estado'] == 1 else 1,
                    key=f"estado_{i}",
                    label_visibility="collapsed"
                )
            
            with col5:
                st.write("")  # Espacio vertical
                st.write("")  # Espacio vertical
                if len(st.session_state.filas_reglamento) > 1:
                    if st.button("🗑️", key=f"eliminar_{i}"):
                        filas_a_eliminar.append(i)
            
            # Actualizar datos en session_state
            st.session_state.filas_reglamento[i] = {
                'numero': fila['numero'],
                'nombre_regla': nombre_regla,
                'descripcion': descripcion,
                'monto_multa': monto_multa,
                'estado': estado
            }
            
            st.markdown("---")

        # Eliminar filas marcadas para eliminar (de atrás hacia adelante)
        for indice in sorted(filas_a_eliminar, reverse=True):
            if 0 <= indice < len(st.session_state.filas_reglamento):
                st.session_state.filas_reglamento.pop(indice)
        
        # Renumerar filas después de eliminar
        if filas_a_eliminar:
            for i, fila in enumerate(st.session_state.filas_reglamento):
                fila['numero'] = i + 1
            st.rerun()

        # Botones de control
        col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
        
        with col_btn1:
            if st.button("➕ Agregar fila", use_container_width=True):
                if len(st.session_state.filas_reglamento) < 50:
                    nuevo_numero = len(st.session_state.filas_reglamento) + 1
                    st.session_state.filas_reglamento.append({
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
            if st.button("🔄 Limpiar todo", use_container_width=True):
                st.session_state.filas_reglamento = [{
                    'numero': 1,
                    'nombre_regla': '',
                    'descripcion': '',
                    'monto_multa': 0.00,
                    'estado': 1
                }]
                st.rerun()

        # Formulario para guardar
        with st.form("form_reglamento"):
            st.subheader("💾 Guardar Reglamento")
            
            confirmar_otro = st.checkbox(
                "📝 Registrar otro reglamento después de guardar",
                help="Si está marcado, podrás registrar otro reglamento inmediatamente después de guardar este."
            )
            
            guardar = st.form_submit_button("✅ Guardar Reglamento", use_container_width=True)
            
            if guardar:
                # Validar que haya al menos una regla con nombre
                reglas_validas = [f for f in st.session_state.filas_reglamento if f['nombre_regla'].strip()]
                
                if not reglas_validas:
                    st.error("❌ Debes ingresar al menos una regla con nombre.")
                    return
                
                # Insertar cada regla en la base de datos
                reglas_guardadas = 0
                errores = []
                
                for fila in st.session_state.filas_reglamento:
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
                    st.success(f"✅ Reglamento guardado exitosamente! Se registraron {reglas_guardadas} regla(s).")
                    
                    if confirmar_otro:
                        # Limpiar y preparar para nuevo reglamento
                        st.session_state.filas_reglamento = [{
                            'numero': 1,
                            'nombre_regla': '',
                            'descripcion': '',
                            'monto_multa': 0.00,
                            'estado': 1
                        }]
                        st.rerun()
                    else:
                        # Mostrar mensaje final
                        st.balloons()
                        st.info("🎉 Reglamento registrado correctamente. Para seguir navegando usa el menú de la izquierda.")

        # Mostrar resumen
        st.subheader("📊 Resumen del Reglamento")
        st.write(f"**Grupo seleccionado:** {grupo_seleccionado}")
        st.write(f"**Total de reglas configuradas:** {len(st.session_state.filas_reglamento)}")
        st.write(f"**Reglas con nombre completado:** {len([f for f in st.session_state.filas_reglamento if f['nombre_regla'].strip()])}")
        
        # Mostrar vista previa de las reglas
        if any(f['nombre_regla'].strip() for f in st.session_state.filas_reglamento):
            st.write("**Vista previa de reglas:**")
            for fila in st.session_state.filas_reglamento:
                if fila['nombre_regla'].strip():
                    estado_texto = "✅ Activo" if fila['estado'] == 1 else "❌ Inactivo"
                    monto_texto = f"${fila['monto_multa']:.2f} USD" if fila['monto_multa'] > 0 else "Sin multa"
                    st.write(f"- **{fila['nombre_regla']}** | {estado_texto} | {monto_texto}")

    except Exception as e:
        st.error(f"❌ Error general: {e}")

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'con' in locals():
            con.close()
