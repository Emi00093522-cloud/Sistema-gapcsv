import streamlit as st
from modulos.config.conexion import obtener_conexion
from datetime import date

def mostrar_ahorros():
    st.header("💰 Registro de Ahorros del Grupo")

    try:
        con = obtener_conexion()
        cursor = con.cursor()

        # -----------------------------
        # CARGAR LISTA DE MIEMBROS
        # -----------------------------
        cursor.execute("SELECT ID_Miembro, nombre FROM Miembro")
        miembros = cursor.fetchall()

        if not miembros:
            st.warning("⚠️ No hay miembros registrados.")
            return

        miembros_dict = {f"{m[1]} (ID {m[0]})": m[0] for m in miembros}

        # -----------------------------
        # CARGAR LISTA DE REUNIONES
        # -----------------------------
        cursor.execute("SELECT ID_Reunion, fecha FROM Reunion")
        reuniones = cursor.fetchall()

        if not reuniones:
            st.warning("⚠️ No hay reuniones registradas.")
            return

        reuniones_dict = {f"Reunión {r[0]} - {r[1]}": r[0] for r in reuniones}

        # -------------------------------------
        # FORMULARIO DE REGISTRO DE AHORRO
        # -------------------------------------
        with st.form("form_ahorro"):

            st.subheader("📝 Datos del ahorro")

            miembro_sel = st.selectbox(
                "Selecciona el miembro:",
                list(miembros_dict.keys())
            )

            reunion_sel = st.selectbox(
                "Selecciona la reunión:",
                list(reuniones_dict.keys())
            )

            fecha_ahorro = st.date_input(
                "Fecha del ahorro:",
                value=date.today()
            )

            monto_ahorro = st.number_input(
                "Monto de ahorro:",
                min_value=0.00,
                format="%.2f"
            )

            monto_otros = st.number_input(
                "Monto otros ingresos:",
                min_value=0.00,
                format="%.2f"
            )

            enviar = st.form_submit_button("💾 Guardar Ahorro")

            if enviar:
                id_m = miembros_dict[miembro_sel]
                id_r = reuniones_dict[reunion_sel]

                # Validación
                if monto_ahorro == 0 and monto_otros == 0:
                    st.warning("⚠️ Debes ingresar al menos un monto de ahorro o monto otros.")
                else:
                    try:
                        cursor.execute("""
                            INSERT INTO Ahorro (ID_Miembro, ID_Reunion, fecha, monto_ahorro, monto_otros)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (id_m, id_r, fecha_ahorro, monto_ahorro, monto_otros))

                        con.commit()
                        st.success("✅ Ahorro registrado correctamente.")
                        st.rerun()

                    except Exception as e:
                        con.rollback()
                        st.error(f"❌ Error al registrar el ahorro: {e}")

    except Exception as e:
        st.error(f"❌ Error general: {e}")

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'con' in locals():
            con.close()
