# modulos/pagoprestamo.py
import streamlit as st
from modulos.config.conexion import obtener_conexion
from datetime import date, datetime

# ----------------------
# UTILIDADES FINANCIERAS
# ----------------------
def add_months(dt: date, months: int) -> date:
    """Suma 'months' meses manteniendo día en lo posible (evita 29-31 tomando 28 como tope)."""
    year = dt.year + (dt.month - 1 + months) // 12
    month = (dt.month - 1 + months) % 12 + 1
    day = min(dt.day, 28)
    return date(year, month, day)

def mensual_payment(principal: float, monthly_rate: float, n_months: int) -> float:
    """
    Calcula la cuota mensual por fórmula de amortización (método francés).
    Si monthly_rate == 0 => simple división.
    Resultados redondeados a 2 decimales.
    """
    principal = float(principal)
    if n_months <= 0:
        return round(principal, 2)
    if monthly_rate == 0:
        # dividir capital entre meses restantes
        return round(principal / n_months, 2)
    r = float(monthly_rate)
    # A = P * r / (1 - (1+r)^-n)
    A = principal * r / (1 - (1 + r) ** (-n_months))
    return round(A, 2)

# ----------------------
# CONSULTAS / HELPERS
# ----------------------
def fetch_prestamos(cursor):
    """
    Trae préstamos con campos esperados:
    ID_Prestamo, ID_Miembro, fecha_desembolso, monto, total_interes, ID_Estado_prestamo, plazo, proposito
    """
    cursor.execute("""
        SELECT ID_Prestamo, ID_Miembro, fecha_desembolso, monto, total_interes, ID_Estado_prestamo, plazo, proposito
        FROM Prestamo
        ORDER BY ID_Prestamo DESC
    """)
    return cursor.fetchall()

def fetch_cuotas(cursor, id_prestamo):
    cursor.execute("""
        SELECT ID_Cuota, numero_cuota, fecha_programada, capital_programado, interes_programado, total_programado,
               capital_pagado, interes_pagado, total_pagado, estado
        FROM CuotaPrestamo
        WHERE ID_Prestamo = %s
        ORDER BY numero_cuota
    """, (id_prestamo,))
    return cursor.fetchall()

def fetch_pagos(cursor, id_prestamo):
    cursor.execute("""
        SELECT ID_Pago, ID_Reunion, fecha_pago, monto_capital, monto_interes, total_cancelado
        FROM PagoPrestamo
        WHERE ID_Prestamo = %s
        ORDER BY fecha_pago
    """, (id_prestamo,))
    return cursor.fetchall()

def saldo_actual_desde_pagos(cursor, id_prestamo, monto_original):
    """
    Calcula el saldo actual (principal restante) como monto_original - suma(monto_capital pagado).
    """
    cursor.execute("SELECT IFNULL(SUM(monto_capital),0) FROM PagoPrestamo WHERE ID_Prestamo = %s", (id_prestamo,))
    suma_capital = cursor.fetchone()[0] or 0.0
    saldo = round(float(monto_original) - float(suma_capital), 2)
    return max(0.0, saldo)

def obtener_tasa_mensual_aproximada(cursor, id_prestamo):
    """
    Calcula una tasa mensual aproximada a partir del campo total_interes almacenado en Prestamo,
    asumiendo total_interes = suma de intereses por mes = tasa_mensual * monto * plazo.
    Si el campo 'total_interes' representa una tasa en vez de monto, intentamos interpretarlo también.
    """
    cursor.execute("SELECT total_interes, monto, plazo FROM Prestamo WHERE ID_Prestamo = %s", (id_prestamo,))
    row = cursor.fetchone()
    if not row:
        return 0.0
    total_interes, monto, plazo = row
    try:
        monto = float(monto)
        plazo = int(plazo) if plazo else 1
        # si total_interes parece una tasa (valor entre 0 y 1 usualmente), interpretarlo como tasa anual/periodo
        total_interes_f = float(total_interes) if total_interes is not None else 0.0
    except Exception:
        return 0.0

    # Heurística:
    # Si total_interes <= 1.5 asumimos que es tasa (ej 0.05) -> esa es la tasa mensual
    # Si total_interes > 1.5 asumimos que es monto total de intereses -> tasa_mensual = total_interes / (monto * plazo)
    if total_interes_f <= 1.5:
        # ya es tasa mensual o fraccional; aseguremos no negativa
        return max(0.0, total_interes_f)
    else:
        # tasa aproximada por periodo
        if monto <= 0 or plazo <= 0:
            return 0.0
        tasa = total_interes_f / (monto * plazo)
        return max(0.0, round(tasa, 8))

# ----------------------
# GENERAR CRONOGRAMA (CuotaPrestamo)
# ----------------------
def generar_cronograma_si_no_existe(cursor, con, id_prestamo, monto, tasa_mensual, plazo_meses, fecha_inicio, cuota_guardada=None, dia_mantener=10):
    """
    Genera filas en CuotaPrestamo si NO existen ya cuotas para ese préstamo.
    - cuota_guardada: si Prestamo contiene una cuota fija, se usa.
    - dia_mantener: si quieres mantener día específico (p.ej. 10), se procura usarlo.
    """
    cursor.execute("SELECT COUNT(*) FROM CuotaPrestamo WHERE ID_Prestamo = %s", (id_prestamo,))
    existe = cursor.fetchone()[0] or 0
    if existe > 0:
        return  # ya hay cronograma

    # Determinar fecha base: si fecha_inicio tiene día, usamos ese día; si no, usamos dia_mantener
    if fecha_inicio:
        base = fecha_inicio
    else:
        base = date.today()

    # preferir mantener día especificado (por ejemplo 10)
    base_day = base.day if base.day <= 28 else min(28, base.day)
    # crear cuotas 1..plazo_meses
    saldo_temp = float(monto)
    # cuota inicial: si cuota_guardada no es None y >0, usarla; sino calcular a partir de principal y tasa
    cuota_inicial = cuota_guardada if cuota_guardada and cuota_guardada > 0 else mensual_payment(saldo_temp, tasa_mensual, plazo_meses)

    for n in range(1, int(plazo_meses) + 1):
        fecha_prog = add_months(base, n)
        # ajustar día para mantener día_base si es posible
        try:
            fecha_prog = fecha_prog.replace(day=base_day)
        except Exception:
            fecha_prog = fecha_prog  # si falla, ya es segura (día <=28)
        interes_prog = round(saldo_temp * tasa_mensual, 2)
        capital_prog = round(cuota_inicial - interes_prog, 2)
        if capital_prog < 0:
            capital_prog = 0.0
        total_prog = round(capital_prog + interes_prog, 2)

        cursor.execute("""
            INSERT INTO CuotaPrestamo
            (ID_Prestamo, numero_cuota, fecha_programada, capital_programado, interes_programado, total_programado)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (id_prestamo, n, fecha_prog, capital_prog, interes_prog, total_prog))

        saldo_temp = round(max(0.0, saldo_temp - capital_prog), 2)

    con.commit()

# ----------------------
# RECALCULAR CUOTAS RESTANTES
# ----------------------
def recalcular_cuotas_desde(cursor, con, id_prestamo, saldo_actual, proximo_numero, cuotas_restantes, fecha_base):
    """
    Re-genera (elimina y vuelve a insertar) cuotas a partir de 'proximo_numero' por 'cuotas_restantes'
    usando 'saldo_actual' como principal. Mantiene el mismo día de fecha_base.
    """
    if cuotas_restantes <= 0:
        return
    # eliminar cuotas pendientes a partir de proximo_numero
    cursor.execute("DELETE FROM CuotaPrestamo WHERE ID_Prestamo = %s AND numero_cuota >= %s", (id_prestamo, proximo_numero))
    con.commit()

    tasa_mensual = obtener_tasa_mensual_aproximada(cursor, id_prestamo)
    nueva_cuota = mensual_payment(saldo_actual, tasa_mensual, cuotas_restantes)

    saldo_temp = saldo_actual
    for i in range(cuotas_restantes):
        numero = proximo_numero + i
        fecha_prog = add_months(date.today(), numero - 1)  # generamos fechas relativas a hoy; esto lo puedes ajustar
        interes_prog = round(saldo_temp * tasa_mensual, 2)
        capital_prog = round(nueva_cuota - interes_prog, 2)
        if capital_prog < 0:
            capital_prog = 0.0
        total_prog = round(capital_prog + interes_prog, 2)

        cursor.execute("""
            INSERT INTO CuotaPrestamo
            (ID_Prestamo, numero_cuota, fecha_programada, capital_programado, interes_programado, total_programado)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (id_prestamo, numero, fecha_prog, capital_prog, interes_prog, total_prog))
        saldo_temp = round(max(0.0, saldo_temp - capital_prog), 2)

    con.commit()

# ----------------------
# LÓGICA DE APLICAR PAGO A CUOTA
# ----------------------
def aplicar_abono_a_cuota(cursor, con, id_prestamo, id_cuota, monto_abono, fecha_pago, id_reunion=None):
    """
    Aplica monto_abono a la cuota identificada por id_cuota:
    - Primero cubre interes pendiente (interes_programado - interes_pagado)
    - Luego cubre capital pendiente (capital_programado - capital_pagado)
    - Actualiza CuotaPrestamo (capital_pagado, interes_pagado, total_pagado, estado)
    - Inserta registro en PagoPrestamo
    - Devuelve dict con info del resultado {'capital_pagado_now', 'interes_pagado_now', 'interes_no_cubierto', 'nuevo_estado', 'nuevo_saldo'}
    """
    # traer cuota
    cursor.execute("""
        SELECT ID_Cuota, numero_cuota, fecha_programada, capital_programado, interes_programado, total_programado,
               capital_pagado, interes_pagado, total_pagado, estado
        FROM CuotaPrestamo
        WHERE ID_Cuota = %s AND ID_Prestamo = %s
        LIMIT 1
    """, (id_cuota, id_prestamo))
    fila = cursor.fetchone()
    if not fila:
        raise ValueError("Cuota no encontrada.")

    # desempaquetar
    (_, numero_cuota, fecha_programada, capital_prog, interes_prog, total_prog,
     capital_pagado_prev, interes_pagado_prev, total_pagado_prev, estado_prev) = fila

    capital_prog = float(capital_prog)
    interes_prog = float(interes_prog)
    capital_pagado_prev = float(capital_pagado_prev or 0.0)
    interes_pagado_prev = float(interes_pagado_prev or 0.0)

    # pendientes
    interes_pendiente = round(max(0.0, interes_prog - interes_pagado_prev), 2)
    capital_pendiente = round(max(0.0, capital_prog - capital_pagado_prev), 2)

    restante = round(float(monto_abono), 2)
    interes_pagado_now = 0.0
    capital_pagado_now = 0.0
    interes_no_cubierto = 0.0

    # cubrir interés pendiente primero
    if restante <= 0:
        pass
    else:
        if restante >= interes_pendiente:
            interes_pagado_now = interes_pendiente
            restante = round(restante - interes_pendiente, 2)
        else:
            # paga parcialmente interés -> capital no se toca, interés no cubierto será capitalizado
            interes_pagado_now = restante
            interes_no_cubierto = round(interes_pendiente - interes_pagado_now, 2)
            restante = 0.0

    # cubrir capital pendiente con lo que quede
    if restante > 0:
        if restante >= capital_pendiente:
            capital_pagado_now = capital_pendiente
            restante = round(restante - capital_pendiente, 2)
        else:
            capital_pagado_now = restante
            restante = 0.0

    # insertar en PagoPrestamo (registro del abono)
    try:
        cursor.execute("""
            INSERT INTO PagoPrestamo
            (ID_Prestamo, ID_Reunion, fecha_pago, monto_capital, monto_interes, total_cancelado)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (id_prestamo, id_reunion, fecha_pago, capital_pagado_now, interes_pagado_now, monto_abono))
        con.commit()
    except Exception as e:
        con.rollback()
        raise

    # actualizar la cuota con los nuevos pagos
    nuevo_capital_pagado = round(capital_pagado_prev + capital_pagado_now, 2)
    nuevo_interes_pagado = round(interes_pagado_prev + interes_pagado_now, 2)
    nuevo_total_pagado = round((total_pagado_prev or 0.0) + monto_abono, 2)

    # determinar nuevo estado
    nuevo_estado = 'pendiente'
    if round(nuevo_capital_pagado, 2) >= round(capital_prog, 2) and round(nuevo_interes_pagado, 2) >= round(interes_prog, 2):
        nuevo_estado = 'pagado'
    elif (round(nuevo_capital_pagado, 2) > 0) or (round(nuevo_interes_pagado, 2) > 0):
        nuevo_estado = 'parcial'

    cursor.execute("""
        UPDATE CuotaPrestamo
        SET capital_pagado = %s, interes_pagado = %s, total_pagado = %s, estado = %s, total_programado = %s
        WHERE ID_Cuota = %s
    """, (nuevo_capital_pagado, nuevo_interes_pagado, nuevo_total_pagado, nuevo_estado, total_prog, id_cuota))
    con.commit()

    # calcular nuevo saldo del préstamo (principal restante)
    cursor.execute("SELECT monto FROM Prestamo WHERE ID_Prestamo = %s", (id_prestamo,))
    monto_original = float(cursor.fetchone()[0] or 0.0)
    cursor.execute("SELECT IFNULL(SUM(monto_capital),0) FROM PagoPrestamo WHERE ID_Prestamo = %s", (id_prestamo,))
    suma_capital_pagado = float(cursor.fetchone()[0] or 0.0)
    nuevo_saldo = round(max(0.0, monto_original - suma_capital_pagado), 2)

    return {
        "capital_pagado_now": capital_pagado_now,
        "interes_pagado_now": interes_pagado_now,
        "interes_no_cubierto": interes_no_cubierto,
        "nuevo_estado": nuevo_estado,
        "nuevo_saldo": nuevo_saldo,
        "restante_abono_no_aplicado": restante
    }

# ----------------------
# INTERFAZ STREAMLIT
# ----------------------
def mostrar_pago_prestamo():
    st.header("💵 Registro de Pago de Préstamo")

    try:
        con = obtener_conexion()
        cursor = con.cursor()

        prestamos = fetch_prestamos(cursor)
        if not prestamos:
            st.warning("No hay préstamos registrados.")
            return

        # selector de préstamo
        opciones = { f"ID {p[0]} - Miembro {p[1]} - ${float(p[3]):,.2f}" : p for p in prestamos }
        seleccionado_lbl = st.selectbox("Selecciona un préstamo:", list(opciones.keys()))
        prestamo = opciones[seleccionado_lbl]

        ID_Prestamo = prestamo[0]
        ID_Miembro = prestamo[1]
        fecha_desembolso = prestamo[2] or date.today()
        monto_original = float(prestamo[3])
        total_interes = float(prestamo[4]) if prestamo[4] is not None else 0.0
        plazo = int(prestamo[6]) if prestamo[6] is not None else 0

        # tasa aproximada
        tasa_mensual = obtener_tasa_mensual_aproximada(cursor, ID_Prestamo)

        # generar cronograma si no existe
        generar_cronograma_si_no_existe(cursor, con, ID_Prestamo, monto_original, tasa_mensual, plazo, fecha_desembolso)

        # mostrar resumen
        st.subheader("Resumen del préstamo")
        st.markdown(f"- **Monto original:** ${monto_original:,.2f}")
        st.markdown(f"- **Plazo (meses):** {plazo}")
        st.markdown(f"- **Tasa mensual (aprox):** {tasa_mensual*100:.3f}%")

        # saldo actual
        saldo = saldo_actual_desde_pagos(cursor, ID_Prestamo, monto_original)
        st.markdown(f"- **Saldo actual (principal):** ${saldo:,.2f}")

        # mostrar pagos previos
        pagos_prev = fetch_pagos(cursor, ID_Prestamo)
        if pagos_prev:
            st.markdown("#### Pagos registrados")
            for p in pagos_prev:
                idp, id_reu, fecha_pago, monto_cap, monto_int, total = p
                st.write(f"- {fecha_pago} — Capital: ${float(monto_cap):.2f} — Interés: ${float(monto_int):.2f} — Total: ${float(total):.2f}")

        st.markdown("---")

        # mostrar cronograma
        st.subheader("Cronograma (Cuotas)")
        cuotas = fetch_cuotas(cursor, ID_Prestamo)
        if not cuotas:
            st.info("No se encontraron cuotas para este préstamo.")
        else:
            # encabezados
            c0, c1, c2, c3, c4, c5, c6 = st.columns([1,2,2,2,2,2,1])
            c0.markdown("**N**")
            c1.markdown("**Fecha**")
            c2.markdown("**Cuota (T)**")
            c3.markdown("**Interés prog.**")
            c4.markdown("**Capital prog.**")
            c5.markdown("**Pagado (cap/int)**")
            c6.markdown("**Estado**")
            for row in cuotas:
                idc, numero, fecha_prog, cap_prog, int_prog, tot_prog, cap_pag, int_pag, tot_pag, estado = row
                r0, r1, r2, r3, r4, r5, r6 = st.columns([1,2,2,2,2,2,1])
                r0.write(numero)
                r1.write(str(fecha_prog))
                r2.write(f"${float(tot_prog):.2f}")
                r3.write(f"${float(int_prog):.2f}")
                r4.write(f"${float(cap_prog):.2f}")
                r5.write(f"${float(cap_pag):.2f} / ${float(int_pag):.2f}")
                r6.write(estado)

        st.markdown("---")

        # Registrar abono
        st.subheader("Registrar abono / pago parcial")
        # cuote pendientes para seleccionar
        pendientes = [c for c in cuotas if c[9] != 'pagado']
        opciones_venc = { f"#{c[1]} • {c[2]} • ${float(c[5]):.2f} • {c[9]}": c for c in pendientes }

        if not opciones_venc:
            st.info("No hay cuotas pendientes para este préstamo.")
            return

        venc_label = st.selectbox("Selecciona cuota pendiente:", list(opciones_venc.keys()))
        cuota_obj = opciones_venc[venc_label]
        id_cuota_sel = cuota_obj[0]
        numero_cuota_sel = cuota_obj[1]
        fecha_cuota_sel = cuota_obj[2]
        total_prog_sel = float(cuota_obj[5])

        st.write(f"Cuota #{numero_cuota_sel} — Fecha: {fecha_cuota_sel} — Total programado: ${total_prog_sel:.2f}")

        monto_abono = st.number_input("Monto a abonar ahora:", min_value=0.0, value=0.0, format="%.2f")
        fecha_pago = st.date_input("Fecha del pago:", value=date.today())
        # lista de reuniones opcional
        cursor.execute("SELECT ID_Reunion, fecha FROM Reunion ORDER BY fecha DESC")
        reuniones = cursor.fetchall()
        reuniones_opts = ["Ninguna"] + [f"{r[0]} - {r[1]}" for r in reuniones]
        id_reunion_sel = st.selectbox("Reunión asociada (opcional):", reuniones_opts)

        if st.button("Registrar abono"):
            if monto_abono <= 0:
                st.warning("Ingresa un monto mayor a 0.")
            else:
                id_reu_val = None
                if isinstance(id_reunion_sel, str) and id_reunion_sel != "Ninguna":
                    try:
                        id_reu_val = int(id_reunion_sel.split(" - ")[0])
                    except:
                        id_reu_val = None

                try:
                    resultado = aplicar_abono_a_cuota(cursor, con, ID_Prestamo, id_cuota_sel, monto_abono, fecha_pago, id_reu_val)
                except Exception as e:
                    st.error(f"Error registrando abono: {e}")
                    return

                # después de aplicar el abono, recalcular cuotas restantes si necesario
                nuevo_saldo = resultado["nuevo_saldo"]
                # contar cuotas pagadas y totales
                cursor.execute("SELECT COUNT(*) FROM CuotaPrestamo WHERE ID_Prestamo = %s AND estado = 'pagado'", (ID_Prestamo,))
                cuotas_pagadas = int(cursor.fetchone()[0] or 0)
                cuotas_totales = int(plazo) if plazo else 0
                cuotas_restantes = max(cuotas_totales - cuotas_pagadas, 0)

                # proximo numero: primer cuota pendiente
                cursor.execute("SELECT MIN(numero_cuota) FROM CuotaPrestamo WHERE ID_Prestamo = %s AND estado != 'pagado'", (ID_Prestamo,))
                res = cursor.fetchone()
                proximo_num = int(res[0]) if res and res[0] is not None else (cuotas_pagadas + 1)

                if cuotas_restantes > 0 and nuevo_saldo > 0:
                    # recalcular desde proximo_num usando nuevo_saldo y cuotas_restantes
                    recalcular_cuotas_desde(cursor, con, ID_Prestamo, nuevo_saldo, proximo_num, cuotas_restantes, fecha_desembolso)
                    st.success("Abono registrado y cuotas restantes recalculadas.")
                else:
                    st.success("Abono registrado.")

                st.experimental_rerun()

    except Exception as e:
        st.error(f"❌ Error: {e}")

    finally:
        try:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'con' in locals() and con:
                con.close()
        except:
            pass
