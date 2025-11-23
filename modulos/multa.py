import streamlit as st
import pandas as pd
from modulos.config.conexion import obtener_conexion
from datetime import date

def mostrar_multas():
    st.header("⚖️ Control de Multas")

    # Verificar si hay una reunión seleccionada
    if 'reunion_actual' not in st.session_state:
        st.warning("⚠️ Primero debes seleccionar una reunión en el módulo de Asistencia.")
        return

    try:
        con = obtener_conexion()
        cursor = con.cursor()

        # Obtener la reunión del session_state
        reunion_info = st.session_state.reunion_actual
        id_reunion = reunion_info['id_reunion']
        id_grupo = reunion_info['id_grupo']
        nombre_reunion = reunion_info['nombre_reunion']

        # Mostrar información de la reunión actual
        st.info(f"📅 **Reunión actual:** {nombre_reunion}")

        # -----------------------------
        # OBTENER REGLAMENTOS DEL GRUPO (TIPOS DE MULTA)
        # -----------------------------
        cursor.execute("""
            SELECT ID_Reglamento, descripcion, monto 
            FROM Reglamento 
            WHERE ID_Grupo = %s AND activo = 1
            ORDER BY descripcion
        """, (id_grupo,))
        
        reglamentos = cursor.fetchall()
        
        if not reglamentos:
            st.warning("⚠️ No hay reglamentos configurados para este grupo.")
            st.info("Por favor, configura los reglamentos y multas primero.")
            return

        # Crear diccionario de reglamentos
        dict_reglamentos = {reg[0]: f"{reg[1]} - ${reg[2]:,.2f}" for reg in reglamentos}
        dict_montos = {reg[0]: reg[2] for reg in reglamentos}

        # -----------------------------
        # CARGAR MIEMBROS QUE ASISTIERON A ESTA REUNIÓN
        # -----------------------------
        cursor.execute("""
            SELECT m.ID_Miembro, m.nombre 
            FROM Miembro m
            JOIN Miembroxreunion mr ON m.ID_Miembro = mr.ID_Miembro
            WHERE mr.ID_Reunion = %s AND mr.asistio = 1
            ORDER BY m.nombre
        """, (id_reunion,))
        
        miembros_presentes = cursor.fetchall()

        if not miembros_presentes:
            st.warning(f"⚠️ No hay miembros registrados como presentes en esta reunión.")
            st.info("Por favor, registra la asistencia primero en el módulo correspondiente.")
            return

        # -------------------------------------
        # FORMULARIO DE MULTAS
        # -------------------------------------
        with st.form("form_multas"):
            st.subheader("📝 Registro de Multas")
            
            # Mostrar fecha de la reunión
            fecha_multa = st.date_input(
                "Fecha de la multa:",
                value=date.today()
            )

            # TABLA DE MULTAS CON FORMATO ESPECÍFICO
            st.markdown("---")
            st.markdown("### ⚖️ Control de Multas")
            
            # ENCABEZADO DE LA TABLA
            cols_titulos = st.columns([2, 2, 1, 1, 1])
            with cols_titulos[0]:
                st.markdown("**Socios/as**")
            with cols_titulos[1]:
                st.markdown("**Tipo de Multa**")
            with cols_titulos[2]:
                st.markdown("**Monto**")
            with cols_titulos[3]:
                st.markdown("**A pagar**")
            with cols_titulos[4]:
                st.markdown("**Pagada**")

            # Diccionarios para almacenar los datos de cada miembro
            multas_data = {}
            pagos_data = {}
            estados_data = {}

            # FILAS PARA CADA MIEMBRO
            for id_miembro, nombre_miembro in miembros_presentes:
                cols = st.columns([2, 2, 1, 1, 1])
                
                with cols[0]:
                    # Mostrar nombre del miembro
                    st.write(f"**{nombre_miembro}**")
                
                with cols[1]:
                    # Selectbox para tipo de multa
                    opciones_multas = ["Sin multa"] + list(dict_reglamentos.values())
                    multa_seleccionada = st.selectbox(
                        "Tipo de multa",
                        options=opciones_multas,
                        key=f"multa_{id_miembro}",
                        label_visibility="collapsed"
                    )
                    
                    # Encontrar el ID_Reglamento seleccionado
                    id_reglamento_seleccionado = None
                    monto_multas = 0.00
                    
                    if multa_seleccionada != "Sin multa":
                        for id_reglamento, descripcion in dict_reglamentos.items():
                            if descripcion == multa_seleccionada:
                                id_reglamento_seleccionado = id_reglamento
                                monto_multas = dict_montos[id_reglamento]
                                break
                
                with cols[2]:
                    # Mostrar monto automáticamente basado en el reglamento
                    if multa_seleccionada != "Sin multa":
                        st.write(f"**${monto_multas:,.2f}**")
                    else:
                        st.write("**$0.00**")
                
                with cols[3]:
                    # Mostrar monto a pagar (igual al monto de la multa)
                    if multa_seleccionada != "Sin multa":
                        st.write(f"**${monto_multas:,.2f}**")
                    else:
                        st.write("**$0.00**")
                
                with cols[4]:
                    # Checkbox para indicar si la multa está pagada
                    if multa_seleccionada != "Sin multa":
                        pagada = st.checkbox(
                            "Pagada",
                            key=f"pagada_{id_miembro}",
                            value=False
                        )
                        estado_multas = 2 if pagada else 1  # 2 = Pagada, 1 = Pendiente
                    else:
                        pagada = False
                        estado_multas = None  # Sin multa
                    
                    if multa_seleccionada != "Sin multa":
                        if pagada:
                            st.success("✅")
                        else:
                            st.warning("⏳")
                    else:
                        st.info("➖")
                
                # Guardar datos en diccionarios
                multas_data[id_miembro] = {
                    'id_reglamento': id_reglamento_seleccionado,
                    'monto': monto_multas,
                    'tiene_multa': multa_seleccionada != "Sin multa"
                }
                estados_data[id_miembro] = estado_multas
                
                # Línea separadora entre miembros
                st.markdown("---")

            # Botón de envío FUERA de las columnas
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                enviar = st.form_submit_button("💾 Guardar Multas")

            if enviar:
                try:
                    registros_guardados = 0
                    total_multas_pagadas = 0.00
                    
                    for id_miembro, nombre_miembro in miembros_presentes:
                        datos_multa = multas_data.get(id_miembro, {})
                        estado_multas = estados_data.get(id_miembro)
                        
                        id_reglamento = datos_multa.get('id_reglamento')
                        monto = datos_multa.get('monto', 0)
                        tiene_multa = datos_multa.get('tiene_multa', False)
                        
                        # Solo procesar si tiene multa asignada
                        if tiene_multa and id_reglamento is not None:
                            # Verificar si ya existe un registro para este miembro en esta reunión
                            cursor.execute("""
                                SELECT ID_Multa, ID_Estado_multa 
                                FROM Multa 
                                WHERE ID_Miembro = %s AND ID_Reunion = %s AND ID_Reglamento = %s
                            """, (id_miembro, id_reunion, id_reglamento))
                            
                            registro_existente = cursor.fetchone()
                            
                            if not registro_existente:
                                # Insertar nueva multa
                                cursor.execute("""
                                    INSERT INTO Multa (
                                        ID_Miembro, ID_Reunion, ID_Reglamento, fecha, ID_Estado_multa
                                    ) VALUES (%s, %s, %s, %s, %s)
                                """, (id_miembro, id_reunion, id_reglamento, fecha_multa, estado_multas))
                                registros_guardados += 1
                                st.success(f"✅ {nombre_miembro}: Multa registrada - ${monto:,.2f}")
                            else:
                                # Actualizar multa existente
                                id_multa_existente = registro_existente[0]
                                cursor.execute("""
                                    UPDATE Multa 
                                    SET ID_Estado_multa = %s, fecha = %s
                                    WHERE ID_Multa = %s
                                """, (estado_multas, fecha_multa, id_multa_existente))
                                registros_guardados += 1
                                st.success(f"✅ {nombre_miembro}: Multa actualizada - ${monto:,.2f}")
                            
                            # Sumar al total si está pagada
                            if estado_multas == 2:  # Pagada
                                total_multas_pagadas += monto
                        else:
                            # Si no tiene multa, eliminar cualquier registro existente para este miembro y reunión
                            cursor.execute("""
                                DELETE FROM Multa 
                                WHERE ID_Miembro = %s AND ID_Reunion = %s
                            """, (id_miembro, id_reunion))
                            if cursor.rowcount > 0:
                                st.info(f"ℹ️ {nombre_miembro}: Multa cancelada/eliminada")

                    con.commit()
                    
                    if registros_guardados > 0:
                        st.success(f"✅ Se procesaron {registros_guardados} registros de multas correctamente.")
                        
                        # Mostrar total de multas pagadas
                        if total_multas_pagadas > 0:
                            st.metric(
                                label="💰 TOTAL MULTAS PAGADAS",
                                value=f"${total_multas_pagadas:,.2f}",
                                delta=None
                            )
                    else:
                        st.info("ℹ️ No se realizaron cambios en los registros de multas.")
                    
                    st.rerun()

                except Exception as e:
                    con.rollback()
                    st.error(f"❌ Error al registrar las multas: {e}")

        # -------------------------------------
        # HISTORIAL DE MULTAS REGISTRADAS
        # -------------------------------------
        st.markdown("---")
        st.subheader("📋 Historial de Multas")
        
        cursor.execute("""
            SELECT 
                mu.ID_Multa,
                m.nombre as socio,
                rgl.descripcion as tipo_multa,
                rgl.monto,
                mu.fecha,
                CASE 
                    WHEN em.ID_Estado_multa = 1 THEN 'Pendiente'
                    WHEN em.ID_Estado_multa = 2 THEN 'Pagada'
                    WHEN em.ID_Estado_multa = 3 THEN 'Cancelada'
                    ELSE 'Desconocido'
                END as estado,
                reu.fecha as fecha_reunion
            FROM Multa mu
            JOIN Miembro m ON mu.ID_Miembro = m.ID_Miembro
            JOIN Reglamento rgl ON mu.ID_Reglamento = rgl.ID_Reglamento
            JOIN Reunion reu ON mu.ID_Reunion = reu.ID_Reunion
            LEFT JOIN Estado_multa em ON mu.ID_Estado_multa = em.ID_Estado_multa
            WHERE mu.ID_Reunion = %s
            ORDER BY m.nombre, mu.fecha
        """, (id_reunion,))
        
        historial = cursor.fetchall()
        
        if historial:
            df = pd.DataFrame(historial, columns=[
                "ID", "Socio", "Tipo de Multa", "Monto", "Fecha Multa", "Estado", "Fecha Reunión"
            ])
            
            # Formatear columna de monto
            df["Monto"] = df["Monto"].apply(lambda x: f"${x:,.2f}")
            
            # Calcular total de multas pagadas
            cursor.execute("""
                SELECT COALESCE(SUM(rgl.monto), 0) as total_pagadas
                FROM Multa mu
                JOIN Reglamento rgl ON mu.ID_Reglamento = rgl.ID_Reglamento
                WHERE mu.ID_Reunion = %s AND mu.ID_Estado_multa = 2
            """, (id_reunion,))
            
            total_pagadas = cursor.fetchone()[0]
            
            st.dataframe(df.drop("ID", axis=1), use_container_width=True)
            
            # Mostrar total de multas pagadas
            st.markdown("---")
            col1, col2 = st.columns([2, 1])
            with col2:
                st.metric(
                    label="**TOTAL MULTAS PAGADAS**",
                    value=f"${total_pagadas:,.2f}",
                    delta=None
                )
            
        else:
            st.info("📝 No hay registros de multas para esta reunión.")

    except Exception as e:
        st.error(f"❌ Error general: {e}")

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'con' in locals():
            con.close()
