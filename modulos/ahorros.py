import streamlit as st
import pandas as pd
from modulos.config.conexion import obtener_conexion
from datetime import date

def mostrar_ahorros():
    st.header("💰 Registro de Ahorros del Grupo - Formato Oficial")

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
        # FORMULARIO DE REGISTRO DE AHORRO CON FORMATO PDF
        # -------------------------------------
        st.subheader("📊 Formulario de Ahorros - Formato Oficial")

        with st.form("form_ahorro"):
            col1, col2 = st.columns(2)
            
            with col1:
                miembro_sel = st.selectbox(
                    "Selecciona el miembro:",
                    list(miembros_dict.keys())
                )

                fecha_ahorro = st.date_input(
                    "Fecha del ahorro:",
                    value=date.today()
                )

            with col2:
                reunion_sel = st.selectbox(
                    "Selecciona la reunión:",
                    list(reuniones_dict.keys())
                )

            # SECCIÓN PRINCIPAL CON FORMATO SIMILAR AL PDF
            st.markdown("---")
            st.markdown("### 📋 Registro de Movimientos de Ahorro")
            
            # Crear estructura de tabla similar al PDF
            col1, col2, col3, col4, col5 = st.columns([0.5, 2, 3, 3, 3])
            
            with col1:
                st.markdown("**#**")
                for i in range(1, 26):
                    st.write(f"{i}")
            
            with col2:
                st.markdown("**Socios/as**")
                # Mostrar solo el miembro seleccionado en formato simplificado
                nombre_miembro = miembro_sel.split('(')[0].strip()
                st.write(nombre_miembro)
                for i in range(24):
                    st.write("")
            
            # Columnas para movimientos (similar al PDF)
            with col3:
                st.markdown("**Ahorros**")
                monto_ahorro = st.number_input(
                    "Monto ahorro:",
                    min_value=0.00,
                    format="%.2f",
                    key="ahorro_input",
                    label_visibility="collapsed"
                )
                for i in range(24):
                    st.write("")
            
            with col4:
                st.markdown("**Otras Actividades**")
                monto_otros = st.number_input(
                    "Monto otros:",
                    min_value=0.00,
                    format="%.2f",
                    key="otros_input",
                    label_visibility="collapsed"
                )
                for i in range(24):
                    st.write("")
            
            with col5:
                st.markdown("**Retiros**")
                monto_retiros = st.number_input(
                    "Monto retiros:",
                    min_value=0.00,
                    format="%.2f",
                    key="retiros_input",
                    label_visibility="collapsed"
                )
                for i in range(24):
                    st.write("")

            # SECCIÓN DE SALDOS (como en el PDF)
            st.markdown("---")
            st.markdown("### 💰 Cálculo de Saldos")
            
            saldo_col1, saldo_col2, saldo_col3, saldo_col4, saldo_col5 = st.columns(5)
            
            with saldo_col1:
                st.markdown("**Saldo Inicial**")
                saldo_inicial = st.number_input(
                    "Saldo inicial:",
                    min_value=0.00,
                    format="%.2f",
                    key="saldo_inicial",
                    label_visibility="collapsed"
                )
            
            with saldo_col2:
                st.markdown("**Ahorros**")
                st.info(f"${monto_ahorro:,.2f}")
            
            with saldo_col3:
                st.markdown("**Otras Actividades**")
                st.info(f"${monto_otros:,.2f}")
            
            with saldo_col4:
                st.markdown("**Retiros**")
                st.warning(f"${monto_retiros:,.2f}")
            
            with saldo_col5:
                st.markdown("**Saldo Final**")
                saldo_final = saldo_inicial + monto_ahorro + monto_otros - monto_retiros
                st.success(f"${saldo_final:,.2f}")

            enviar = st.form_submit_button("💾 Guardar Registro de Ahorro")

            if enviar:
                id_m = miembros_dict[miembro_sel]
                id_r = reuniones_dict[reunion_sel]

                # Validación
                if monto_ahorro == 0 and monto_otros == 0 and monto_retiros == 0:
                    st.warning("⚠️ Debes ingresar al menos un movimiento (ahorro, otros ingresos o retiros).")
                else:
                    try:
                        cursor.execute("""
                            INSERT INTO Ahorro (ID_Miembro, ID_Reunion, fecha, monto_ahorro, monto_otros, monto_retiros, saldo_inicial, saldo_final)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (id_m, id_r, fecha_ahorro, monto_ahorro, monto_otros, monto_retiros, saldo_inicial, saldo_final))

                        con.commit()
                        st.success("✅ Registro de ahorro guardado correctamente.")
                        st.rerun()

                    except Exception as e:
                        con.rollback()
                        st.error(f"❌ Error al registrar el ahorro: {e}")

        # -------------------------------------
        # HISTORIAL DE AHORROS REGISTRADOS
        # -------------------------------------
        st.markdown("---")
        st.subheader("📋 Historial de Ahorros Registrados")
        
        cursor.execute("""
            SELECT a.ID_Ahorro, m.nombre, r.fecha, a.fecha, a.monto_ahorro, a.monto_otros, a.monto_retiros, a.saldo_inicial, a.saldo_final
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
