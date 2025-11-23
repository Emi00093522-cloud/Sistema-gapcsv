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
        # CARGAR EL REGLAMENTO DEL GRUPO PARA OBTENER EL MONTO DE MULTA
        # -----------------------------
        cursor.execute("""
            SELECT ID_Reglamento, monto_multa_asistencia 
            FROM Reglamento 
            WHERE ID_Grupo = %s AND ID_Estado = 1
            LIMIT 1
        """, (id_grupo,))
        
        resultado_reglamento = cursor.fetchone()

        if not resultado_reglamento:
            st.warning("⚠️ No hay reglamento configurado para este grupo.")
            st.info("Por favor, configura el reglamento primero.")
            return

        id_reglamento_grupo = resultado_reglamento[0]
        monto_multa = float(resultado_reglamento[1]) if resultado_reglamento[1] else 0.0

        if monto_multa <= 0:
            st.warning("⚠️ El monto de multa en el reglamento es $0. No se pueden asignar multas.")
            st.info("Por favor, configura un monto de multa mayor a 0 en el reglamento.")
            return

        # -----------------------------
        # CARGAR MULTAS EXISTENTES PARA ESTA REUNIÓN
        # -----------------------------
        cursor.execute("""
            SELECT ID_Multa, ID_Reunion, ID_Miembro, ID_Estado_multa
            FROM multa 
            WHERE ID_Reunion = %s
        """, (id_reunion,))
        
        multas_existentes = cursor.fetchall()

        # Crear diccionario de multas existentes por miembro
        multas_por_miembro = {}
        for multa in multas_existentes:
            id_multa, id_reunion_multa, id_miembro, id_estado = multa
            multas_por_miembro[id_miembro] = {
                "id_multa": id_multa,
                "id_reglamento": id_reglamento_grupo,  # Usamos el mismo reglamento para todos
                "monto": monto_multa,
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

            # INFORMACIÓN DE LA MULTA
            st.markdown("### 🔨 Información de la Multa")
            st.info(f"**Tipo de multa:** Multa por infracción - **Monto:** ${monto_multa:,.2f}")

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

            # Campo para justificación/observaciones
            observaciones = st.text_area(
                "Observaciones o justificación de las multas:",
                placeholder="Ej: Multas por llegar tarde, no cumplir con tareas asignadas..."
            )

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
                                # INSERTAR NUEVA MULTA (asumiendo que las columnas son: ID_Multa, ID_Reunion, ID_Miembro, ID_Estado_multa)
                                cursor.execute("""
                                    INSERT INTO multa (
                                        ID_Reunion, ID_Miembro, ID_Estado_multa
                                    ) VALUES (%s, %s, %s)
                                """, (id_reunion, id_miembro, 1))  # 1 = Pendiente
                                
                                registros_guardados += 1
                                st.success(f"✅ Multa asignada a {nombre_miembro}: ${monto_multa:,.2f}")
                                
                            else:
                                # VERIFICAR SI HAY CAMBIOS EN LA MULTA EXISTENTE
                                multa_actual = multas_por_miembro[id_miembro]
                                if multa_actual["estado"] != 1:  # Si el estado no es pendiente
                                    
                                    cursor.execute("""
                                        UPDATE multa 
                                        SET ID_Estado_multa = 1
                                        WHERE ID_Multa = %s
                                    """, (multa_actual["id_multa"],))
                                    
                                    registros_actualizados += 1
                                    st.success(f"✅ Multa reactivada para {nombre_miembro}")
                        
                        else:
                            # Si el miembro NO debe tener multa pero tiene una existente
                            if tiene_multa_actual:
                                # ELIMINAR MULTA EXISTENTE
                                cursor.execute("""
                                    DELETE FROM multa 
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
                mult.ID_Multa,
                mb.nombre as miembro,
                'Multa por infracción' as infraccion,
                %s as monto,
                'Fecha no disponible' as fecha,
                CASE 
                    WHEN mult.ID_Estado_multa = 1 THEN 'Pendiente'
                    WHEN mult.ID_Estado_multa = 2 THEN 'Pagada' 
                    ELSE 'Cancelada'
                END as estado
            FROM multa mult
            JOIN Miembro mb ON mult.ID_Miembro = mb.ID_Miembro
            WHERE mult.ID_Reunion = %s
            ORDER BY mult.ID_Estado_multa, mb.nombre
        """, (monto_multa, id_reunion))
        
        multas_actuales = cursor.fetchall()
        
        if multas_actuales:
            df = pd.DataFrame(multas_actuales, columns=[
                "ID", "Miembro", "Infracción", "Monto", "Fecha", "Estado"
            ])
            
            # Formatear columna de monto
            df["Monto"] = df["Monto"].apply(lambda x: f"${float(x):,.2f}" if x else "$0.00")
            
            # Contar totales
            total_multas = len(df)
            total_pendientes = len(df[df["Estado"] == "Pendiente"])
            total_pagadas = len(df[df["Estado"] == "Pagada"])
            
            # Calcular montos
            monto_pendiente = sum([float(monto_multa) for _ in multas_actuales if _[5] == "Pendiente"])
            monto_total = sum([float(monto_multa) for _ in multas_actuales])
            
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
