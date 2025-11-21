# pagoprestamo.py
import streamlit as st
from modulos.config.conexion import obtener_conexion
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta  # pip install python-dateutil
import pandas as pd

st.set_page_config(layout="wide")

def fecha_siguiente_mes(fecha, dia_original):
    """Devuelve fecha un mes después intentando mantener dia_original; si no posible, último día del mes."""
    sig = fecha + relativedelta(months=1)
    try:
        return sig.replace(day=dia_original)
    except Exception:
        # último día del mes
        ultimo = (sig.replace(day=1) + relativedelta(months=1) - timedelta(days=1)).day
        return sig.replace(day=ultimo)

def calcular_cuota_simple(principal: float, tasa_mensual_pct: float, meses: int) -> float:
    """Usa el método simple que tienes: interés mensual fijo = principal * tasa, interés_total = interes_mensual * meses,
       cuota = (principal + interes_total) / meses."""
    if meses <= 0:
        return 0.0
    tasa_decimal = tasa_mensual_pct / 100.0
    interes_mensual = principal * tasa_decimal
    interes_total = interes_mensual * meses
    cuota = (principal + interes_total) / meses
    return round(cuota, 2)

def mostrar_pago_prestamo():
    st.header("💵 Registro Inteligente de Pago de Préstamo (recalcula cuota)")

    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)

        # CARGAR PRÉSTAMOS (con datos necesarios)
        cursor.execute("""
            SELECT ID_Prestamo, ID_Miembro, fecha_desembolso, monto, total_interes AS tasa_mensual, plazo
            FROM Prestamo
        """)
        prestamos = cursor.fetchall()

        if not prestamos:
            st.warning("⚠️ No hay préstamos registrados.")
            return

        prestamos_dict = {
            f"Préstamo {p['ID_Prestamo']} - Miembro {p['ID_Miembro']} - ${float(p['monto']):.2f}": p['ID_Prestamo']
            for p in prestamos
        }

        prestamo_sel = st.selectbox("Selecciona el préstamo:", list(prestamos_dict.keys()))
        id_prestamo = prestamos_dict[prestamo_sel]

        # obtener detalles del préstamo seleccionado
        cursor.execute("""
            SELECT ID_Prestamo, ID_Miembro, fecha_desembolso, monto, total_interes AS tasa_mensual, plazo
            FROM Prestamo WHERE ID_Prestamo = %s
        """, (id_prestamo,))
        prestamo = cursor.fetchone()
        if not prestamo:
            st.error("Prestamo no encontrado.")
            return

        monto = float(prestamo['monto'])
        tasa_mensual = float(prestamo['tasa_mensual'])  # en % según tu esquema
        plazo = int(prestamo['plazo'])
        fecha_desembolso = prestamo['fecha_desembolso']
        dia_pago = fecha_desembolso.day if hasattr(fecha_desembolso, 'day') else int(str(fecha_desembolso).split('-')[-1])

        # calcular cuota original (tal como en tu módulo de registro)
        cuota_original = calcular_cuota_simple(monto, tasa_mensual, plazo)
        st.subheader("Resumen del préstamo")
        st.write(f"- Monto: **${monto:,.2f}**")
        st.write(f"- Tasa mensual: **{tasa_mensual:.2f}%**")
        st.write(f"- Plazo: **{plazo} meses**")
        st.write(f"- Cuota original (aprox): **${cuota_original:,.2f}**")

        # CARGAR CRONOGRAMA desde CuotaPrestamo
        cursor.execute("""
            SELECT ID_Cuota, numero_cuota, fecha_programada, capital_programado, interes_programado,
                   total_programado, capital_pagado, interes_pagado, total_pagado, estado
            FROM CuotaPrestamo
            WHERE ID_Prestamo = %s
            ORDER BY numero_cuota
        """, (id_prestamo,))
        filas = cursor.fetchall()

        if not filas:
            st.info("No hay cuotas generadas para este préstamo. (Si acabas de registrar el préstamo, revisa que la generación automática de cuotas se ejecutó.)")
            return

        # Mostrar cronograma en tabla
        df = pd.DataFrame(filas)
        # asegurarse de tipos
        df['fecha_programada'] = pd.to_datetime(df['fecha_programada']).dt.date
        df_display = df.rename(columns={
            "ID_Cuota":"ID",
            "numero_cuota":"N°",
            "fecha_programada":"Fecha",
            "capital_programado":"Capital prog.",
            "interes_programado":"Interés prog.",
            "total_programado":"Total prog.",
            "capital_pagado":"Capital pagado",
            "interes_pagado":"Interés pagado",
            "total_pagado":"Total pagado",
            "estado":"Estado"
        })[["ID","N°","Fecha","Capital prog.","Interés prog.","Total prog.","Capital pagado","Interés pagado","Total pagado","Estado"]]

        st.subheader("Cronograma de cuotas (tabla)")
        st.dataframe(df_display.style.format({
            "Capital prog.": "${:,.2f}",
            "Interés prog.": "${:,.2f}",
            "Total prog.": "${:,.2f}",
            "Capital pagado": "${:,.2f}",
            "Interés pagado": "${:,.2f}",
            "Total pagado": "${:,.2f}"
        }), height=350)

        # Mostrar resumen de saldos
        total_pagado_capital = float(df["capital_pagado"].sum())
        total_pagado_interes = float(df["interes_pagado"].sum())
        capital_programado_total = float(df["capital_programado"].sum())
        interes_programado_total = float(df["interes_programado"].sum())
        total_pagado = float(df["total_pagado"].sum())
        capital_restante = round(monto - total_pagado_capital, 2)
        meses_restantes = int((df[df['estado'] != 'pagado'].shape[0]))

        st.markdown("---")
        st.subheader("Saldos actuales")
        st.write(f"- Capital pagado: **${total_pagado_capital:,.2f}**")
        st.write(f"- Interés pagado: **${total_pagado_interes:,.2f}**")
        st.write(f"- Capital restante: **${capital_restante:,.2f}**")
        st.write(f"- Cuotas pendientes: **{meses_restantes}**")

        if meses_restantes > 0:
            nueva_cuota_sugerida = calcular_cuota_simple(capital_restante, tasa_mensual, meses_restantes)
            st.write(f"- Nueva cuota sugerida (si recalculamos ahora): **${nueva_cuota_sugerida:,.2f}**")
        else:
            st.write("- El préstamo parece estar completamente pagado.")

        st.markdown("---")
        st.subheader("Registrar abono / pago (se aplicará automáticamente a interés y capital)")

        with st.form("form_pago"):
            st.write("Puedes seleccionar una cuota para aplicar el pago manualmente; si no, el sistema aplicará al primer pendiente.")
            # construir options con id y descripción
            opciones_cuotas = []
            for r in filas:
                estado = r['estado']
                total_prog = float(r['total_programado'])
                total_pag = float(r['total_pagado'])
                pendiente = round(total_prog - total_pag, 2)
                opciones_cuotas.append((r['ID_Cuota'], f"N°{r['numero_cuota']} - {r['fecha_programada']} - Pendiente ${pendiente:.2f} - {estado}"))

            opciones_map = {desc: idx for idx, (_, desc) in enumerate(opciones_cuotas)}
            opcion_selec = st.selectbox("Aplicar a cuota (opcional):", ["(Aplicar al primer pendiente)"] + [desc for _, desc in opciones_cuotas])
            monto_abono = st.number_input("Monto a abonar ahora ($):", min_value=0.00, format="%.2f")
            fecha_abono = st.date_input("Fecha de pago:", value=date.today())

            enviar = st.form_submit_button("Registrar abono inteligente")

            if enviar:
                if monto_abono <= 0:
                    st.warning("⚠️ Ingresa monto mayor que 0.")
                else:
                    try:
                        monto_disp = float(monto_abono)
                        total_capital_pagado_en_abono = 0.0
                        total_interes_pagado_en_abono = 0.0

                        # definir lista de cuotas pendientes en orden (a partir de la cuota seleccionada o primer pendiente)
                        # obtener filas actuales (refrescar por seguridad)
                        cursor.execute("""
                            SELECT ID_Cuota, numero_cuota, fecha_programada, capital_programado, interes_programado,
                                   total_programado, capital_pagado, interes_pagado, total_pagado, estado
                            FROM CuotaPrestamo
                            WHERE ID_Prestamo = %s
                            ORDER BY numero_cuota
                        """, (id_prestamo,))
                        filas_actual = cursor.fetchall()

                        # elegir índice de inicio
                        start_idx = 0
                        if opcion_selec != "(Aplicar al primer pendiente)":
                            # encontrar el ID a partir de la descripción seleccionada
                            selected_desc = opcion_selec
                            # localizar índice
                            for idx, f in enumerate(filas_actual):
                                estado = f['estado']
                                pendiente = round(float(f['total_programado']) - float(f['total_pagado']), 2)
                                desc = f"N°{f['numero_cuota']} - {f['fecha_programada']} - Pendiente ${pendiente:.2f} - {estado}"
                                if desc == selected_desc:
                                    start_idx = idx
                                    break
                        else:
                            # primer pendiente
                            for idx, f in enumerate(filas_actual):
                                if f['estado'] != 'pagado':
                                    start_idx = idx
                                    break

                        # aplicar pago secuencialmente sobre cuotas desde start_idx
                        idx = start_idx
                        any_update = False
                        while monto_disp > 0 and idx < len(filas_actual):
                            fila = filas_actual[idx]
                            id_cuota = fila['ID_Cuota']
                            estado = fila['estado']
                            total_prog = float(fila['total_programado'])
                            capital_prog = float(fila['capital_programado'])
                            interes_prog = float(fila['interes_programado'])
                            capital_pag = float(fila['capital_pagado'])
                            interes_pag = float(fila['interes_pagado'])
                            total_pag = float(fila['total_pagado'])

                            pendiente_total = round(total_prog - total_pag, 10)
                            if pendiente_total <= 0:
                                idx += 1
                                continue

                            # interés pendiente en esta cuota
                            interes_pend = round(interes_prog - interes_pag, 10)
                            if interes_pend < 0:
                                interes_pend = 0.0

                            # primero pagar interés pendiente
                            pagar_interes = min(monto_disp, interes_pend)
                            interes_pag_n = round(interes_pag + pagar_interes, 2)
                            monto_disp = round(monto_disp - pagar_interes, 2)
                            total_interes_pagado_en_abono += pagar_interes

                            # luego pagar capital pendiente
                            capital_pend = round(capital_prog - capital_pag, 10)
                            pagar_capital = min(monto_disp, capital_pend)
                            capital_pag_n = round(capital_pag + pagar_capital, 2)
                            monto_disp = round(monto_disp - pagar_capital, 2)
                            total_capital_pagado_en_abono += pagar_capital

                            total_pag_n = round(float(total_pag) + pagar_interes + pagar_capital, 2)

                            # determinar nuevo estado
                            if round(total_pag_n,2) >= round(total_prog,2):
                                nuevo_estado = 'pagado'
                            elif round(total_pag_n,2) > 0:
                                nuevo_estado = 'parcial'
                            else:
                                nuevo_estado = 'pendiente'

                            # actualizar esta cuota
                            cursor.execute("""
                                UPDATE CuotaPrestamo
                                SET capital_pagado = %s, interes_pagado = %s, total_pagado = %s, estado = %s
                                WHERE ID_Cuota = %s
                            """, (capital_pag_n, interes_pag_n, total_pag_n, nuevo_estado, id_cuota))
                            any_update = True

                            # si quedó parcial, mover fecha_programada de esta cuota al siguiente mes desde fecha_abono
                            if nuevo_estado == 'parcial':
                                # conservar dia original si es posible
                                dia_original = fila['fecha_programada'].day if hasattr(fila['fecha_programada'], 'day') else int(str(fila['fecha_programada']).split('-')[-1])
                                nueva_fecha = fecha_siguiente_mes(fecha_abono, dia_original)
                                cursor.execute("""
                                    UPDATE CuotaPrestamo SET fecha_programada = %s WHERE ID_Cuota = %s
                                """, (nueva_fecha, id_cuota))
                                # reprogramaremos las siguientes cuotas en cadena más abajo

                            idx += 1

                        # registrar en PagoPrestamo (registro general del abono)
                        cursor.execute("""
                            INSERT INTO PagoPrestamo
                            (ID_Prestamo, ID_Reunion, fecha_pago, monto_capital, monto_interes, total_cancelado)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (id_prestamo, None, fecha_abono, round(total_capital_pagado_en_abono,2), round(total_interes_pagado_en_abono,2), float(monto_abono) - monto_disp))
                        # nota: puse ID_Reunion = NULL; si quieres vincular añade selector de reuniones arriba

                        # Si actualizamos alguna cuota y hay cuotas pendientes, recalcular nueva cuota para las pendientes
                        # Recalcular capital pendiente actual (sum de capital_programado - capital_pagado)
                        cursor.execute("""
                            SELECT SUM(capital_programado - capital_pagado) AS capital_restante
                            FROM CuotaPrestamo
                            WHERE ID_Prestamo = %s
                        """, (id_prestamo,))
                        res = cursor.fetchone()
                        capital_restante_db = float(res['capital_restante'] or 0.0)

                        # contar cuotas pendientes
                        cursor.execute("""
                            SELECT COUNT(*) AS cnt FROM CuotaPrestamo
                            WHERE ID_Prestamo = %s AND estado != 'pagado'
                        """, (id_prestamo,))
                        cnt_res = cursor.fetchone()
                        cuotas_pendientes = int(cnt_res['cnt'] or 0)

                        if cuotas_pendientes > 0 and capital_restante_db > 0:
                            # nueva cuota con método simple
                            nueva_cuota = calcular_cuota_simple(capital_restante_db, tasa_mensual, cuotas_pendientes)
                            interes_mensual_n = round(capital_restante_db * (tasa_mensual/100.0), 2)
                            # actualizar las cuotas pendientes en orden:
                            # buscamos la primer cuota pendiente (por numero_cuota)
                            cursor.execute("""
                                SELECT ID_Cuota, numero_cuota, fecha_programada
                                FROM CuotaPrestamo
                                WHERE ID_Prestamo = %s AND estado != 'pagado'
                                ORDER BY numero_cuota
                            """, (id_prestamo,))
                            pendientes = cursor.fetchall()

                            # reprogramar fechas en cadena: si existe una cuota parcial que fue movida, iniciamos desde su fecha_programada; si no, iniciamos desde la fecha_programada original de la primer pendiente
                            fecha_inicio_programacion = None
                            # verificar si hay alguna cuota parcial (podría haber sido movida)
                            for p in pendientes:
                                cursor.execute("SELECT estado, fecha_programada FROM CuotaPrestamo WHERE ID_Cuota = %s", (p['ID_Cuota'],))
                                check = cursor.fetchone()
                                if check and check['estado'] == 'parcial':
                                    fecha_inicio_programacion = check['fecha_programada']
                                    break
                            if fecha_inicio_programacion is None:
                                # usar la fecha_programada de la primer pendiente
                                fecha_inicio_programacion = pendientes[0]['fecha_programada']

                            # aplicar nueva programación
                            cap_rest = capital_restante_db
                            fecha_p = fecha_inicio_programacion
                            for idx_p, p in enumerate(pendientes, start=1):
                                idc = p['ID_Cuota']
                                # para cada cuota calculamos interes mensual (fijo) y capital por cuota
                                interes_prog_n = round(capital_restante_db * (tasa_mensual/100.0), 2)
                                capital_prog_n = round(nueva_cuota - interes_prog_n, 2)
                                # en la última cuota ajustar para evitar residuo por redondeo
                                if idx_p == len(pendientes):
                                    capital_prog_n = round(cap_rest, 2)
                                    total_prog_n = round(capital_prog_n + interes_prog_n, 2)
                                else:
                                    total_prog_n = round(capital_prog_n + interes_prog_n, 2)

                                nuevo_cap_rest = round(cap_rest - capital_prog_n, 2)

                                cursor.execute("""
                                    UPDATE CuotaPrestamo
                                    SET cuota_programada = %s, -- si tu tabla no tiene cuota_programada puedes ignorar este campo
                                        capital_programado = %s, interes_programado = %s, total_programado = %s,
                                        fecha_programada = %s
                                    WHERE ID_Cuota = %s
                                """, (nueva_cuota, capital_prog_n, interes_prog_n, total_prog_n, fecha_p, idc))

                                cap_rest = nuevo_cap_rest
                                # siguiente fecha: un mes después manteniendo día
                                dia_or = fecha_p.day if hasattr(fecha_p, 'day') else int(str(fecha_p).split('-')[-1])
                                fecha_p = fecha_siguiente_mes(fecha_p, dia_or)

                        # commit de todas las operaciones
                        con.commit()
                        st.success("✅ Abono registrado y cuotas recalculadas correctamente.")
                        st.experimental_rerun()

                    except Exception as e:
                        con.rollback()
                        st.error(f"❌ Error al registrar el abono: {e}")

    except Exception as e:
        st.error(f"❌ Error general: {e}")

    finally:
        if "cursor" in locals():
            cursor.close()
        if "con" in locals():
            con.close()

if __name__ == "__main__":
    mostrar_pago_prestamo()
