import streamlit as st
from modulos.config.conexion import obtener_conexion

def mostrar_reglamento():
    st.header("📜 Registrar Reglamento")

    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)

        # Cargar grupos existentes - BUSCAR LA TABLA CORRECTA
        try:
            # Primero verificar qué tablas existen
            cursor.execute("SHOW TABLES")
            tablas = cursor.fetchall()
            st.write("🔍 Tablas disponibles en la base de datos:")
            for tabla in tablas:
                st.write(f"- {list(tabla.values())[0]}")
            
            # Buscar la tabla de grupos (puede tener diferentes nombres)
            nombres_posibles = ['grupos', 'Grupos', 'grupo', 'Grupo', 'reglamentos', 'Reglamentos']
            tabla_grupos_encontrada = None
            
            for nombre in nombres_posibles:
                cursor.execute(f"SHOW TABLES LIKE '{nombre}'")
                if cursor.fetchone():
                    tabla_grupos_encontrada = nombre
                    st.success(f"✅ Tabla encontrada: {nombre}")
                    break
            
            if not tabla_grupos_encontrada:
                st.error("❌ No se encontró ninguna tabla de grupos o reglamentos.")
                st.info("""
                **Para usar este módulo necesitas:**
                1. Crear la tabla de grupos en tu base de datos
                2. O contactar al administrador de la base de datos
                """)
                return
            
            # Cargar los grupos/reglamentos existentes
            cursor.execute(f"SELECT * FROM {tabla_grupos_encontrada} LIMIT 5")
            muestra_datos = cursor.fetchall()
            st.write("📋 Muestra de datos de la tabla:")
            st.write(muestra_datos)
            
            # Intentar determinar la estructura de la tabla
            cursor.execute(f"DESCRIBE {tabla_grupos_encontrada}")
            columnas = cursor.fetchall()
            st.write("🔍 Estructura de la tabla:")
            for columna in columnas:
                st.write(f"- {columna['Field']} ({columna['Type']})")
            
            # Buscar columnas ID y nombre
            id_columna = None
            nombre_columna = None
            
            for columna in columnas:
                field_lower = columna['Field'].lower()
                if field_lower in ['id_grupo', 'id', 'grupo_id', 'id_reglamento']:
                    id_columna = columna['Field']
                elif field_lower in ['nombre_grupo', 'nombre', 'name', 'grupo_nombre', 'nombre_regla', 'regla']:
                    nombre_columna = columna['Field']
            
            if not id_columna or not nombre_columna:
                st.error("❌ No se pudieron identificar las columnas ID y nombre en la tabla.")
                return
                
            # Cargar los datos usando las columnas identificadas
            cursor.execute(f"SELECT {id_columna} as ID, {nombre_columna} as nombre FROM {tabla_grupos_encontrada} ORDER BY {nombre_columna}")
            grupos = cursor.fetchall()
            
            if not grupos:
                st.error("❌ No se encontraron grupos/reglamentos en la tabla.")
                return
                
            grupo_opciones = {f"{g['nombre']} (ID: {g['ID']})": g['ID'] for g in grupos}
            st.success(f"✅ Se cargaron {len(grupos)} grupos/reglamentos correctamente.")
            
        except Exception as e:
            st.error(f"❌ Error al cargar grupos: {e}")
            return

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
                    f"Nombre regla {fila['numero']}",
                    value=fila['nombre_regla'],
                    key=f"nombre_{i}",
                    placeholder="Ej: Puntualidad en reuniones"
                )
            
            with col2:
                descripcion = st.text_area(
                    f"Descripción {fila['numero']}",
                    value=fila['descripcion'],
                    key=f"desc_{i}",
                    placeholder="Describe la regla y a qué se refiere...",
                    height=60
                )
            
            with col3:
                monto_multa = st.number_input(
                    f"Monto Multa (USD) {fila['numero']}",
                    min_value=0.00,
                    value=float(fila['monto_multa']),
                    step=0.50,
                    format="%.2f",
                    key=f"monto_{i}"
                )
            
            with col4:
                estado = st.selectbox(
                    f"Estado {fila['numero']}",
                    options=[1, 2],
                    format_func=lambda x: "✅ Activo" if x == 1 else "❌ Inactivo",
                    index=0 if fila['estado'] == 1 else 1,
                    key=f"estado_{i}"
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
                
                # Verificar si existe la tabla para guardar reglamentos
                try:
                    cursor.execute("SHOW TABLES LIKE 'reglamentos'")
                    if not cursor.fetchone():
                        # Crear la tabla si no existe
                        st.info("🔄 Creando tabla 'reglamentos'...")
                        cursor.execute("""
                            CREATE TABLE reglamentos (
                                ID_Reglamento INT AUTO_INCREMENT PRIMARY KEY,
                                ID_Grupo INT NOT NULL,
                                nombre_regla VARCHAR(255) NOT NULL,
                                descripcion TEXT,
                                monto_multa DECIMAL(10,2),
                                tipo_sanción VARCHAR(50),
                                ID_Estado INT DEFAULT 1,
                                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        """)
                        st.success("✅ Tabla 'reglamentos' creada automáticamente")
                except Exception as e:
                    st.error(f"❌ Error al verificar/crear tabla: {e}")
                    return
                
                # Insertar cada regla en la base de datos
                reglas_guardadas = 0
                errores = []
                
                for fila in st.session_state.filas_reglamento:
                    # Solo guardar reglas que tengan nombre
                    if fila['nombre_regla'].strip():
                        try:
                            cursor.execute(
                                """INSERT INTO reglamentos 
                                   (ID_Grupo, nombre_regla, descripcion, monto_multa, tipo_sanción, ID_Estado) 
                                   VALUES (%s, %s, %s, %s, %s, %s)""",
                                (
                                    id_grupo,
                                    fila['nombre_regla'].strip(),
                                    fila['descripcion'].strip() if fila['descripcion'] else None,
                                    fila['monto_multa'],
                                    "Multa económica",  # tipo_sanción por defecto
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
