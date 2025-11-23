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
            SELECT ID_Reglamento, monto_multa_asistencia
            FROM Reglamento 
            WHERE ID_Grupo = %s 
            ORDER BY ID_Reglamento DESC 
            LIMIT 1
        """, (id_grupo,))
        
        reglamento = cursor.fetchone()
        
        if reglamento and reglamento['monto_multa_asistencia'] is not None:
            monto_multa = float(reglamento['monto_multa_asistencia'])
            id_reglamento = reglamento['ID_Reglamento']
        else:
            # Si no hay monto definido, usar valor por defecto
            monto_multa = 10.00
            st.warning("⚠️ No se encontró monto de multa definido en el reglamento. Usando valor por defecto.")
            
            # Buscar si existe algún reglamento para el grupo
            cursor.execute("SELECT ID_Reglamento FROM Reglamento WHERE ID_Grupo = %s LIMIT 1", (id_grupo,))
            reglamento_existente = cursor.fetchone()
            
            if reglamento_existente:
                id_reglamento = reglamento_existente['ID_Reglamento']
            else:
                # Crear un reglamento básico si no existe
                cursor.execute("""
                    INSERT INTO Reglamento (ID_Grupo, monto_multa_asistencia, fecha_creacion)
                    VALUES (%s, %s, %s)
                """, (id_grupo, monto_multa, datetime.now().date()))
                con.commit()
                
                cursor.execute("SELECT LAST_INSERT_ID() as ID_Reglamento")
                id_reglamento = cursor.fetchone()['ID_Reglamento']

        st.success(f"💰 **Monto de multa por inasistencia:** ${monto_multa:,.2f}")

        # Cargar TODOS los miembros del grupo y su estado de asistencia - CORREGIDO
        cursor.execute("""
            SELECT 
                m.ID_Miembro, 
                CONCAT(m.nombre, ' ', m.apellido) as nombre_completo,
                COALESCE(mr.asistio, 0) as asistio,
                mr.justificacion
            FROM Miembro m
            LEFT JOIN Miembroxreunion mr ON m.ID_Miembro = mr.ID_Miembro AND mr.ID_Reunion = %s
            WHERE m.ID_Grupo = %s
            ORDER BY m.nombre, m.apellido
        """, (id_reunion, id_grupo))
        
        todos_miembros = cursor.fetchall()

        if not todos_miembros:
            st.warning("⚠️ No hay miembros registrados en este grupo.")
            return

        # Separar miembros por estado de asistencia
        miembros_presentes = [m for m in todos_miembros if m['asistio'] == 1]
        miembros_ausentes = [m for m in todos_miembros if m['asistio'] == 0]

        # Mostrar resumen de asistencia
        col1, col2 = st.columns(2)
        with col1:
            st.metric("✅ Presentes", len(miembros_presentes))
        with col2:
            st.metric("❌ Ausentes", len(miembros_ausentes))

        # FORMULARIO DE MULTAS - Estilo similar a tu imagen
        st.subheader("📊 Formulario de Multas")

        # Crear tabla estilo formulario
        st.write("### Registro de Multas por Inasistencia")

        # Encabezado de la tabla
        cols = st.columns([3, 2, 2, 2])
        headers = ["Socio", "A pagar", "Pagada", "Justificación"]
        for i, header in enumerate(headers):
            with cols[i]:
                st.write(f"**{header}**")

        # Filas para cada miembro ausente
        multas_a_registrar = []
        
        for i, miembro in enumerate(miembros_ausentes):
            cols = st.columns([3, 2, 2, 2])
            
            with cols[0]:
                st.write(f"{miembro['nombre_completo']}")
            
            # Verificar si ya existe multa para este miembro - CORREGIDO
            cursor.execute("""
                SELECT ID_Multa, ID_Estado_multa 
                FROM Multa 
                WHERE ID_Reunion = %s AND ID_Miembro = %s
            """, (id_reunion, miembro['ID_Miembro']))
            
            multa_existente = cursor.fetchone()
            
            with cols[1]:
                st.write(f"${monto_multa:,.2f}")
            
            with cols[2]:
                if multa_existente:
                    # Si ya existe multa, mostrar estado
                    if multa_existente['ID_Estado_multa'] == 2:  # Pagada
                        st.write("✅ Pagada")
                    else:
                        st.write("⏳ Pendiente")
                else:
                    # Si no existe multa, mostrar opción para registrar
                    checkbox = st.checkbox(
                        "Marcar como pagada", 
                        key=f"pagada_{miembro['ID_Miembro']}",
                        value=False,
                        label_visibility="collapsed"
                    )
            
            with cols[3]:
                justificacion = miembro['justificacion'] if miembro['justificacion'] else "Sin justificación"
                st.write(f"📝 {justificacion}")
            
            multas_a_registrar.append({
                'ID_Miembro': miembro['ID_Miembro'],
                'nombre': miembro['nombre_completo'],
                'monto': monto_multa,
                'registrar': checkbox if not multa_existente else False,
                'ya_registrada': multa_existente is not None,
                'ID_Multa_existente': multa_existente['ID_Multa'] if multa_existente else None,
                'estado_actual': multa_existente['ID_Estado_multa'] if multa_existente else None,
                'justificacion': miembro['justificacion']
            })

        # Botón para guardar multas
        if miembros_ausentes:
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("💾 Guardar Multas", type="primary", use_container_width=True):
                    try:
                        multas_registradas = 0
                        multas_como_pagadas = 0

                        for multa in multas_a_registrar:
                            if not multa['ya_registrada']:
                                # Determinar el estado basado en el checkbox
                                estado_multa = 2 if multa['registrar'] else 1  # 2=Pagada, 1=Pendiente
                                
                                # Insertar nueva multa - CORREGIDO
                                cursor.execute("""
                                    INSERT INTO Multa 
                                    (ID_Reunion, ID_Miembro, ID_Reglamento, fecha, ID_Estado_multa) 
                                    VALUES (%s, %s, %s, %s, %s)
                                """, (id_reunion, multa['ID_Miembro'], id_reglamento, 
                                      datetime.now().date(), estado_multa))
                                multas_registradas += 1
                                
                                if estado_multa == 2:
                                    multas_como_pagadas += 1

                        con.commit()

                        if multas_registradas > 0:
                            st.success(f"✅ Se registraron {multas_registradas} multas correctamente.")
                            if multas_como_pagadas > 0:
                                st.success(f"💰 {multas_como_pagadas} multas registradas como pagadas.")
                        else:
                            st.info("ℹ️ No se registraron nuevas multas.")

                        st.rerun()

                    except Exception as e:
                        con.rollback()
                        st.error(f"❌ Error al registrar las multas: {e}")
        else:
            st.success("🎉 No hay miembros ausentes para multar.")

        # SECCIÓN: GESTIÓN DE MULTAS EXISTENTES
        st.subheader("📋 Gestión de Multas Registradas")

        # Obtener todas las multas de esta reunión - CORREGIDO
        cursor.execute("""
            SELECT 
                mu.ID_Multa,
                CONCAT(mb.nombre, ' ', mb.apellido) as nombre_completo,
                mu.fecha,
                em.estado_multa,
                mu.ID_Estado_multa
            FROM Multa mu
            JOIN Miembro mb ON mu.ID_Miembro = mb.ID_Miembro
            JOIN Estado_multa em ON mu.ID_Estado_multa = em.ID_Estado_multa
            WHERE mu.ID_Reunion = %s
            ORDER BY mb.nombre, mb.apellido
        """, (id_reunion,))
        
        multas_existentes = cursor.fetchall()

        if multas_existentes:
            # Mostrar resumen
            multas_pagadas = [m for m in multas_existentes if m['ID_Estado_multa'] == 2]
            multas_pendientes = [m for m in multas_existentes if m['ID_Estado_multa'] == 1]

            st.write("#### Resumen de Multas")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📊 Total Multas", len(multas_existentes))
            with col2:
                st.metric("⏳ Pendientes", len(multas_pendientes))
            with col3:
                st.metric("✅ Pagadas", len(multas_pagadas))
                st.caption("**TOTAL MULTAS PAGADAS**")

            # Lista detallada de multas con opciones de gestión
            st.write("#### Detalle de Multas")
            for multa in multas_existentes:
                col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 3])
                
                with col1:
                    st.write(f"**{multa['nombre_completo']}**")
                
                with col2:
                    st.write(f"${monto_multa:,.2f}")
                
                with col3:
                    estado = "✅ PAGADA" if multa['ID_Estado_multa'] == 2 else "⏳ PENDIENTE"
                    st.write(estado)
                
                with col4:
                    st.write(f"{multa['fecha']}")
                
                with col5:
                    # Botones para cambiar estado
                    if multa['ID_Estado_multa'] == 1:  # Pendiente
                        if st.button("✅ Marcar como Pagada", key=f"pagar_{multa['ID_Multa']}"):
                            try:
                                cursor.execute("""
                                    UPDATE Multa 
                                    SET ID_Estado_multa = 2 
                                    WHERE ID_Multa = %s
                                """, (multa['ID_Multa'],))
                                con.commit()
                                st.success(f"✅ Multa de {multa['nombre_completo']} marcada como pagada.")
                                st.rerun()
                            except Exception as e:
                                con.rollback()
                                st.error(f"❌ Error al actualizar: {e}")
                    else:  # Pagada
                        if st.button("↩️ Marcar como Pendiente", key=f"revertir_{multa['ID_Multa']}"):
                            try:
                                cursor.execute("""
                                    UPDATE Multa 
                                    SET ID_Estado_multa = 1 
                                    WHERE ID_Multa = %s
                                """, (multa['ID_Multa'],))
                                con.commit()
                                st.warning(f"↩️ Multa de {multa['nombre_completo']} marcada como pendiente.")
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
