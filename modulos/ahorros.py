import streamlit as st
import pandas as pd
from modulos.config.conexion import obtener_conexion
from datetime import date

def mostrar_ahorros():
    st.header("💰 Control de Ahorros")

    # Verificar si hay una reunión seleccionada
    if 'reunion_actual' not in st.session_state:
        st.warning("⚠️ Primero debes seleccionar una reunión en el módulo de Asistencia.")
        return

    try:
        con = obtener_conexion()
        cursor = con.cursor()

        # Obtener la reunión del session_state
        reunion_info = st.session_state.reunion_actual
        id_reunion = reunion_info['id_reunion']
        id_grupo = reunion_info['id_grupo']
        nombre_reunion = reunion_info['nombre_reunion']

        # Mostrar información de la reunión actual
        st.info(f"📅 **Reunión actual:** {nombre_reunion}")

        # Obtener la fecha de la reunión actual para encontrar la reunión anterior
        cursor.execute("""
            SELECT fecha FROM Reunion WHERE ID_Reunion = %s
        """, (id_reunion,))
        fecha_reunion_actual = cursor.fetchone()[0]

        # -----------------------------
        # CARGAR MIEMBROS QUE ASISTIERON A ESTA REUNIÓN (SOLO LOS QUE MARCARON SI)
        # -----------------------------
        cursor.execute("""
            SELECT m.ID_Miembro, m.nombre 
            FROM Miembro m
            JOIN Miembroxreunion mr ON m.ID_Miembro = mr.ID_Miembro
            WHERE mr.ID_Reunion = %s AND mr.asistio = 1
            ORDER BY m.nombre
        """, (id_reunion,))
        
        miembros_presentes = cursor.fetchall()

        if not miembros_presentes:
            st.warning(f"⚠️ No hay miembros registrados como presentes en esta reunión.")
            st.info("Por favor, registra la asistencia primero en el módulo correspondiente.")
            return

        # -------------------------------------
        # TABLA DE AHORROS PARA TODOS LOS MIEMBROS
        # -------------------------------------
        with st.form("form_ahorro"):
            st.subheader("📝 Registro de Ahorros")
            
            # Mostrar fecha de la reunión
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

            # Diccionarios para almacenar los datos de cada miembro
            ahorros_data = {}
            otros_data = {}
            retiros_data = {}
            saldos_iniciales = {}

            # Filas para cada miembro
            for id_miembro, nombre_miembro in miembros_presentes:
                cols = st.columns([2, 1, 1, 1, 1, 1])
                
                with cols[0]:
                    # Mostrar nombre del miembro
                    st.write(nombre_miembro)
                
                with cols[1]:
                    # OBTENER SALDO FINAL DE LA REUNIÓN ANTERIOR
                    cursor.execute("""
                        SELECT COALESCE(SUM(a.monto_ahorro + a.monto_otros), 0) as saldo_final_anterior
                        FROM Ahorro a
                        JOIN Reunion r ON a.ID_Reunion = r.ID_Reunion
                        WHERE a.ID_Miembro = %s 
                        AND r.fecha < %s
                        ORDER BY r.fecha DESC
                        LIMIT 1
                    """, (id_miembro, fecha_reunion_actual))
                    
                    saldo_final_anterior_result = cursor.fetchone()
                    saldo_inicial = float(saldo_final_anterior_result[0]) if saldo_final_anterior_result else 0.00
                    
                    # Mostrar saldo inicial (saldo final de la reunión anterior)
                    st.metric("", f"${saldo_inicial:,.2f}", label_visibility="collapsed")
                    saldos_iniciales[id_miembro] = saldo_inicial
                
                with cols[2]:
                    # Input para ahorro
                    monto_ahorro = st.number_input(
                        "Ahorro",
                        min_value=0.00,
                        value=0.00,
                        format="%.2f",
                        key=f"ahorro_{id_miembro}",
                        label_visibility="collapsed"
                    )
                    ahorros_data[id_miembro] = monto_ahorro
                
                with cols[3]:
                    # Input para otras actividades
                    monto_otros = st.number_input(
                        "Otras actividades",
                        min_value=0.00,
                        value=0.00,
                        format="%.2f",
                        key=f"otros_{id_miembro}",
                        label_visibility="collapsed"
                    )
                    otros_data[id_miembro] = monto_otros
                
                with cols[4]:
                    # Checkbox para activar retiros
                    retiro_activado = st.checkbox(
                        "Activar retiro", 
                        key=f"retiro_check_{id_miembro}",
                        value=False
                    )
                    
                    if retiro_activado:
                        # Calcular el monto máximo que se puede retirar (saldo inicial + nuevos ahorros)
                        monto_max_retiro = saldos_iniciales[id_miembro] + ahorros_data[id_miembro] + otros_data[id_miembro]
                        
                        # Input para el monto de retiro (no puede superar el saldo disponible)
                        monto_retiros = st.number_input(
                            "Monto retiro",
                            min_value=0.00,
                            max_value=float(monto_max_retiro),
                            value=0.00,
                            format="%.2f",
                            key=f"retiro_{id_miembro}",
                            label_visibility="collapsed"
                        )
                        st.error(f"-${monto_retiros:,.2f}")
                        retiros_data[id_miembro] = monto_retiros
                    else:
                        monto_retiros = 0.00
                        st.info("$0.00")
                        retiros_data[id_miembro] = 0.00
                
                with cols[5]:
                    # Calcular saldo final
                    saldo_final = saldos_iniciales[id_miembro] + ahorros_data[id_miembro] + otros_data[id_miembro] - retiros_data[id_miembro]
                    
                    # Mostrar con color según si hay ganancia o pérdida
                    if saldo_final > saldos_iniciales[id_miembro]:
                        st.success(f"${saldo_final:,.2f}")
                    elif saldo_final < saldos_iniciales[id_miembro]:
                        st.error(f"${saldo_final:,.2f}")
                    else:
                        st.info(f"${saldo_final:,.2f}")

            # Botón de envío
            enviar = st.form_submit_button("💾 Guardar Ahorros")

            if enviar:
                try:
                    registros_guardados = 0
                    
                    for id_miembro, nombre_miembro in miembros_presentes:
                        monto_ahorro = ahorros_data.get(id_miembro, 0)
                        monto_otros = otros_data.get(id_miembro, 0)
                        monto_retiros = retiros_data.get(id_miembro, 0)
                        
                        # Solo guardar si hay al menos un monto ingresado o retiro
                        if monto_ahorro > 0 or monto_otros > 0 or monto_retiros > 0:
                            # Verificar si ya existe un registro para este miembro en esta reunión
                            cursor.execute("""
                                SELECT COUNT(*) FROM Ahorro 
                                WHERE ID_Miembro = %s AND ID_Reunion = %s
                            """, (id_miembro, id_reunion))
                            
                            if cursor.fetchone()[0] == 0:
                                # Insertar el nuevo registro (incluyendo retiros si los hay)
                                cursor.execute("""
                                    INSERT INTO Ahorro (ID_Miembro, ID_Reunion, fecha, monto_ahorro, monto_otros, monto_retiros)
                                    VALUES (%s, %s, %s, %s, %s, %s)
                                """, (id_miembro, id_reunion, fecha_ahorro, monto_ahorro, monto_otros, monto_retiros))
                                registros_guardados += 1
                            else:
                                # Actualizar registro existente
                                cursor.execute("""
                                    UPDATE Ahorro 
                                    SET monto_ahorro = %s, monto_otros = %s, monto_retiros = %s, fecha = %s
                                    WHERE ID_Miembro = %s AND ID_Reunion = %s
                                """, (monto_ahorro, monto_otros, monto_retiros, fecha_ahorro, id_miembro, id_reunion))
                                registros_guardados += 1

                    con.commit()
                    
                    if registros_guardados > 0:
                        st.success(f"✅ Se guardaron/actualizaron {registros_guardados} registros de ahorro correctamente.")
                    else:
                        st.info("ℹ️ No se guardaron registros nuevos (no se ingresaron montos o retiros).")
                    
                    st.rerun()

                except Exception as e:
                    con.rollback()
                    st.error(f"❌ Error al registrar los ahorros: {e}")

        # -------------------------------------
        # HISTORIAL DE AHORROS REGISTRADOS
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
                    a.monto_retiros,
                    COALESCE((
                        SELECT SUM(a2.monto_ahorro + a2.monto_otros - a2.monto_retiros)
                        FROM Ahorro a2
                        JOIN Reunion r2 ON a2.ID_Reunion = r2.ID_Reunion
                        WHERE a2.ID_Miembro = a.ID_Miembro 
                        AND r2.fecha < (SELECT r3.fecha FROM Reunion r3 WHERE r3.ID_Reunion = a.ID_Reunion)
                    ), 0) as saldo_inicial,
                    (a.monto_ahorro + a.monto_otros - a.monto_retiros) as saldo_actual
                FROM Ahorro a
            )
            SELECT 
                sa.ID_Ahorro,
                m.nombre,
                r.fecha as fecha_reunion,
                sa.fecha as fecha_ahorro,
                sa.monto_ahorro,
                sa.monto_otros,
                sa.monto_retiros,
                sa.saldo_inicial,
                sa.saldo_inicial + sa.saldo_actual as saldo_final
            FROM SaldosAcumulados sa
            JOIN Miembro m ON sa.ID_Miembro = m.ID_Miembro
            JOIN Reunion r ON sa.ID_Reunion = r.ID_Reunion
            WHERE r.ID_Reunion = %s
            ORDER BY m.nombre, sa.fecha, sa.ID_Ahorro
        """, (id_reunion,))
        
        historial = cursor.fetchall()
        
        if historial:
            df = pd.DataFrame(historial, columns=[
                "ID", "Miembro", "Reunión", "Fecha Ahorro", "Ahorros", 
                "Otros", "Retiros", "Saldo Inicial", "Saldo Final"
            ])
            
            # Formatear columnas numéricas
            numeric_cols = ["Ahorros", "Otros", "Retiros", "Saldo Inicial", "Saldo Final"]
            for col in numeric_cols:
                df[col] = df[col].apply(lambda x: f"${x:,.2f}")
            
            st.dataframe(df.drop("ID", axis=1), use_container_width=True)
            
        else:
            st.info("📝 No hay registros de ahorros para esta reunión.")

    except Exception as e:
        st.error(f"❌ Error general: {e}")

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'con' in locals():
            con.close()
