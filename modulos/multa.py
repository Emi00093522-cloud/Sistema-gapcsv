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

        # Obtener reunión desde session_state
        reunion_info = st.session_state.reunion_actual
        id_reunion = reunion_info['id_reunion']
        id_grupo = reunion_info['id_grupo']
        nombre_reunion = reunion_info['nombre_reunion']

        st.info(f"📅 **Reunión actual:** {nombre_reunion}")

        # Obtener monto de multa
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
            monto_multa = 10.00
            st.warning("⚠️ No se encontró monto de multa definido en el reglamento. Usando valor por defecto.")
            
            cursor.execute("SELECT ID_Reglamento FROM Reglamento WHERE ID_Grupo = %s LIMIT 1", (id_grupo,))
            reglamento_existente = cursor.fetchone()
            
            if reglamento_existente:
                id_reglamento = reglamento_existente['ID_Reglamento']
            else:
                cursor.execute("""
                    INSERT INTO Reglamento (ID_Grupo, monto_multa_asistencia, fecha_creacion)
                    VALUES (%s, %s, %s)
                """, (id_grupo, monto_multa, datetime.now().date()))
                con.commit()
                cursor.execute("SELECT LAST_INSERT_ID() as ID_Reglamento")
                id_reglamento = cursor.fetchone()['ID_Reglamento']

        st.success(f"💰 **Monto de multa por inasistencia:** ${monto_multa:,.2f}")

        # Cargar miembros del grupo y asistencia
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

        # Clasificación:
        miembros_presentes = [m for m in todos_miembros if m['asistio'] == 1]

        miembros_ausentes_sin = [
            m for m in todos_miembros
            if m['asistio'] == 0 and (m['justificacion'] is None or m['justificacion'].strip() == "")
        ]

        miembros_ausentes_con = [
            m for m in todos_miembros
            if m['asistio'] == 0 and (m['justificacion'] is not None and m['justificacion'].strip() != "")
        ]

        # Mostrar métricas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("✅ Presentes", len(miembros_presentes))
        with col2:
            st.metric("❌ Ausentes sin justificación", len(miembros_ausentes_sin))
        with col3:
            st.metric("📝 Ausentes con justificación", len(miembros_ausentes_con))

        # FORMULARIO DE MULTAS
        st.subheader("📊 Formulario de Multas")
        st.write("### Registro de Multas por Inasistencia (solo sin justificación)")

        cols = st.columns([3, 2, 2, 2])
        headers = ["Socio", "A pagar", "Pagada", "Justificación"]
        for i, header in enumerate(headers):
            with cols[i]:
                st.write(f"**{header}**")

        multas_a_registrar = []
        
        for miembro in miembros_ausentes_sin:
            cols = st.columns([3, 2, 2, 2])
            
            with cols[0]:
                st.write(miembro['nombre_completo'])
            
            cursor.execute("""
                SELECT mxm.ID_Miembro, mxm.ID_Multa, mxm.monto_a_pagar, mxm.monto_pagado,
                       m.ID_Multa as multa_id, m.ID_Estado_multa
                FROM MiembroxMulta mxm
                JOIN Multa m ON mxm.ID_Multa = m.ID_Multa
                WHERE mxm.ID_Miembro = %s AND m.ID_Reunion = %s
            """, (miembro['ID_Miembro'], id_reunion))
            
            multa_existente = cursor.fetchone()
            
            with cols[1]:
                st.write(f"${monto_multa:,.2f}")
            
            with cols[2]:
                if multa_existente:
                    if multa_existente["monto_pagado"] >= multa_existente["monto_a_pagar"]:
                        st.write("✅ Pagada")
                    else:
                        st.write("⏳ Pendiente")
                else:
                    checkbox = st.checkbox(
                        "Marcar como pagada",
                        key=f"pagada_{miembro['ID_Miembro']}",
                        value=False,
                        label_visibility="collapsed"
                    )

            with cols[3]:
                st.write("Sin justificación")

            multas_a_registrar.append({
                "ID_Miembro": miembro["ID_Miembro"],
                "registrar": checkbox if not multa_existente else False,
                "ya_registrada": multa_existente is not None,
                "monto": monto_multa
            })

        # Guardar multas
        if miembros_ausentes_sin:
            if st.button("💾 Registrar Multas", type="primary"):
                try:
                    registradas = 0
                    pagadas = 0

                    for multa in multas_a_registrar:
                        if not multa["ya_registrada"]:

                            cursor.execute("""
                                INSERT INTO Multa (ID_Reunion, ID_Reglamento, fecha, ID_Estado_multa)
                                VALUES (%s, %s, %s, %s)
                            """, (id_reunion, id_reglamento, datetime.now().date(), 1))

                            id_multa_nueva = cursor.lastrowid

                            monto_pagado = multa["monto"] if multa["registrar"] else 0.00

                            cursor.execute("""
                                INSERT INTO MiembroxMulta (ID_Miembro, ID_Multa, monto_a_pagar, monto_pagado)
                                VALUES (%s, %s, %s, %s)
                            """, (multa["ID_Miembro"], id_multa_nueva, multa["monto"], monto_pagado))

                            registradas += 1
                            if multa["registrar"]:
                                pagadas += 1

                    con.commit()

                    st.success(f"✅ {registradas} multas registradas.")
                    if pagadas > 0:
                        st.success(f"💰 {pagadas} multas marcadas como pagadas.")
                    st.rerun()

                except Exception as e:
                    con.rollback()
                    st.error(f"❌ Error: {e}")
        else:
            st.success("🎉 No hay miembros ausentes sin justificación.")

        # GESTIÓN DE MULTAS EXISTENTES
        st.subheader("📋 Gestión de Multas Registradas")

        cursor.execute("""
            SELECT 
                mxm.ID_Miembro,
                CONCAT(mb.nombre, ' ', mb.apellido) as nombre_completo,
                mxm.monto_a_pagar,
                mxm.monto_pagado,
                mu.ID_Multa,
                mu.fecha
            FROM MiembroxMulta mxm
            JOIN Miembro mb ON mxm.ID_Miembro = mb.ID_Miembro
            JOIN Multa mu ON mxm.ID_Multa = mu.ID_Multa
            WHERE mu.ID_Reunion = %s
            ORDER BY mb.nombre, mb.apellido
        """, (id_reunion,))
        
        multas_existentes = cursor.fetchall()

        if multas_existentes:
            for multa in multas_existentes:
                col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                
                with col1:
                    st.write(f"**{multa['nombre_completo']}**")
                with col2:
                    st.write(f"${multa['monto_a_pagar']:,.2f}")
                with col3:
                    if multa["monto_pagado"] >= multa["monto_a_pagar"]:
                        st.write("✅ Pagada")
                    else:
                        st.write(f"⏳ ${multa['monto_pagado']:,.2f}")
                with col4:
                    st.write(multa["fecha"])

        else:
            st.info("📝 No hay multas registradas.")

    except Exception as e:
        st.error(f"❌ Error general: {e}")

    finally:
        if "cursor" in locals():
            cursor.close()
        if "con" in locals():
            con.close()
