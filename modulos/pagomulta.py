import streamlit as st
from modulos.config.conexion import obtener_conexion
from datetime import datetime, timedelta
import calendar

def calcular_fecha_limite(dia_reunion):
    """Calcula la fecha límite de pago según el día de reunión (lunes = 0 ... domingo = 6)."""
    hoy = datetime.now().date()
    dia_actual = hoy.weekday()

    # cuántos días faltan para el siguiente día de reunión
    dias_faltantes = (dia_reunion - dia_actual) % 7
    if dias_faltantes == 0:
        dias_faltantes = 7  # si es hoy, aplica para la próxima semana

    return hoy + timedelta(days=dias_faltantes)

def mostrar_multas():
    st.header("📋 Sistema de Multas")

    # Verificar si hay una reunión seleccionada
    if 'reunion_actual' not in st.session_state:
        st.warning("⚠️ Primero debes seleccionar una reunión en el módulo de Asistencia.")
        return

    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)

        # Obtener la reunión seleccionada
        reunion_info = st.session_state.reunion_actual
        id_reunion = reunion_info['id_reunion']
        id_grupo = reunion_info['id_grupo']
        nombre_reunion = reunion_info['nombre_reunion']

        st.info(f"📅 **Reunión actual:** {nombre_reunion}")

        # Obtener el monto de multa y el día de reunión desde Reglamento
        cursor.execute("""
            SELECT ID_Reglamento, monto_multa_asistencia, dia_reunion
            FROM Reglamento
            WHERE ID_Grupo = %s
            ORDER BY ID_Reglamento DESC LIMIT 1
        """, (id_grupo,))
        reglamento = cursor.fetchone()

        if reglamento:
            monto_multa = float(reglamento['monto_multa_asistencia'])
            id_reglamento = reglamento['ID_Reglamento']
            dia_reunion = reglamento['dia_reunion']  # día reunión ya viene de BD
        else:
            monto_multa = 10.00
            dia_reunion = 0  # Lunes por defecto
            st.warning("⚠️ No se encontró reglamento, usando valores por defecto.")

        st.success(f"💰 **Monto de multa por inasistencia:** ${monto_multa:,.2f}")

        # Cargar miembros y estado de asistencia
        cursor.execute("""
            SELECT 
                m.ID_Miembro, 
                CONCAT(m.nombre, ' ', m.apellido) AS nombre_completo,
                COALESCE(mr.asistio, 0) AS asistio,
                mr.justificacion
            FROM Miembro m
            LEFT JOIN Miembroxreunion mr 
                ON m.ID_Miembro = mr.ID_Miembro 
                AND mr.ID_Reunion = %s
            WHERE m.ID_Grupo = %s
            ORDER BY m.nombre, m.apellido
        """, (id_reunion, id_grupo))

        todos_miembros = cursor.fetchall()

        if not todos_miembros:
            st.warning("⚠️ No hay miembros en este grupo.")
            return

        # Clasificación
        presentes = [m for m in todos_miembros if m['asistio'] == 1]
        ausentes_sj = [m for m in todos_miembros if m['asistio'] == 0 and not m['justificacion']]
        ausentes_cj = [m for m in todos_miembros if m['asistio'] == 0 and m['justificacion']]

        # Métricas
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("Presentes", len(presentes))
        with col2: st.metric("Ausencias sin justificación", len(ausentes_sj))
        with col3: st.metric("Ausencias con justificación", len(ausentes_cj))

        st.subheader("📊 Formulario de Multas (solo ausentes sin justificación)")

        # Tabla encabezado
        cols = st.columns([3, 2, 2, 3])
        for col, h in zip(cols, ["Socio", "A pagar", "Pagada", "Justificación"]):
            with col: st.write(f"**{h}**")

        multas_a_registrar = []

        for miembro in ausentes_sj:
            cols = st.columns([3, 2, 2, 3])

            with cols[0]:
                st.write(miembro['nombre_completo'])

            # Buscar multa existente
            cursor.execute("""
                SELECT mxm.*, m.ID_Estado_multa
                FROM MiembroxMulta mxm
                JOIN Multa m ON mxm.ID_Multa = m.ID_Multa
                WHERE mxm.ID_Miembro = %s AND m.ID_Reunion = %s
            """, (miembro['ID_Miembro'], id_reunion))
            multa_existente = cursor.fetchone()

            with cols[1]:
                st.write(f"${monto_multa:,.2f}")

            with cols[2]]:
                if multa_existente:
                    if multa_existente['monto_pagado'] >= multa_existente['monto_a_pagar']:
                        st.write("✅ Pagada")
                    else:
                        st.write("⏳ Pendiente")
                    marcar_pagada = False
                else:
                    marcar_pagada = st.checkbox(
                        "Marcar pagada",
                        key=f"pagada_{miembro['ID_Miembro']}"
                    )

            with cols[3]:
                st.write("Sin justificación")

            multas_a_registrar.append({
                "ID_Miembro": miembro["ID_Miembro"],
                "registrar": not bool(multa_existente),
                "marcar_pagada": marcar_pagada,
                "monto": monto_multa
            })

        # Botón registrar multas
        if ausentes_sj:
            if st.button("💾 Registrar Multas", type="primary"):
                try:
                    for multa in multas_a_registrar:
                        if multa["registrar"]:
                            # 1. Insertar multa
                            cursor.execute("""
                                INSERT INTO Multa (ID_Reunion, ID_Reglamento, fecha, ID_Estado_multa)
                                VALUES (%s, %s, %s, %s)
                            """, (id_reunion, id_reglamento, datetime.now().date(), 1))

                            id_multa_nueva = cursor.lastrowid

                            monto_pagado = multa["monto"] if multa["marcar_pagada"] else 0

                            # 2. Insertar en MiembroxMulta
                            cursor.execute("""
                                INSERT INTO MiembroxMulta
                                (ID_Miembro, ID_Multa, monto_a_pagar, monto_pagado)
                                VALUES (%s, %s, %s, %s)
                            """, (multa["ID_Miembro"], id_multa_nueva, multa["monto"], monto_pagado))

                            # 3. Insertar fecha límite en PagoMulta  ← CORREGIDO
                            fecha_limite = calcular_fecha_limite(dia_reunion)

                            cursor.execute("""
                                INSERT INTO PagoMulta
                                (ID_Multa, fecha_limite_pago)
                                VALUES (%s, %s)
                            """, (id_multa_nueva, fecha_limite))

                    con.commit()
                    st.success("Multas registradas correctamente.")
                    st.rerun()

                except Exception as e:
                    con.rollback()
                    st.error(f"Error al registrar multas: {e}")

        else:
            st.success("🎉 No hay multas que registrar.")

        # ------------------------------------
        #   SECCIÓN: MULTAS EXISTENTES
        # ------------------------------------

        st.subheader("📋 Gestión de Multas Registradas")

        cursor.execute("""
            SELECT 
                mxm.ID_Miembro,
                CONCAT(m.nombre, ' ', m.apellido) AS nombre_completo,
                mxm.monto_a_pagar,
                mxm.monto_pagado,
                mu.ID_Multa,
                mu.fecha,
                em.estado_multa,
                pm.fecha_limite_pago
            FROM MiembroxMulta mxm
            JOIN Miembro m ON mxm.ID_Miembro = m.ID_Miembro
            JOIN Multa mu ON mxm.ID_Multa = mu.ID_Multa
            JOIN Estado_multa em ON mu.ID_Estado_multa = em.ID_Estado_multa
            LEFT JOIN PagoMulta pm ON pm.ID_Multa = mu.ID_Multa   -- ← CORREGIDO
            WHERE mu.ID_Reunion = %s
            ORDER BY nombre_completo
        """, (id_reunion,))
        multas = cursor.fetchall()

        if multas:
            for multa in multas:
                col1, col2, col3, col4, col5 = st.columns([3,2,2,2,2])
                with col1: st.write(f"**{multa['nombre_completo']}**")
                with col2: st.write(f"${multa['monto_a_pagar']:,.2f}")
                with col3:
                    if multa['monto_pagado'] >= multa['monto_a_pagar']:
                        st.write("✅ Pagada")
                    else:
                        st.write("⏳ Pendiente")
                with col4: st.write(multa['fecha_limite_pago'])

                with col5:
                    if multa['monto_pagado'] < multa['monto_a_pagar']:
                        if st.button("Pagar", key=f"pagar_{multa['ID_Multa']}"):
                            cursor.execute("""
                                UPDATE MiembroxMulta
                                SET monto_pagado = monto_a_pagar
                                WHERE ID_Multa = %s
                            """, (multa['ID_Multa'],))
                            con.commit()
                            st.rerun()
                    else:
                        if st.button("Revertir", key=f"rev_{multa['ID_Multa']}"):
                            cursor.execute("""
                                UPDATE MiembroxMulta
                                SET monto_pagado = 0
                                WHERE ID_Multa = %s
                            """, (multa['ID_Multa'],))
                            con.commit()
                            st.rerun()

        else:
            st.info("No hay multas registradas.")

    except Exception as e:
        st.error(f"❌ Error: {e}")

    finally:
        if "cursor" in locals(): cursor.close()
        if "con" in locals(): con.close()
