import streamlit as st
from modulos.config.conexion import obtener_conexion
from datetime import datetime, timedelta, date
from decimal import Decimal
import calendar

# -------------------------
# Helpers de fecha / util
# -------------------------
SPANISH_WEEKDAY = {
    'LUNES': 0, 'MARTES': 1, 'MIERCOLES': 2, 'MIÉRCOLES': 2, 'MIERCOLES': 2,
    'JUEVES': 3, 'VIERNES': 4, 'SABADO': 5, 'SÁBADO': 5, 'DOMINGO': 6
}

def parsear_dia_reunion(valor):
    """
    Acepta entero 0..6 o string con nombre en español y devuelve 0..6
    Si no puede parsear, devuelve 0 (lunes) por defecto.
    """
    if valor is None:
        return 0
    try:
        # si ya es int
        if isinstance(valor, int):
            if 0 <= valor <= 6:
                return valor
            return 0
        # si es string con número
        if isinstance(valor, str) and valor.strip().isdigit():
            n = int(valor.strip())
            return n if 0 <= n <= 6 else 0
        # si es nombre de día
        clave = str(valor).strip().upper()
        return SPANISH_WEEKDAY.get(clave, 0)
    except Exception:
        return 0

def calcular_fecha_siguiente_reunion(fecha_base: date, dia_reunion, frecuencia: str) -> date:
    """
    Calcula la fecha de la PRÓXIMA reunión a partir de:
      - fecha_base: fecha de la reunión en la que se multó (date)
      - dia_reunion: 0=lunes .. 6=domingo  (o valor parseable)
      - frecuencia: 'SEMANAL', 'QUINCENAL', 'MENSUAL' (case-insensitive)
    Reglas:
      - Si la próxima reunión cae el mismo día de la semana, se toma la siguiente ocurrencia (no la misma fecha).
      - QUINCENAL = siguiente ocurrencia + 7 días (es decir, 2 semanas desde la actual ocurrencia).
      - MENSUAL = buscar el primer día_de_semana igual en el mes siguiente.
    """
    try:
        dia = parsear_dia_reunion(dia_reunion)
        freq = (frecuencia or 'SEMANAL').strip().upper()

        dia_actual = fecha_base.weekday()
        dias_hasta = (dia - dia_actual) % 7
        if dias_hasta == 0:
            dias_hasta = 7  # si la reunión fue hoy, la siguiente es la próxima semana

        if freq == 'SEMANAL':
            return fecha_base + timedelta(days=dias_hasta)

        if freq == 'QUINCENAL':
            # próximo día de reunión + 7 días
            return fecha_base + timedelta(days=dias_hasta + 7)

        if freq == 'MENSUAL':
            # Saltar al primer día del mes siguiente y buscar la primera ocurrencia del dia de semana
            year = fecha_base.year
            month = fecha_base.month + 1
            if month > 12:
                month = 1
                year += 1
            # primer día del mes siguiente
            primer_dia_mes = date(year, month, 1)
            primer_weekday = primer_dia_mes.weekday()
            delta = (dia - primer_weekday) % 7
            return primer_dia_mes + timedelta(days=delta)

        # por defecto, igual que semanal
        return fecha_base + timedelta(days=dias_hasta)

    except Exception:
        # fallback simple
        return fecha_base + timedelta(days=7)

# -------------------------
# Funciones públicas
# -------------------------

def obtener_multas_grupo():
    """
    Retorna todas las entradas de PagoMulta (histórico) para el grupo de la reunion actual.
    """
    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)

        if 'reunion_actual' not in st.session_state:
            st.error("No hay reunión activa seleccionada")
            return []

        id_grupo = st.session_state.reunion_actual['id_grupo']

        cursor.execute("""
            SELECT 
                pm.ID_PagoMulta,
                pm.ID_Miembro,
                pm.ID_Multa,
                pm.monto_pagado,
                pm.fecha_pago,
                pm.ID_Reunion_pago,
                pm.fecha_limite_pago,
                m.nombre as nombre_miembro,
                mu.fecha as fecha_multa
            FROM PagoMulta pm
            JOIN Miembro m ON pm.ID_Miembro = m.ID_Miembro
            JOIN Multa mu ON pm.ID_Multa = mu.ID_Multa
            WHERE m.ID_Grupo = %s
            ORDER BY pm.fecha_pago
        """, (id_grupo,))

        datos = cursor.fetchall()
        resultado = []
        for row in datos:
            resultado.append({
                'ID_PagoMulta': row['ID_PagoMulta'],
                'ID_Miembro': row['ID_Miembro'],
                'ID_Multa': row['ID_Multa'],
                'monto_pagado': float(row['monto_pagado'] or 0),
                'fecha_pago': row['fecha_pago'],
                'ID_Reunion_pago': row['ID_Reunion_pago'],
                'fecha_limite_pago': row.get('fecha_limite_pago'),
                'nombre_miembro': row.get('nombre_miembro'),
                'fecha_multa': row.get('fecha_multa')
            })
        return resultado

    except Exception as e:
        st.error(f"❌ Error en obtener_multas_grupo: {e}")
        return []
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'con' in locals(): con.close()


def obtener_total_multas_ciclo():
    """
    Suma total de todos los pagos registrados en PagoMulta para el grupo.
    """
    try:
        pagos = obtener_multas_grupo()
        if not pagos:
            return 0.00
        return sum(p['monto_pagado'] for p in pagos)
    except Exception as e:
        st.error(f"❌ Error calculando total de multas: {e}")
        return 0.00

# -------------------------
# Interfaz streamlit
# -------------------------

def mostrar_pago_multas():
    st.header("💵 Pago de Multas")

    if 'reunion_actual' not in st.session_state:
        st.warning("⚠️ Primero debes seleccionar una reunión en el módulo de Asistencia o Multas.")
        return

    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)

        reunion_info = st.session_state.reunion_actual
        id_reunion = reunion_info['id_reunion']
        id_grupo = reunion_info['id_grupo']
        nombre_reunion = reunion_info.get('nombre_reunion', f"ID {id_reunion}")

        st.info(f"📅 Reunión actual: {nombre_reunion}")

        # Obtener reglamento (frecuencia + dia_reunion)
        cursor.execute("""
            SELECT frecuencia_reunion, dia_reunion
            FROM Reglamento
            WHERE ID_Grupo = %s
            ORDER BY ID_Reglamento DESC
            LIMIT 1
        """, (id_grupo,))
        regl = cursor.fetchone() or {}
        frecuencia = (regl.get('frecuencia_reunion') or 'SEMANAL').strip().upper()
        dia_reunion_raw = regl.get('dia_reunion')
        dia_reunion = parsear_dia_reunion(dia_reunion_raw)

        # Obtener la fecha de la reunión actual (tabla Reunion)
        cursor.execute("SELECT fecha FROM Reunion WHERE ID_Reunion = %s", (id_reunion,))
        row_reunion = cursor.fetchone()
        fecha_reunion_actual = row_reunion['fecha'] if row_reunion and row_reunion.get('fecha') else datetime.now().date()

        # Consultar multas pendientes (saldo > 0) para el grupo
        cursor.execute("""
            SELECT
                mxm.ID_Miembro,
                mxm.ID_Multa,
                mxm.monto_a_pagar,
                mxm.monto_pagado,
                CONCAT(m.nombre, ' ', m.apellido) AS nombre_completo,
                mu.fecha AS fecha_multa,
                mu.ID_Reunion AS ID_Reunion_Multa,
                (mxm.monto_a_pagar - mxm.monto_pagado) AS saldo_pendiente,
                mr.justificacion,
                DATEDIFF(%s, mu.fecha) AS dias_transcurridos
            FROM MiembroxMulta mxm
            JOIN Miembro m ON mxm.ID_Miembro = m.ID_Miembro
            JOIN Multa mu ON mxm.ID_Multa = mu.ID_Multa
            LEFT JOIN Reunion r ON mu.ID_Reunion = r.ID_Reunion
            LEFT JOIN Miembroxreunion mr ON m.ID_Miembro = mr.ID_Miembro AND mr.ID_Reunion = mu.ID_Reunion
            WHERE m.ID_Grupo = %s
              AND (mxm.monto_a_pagar - mxm.monto_pagado) > 0
            ORDER BY mu.fecha DESC, m.nombre, m.apellido
        """, (fecha_reunion_actual, id_grupo))

        multas_pendientes = cursor.fetchall()

        # resumen de la reunion actual: pagos registrados en esta reunion
        cursor.execute("""
            SELECT COUNT(*) AS total_multas_pagadas,
                   COALESCE(SUM(mxm.monto_pagado), 0) AS total_monto_pagado
            FROM MiembroxMulta mxm
            JOIN Multa mu ON mxm.ID_Multa = mu.ID_Multa
            WHERE mu.ID_Reunion = %s AND mxm.monto_pagado > 0
        """, (id_reunion,))
        resumen = cursor.fetchone() or {'total_multas_pagadas': 0, 'total_monto_pagado': 0}
        total_multas_pagadas = resumen['total_multas_pagadas']
        total_monto_pagado = float(resumen['total_monto_pagado'])

        # Mostrar métricas
        if multas_pendientes:
            total_pendiente = sum(float(m['saldo_pendiente']) for m in multas_pendientes)
            multas_vencidas = [m for m in multas_pendientes if m.get('dias_transcurridos') is not None and m['dias_transcurridos'] > 7]

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("👥 Total Pendientes", len(multas_pendientes))
            with col2:
                st.metric("💰 Total Pendiente", f"${total_pendiente:,.2f}")
            with col3:
                st.metric("⚠️ Multas Vencidas", len(multas_vencidas))
            with col4:
                st.metric("✅ Pagadas Hoy", total_multas_pagadas, f"${total_monto_pagado:,.2f}")

            # Mostrar cada multa y opciones de pago
            for multa in multas_pendientes:
                monto_a_pagar = float(multa['monto_a_pagar'])
                monto_pagado = float(multa['monto_pagado'])
                saldo_pendiente = float(multa['saldo_pendiente'])
                dias = multa.get('dias_transcurridos') or 0
                esta_vencida = dias > 7

                with st.container():
                    c1, c2, c3, c4 = st.columns([3,2,2,2])
                    with c1:
                        st.write(f"**{multa['nombre_completo']}**")
                        st.write(f"Multa fecha: {multa.get('fecha_multa')}")
                        if multa.get('justificacion'):
                            st.caption(f"📝 Justificación: {multa['justificacion']}")
                        st.write("🚩 Vencida" if esta_vencida else f"⏳ {dias} días")
                    with c2:
                        st.write(f"**Monto:** ${monto_a_pagar:,.2f}")
                        st.write(f"**Pagado:** ${monto_pagado:,.2f}")
                        st.write(f"**Saldo:** ${saldo_pendiente:,.2f}")
                    with c3:
                        # input para pago parcial o total
                        if saldo_pendiente > 0:
                            monto_pago = st.number_input(
                                f"Monto a pagar ({multa['ID_Miembro']}/{multa['ID_Multa']})",
                                min_value=0.0,
                                max_value=saldo_pendiente,
                                value=round(saldo_pendiente, 2),
                                step=1.0,
                                key=f"pago_{multa['ID_Miembro']}_{multa['ID_Multa']}"
                            )
                        else:
                            monto_pago = 0.0

                        if monto_pagado > 0:
                            st.success(f"✅ {monto_pagado:,.2f} pagados")
                        if esta_vencida:
                            st.error("🚨 MULTA VENCIDA")

                    with c4:
                        # Botón pagar
                        if saldo_pendiente > 0 and st.button("💳 Pagar", key=f"btn_pagar_{multa['ID_Miembro']}_{multa['ID_Multa']}"):
                            try:
                                nuevo_pagado = Decimal(str(monto_pagado + monto_pago))

                                # 1) actualizar MiembroxMulta
                                cursor.execute("""
                                    UPDATE MiembroxMulta
                                    SET monto_pagado = %s
                                    WHERE ID_Miembro = %s AND ID_Multa = %s
                                """, (nuevo_pagado, multa['ID_Miembro'], multa['ID_Multa']))

                                # 2) calcular fecha limite (la siguiente reunion relativa a la multa)
                                fecha_multa = multa.get('fecha_multa') or fecha_reunion_actual
                                if isinstance(fecha_multa, datetime):
                                    fecha_multa = fecha_multa.date()
                                fecha_limite = calcular_fecha_siguiente_reunion(fecha_multa, dia_reunion, frecuencia)

                                # 3) insertar registro en PagoMulta (histórico)
                                cursor.execute("""
                                    INSERT INTO PagoMulta
                                    (ID_Miembro, ID_Multa, monto_pagado, fecha_pago, ID_Reunion_pago, fecha_limite_pago)
                                    VALUES (%s, %s, %s, %s, %s, %s)
                                """, (
                                    multa['ID_Miembro'],
                                    multa['ID_Multa'],
                                    Decimal(str(monto_pago)),
                                    datetime.now().date(),
                                    id_reunion,
                                    fecha_limite
                                ))

                                con.commit()
                                st.success(f"✅ Pago ${monto_pago:,.2f} registrado para {multa['nombre_completo']}")
                                st.experimental_rerun()

                            except Exception as e:
                                con.rollback()
                                st.error(f"❌ Error al registrar pago: {e}")

                        # Botón acumular (si vencida) - deja pendiente la lógica para acumular nuevas multas
                        if esta_vencida and st.button("🔄 Acumular", key=f"btn_acumular_{multa['ID_Miembro']}_{multa['ID_Multa']}"):
                            st.info("🔔 Acumular: función que deberá crear una nueva Multa y relacionarla al mismo miembro. Pendiente implementar según reglas exactas.")
                    st.divider()

            # Pago masivo: pagar todos los saldos pendientes
            st.subheader("Pago Masivo")
            c1, c2, c3 = st.columns([2,1,1])
            with c2:
                if st.button("💳 Pagar Todas (saldos)", use_container_width=True):
                    try:
                        total_pagado = 0
                        cont = 0
                        for multa in multas_pendientes:
                            saldo = float(multa['saldo_pendiente'])
                            if saldo <= 0:
                                continue

                            # actualizar MiembroxMulta
                            monto_a_actualizar = Decimal(str(multa['monto_a_pagar']))
                            cursor.execute("""
                                UPDATE MiembroxMulta
                                SET monto_pagado = %s
                                WHERE ID_Miembro = %s AND ID_Multa = %s
                            """, (monto_a_actualizar, multa['ID_Miembro'], multa['ID_Multa']))

                            # calcular fecha limite usando fecha de la multa
                            fecha_multa = multa.get('fecha_multa') or fecha_reunion_actual
                            if isinstance(fecha_multa, datetime):
                                fecha_multa = fecha_multa.date()
                            fecha_limite = calcular_fecha_siguiente_reunion(fecha_multa, dia_reunion, frecuencia)

                            # insertar PagoMulta (histórico)
                            try:
                                cursor.execute("""
                                    INSERT INTO PagoMulta
                                    (ID_Miembro, ID_Multa, monto_pagado, fecha_pago, ID_Reunion_pago, fecha_limite_pago)
                                    VALUES (%s, %s, %s, %s, %s, %s)
                                """, (multa['ID_Miembro'], multa['ID_Multa'], Decimal(str(saldo)), datetime.now().date(), id_reunion, fecha_limite))
                            except Exception:
                                # no crítico: seguir con el resto
                                pass

                            total_pagado += saldo
                            cont += 1

                        con.commit()
                        st.success(f"✅ Se pagaron {cont} multas (todos los saldos) por un total de ${total_pagado:,.2f}")
                        st.experimental_rerun()
                    except Exception as e:
                        con.rollback()
                        st.error(f"❌ Error al pagar todas las multas: {e}")

            with c3:
                if st.button("📊 Ver Resumen", use_container_width=True):
                    st.info(f"""
                    **Resumen de la reunión {nombre_reunion}:**
                    - Multas pagadas (hoy): {total_multas_pagadas}
                    - Total recaudado (hoy): ${total_monto_pagado:,.2f}
                    - Multas pendientes totales: {len(multas_pendientes)}
                    - Total pendiente: ${total_pendiente:,.2f}
                    """)

        else:
            st.success("🎉 No hay multas pendientes de pago")
            if total_multas_pagadas > 0:
                st.info(f"**Resumen de esta reunión:** {total_multas_pagadas} multas pagadas por un total de ${total_monto_pagado:,.2f}")

    except Exception as e:
        st.error(f"❌ Error en mostrar_pago_multas: {e}")
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'con' in locals(): con.close()
