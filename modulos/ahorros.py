import streamlit as st
import pandas as pd
from modulos.config.conexion import obtener_conexion
from datetime import date

def obtener_ahorros_grupo():
    """
    Función para el módulo de cierre de ciclo
    Retorna todos los ahorros del grupo actual para consolidar en el cierre
    """
    try:
        con = obtener_conexion()
        cursor = con.cursor()
       
        # Obtener el ID del grupo actual desde session_state
        if 'reunion_actual' not in st.session_state:
            st.error("No hay reunión activa seleccionada")
            return []
       
        id_grupo = st.session_state.reunion_actual['id_grupo']
       
        # Obtener todos los ahorros del grupo (suma de ahorros + otros ingresos)
        cursor.execute("""
            SELECT
                a.ID_Ahorro,
                a.ID_Miembro,
                a.ID_Reunion,
                a.fecha,
                a.monto_ahorro,
                a.monto_otros,
                a.monto_retiros,
                a.saldo_inicial,
                a.saldos_ahorros as saldo_final,
                (a.monto_ahorro + a.monto_otros) as total_ingresos
            FROM Ahorro a
            JOIN Reunion r ON a.ID_Reunion = r.ID_Reunion
            WHERE r.ID_Grupo = %s
            ORDER BY a.fecha
        """, (id_grupo,))
       
        ahorros_data = cursor.fetchall()
       
        # Convertir a lista de diccionarios
        resultado = []
        for ahorro in ahorros_data:
            resultado.append({
                'id_ahorro': ahorro[0],
                'id_miembro': ahorro[1],
                'id_reunion': ahorro[2],
                'fecha': ahorro[3],
                'monto_ahorro': float(ahorro[4]),
                'monto_otros': float(ahorro[5]),
                'monto_retiros': float(ahorro[6]),
                'saldo_inicial': float(ahorro[7]),
                'saldo_final': float(ahorro[8]),
                'total_ingresos': float(ahorro[9])
            })
       
        return resultado
       
    except Exception as e:
        st.error(f"❌ Error en obtener_ahorros_grupo: {e}")
        return []
   
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'con' in locals():
            con.close()

def obtener_total_ahorros_ciclo():
    """
    Función específica para cierre de ciclo
    Retorna la suma total de todos los ahorros + otros ingresos del grupo
    """
    try:
        ahorros_data = obtener_ahorros_grupo()
       
        if not ahorros_data:
            return 0.00
       
        # Sumar todos los ahorros + otros ingresos (excluyendo retiros)
        total_ahorros = sum(item['monto_ahorro'] for item in ahorros_data)
        total_otros = sum(item['monto_otros'] for item in ahorros_data)
       
        total_general = total_ahorros + total_otros
       
        return total_general
       
    except Exception as e:
        st.error(f"❌ Error calculando total de ahorros: {e}")
        return 0.00

def obtener_saldo_inicial_corregido(id_miembro, fecha_reunion_actual):
    """
    Obtiene el saldo inicial CORREGIDO - saldo final de la reunión anterior
    """
    try:
        con = obtener_conexion()
        cursor = con.cursor()
       
        # Obtener el saldo final de la reunión anterior MÁS RECIENTE
        cursor.execute("""
            SELECT COALESCE(a.saldos_ahorros, 0) as saldo_final_anterior
            FROM Ahorro a
            JOIN Reunion r ON a.ID_Reunion = r.ID_Reunion
            WHERE a.ID_Miembro = %s
            AND r.fecha < %s
            ORDER BY r.fecha DESC, a.ID_Ahorro DESC
            LIMIT 1
        """, (id_miembro, fecha_reunion_actual))
       
        resultado = cursor.fetchone()
        saldo_inicial = float(resultado[0]) if resultado and resultado[0] is not None else 0.00
       
        return saldo_inicial
       
    except Exception as e:
        st.error(f"❌ Error obteniendo saldo inicial: {e}")
        return 0.00
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'con' in locals():
            con.close()

def obtener_deuda_prestamo_pendiente(id_miembro, con):
    """
    Obtiene la deuda total pendiente de préstamos para un miembro
    Basado en el catálogo ID_Estado_prestamo donde 3 = cancelado
    """
    try:
        cursor = con.cursor()
        
        # Consulta que excluye préstamos cancelados (ID_Estado_prestamo = 3)
        cursor.execute("""
            SELECT 
                COALESCE(SUM(p.monto_total_pagar - (
                    SELECT COALESCE(SUM(cp.total_pagado), 0) 
                    FROM CuotaPrestamo cp 
                    WHERE cp.ID_Prestamo = p.ID_Prestamo
                )), 0) as deuda_pendiente
            FROM Prestamo p
            WHERE p.ID_Miembro = %s 
            AND p.ID_Estado_prestamo != 3  -- Excluir préstamos cancelados
            AND p.monto_total_pagar > (
                SELECT COALESCE(SUM(cp.total_pagado), 0) 
                FROM CuotaPrestamo cp 
                WHERE cp.ID_Prestamo = p.ID_Prestamo
            )
        """, (id_miembro,))
        
        resultado = cursor.fetchone()
        deuda_pendiente = float(resultado[0]) if resultado and resultado[0] is not None else 0.00
        
        return deuda_pendiente
        
    except Exception as e:
        st.error(f"❌ Error obteniendo deuda pendiente: {e}")
        return 0.00
    finally:
        if 'cursor' in locals():
            cursor.close()

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
            cols_titulos = st.columns([2, 1, 1, 1, 1, 1, 1])  # Agregada columna para Deuda
            with cols_titulos[0]:
                st.markdown("**Socios/as**")
            with cols_titulos[1]:
                st.markdown("**Saldo inicial**")
            with cols_titulos[2]:
                st.markdown("**Ahorro**")
            with cols_titulos[3]:
                st.markdown("**Otras actividades**")
            with cols_titulos[4]:
                st.markdown("**Deuda préstamo**")
            with cols_titulos[5]:
                st.markdown("**Retiros**")
            with cols_titulos[6]:
                st.markdown("**Saldo final**")

            # Diccionarios para almacenar los datos de cada miembro
            ahorros_data = {}
            otros_data = {}
            retiros_data = {}
            saldos_iniciales = {}
            retiros_activados = {}
            montos_retiro_calculados = {}
            saldos_finales = {}
            deudas_miembros = {}

            # FILAS PARA CADA MIEMBRO - UNA FILA POR MIEMBRO
            for id_miembro, nombre_miembro in miembros_presentes:
                cols = st.columns([2, 1, 1, 1, 1, 1, 1])  # Agregada columna para Deuda
               
                with cols[0]:
                    # Mostrar nombre del miembro
                    st.write(f"**{nombre_miembro}**")
               
                with cols[1]:
                    # OBTENER EL SALDO INICIAL CORREGIDO
                    saldo_inicial = obtener_saldo_inicial_corregido(id_miembro, fecha_reunion_actual)
                   
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
                    # OBTENER DEUDA DE PRÉSTAMOS PENDIENTES
                    deuda_pendiente = obtener_deuda_prestamo_pendiente(id_miembro, con)
                    deudas_miembros[id_miembro] = deuda_pendiente
                    
                    if deuda_pendiente > 0:
                        st.error(f"**${deuda_pendiente:,.2f}**")
                    else:
                        st.success(f"**$0.00**")
               
                with cols[5]:
                    # Checkbox para activar retiros
                    retiro_activado = st.checkbox(
                        "Activar retiro",
                        key=f"retiro_check_{id_miembro}",
                        value=False
                    )
                    retiros_activados[id_miembro] = retiro_activado
                   
                    if retiro_activado:
                        # CALCULAR RETIRO CONSIDERANDO DEUDA: (Saldo Inicial + Ahorros actuales + Otros actuales) - Deuda pendiente
                        total_acumulado = saldo_inicial + monto_ahorro + monto_otros
                        monto_retiros_calculado = max(0, total_acumulado - deuda_pendiente)
                       
                        # Mostrar el monto de retiro calculado
                        if deuda_pendiente > 0:
                            st.warning(f"**${monto_retiros_calculado:,.2f}**")
                            st.caption(f"💡 Con deuda: ${total_acumulado:,.2f} - ${deuda_pendiente:,.2f}")
                        else:
                            st.error(f"**${monto_retiros_calculado:,.2f}**")
                       
                        # Guardar el cálculo del retiro
                        montos_retiro_calculados[id_miembro] = monto_retiros_calculado
                        retiros_data[id_miembro] = monto_retiros_calculado
                    else:
                        monto_retiros = 0.00
                        st.info("**$0.00**")
                        retiros_data[id_miembro] = 0.00
                        montos_retiro_calculados[id_miembro] = 0.00
               
                with cols[6]:
                    # CALCULAR Y MOSTRAR SALDO FINAL CORREGIDO
                    if retiro_activado:
                        if deuda_pendiente > 0:
                            # Si hay deuda y retiro: Saldo final = Deuda pendiente (porque se usó el dinero para pagar la deuda)
                            saldo_final = deuda_pendiente
                        else:
                            # Si no hay deuda y hay retiro: Saldo final = 0
                            saldo_final = 0.00
                    else:
                        # Sin retiro: Saldo Inicial + Ahorros + Otros
                        saldo_final = saldo_inicial + monto_ahorro + monto_otros
                   
                    saldos_finales[id_miembro] = saldo_final
                   
                    # Mostrar saldo final con color según el resultado
                    if saldo_final == 0 and retiro_activado and deuda_pendiente == 0:
                        st.success(f"**${saldo_final:,.2f}** 🏁 RETIRADO")
                    elif saldo_final == deuda_pendiente and retiro_activado and deuda_pendiente > 0:
                        st.warning(f"**${saldo_final:,.2f}** 📋 DEUDA PENDIENTE")
                    elif saldo_final < 0:
                        st.error(f"**${saldo_final:,.2f}**")
                    else:
                        st.success(f"**${saldo_final:,.2f}**")

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
                        retiro_activado = retiros_activados.get(id_miembro, False)
                        saldo_final = saldos_finales.get(id_miembro, 0)
                        deuda_pendiente = deudas_miembros.get(id_miembro, 0)
                       
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
                                
                                # Mostrar mensaje detallado
                                if retiro_activado:
                                    if deuda_pendiente > 0:
                                        total_acumulado = saldo_inicial + monto_ahorro + monto_otros
                                        st.success(f"✅ {nombre_miembro}: (${saldo_inicial:,.2f} + ${monto_ahorro:,.2f} + ${monto_otros:,.2f}) - ${deuda_pendiente:,.2f} = ${monto_retiros:,.2f} RETIRADO | Deuda pendiente: ${deuda_pendiente:,.2f}")
                                    else:
                                        st.success(f"✅ {nombre_miembro}: ${saldo_inicial:,.2f} + ${monto_ahorro:,.2f} + ${monto_otros:,.2f} - ${monto_retiros:,.2f} = ${saldo_final:,.2f} (RETIRADO)")
                                else:
                                    st.success(f"✅ {nombre_miembro}: ${saldo_inicial:,.2f} + ${monto_ahorro:,.2f} + ${monto_otros:,.2f} = ${saldo_final:,.2f}")
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
                                if retiro_activado:
                                    if deuda_pendiente > 0:
                                        total_acumulado = saldo_inicial + monto_ahorro + monto_otros
                                        st.success(f"✅ {nombre_miembro}: Registro actualizado - (${saldo_inicial:,.2f} + ${monto_ahorro:,.2f} + ${monto_otros:,.2f}) - ${deuda_pendiente:,.2f} = ${monto_retiros:,.2f} RETIRADO | Deuda pendiente: ${deuda_pendiente:,.2f}")
                                    else:
                                        st.success(f"✅ {nombre_miembro}: Registro actualizado - ${saldo_inicial:,.2f} + ${monto_ahorro:,.2f} + ${monto_otros:,.2f} - ${monto_retiros:,.2f} = ${saldo_final:,.2f} (RETIRADO)")
                                else:
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
