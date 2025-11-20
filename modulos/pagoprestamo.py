import streamlit as st
from modulos.config.conexion import obtener_conexion
from datetime import date

def mostrar_pago_prestamo():
    st.header("💵 Registro de Pago de Préstamo")

    try:
        con = obtener_conexion()
        cursor = con.cursor()

        # ------------------------------------------
        # CARGAR PRÉSTAMOS EXISTENTES
        # ------------------------------------------
        cursor.execute("""
            SELECT ID_Prestamo, ID_Miembro, monto
            FROM Prestamo
        """)
        prestamos = cursor.fetchall()

        if not prestamos:
            st.warning("⚠️ No hay préstamos registrados.")
            return

        prestamos_dict = {
            f"Préstamo {p[0]} - Miembro {p[1]} - ${p[2]}": p[0]
            for p in prestamos
        }

        # ------------------------------------------
        # CARGAR REUNIONES EXISTENTES
        # ------------------------------------------
        cursor.execute("SELECT ID_Reunion, fecha FROM Reunion")
        reuniones = cursor.fetchall()

        if not reuniones:
            st.warning("⚠️ No hay reuniones registradas.")
            return

        reuniones_dict = {
            f"Reunión {r[0]} - {r[1]}": r[0]
            for r in reuniones
        }

        # ------------------------------------------
        # FORMULARIO DE PAGO
        # ------------------------------------------
        with st.form("form_pago_prestamo"):
            st.subheader("📝 Datos del Pago")

            prestamo_sel = st.selectbox(
                "Selecciona el préstamo:",
                list(prestamos_dict.keys())
            )

            reunion_sel = st.selectbox(
                "Selecciona la reunión:",
                list(reuniones_dict.keys())
            )

            fecha_pago = st.date_input(
                "Fecha del pago:",
                value=date.today()
            )

            monto_capital = st.number_input(
                "Monto capital pagado:",
                min_value=0.00, format="%.2f"
            )

            monto_interes = st.number_input(
                "Monto interés pagado:",
                min_value=0.00, format="%.2f"
            )

            total_cancelado = monto_capital + monto_interes

            st.info(f"💲 Total cancelado: **${total_cancelado:.2f}**")

            enviar = st.form_submit_button("💾 Registrar Pago")

            if enviar:
                id_prestamo = prestamos_dict[prestamo_sel]
                id_reunion = reuniones_dict[reunion_sel]

                if total_cancelado <= 0:
                    st.warning("⚠️ Debes ingresar al menos un monto.")
                else:
                    try:
                        cursor.execute("""
                            INSERT INTO PagoPrestamo
                            (ID_Prestamo, ID_Reunion, fecha_pago, monto_capital, monto_interes, total_cancelado)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (
                            id_prestamo,
                            id_reunion,
                            fecha_pago,
                            monto_capital,
                            monto_interes,
                            total_cancelado
                        ))

                        con.commit()
                        st.success("✅ Pago registrado correctamente.")
                        st.rerun()

                    except Exception as e:
                        con.rollback()
                        st.error(f"❌ Error al registrar el pago: {e}")

    except Exception as e:
        st.error(f"❌ Error general: {e}")

    finally:
        if "cursor" in locals():
            cursor.close()
        if "con" in locals():
            con.close()
