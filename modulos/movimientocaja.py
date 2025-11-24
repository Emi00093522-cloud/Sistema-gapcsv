import streamlit as st
from modulos.config.conexion import obtener_conexion
from datetime import datetime

# =====================================================================================
#  MÓDULO PRINCIPAL - MOVIMIENTO DE CAJA
# =====================================================================================

def mostrar_movimiento_caja():
    st.header("💰 Movimientos de Caja - Sistema Automático")

    if 'reunion_actual' not in st.session_state:
        st.warning("⚠️ Primero debes seleccionar una reunión en el módulo de Asistencia.")
        return

    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)

        # Datos de sesión
        reunion_info = st.session_state.reunion_actual
        id_reunion = reunion_info['id_reunion']
        id_grupo = reunion_info['id_grupo']
        nombre_reunion = reunion_info['nombre_reunion']

        st.info(f"📅 **Reunión actual:** {nombre_reunion}")

        # SALDO INICIAL = saldo_final de reunión previa
        saldo_anterior = obtener_saldo_anterior(cursor, id_reunion, id_grupo)
        st.success(f"💰 **Saldo inicial: ${saldo_anterior:,.2f}**")

        # Tabs
        tab1, tab2 = st.tabs(["📊 Resumen Automático", "📋 Detalle de Movimientos"])

        with tab1:
            resumen_automatico(cursor, con, id_reunion, saldo_anterior)

        with tab2:
            detalle_movimientos(cursor, id_reunion, saldo_anterior)

    except Exception as e:
        st.error(f"❌ Error general: {e}")

    finally:
        try:
            cursor.close()
            con.close()
        except:
            pass

# =====================================================================================
#  OBTENER SALDO ANTERIOR
# =====================================================================================

def obtener_saldo_anterior(cursor, id_reunion_actual, id_grupo):

    try:
        cursor.execute("""
            SELECT ID_Reunion
            FROM Reunion
            WHERE ID_Grupo = %s AND ID_Reunion < %s
            ORDER BY ID_Reunion DESC
            LIMIT 1
        """, (id_grupo, id_reunion_actual))

        reunion_anterior = cursor.fetchone()

        if not reunion_anterior:
            return 0

        cursor.execute("""
            SELECT saldo_final
            FROM Movimiento_de_caja
            WHERE ID_Reunion = %s
            ORDER BY ID_Movimiento_caja DESC
            LIMIT 1
        """, (reunion_anterior['ID_Reunion'],))

        mov = cursor.fetchone()

        return float(mov['saldo_final']) if mov else 0

    except Exception as e:
        st.error(f"Error al obtener saldo anterior: {e}")
        return 0

# =====================================================================================
#  OBTENER ID TIPO MOVIMIENTO
# =====================================================================================

def obtener_tipo_movimiento_id(cursor, tipo_ingreso_egreso, categoria):

    try:
        cursor.execute("""
            SELECT ID_Tipo_movimiento 
            FROM Tipo_de_movimiento
            WHERE tipo = %s AND nombre = %s
        """, (tipo_ingreso_egreso, categoria))

        resultado = cursor.fetchone()

        return resultado['ID_Tipo_movimiento'] if resultado else None

    except Exception as e:
        st.error(f"Error al obtener ID_Tipo_movimiento: {e}")
        return None

# =====================================================================================
#  OBTENER TODOS LOS MOVIMIENTOS AUTOMÁTICOS
# =====================================================================================

def obtener_movimientos_automaticos(cursor, id_reunion):
    movimientos = []

    try:
        # 1) AHORROS - INGRESO
        cursor.execute("""
            SELECT Monto_Ahorro AS monto, Fecha_Ahorro AS fecha,
                   'Ahorro' AS categoria,
                   CONCAT('Ahorro de ', m.Nombre) AS descripcion,
                   'Ingreso' AS tipo_ingreso_egreso
            FROM Ahorro a
            JOIN Miembro m ON a.ID_Miembro = m.ID_Miembro
            WHERE a.ID_Reunion = %s
        """, (id_reunion,))
        ahorros = cursor.fetchall()

        for mov in ahorros:
            mov["ID_Tipo_movimiento"] = obtener_tipo_movimiento_id(cursor, "Ingreso", "Ahorro") or 1

        movimientos.extend(ahorros)

        # 2) PRÉSTAMOS - EGRESO
        cursor.execute("""
            SELECT Monto_Prestamo AS monto, Fecha_Desembolso AS fecha,
                   'Préstamo' AS categoria,
                   CONCAT('Préstamo para ', m.Nombre) AS descripcion,
                   'Egreso' AS tipo_ingreso_egreso
            FROM Prestamo p
            JOIN Miembro m ON p.ID_Miembro = m.ID_Miembro
            WHERE p.ID_Reunion = %s AND p.Estado = 'APROBADO'
        """, (id_reunion,))
        prestamos = cursor.fetchall()

        for mov in prestamos:
            mov["ID_Tipo_movimiento"] = obtener_tipo_movimiento_id(cursor, "Egreso", "Préstamo") or 1

        movimientos.extend(prestamos)

        # 3) PAGO PRÉSTAMO - INGRESO
        cursor.execute("""
            SELECT Monto_Pagado AS monto, Fecha_Pago AS fecha,
                   'Pago Préstamo' AS categoria,
                   CONCAT('Pago préstamo de ', m.Nombre) AS descripcion,
                   'Ingreso' AS tipo_ingreso_egreso
            FROM Pago_Prestamo pp
            JOIN Prestamo p ON pp.ID_Prestamo = p.ID_Prestamo
            JOIN Miembro m ON p.ID_Miembro = m.ID_Miembro
            WHERE pp.ID_Reunion = %s
        """, (id_reunion,))
        pagos_prestamo = cursor.fetchall()

        for mov in pagos_prestamo:
            mov["ID_Tipo_movimiento"] = obtener_tipo_movimiento_id(cursor, "Ingreso", "Pago Préstamo") or 1

        movimientos.extend(pagos_prestamo)

        # 4) PAGO MULTA - INGRESO
        cursor.execute("""
            SELECT Monto_Pagado AS monto, Fecha_Pago AS fecha,
                   'Pago Multa' AS categoria,
                   CONCAT('Pago multa de ', m.Nombre) AS descripcion,
                   'Ingreso' AS tipo_ingreso_egreso
            FROM Pago_Multa pm
            JOIN Multa mt ON pm.ID_Multa = mt.ID_Multa
            JOIN Miembro m ON mt.ID_Miembro = m.ID_Miembro
            WHERE pm.ID_Reunion = %s
        """, (id_reunion,))
        pagos_multas = cursor.fetchall()

        for mov in pagos_multas:
            mov["ID_Tipo_movimiento"] = obtener_tipo_movimiento_id(cursor, "Ingreso", "Pago Multa") or 1

        movimientos.extend(pagos_multas)

        return movimientos

    except Exception as e:
        st.error(f"Error al obtener movimientos automáticos: {e}")
        return []

# =====================================================================================
#  ACTUALIZAR MOVIMIENTOS Y CALCULAR SALDO FINAL
# =====================================================================================

def actualizar_saldos_finales(cursor, con, id_reunion, movimientos, saldo_anterior):

    try:
        cursor.execute("DELETE FROM Movimiento_de_caja WHERE ID_Reunion = %s", (id_reunion,))

        # Normalizar fechas
        for mov in movimientos:
            if isinstance(mov["fecha"], str):
                mov["fecha"] = datetime.fromisoformat(mov["fecha"])
            elif not isinstance(mov["fecha"], datetime):
                mov["fecha"] = datetime.combine(mov["fecha"], datetime.min.time())

        movimientos = sorted(movimientos, key=lambda x: x["fecha"])
        saldo_actual = saldo_anterior

        for mov in movimientos:
            monto = float(mov["monto"])

            if mov["tipo_ingreso_egreso"] == "Ingreso":
                saldo_actual += monto
            else:
                saldo_actual -= monto

            cursor.execute("""
                INSERT INTO Movimiento_de_caja
                (ID_Reunion, ID_Tipo_movimiento, monto, categoria, descripcion, fecha, saldo_final)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                id_reunion,
                mov["ID_Tipo_movimiento"],
                monto,
                mov["categoria"],
                mov["descripcion"],
                mov["fecha"].strftime("%Y-%m-%d %H:%M:%S"),
                saldo_actual
            ))

        con.commit()
        return saldo_actual

    except Exception as e:
        con.rollback()
        st.error(f"Error al actualizar saldos: {e}")
        return saldo_anterior

# =====================================================================================
#  RESUMEN AUTOMÁTICO
# =====================================================================================

def resumen_automatico(cursor, con, id_reunion, saldo_anterior):

    st.subheader("📊 Resumen Automático de Caja")

    movimientos = obtener_movimientos_automaticos(cursor, id_reunion)

    if not movimientos:
        st.info("📭 No hay movimientos registrados en esta reunión.")
        return

    if st.button("🔄 Calcular Movimientos Automáticos", type="primary"):

        saldo_final = actualizar_saldos_finales(cursor, con, id_reunion, movimientos, saldo_anterior)

        total_ingresos = sum(float(mov["monto"]) for mov in movimientos if mov["tipo_ingreso_egreso"] == "Ingreso")
        total_egresos = sum(float(mov["monto"]) for mov in movimientos if mov["tipo_ingreso_egreso"] == "Egreso")

        st.metric("💰 Saldo Inicial", f"${saldo_anterior:,.2f}")
        st.metric("📈 Total Ingresos", f"${total_ingresos:,.2f}")
        st.metric("📉 Total Egresos", f"${total_egresos:,.2f}")
        st.metric("💵 Saldo Final", f"${saldo_final:,.2f}")

        st.success("✔️ Movimientos actualizados correctamente.")

# =====================================================================================
#  DETALLE DE MOVIMIENTOS
# =====================================================================================

def detalle_movimientos(cursor, id_reunion, saldo_anterior):

    st.subheader("📋 Detalle de Movimientos")

    cursor.execute("""
        SELECT mc.*, tm.tipo, tm.nombre AS nombre_movimiento
        FROM Movimiento_de_caja mc
        JOIN Tipo_de_movimiento tm ON mc.ID_Tipo_movimiento = tm.ID_Tipo_movimiento
        WHERE mc.ID_Reunion = %s
        ORDER BY mc.fecha ASC, mc.ID_Movimiento_caja ASC
    """, (id_reunion,))

    movimientos = cursor.fetchall()

    if not movimientos:
        st.info("No hay movimientos cargados todavía.")
        return

    st.write("**Saldo Inicial:**", f"${saldo_anterior:,.2f}")
    st.divider()

    for mov in movimientos:
        st.write(f"**{mov['descripcion']}** — {mov['tipo']} — ${mov['monto']:,.2f} — 💰 {mov['saldo_final']:,.2f}")
        st.caption(f"📅 {mov['fecha']} — {mov['nombre_movimiento']}")
        st.divider()


# =====================================================================================
#  EJECUTABLE
# =====================================================================================

def main():
    mostrar_movimiento_caja()

if __name__ == "__main__":
    main()
