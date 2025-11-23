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

        # OBTENER LA FECHA DE LA REUNIÓN ACTUAL PARA ENCONTRAR LA REUNIÓN ANTERIOR
        cursor.execute("SELECT fecha FROM Reunion WHERE ID_Reunion = %s", (id_reunion,))
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
            st.markdown("### 💰 Control de Ahorros")
            
            # ENCABEZADO DE LA TABLA - UNA SOLA FILA PARA LOS TÍTULOS
            cols_titulos = st.columns([2, 1, 1, 1, 1,1])
            with cols_titulos[0]:
                st.markdown("**Socios/as**")
            with cols_titulos[1]:
                st.markdown("**Saldo mín inicial**")
            with cols_titulos[2]:
                st.markdown("**Ahorro**")
            with cols_titulos[3]:
                st.markdown("**Otras actividades**")
            with cols_titulos[4]:
                st.markdown("**Retiros**")


            # Diccionarios para almacenar los datos de cada miembro
            ahorros_data = {}
            otros_data = {}
            retiros_data = {}
            saldos_iniciales = {}

            # FILAS PARA CADA MIEMBRO - UNA FILA POR MIEMBRO
            for id_miembro, nombre_miembro in miembros_presentes:
                cols = st.columns([2, 1, 1, 1, 1, 1])
                
                with cols[0]:
                    # Mostrar nombre del miembro
                    st.write(f"**{nombre_miembro}**")
                
                with cols[1]:
                    # OBTENER EL SALDO FINAL DE LA REUNIÓN ANTERIOR DEL MISMO MIEMBRO
                    cursor.execute("""
                        SELECT COALESCE(
                            (SELECT a.saldos_ahorros 
                             FROM Ahorro a
                             JOIN Reunion r ON a.ID_Reunion = r.ID_Reunion
                             WHERE a.ID_Miembro = %s 
                             AND r.fecha < %s
                             ORDER BY r.fecha DESC, a.ID_Ahorro DESC 
                             LIMIT 1), 0) as saldo_final_anterior
                    """, (id_miembro, fecha_reunion_actual))
                    
                    saldo_final_anterior_result = cursor.fetchone()
                    saldo_inicial = float(saldo_final_anterior_result[0]) if saldo_final_anterior_result else 0.00
                    
                    # Mostrar saldo inicial (saldo final de la reunión anterior)
                    st.write(f"${saldo_inicial:,.2f}")
                    saldos_iniciales[id_miembro] = saldo_inicial
                
                with cols[2]:
                    # Input para ahorro - INICIA EN 0 (limpio)
                    monto_ahorro = st.number_input(
                        "Ahorro",
                        min_value=0.00,
                        value=0.00,
                        format="%.2f",
                        step=0.01,
                        key=f"ahorro_{id_miembro}",
                        label_visibility="collapsed"
                    )
                    ahorros_data[id_miembro] = monto_ahorro
                
                with cols[3]:
                    # Input para otras actividades - INICIA EN 0 (limpio)
                    monto_otros = st.number_input(
                        "Otras actividades",
                        min_value=0.00,
                        value=0.00,
                        format="%.2f",
                        step=0.01,
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
                        # Input para el monto de retiro - INICIA EN 0
                        monto_retiros = st.number_input(
                            "Monto retiro",
                            min_value=0.00,
                            max_value=float(saldos_iniciales[id_miembro] + ahorros_data[id_miembro] + otros_data[id_miembro]),
                            value=0.00,
                            format="%.2f",
                            step=0.01,
                            key=f"retiro_{id_miembro}",
                            label_visibility="collapsed"
                        )
                        st.error(f"**-${monto_retiros:,.2f}**")
                        retiros_data[id_miembro] = monto_retiros
                    else:
                        monto_retiros = 0.00
                        st.info("**$0.00**")
                        retiros_data[id_miembro] = 0.00
                
                # Línea separadora entre miembros
                st.markdown("---")

            # Botón de envío FUERA de las columnas
            enviar = st.form_submit_button("💾 Guardar Ahorros")

            if enviar:
                try:
                    registros_guardados = 0
                    
                    for id_miembro, nombre_miembro in miembros_presentes:
                        monto_ahorro = ahorros_data.get(id_miembro, 0)
                        monto_otros = otros_data.get(id_miembro, 0)
                        monto_retiros = retiros_data.get(id_miembro, 0)
                        saldo_inicial = saldos_iniciales.get(id_miembro, 0)
                        
                        # CALCULAR EL SALDO FINAL SOLO AL GUARDAR
                        saldo_final = saldo_inicial + monto_ahorro + monto_otros - monto_retiros
                        
                        # Solo guardar si hay al menos un monto ingresado o retiro
                        if monto_ahorro > 0 or monto_otros > 0 or monto_retiros > 0:
                            # Verificar si ya existe un registro para este miembro en esta reunión
                            cursor.execute("""
                                SELECT COUNT(*) FROM Ahorro 
                                WHERE ID_Miembro = %s AND ID_Reunion = %s
                            """, (id_miembro, id_reunion))
                            
                            existe_registro = cursor.fetchone()[0] > 0
                            
                            if not existe_registro:
                                # Insertar el nuevo registro
                                cursor.execute("""
                                    INSERT INTO Ahorro (
                                        ID_Miembro, ID_Reunion, fecha, 
                                        monto_ahorro, monto_otros, monto_retiros,
                                        saldos_ahorros, saldo_inicial
                                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                """, (
                                    id_miembro, id_reunion, fecha_ahorro, 
                                    monto_ahorro, monto_otros, monto_retiros,
                                    saldo_final, saldo_inicial
                                ))
                                registros_guardados += 1
                                st.success(f"✅ {nombre_miembro}: ${saldo_inicial:,.2f} + ${monto_ahorro:,.2f} + ${monto_otros:,.2f} - ${monto_retiros:,.2f} = ${saldo_final:,.2f}")
                            else:
                                # Actualizar registro existente
                                cursor.execute("""
                                    UPDATE Ahorro 
                                    SET monto_ahorro = %s, monto_otros = %s, monto_retiros = %s, 
                                        saldos_ahorros = %s, saldo_inicial = %s, fecha = %s
                                    WHERE ID_Miembro = %s AND ID_Reunion = %s
                                """, (
                                    monto_ahorro, monto_otros, monto_retiros,
                                    saldo_final, saldo_inicial, fecha_ahorro,
                                    id_miembro, id_reunion
                                ))
                                registros_guardados += 1
                                st.success(f"✅ {nombre_miembro}: Registro actualizado - ${saldo_final:,.2f}")

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
        # HISTORIAL DE AHORROS REGISTRADOS (ACTUALIZADO DESPUÉS DE GUARDAR)
        # -------------------------------------
        st.markdown("---")
        st.subheader("📋 Historial de Ahorros")
        
        cursor.execute("""
            SELECT 
                a.ID_Ahorro,
                m.nombre,
                r.fecha as fecha_reunion,
                a.fecha as fecha_ahorro,
                a.monto_ahorro,
                a.monto_otros,
                a.monto_retiros,
                a.saldo_inicial,
                a.saldos_ahorros as saldo_final
            FROM Ahorro a
            JOIN Miembro m ON a.ID_Miembro = m.ID_Miembro
            JOIN Reunion r ON a.ID_Reunion = r.ID_Reunion
            WHERE r.ID_Reunion = %s
            ORDER BY m.nombre, a.fecha, a.ID_Ahorro
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
