import streamlit as st
from modulos.config.conexion import obtener_conexion
from datetime import datetime

def mostrar_multas():
    st.header("📋 Sistema de Multas")

    # Verificar si hay una reunión seleccionada
    if 'reunion_actual' not in st.session_state:
        st.warning("⚠️ Primero debes seleccionar una reunión en el módulo de Asistencia.")
        return

    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)

        # Obtener la reunión del session_state
        reunion_info = st.session_state.reunion_actual
        id_reunion = reunion_info['id_reunion']
        id_grupo = reunion_info['id_grupo']
        nombre_reunion = reunion_info['nombre_reunion']

        # Mostrar información de la reunión actual
        st.info(f"📅 **Reunión actual:** {nombre_reunion}")

        # Obtener el monto de multa desde el reglamento
        cursor.execute("""
            SELECT monto_multa 
            FROM Reglamento 
            WHERE ID_Grupo = %s 
            ORDER BY ID_Reglamento DESC 
            LIMIT 1
        """, (id_grupo,))
        
        reglamento = cursor.fetchone()
        monto_multa = reglamento['monto_multa'] if reglamento and reglamento['monto_multa'] else 0

        st.success(f"💰 **Monto de multa establecido:** ${monto_multa:,.2f}")

        # Cargar TODOS los miembros del grupo y su estado de asistencia
        cursor.execute("""
            SELECT 
                m.ID_Miembro, 
                m.nombre,
                COALESCE(mr.asistio, 0) as asistio,
                COALESCE(mr.justificado, 0) as justificado
            FROM Miembro m
            LEFT JOIN Miembroxreunion mr ON m.ID_Miembro = mr.ID_Miembro AND mr.ID_Reunion = %s
            WHERE m.ID_Grupo = %s
            ORDER BY m.nombre
        """, (id_reunion, id_grupo))
        
        todos_miembros = cursor.fetchall()

        if not todos_miembros:
            st.warning("⚠️ No hay miembros registrados en este grupo.")
            return

        # Separar miembros por estado de asistencia
        miembros_presentes = [m for m in todos_miembros if m['asistio'] == 1]
        miembros_ausentes = [m for m in todos_miembros if m['asistio'] == 0]
        miembros_justificados = [m for m in todos_miembros if m['justificado'] == 1]

        # Mostrar resumen de asistencia
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("✅ Presentes", len(miembros_presentes))
        with col2:
            st.metric("❌ Ausentes", len(miembros_ausentes))
        with col3:
            st.metric("📝 Justificados", len(miembros_justificados))

        # Verificar si ya existen multas para esta reunión
        cursor.execute("""
            SELECT COUNT(*) as total_multas 
            FROM Multa 
            WHERE ID_Reunion = %s
        """, (id_reunion,))
        
        total_multas_existentes = cursor.fetchone()['total_multas']

        # FORMULARIO DE MULTAS
        st.subheader("📊 Formulario de Multas")

        with st.form("form_multas"):
            st.write("### Registrar Multas para Ausentes")

            if miembros_ausentes:
                st.write(f"**Miembros ausentes ({len(miembros_ausentes)}):**")
                
                # Crear tabla similar al formulario proporcionado
                col1, col2, col3 = st.columns([3, 2, 2])
                with col1:
                    st.write("**Miembro**")
                with col2:
                    st.write("**A Pagar**")
                with col3:
                    st.write("**Pagada**")

                multas_a_registrar = []

                for miembro in miembros_ausentes:
                    col1, col2, col3 = st.columns([3, 2, 2])
                    
                    with col1:
                        st.write(f"{miembro['nombre']}")
                    
                    with col2:
                        st.write(f"${monto_multa:,.2f}")
                    
                    with col3:
                        # Solo mostrar checkbox si no hay multa registrada
                        cursor.execute("""
                            SELECT ID_Multa, ID_Estado_multa 
                            FROM Multa 
                            WHERE ID_Reunion = %s AND ID_Miembro = %s
                        """, (id_reunion, miembro['ID_Miembro']))
                        
                        multa_existente = cursor.fetchone()
                        
                        if multa_existente:
                            estado_pagada = (multa_existente['ID_Estado_multa'] == 2)  # Suponiendo que 2 = Pagada
                            checkbox = st.checkbox(
                                f"Pagada_{miembro['ID_Miembro']}", 
                                value=estado_pagada,
                                disabled=True  # No editable desde aquí
                            )
                            st.caption("✅ Multa ya registrada")
                        else:
                            checkbox = st.checkbox(f"Pagada_{miembro['ID_Miembro']}", value=False)
                    
                    multas_a_registrar.append({
                        'ID_Miembro': miembro['ID_Miembro'],
                        'nombre': miembro['nombre'],
                        'monto': monto_multa,
                        'pagada': checkbox,
                        'ya_registrada': multa_existente is not None
                    })

            else:
                st.success("🎉 No hay miembros ausentes en esta reunión.")
                multas_a_registrar = []

            enviar = st.form_submit_button("💾 Guardar Multas")

            if enviar:
                if not miembros_ausentes:
                    st.info("No hay multas para registrar.")
                else:
                    try:
                        multas_registradas = 0
                        multas_actualizadas = 0

                        for multa in multas_a_registrar:
                            if not multa['ya_registrada'] and multa['pagada']:
                                # Insertar nueva multa como pagada
                                cursor.execute("""
                                    INSERT INTO Multa 
                                    (ID_Reunion, ID_Miembro, ID_Reglamento, fecha, ID_Estado_multa) 
                                    VALUES (%s, %s, %s, %s, %s)
                                """, (id_reunion, multa['ID_Miembro'], reglamento['ID_Reglamento'], 
                                      datetime.now().date(), 2))  # 2 = Pagada
                                multas_registradas += 1
                            
                            elif not multa['ya_registrada'] and not multa['pagada']:
                                # Insertar nueva multa como pendiente
                                cursor.execute("""
                                    INSERT INTO Multa 
                                    (ID_Reunion, ID_Miembro, ID_Reglamento, fecha, ID_Estado_multa) 
                                    VALUES (%s, %s, %s, %s, %s)
                                """, (id_reunion, multa['ID_Miembro'], reglamento['ID_Reglamento'], 
                                      datetime.now().date(), 1))  # 1 = Pendiente
                                multas_registradas += 1

                        con.commit()

                        if multas_registradas > 0:
                            st.success(f"✅ Se registraron {multas_registradas} multas correctamente.")
                        
                        if multas_actualizadas > 0:
                            st.success(f"🔄 Se actualizaron {multas_actualizadas} multas.")

                        st.rerun()

                    except Exception as e:
                        con.rollback()
                        st.error(f"❌ Error al registrar las multas: {e}")

        # SECCIÓN: CONSULTA Y GESTIÓN DE MULTAS EXISTENTES
        st.subheader("📋 Multas Registradas")

        # Obtener multas de esta reunión
        cursor.execute("""
            SELECT 
                m.ID_Multa,
                mb.nombre as nombre_miembro,
                mu.fecha,
                em.estado_multa,
                mu.ID_Estado_multa,
                r.monto_multa
            FROM Multa mu
            JOIN Miembro mb ON mu.ID_Miembro = mb.ID_Miembro
            JOIN Estado_multa em ON mu.ID_Estado_multa = em.ID_Estado_multa
            JOIN Reglamento r ON mu.ID_Reglamento = r.ID_Reglamento
            WHERE mu.ID_Reunion = %s
            ORDER BY em.estado_multa, mb.nombre
        """, (id_reunion,))
        
        multas_existentes = cursor.fetchall()

        if multas_existentes:
            # Mostrar resumen
            multas_pagadas = [m for m in multas_existentes if m['ID_Estado_multa'] == 2]
            multas_pendientes = [m for m in multas_existentes if m['ID_Estado_multa'] == 1]

            col1, col2 = st.columns(2)
            with col1:
                st.metric("💰 Total Multas", len(multas_existentes))
            with col2:
                st.metric("✅ Multas Pagadas", len(multas_pagadas))

            # Tabla de multas
            st.write("**Detalle de multas:**")
            for multa in multas_existentes:
                col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 2])
                
                with col1:
                    st.write(f"**{multa['nombre_miembro']}**")
                
                with col2:
                    st.write(f"${multa['monto_multa']:,.2f}")
                
                with col3:
                    estado_color = "✅" if multa['ID_Estado_multa'] == 2 else "❌"
                    st.write(f"{estado_color} {multa['estado_multa']}")
                
                with col4:
                    st.write(f"{multa['fecha']}")
                
                with col5:
                    # Botón para cambiar estado de pago
                    if multa['ID_Estado_multa'] == 1:  # Pendiente
                        if st.button(f"✅ Pagar", key=f"pagar_{multa['ID_Multa']}"):
                            try:
                                cursor.execute("""
                                    UPDATE Multa 
                                    SET ID_Estado_multa = 2 
                                    WHERE ID_Multa = %s
                                """, (multa['ID_Multa'],))
                                con.commit()
                                st.success(f"✅ Multa de {multa['nombre_miembro']} marcada como pagada.")
                                st.rerun()
                            except Exception as e:
                                con.rollback()
                                st.error(f"❌ Error al actualizar: {e}")
                    
                    else:  # Pagada
                        if st.button(f"↩️ Revertir", key=f"revertir_{multa['ID_Multa']}"):
                            try:
                                cursor.execute("""
                                    UPDATE Multa 
                                    SET ID_Estado_multa = 1 
                                    WHERE ID_Multa = %s
                                """, (multa['ID_Multa'],))
                                con.commit()
                                st.warning(f"↩️ Multa de {multa['nombre_miembro']} revertida a pendiente.")
                                st.rerun()
                            except Exception as e:
                                con.rollback()
                                st.error(f"❌ Error al actualizar: {e}")

        else:
            st.info("📝 No hay multas registradas para esta reunión.")

    except Exception as e:
        st.error(f"❌ Error general: {e}")

    finally:
        if "cursor" in locals():
            cursor.close()
        if "con" in locals():
            con.close()
