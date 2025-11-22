import streamlit as st
import pandas as pd
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
        # FORMULARIO DE REGISTRO DE AHORRO EN COLUMNAS
        # -------------------------------------
        with st.form("form_ahorro"):
            st.subheader("📝 Datos del ahorro")
            
            # PRIMERA FILA DE COLUMNAS
            col1, col2, col3 = st.columns(3)
            
            with col1:
                miembro_sel = st.selectbox(
                    "Selecciona el miembro:",
                    list(miembros_dict.keys())
                )
            
            with col2:
                reunion_sel = st.selectbox(
                    "Selecciona la reunión:",
                    list(reuniones_dict.keys())
                )
            
            with col3:
                fecha_ahorro = st.date_input(
                    "Fecha del ahorro:",
                    value=date.today()
                )

            # SEGUNDA FILA DE COLUMNAS PARA MONTOS
            col4, col5, col6 = st.columns(3)
            
            with col4:
                monto_ahorro = st.number_input(
                    "Monto de ahorro:",
                    min_value=0.00,
                    format="%.2f"
                )
            
            with col5:
                monto_otros = st.number_input(
                    "Monto otros ingresos:",
                    min_value=0.00,
                    format="%.2f"
                )
            
            with col6:
                monto_retiros = st.number_input(
                    "Monto de retiros:",
                    min_value=0.00,
                    format="%.2f"
                )

            # TERCERA FILA PARA SALDOS
            st.markdown("---")
            st.subheader("💰 Saldos")
            
            col7, col8, col9, col10, col11 = st.columns(5)
            
            with col7:
                saldo_inicial = st.number_input(
                    "Saldo inicial:",
                    min_value=0.00,
                    format="%.2f"
                )
            
            with col8:
                st.metric("Ahorros", f"${monto_ahorro:,.2f}")
            
            with col9:
                st.metric("Otros ingresos", f"${monto_otros:,.2f}")
            
            with col10:
                st.metric("Retiros", f"-${monto_retiros:,.2f}")
            
            with col11:
                saldo_final = saldo_inicial + monto_ahorro + monto_otros - monto_retiros
                st.metric("Saldo final", f"${saldo_final:,.2f}", delta=f"${saldo_final - saldo_inicial:,.2f}")

            enviar = st.form_submit_button("💾 Guardar Ahorro")

            if enviar:
                id_m = miembros_dict[miembro_sel]
                id_r = reuniones_dict[reunion_sel]

                # Validación
                if monto_ahorro == 0 and monto_otros == 0 and monto_retiros == 0:
                    st.warning("⚠️ Debes ingresar al menos un monto de ahorro, otros ingresos o retiros.")
                else:
                    try:
                        cursor.execute("""
                            INSERT INTO Ahorro (ID_Miembro, ID_Reunion, fecha, monto_ahorro, monto_otros, monto_retiros, saldo_inicial, saldo_final)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (id_m, id_r, fecha_ahorro, monto_ahorro, monto_otros, monto_retiros, saldo_inicial, saldo_final))

                        con.commit()
                        st.success("✅ Ahorro registrado correctamente.")
                        st.rerun()

                    except Exception as e:
                        con.rollback()
                        st.error(f"❌ Error al registrar el ahorro: {e}")

        # -------------------------------------
        # HISTORIAL DE AHORROS REGISTRADOS
        # -------------------------------------
        st.markdown("---")
        st.subheader("📋 Historial de Ahorros")
        
        cursor.execute("""
            SELECT a.ID_Ahorro, m.nombre, r.fecha, a.fecha, a.monto_ahorro, a.monto_otros, a.saldo_inicial, a.saldo_final
            FROM Ahorro a
            JOIN Miembro m ON a.ID_Miembro = m.ID_Miembro
            JOIN Reunion r ON a.ID_Reunion = r.ID_Reunion
            ORDER BY a.fecha DESC
        """)
        
        historial = cursor.fetchall()
        
        if historial:
            df = pd.DataFrame(historial, columns=[
                "ID", "Miembro", "Reunión", "Fecha", "Ahorros", 
                "Otros", "Retiros", "Saldo Inicial", "Saldo Final"
            ])
            
            # Formatear columnas numéricas
            numeric_cols = ["Ahorros", "Otros", "Retiros", "Saldo Inicial", "Saldo Final"]
            for col in numeric_cols:
                df[col] = df[col].apply(lambda x: f"${x:,.2f}")
            
            st.dataframe(df.drop("ID", axis=1), use_container_width=True)
        else:
            st.info("📝 No hay registros de ahorros aún.")

    except Exception as e:
        st.error(f"❌ Error general: {e}")

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'con' in locals():
            con.close()
