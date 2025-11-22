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

            # TABLA DE AHORROS CON FORMATO ESPECÍFICO
            st.markdown("---")
            st.subheader("💰 Control de Ahorros")
            
            # Encabezado de la tabla
            cols = st.columns([2, 1, 1, 1, 1, 1])
            with cols[0]:
                st.markdown("**Socios/as**")
            with cols[1]:
                st.markdown("**Saldo mín inicial**")
            with cols[2]:
                st.markdown("**Ahorro**")
            with cols[3]:
                st.markdown("**Otras actividades**")
            with cols[4]:
                st.markdown("**Retiros**")
            with cols[5]:
                st.markdown("**Saldos ahorros**")
            
            # Fila de datos
            cols = st.columns([2, 1, 1, 1, 1, 1])
            
            with cols[0]:
                # Mostrar el miembro seleccionado
                st.write(miembro_sel.split('(')[0].strip())
            
            with cols[1]:
                # Saldo inicial del registro anterior del mismo miembro
                id_miembro_actual = miembros_dict[miembro_sel]
                cursor.execute("""
                    SELECT (monto_ahorro + monto_otros) as saldo_anterior
                    FROM Ahorro 
                    WHERE ID_Miembro = %s 
                    ORDER BY fecha DESC, ID_Ahorro DESC 
                    LIMIT 1
                """, (id_miembro_actual,))
                
                saldo_anterior_result = cursor.fetchone()
                saldo_inicial = float(saldo_anterior_result[0]) if saldo_anterior_result else 0.00
                st.metric("", f"${saldo_inicial:,.2f}", label_visibility="collapsed")
            
            with cols[2]:
                monto_ahorro = st.number_input(
                    "Monto ahorro:",
                    min_value=0.00,
                    format="%.2f",
                    key="ahorro_input",
                    label_visibility="collapsed"
                )
            
            with cols[3]:
                monto_otros = st.number_input(
                    "Otras actividades:",
                    min_value=0.00,
                    format="%.2f",
                    key="otros_input",
                    label_visibility="collapsed"
                )
            
            with cols[4]:
                # Checkbox para activar retiros
                retiro_activado = st.checkbox("Activar retiro", key="retiro_checkbox")
                
                if retiro_activado:
                    monto_retiros = monto_ahorro + monto_otros
                    st.error(f"-${monto_retiros:,.2f}")
                else:
                    monto_retiros = 0.00
                    st.info("$0.00")
            
            with cols[5]:
                # Calcular saldo final
                saldo_final = saldo_inicial + monto_ahorro + monto_otros - monto_retiros
                
                # Mostrar con color según si hay ganancia o pérdida
                if saldo_final > saldo_inicial:
                    st.success(f"${saldo_final:,.2f}")
                elif saldo_final < saldo_inicial:
                    st.error(f"${saldo_final:,.2f}")
                else:
                    st.info(f"${saldo_final:,.2f}")

            # Botón de envío
            enviar = st.form_submit_button("💾 Guardar Ahorro")

            if enviar:
                id_m = miembros_dict[miembro_sel]
                id_r = reuniones_dict[reunion_sel]

                # Validación
                if monto_ahorro == 0 and monto_otros == 0:
                    st.warning("⚠️ Debes ingresar al menos un monto de ahorro u otras actividades.")
                else:
                    try:
                        # Verificar si ya existe un registro para este miembro en esta reunión
                        cursor.execute("""
                            SELECT COUNT(*) FROM Ahorro 
                            WHERE ID_Miembro = %s AND ID_Reunion = %s
                        """, (id_m, id_r))
                        
                        if cursor.fetchone()[0] > 0:
                            st.warning("⚠️ Ya existe un registro de ahorro para este miembro en esta reunión.")
                        else:
                            # Insertar el nuevo registro
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

        # -------------------------------------
        # HISTORIAL DE AHORROS REGISTRADOS CON SALDOS ACUMULATIVOS
        # -------------------------------------
        st.markdown("---")
        st.subheader("📋 Historial de Ahorros")
        
        cursor.execute("""
            WITH SaldosAcumulados AS (
                SELECT 
                    a.ID_Ahorro,
                    a.ID_Miembro,
                    a.ID_Reunion,
                    a.fecha,
                    a.monto_ahorro,
                    a.monto_otros,
                    COALESCE(LAG(a.monto_ahorro + a.monto_otros) OVER (
                        PARTITION BY a.ID_Miembro 
                        ORDER BY a.fecha, a.ID_Ahorro
                    ), 0) as saldo_inicial,
                    (a.monto_ahorro + a.monto_otros) as saldo_actual
                FROM Ahorro a
            )
            SELECT 
                sa.ID_Ahorro,
                m.nombre,
                r.fecha as fecha_reunion,
                sa.fecha as fecha_ahorro,
                sa.monto_ahorro,
                sa.monto_otros,
                sa.saldo_inicial,
                sa.saldo_inicial + sa.saldo_actual as saldo_final
            FROM SaldosAcumulados sa
            JOIN Miembro m ON sa.ID_Miembro = m.ID_Miembro
            JOIN Reunion r ON sa.ID_Reunion = r.ID_Reunion
            ORDER BY m.nombre, sa.fecha, sa.ID_Ahorro
        """)
        
        historial = cursor.fetchall()
        
        if historial:
            df = pd.DataFrame(historial, columns=[
                "ID", "Miembro", "Reunión", "Fecha Ahorro", "Ahorros", 
                "Otros", "Saldo Inicial", "Saldo Final"
            ])
            
            # Formatear columnas numéricas
            numeric_cols = ["Ahorros", "Otros", "Saldo Inicial", "Saldo Final"]
            for col in numeric_cols:
                df[col] = df[col].apply(lambda x: f"${x:,.2f}")
            
            st.dataframe(df.drop("ID", axis=1), use_container_width=True)
            
            # Mostrar también un resumen por miembro
            st.subheader("📊 Resumen por Miembro")
            cursor.execute("""
                SELECT 
                    m.nombre,
                    COUNT(a.ID_Ahorro) as total_registros,
                    COALESCE(SUM(a.monto_ahorro), 0) as total_ahorros,
                    COALESCE(SUM(a.monto_otros), 0) as total_otros,
                    COALESCE(SUM(a.monto_ahorro + a.monto_otros), 0) as saldo_total
                FROM Miembro m
                LEFT JOIN Ahorro a ON m.ID_Miembro = a.ID_Miembro
                GROUP BY m.ID_Miembro, m.nombre
                ORDER BY m.nombre
            """)
            
            resumen = cursor.fetchall()
            df_resumen = pd.DataFrame(resumen, columns=[
                "Miembro", "Total Registros", "Total Ahorros", "Total Otros", "Saldo Total"
            ])
            
            # Formatear columnas numéricas del resumen
            numeric_cols_resumen = ["Total Ahorros", "Total Otros", "Saldo Total"]
            for col in numeric_cols_resumen:
                df_resumen[col] = df_resumen[col].apply(lambda x: f"${x:,.2f}")
            
            st.dataframe(df_resumen, use_container_width=True)
            
        else:
            st.info("📝 No hay registros de ahorros aún.")

    except Exception as e:
        st.error(f"❌ Error general: {e}")

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'con' in locals():
            con.close()
