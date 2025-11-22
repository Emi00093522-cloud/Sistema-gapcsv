import streamlit as st
import pandas as pd
from modulos.config.conexion import obtener_conexion
from datetime import date

def mostrar_ahorros():
    st.header("💰 Registro de Ahorros del Grupo")

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

        miembros_dict = {f"{m[1]} (ID {m[0]})": m[0] for m in miembros_presentes}

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
                # Mostrar reunión seleccionada (solo lectura)
                st.text_input(
                    "Reunión:",
                    value=nombre_reunion,
                    disabled=True
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
                id_r = id_reunion

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

        # ... (el resto del código del historial se mantiene igual) ...

    except Exception as e:
        st.error(f"❌ Error general: {e}")

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'con' in locals():
            con.close()
