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

        # -----------------------------
        # CARGAR REGLAMENTOS DEL GRUPO (MULTAS DISPONIBLES)
        # -----------------------------
        cursor.execute("""
            SELECT ID_Reglamento, descripcion, monto 
            FROM Reglamento 
            WHERE ID_Grupo = %s AND activo = 1
            ORDER BY monto DESC
        """, (id_grupo,))
        
        reglamentos = cursor.fetchall()

        if not reglamentos:
            st.warning("⚠️ No hay multas configuradas en el reglamento de este grupo.")
            st.info("Por favor, configura las multas en el módulo de Reglamento primero.")
            return

        # Crear diccionario de reglamentos para fácil acceso
        reglamentos_dict = {reg[0]: {"descripcion": reg[1], "monto": reg[2]} for reg in reglamentos}

        # -----------------------------
        # CARGAR MULTAS EXISTENTES PARA ESTA REUNIÓN
        # -----------------------------
        cursor.execute("""
            SELECT ID_Multa, ID_Miembro, ID_Reglamento, fecha, ID_Estado_multa
            FROM multas 
            WHERE ID_Reunion = %s
        """, (id_reunion,))
        
        multas_existentes = cursor.fetchall()

        # Crear diccionario de multas existentes por miembro
        multas_por_miembro = {}
        for multa in multas_existentes:
            id_multa, id_miembro, id_reglamento, fecha_multa, id_estado = multa
            multas_por_miembro[id_miembro] = {
                "id_multa": id_multa,
                "id_reglamento": id_reglamento,
                "monto": reglamentos_dict.get(id_reglamento, {}).get("monto", 0),
                "estado": id_estado
            }

        # -------------------------------------
        # FORMULARIO DE MULTAS
        # -------------------------------------
        with st.form("form_multas"):
            st.subheader("📝 Registro de Multas")
            
            # Mostrar fecha para las multas
            fecha_multa = st.date_input(
                "Fecha de la multa:",
                value=date.today()
            )

            # SELECTOR DE REGLAMENTO (MULTA A APLICAR)
            st.markdown("### 🔨 Seleccionar Tipo de Multa")
            
            # Crear opciones para el selectbox
            opciones_reglamento = [
                f"${reg[2]} - {reg[1]}" for reg in reglamentos
            ]
            ids_reglamento = [reg[0] for reg in reglamentos]
            
            # Selector de multa a aplicar
            multa_seleccionada = st.selectbox(
                "Selecciona la multa a aplicar:",
                options=range(len(opciones_reglamento)),
                format_func=lambda x: opciones_reglamento[x],
                key="selector_multa"
            )
            
            id_reglamento_seleccionado = ids_reglamento[multa_seleccionada]
            monto_multa = reglamentos_dict[id_reglamento_seleccionado]["monto"]
            descripcion_multa = reglamentos_dict[id_reglamento_seleccionado]["descripcion"]
            
            st.info(f"**Multa seleccionada:** {descripcion_multa} - **Monto:** ${monto_multa:,.2f}")

            # TABLA DE MULTAS
            st.markdown("---")
            st.markdown("### 👥 Lista de Miembros para Multar")
            
            # ENCABEZADO DE LA TABLA
            cols_titulos = st.columns([1, 2, 1, 1, 1])
            with cols_titulos[0]:
                st.markdown("**Multar**")
            with cols_titulos[1]:
                st.markdown("**Socios/as**")
            with cols_titulos[2]:
                st.markdown("**Estado actual**")
            with cols_titulos[3]:
                st.markdown("**A pagar**")
            with cols_titulos[4]:
                st.markdown("**Pagada**")

            # Diccionarios para almacenar los datos
            miembros_a_multar = {}
            estados_actuales = {}

            # FILAS PARA CADA MIEMBRO
            for id_miembro, nombre_miembro in miembros_presentes:
                cols = st.columns([1, 2, 1, 1, 1])
                
                with cols[0]:
                    # Checkbox para multar - ya seleccionado si tiene multa existente
                    tiene_multa_actual = id_miembro in multas_por_miembro
                    multar = st.checkbox(
                        "Seleccionar",
                        value=tiene_multa_actual,
                        key=f"multar_{id_miembro}",
                        label_visibility="collapsed"
                    )
                    miembros_a_multar[id_miembro] = multar
                
                with cols[1]:
                    # Mostrar nombre del miembro
                    st.write(f"**{nombre_miembro}**")
                
                with cols[2]:
                    # Mostrar estado actual de la multa
                    if tiene_multa_actual:
                        estado_actual = multas_por_miembro[id_miembro]["estado"]
                        estado_texto = "Pendiente" if estado_actual == 1 else "Pagada" if estado_actual == 2 else "Cancelada"
                        color = "🔴" if estado_actual == 1 else "🟢" if estado_actual == 2 else "🟡"
                        st.write(f"{color} {estado_texto}")
                    else:
                        st.write("🟢 Sin multa")
                    estados_actuales[id_miembro] = multas_por_miembro[id_miembro]["estado"] if tiene_multa_actual else 0
                
                with cols[3]:
                    # Mostrar monto a pagar (solo si está seleccionado para multar)
                    if multar:
                        st.write(f"**${monto_multa:,.2f}**")
                    else:
                        st.write("$0.00")
                
                with cols[4]:
                    # Mostrar estado de pago (se actualiza automáticamente)
                    if tiene_multa_actual:
                        estado_actual = multas_por_miembro[id_miembro]["estado"]
                        if estado_actual == 2:  # Pagada
                            st.success("✅ Pagada")
                        elif estado_actual == 1:  # Pendiente
                            st.error("❌ Pendiente")
                        else:  # Cancelada u otro
                            st.warning("⚠️ Cancelada")
                    else:
                        st.info("---")

                # Línea separadora entre miembros
                st.markdown("---")

            # Botón de envío
            enviar = st.form_submit_button("💾 Guardar Multas")

            if enviar:
                try:
                    registros_guardados = 0
                    registros_actualizados = 0
                    
                    for id_miembro, nombre_miembro in miembros_presentes:
                        multar = miembros_a_multar.get(id_miembro, False)
                        tiene_multa_actual = id_miembro in multas_por_miembro
                        
                        if multar:
                            # Si el miembro debe tener multa
                            if not tiene_multa_actual:
                                # INSERTAR NUEVA MULTA
                                cursor.execute("""
                                    INSERT INTO multas (
                                        ID_Reunion, ID_Reglamento, fecha, ID_Estado_multa
                                    ) VALUES (%s, %s, %s, %s)
                                """, (id_reunion, id_reglamento_seleccionado, fecha_multa, 1))  # 1 = Pendiente
                                
                                registros_guardados += 1
                                st.success(f"✅ Multa asignada a {nombre_miembro}: ${monto_multa:,.2f}")
                                
                            else:
                                # VERIFICAR SI HAY CAMBIOS EN LA MULTA EXISTENTE
                                multa_actual = multas_por_miembro[id_miembro]
                                if (multa_actual["id_reglamento"] != id_reglamento_seleccionado or 
                                    multa_actual["estado"] != 1):  # Si cambió el reglamento o el estado no es pendiente
                                    
                                    cursor.execute("""
                                        UPDATE multas 
                                        SET ID_Reglamento = %s, fecha = %s, ID_Estado_multa = 1
                                        WHERE ID_Multa = %s
                                    """, (id_reglamento_seleccionado, fecha_multa, multa_actual["id_multa"]))
                                    
                                    registros_actualizados += 1
                                    st.success(f"✅ Multa actualizada para {nombre_miembro}")
                        
                        else:
                            # Si el miembro NO debe tener multa pero tiene una existente
                            if tiene_multa_actual:
                                # ELIMINAR MULTA EXISTENTE (o cambiar estado a cancelado)
                                cursor.execute("""
                                    DELETE FROM multas 
                                    WHERE ID_Multa = %s
                                """, (multas_por_miembro[id_miembro]["id_multa"],))
                                
                                st.info(f"🗑️ Multa eliminada para {nombre_miembro}")

                    con.commit()
                    
                    if registros_guardados > 0 or registros_actualizados > 0:
                        st.success(f"✅ Operación completada: {registros_guardados} nuevas multas, {registros_actualizados} actualizadas")
                    else:
                        st.info("ℹ️ No se realizaron cambios en las multas.")
                    
                    st.rerun()

                except Exception as e:
                    con.rollback()
                    st.error(f"❌ Error al registrar las multas: {e}")

        # -------------------------------------
        # RESUMEN DE MULTAS ACTUALES
        # -------------------------------------
        st.markdown("---")
        st.subheader("📋 Resumen de Multas Actuales")
        
        cursor.execute("""
            SELECT 
                m.ID_Multa,
                mb.nombre as miembro,
                r.descripcion as infraccion,
                r.monto,
                mult.fecha,
                CASE 
                    WHEN mult.ID_Estado_multa = 1 THEN 'Pendiente'
                    WHEN mult.ID_Estado_multa = 2 THEN 'Pagada' 
                    ELSE 'Cancelada'
                END as estado
            FROM multas mult
            JOIN Miembro mb ON mult.ID_Miembro = mb.ID_Miembro
            JOIN Reglamento r ON mult.ID_Reglamento = r.ID_Reglamento
            WHERE mult.ID_Reunion = %s
            ORDER BY mult.ID_Estado_multa, mb.nombre
        """, (id_reunion,))
        
        multas_actuales = cursor.fetchall()
        
        if multas_actuales:
            df = pd.DataFrame(multas_actuales, columns=[
                "ID", "Miembro", "Infracción", "Monto", "Fecha", "Estado"
            ])
            
            # Formatear columna de monto
            df["Monto"] = df["Monto"].apply(lambda x: f"${x:,.2f}")
            
            # Contar totales
            total_multas = len(df)
            total_pendientes = len(df[df["Estado"] == "Pendiente"])
            total_pagadas = len(df[df["Estado"] == "Pagada"])
            monto_total = sum([float(m[3]) for m in multas_actuales])
            monto_pendiente = sum([float(m[3]) for m in multas_actuales if m[5] == "Pendiente"])
            
            # Mostrar métricas
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Multas", total_multas)
            with col2:
                st.metric("Pendientes", total_pendientes)
            with col3:
                st.metric("Pagadas", total_pagadas)
            with col4:
                st.metric("Monto Pendiente", f"${monto_pendiente:,.2f}")
            
            st.dataframe(df.drop("ID", axis=1), use_container_width=True)
            
        else:
            st.info("📝 No hay multas registradas para esta reunión.")

    except Exception as e:
        st.error(f"❌ Error general: {e}")

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'con' in locals():
            con.close()
