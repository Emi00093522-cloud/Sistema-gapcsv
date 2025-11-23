import streamlit as st
from modulos.config.conexion import obtener_conexion
from datetime import datetime
from decimal import Decimal

def mostrar_pago_multas():
    st.header("💵 Pago de Multas")
    
    # Verificar si hay una reunión seleccionada
    if 'reunion_actual' not in st.session_state:
        st.warning("⚠️ Primero debes seleccionar una reunión en el módulo de Asistencia o Multas.")
        return

    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)

        # Obtener la reunión del session_state
        reunion_info = st.session_state.reunion_actual
        id_reunion = reunion_info['id_reunion']
        id_grupo = reunion_info['id_grupo']
        nombre_reunion = reunion_info['nombre_reunion']

        st.info(f"📅 **Reunión actual:** {nombre_reunion}")

        # Obtener SOLO las multas registradas para esta reunión específica
        cursor.execute("""
            SELECT 
                mxm.ID_Miembro,
                mxm.ID_Multa,
                mxm.monto_a_pagar,
                mxm.monto_pagado,
                CONCAT(m.nombre, ' ', m.apellido) as nombre_completo,
                mu.fecha as fecha_multa,
                r.fecha as fecha_reunion,
                (mxm.monto_a_pagar - mxm.monto_pagado) as saldo_pendiente,
                mr.justificacion
            FROM MiembroxMulta mxm
            JOIN Miembro m ON mxm.ID_Miembro = m.ID_Miembro
            JOIN Multa mu ON mxm.ID_Multa = mu.ID_Multa
            JOIN Reunion r ON mu.ID_Reunion = r.ID_Reunion
            LEFT JOIN Miembroxreunion mr ON m.ID_Miembro = mr.ID_Miembro AND mr.ID_Reunion = %s
            WHERE mu.ID_Reunion = %s 
            AND mxm.monto_pagado < mxm.monto_a_pagar
            ORDER BY m.nombre, m.apellido
        """, (id_reunion, id_reunion))
        
        multas_pendientes = cursor.fetchall()
        
        if multas_pendientes:
            st.subheader("📋 Multas Pendientes de Pago")
            
            # Mostrar resumen
            total_pendiente = sum(float(multa['saldo_pendiente']) for multa in multas_pendientes)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("👥 Total Miembros", len(multas_pendientes))
            with col2:
                st.metric("💰 Total Pendiente", f"${total_pendiente:,.2f}")
            with col3:
                miembros_pagados = len([m for m in multas_pendientes if float(m['monto_pagado']) > 0])
                st.metric("✅ Con Pagos", miembros_pagados)

            # Mostrar cada multa pendiente
            for multa in multas_pendientes:
                # Convertir a float para evitar problemas de tipo
                monto_a_pagar = float(multa['monto_a_pagar'])
                monto_pagado = float(multa['monto_pagado'])
                saldo_pendiente = float(multa['saldo_pendiente'])
                
                # Crear un contenedor para cada multa
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                    
                    with col1:
                        st.write(f"**{multa['nombre_completo']}**")
                        if multa['justificacion']:
                            st.caption(f"📝 Justificación: {multa['justificacion']}")
                    
                    with col2:
                        st.write(f"**Monto:** ${monto_a_pagar:,.2f}")
                        st.write(f"**Pagado:** ${monto_pagado:,.2f}")
                    
                    with col3:
                        st.write(f"**Saldo:** ${saldo_pendiente:,.2f}")
                        if monto_pagado > 0:
                            st.success(f"✅ ${monto_pagado:,.2f} pagados")
                    
                    with col4:
                        # Opciones de pago
                        if saldo_pendiente > 0:
                            monto_pago = st.number_input(
                                "Monto a pagar",
                                min_value=0.0,
                                max_value=saldo_pendiente,
                                value=saldo_pendiente,
                                step=10.0,
                                key=f"pago_{multa['ID_Miembro']}_{multa['ID_Multa']}"
                            )
                            
                            if st.button("💳 Pagar", key=f"btn_{multa['ID_Miembro']}_{multa['ID_Multa']}"):
                                try:
                                    # CORRECCIÓN: Calcular el nuevo monto pagado correctamente
                                    nuevo_monto_pagado = monto_pagado + monto_pago
                                    
                                    cursor.execute("""
                                        UPDATE MiembroxMulta 
                                        SET monto_pagado = %s 
                                        WHERE ID_Miembro = %s AND ID_Multa = %s
                                    """, (Decimal(str(nuevo_monto_pagado)), multa['ID_Miembro'], multa['ID_Multa']))
                                    
                                    # Registrar en historial si la tabla existe
                                    try:
                                        cursor.execute("""
                                            INSERT INTO PagoMulta 
                                            (ID_Miembro, ID_Multa, monto_pagado, fecha_pago, ID_Reunion_pago) 
                                            VALUES (%s, %s, %s, %s, %s)
                                        """, (multa['ID_Miembro'], multa['ID_Multa'], Decimal(str(monto_pago)), 
                                              datetime.now().date(), id_reunion))
                                    except Exception as hist_error:
                                        # Si la tabla PagoMulta no existe, continuar sin error
                                        pass
                                    
                                    con.commit()
                                    st.success(f"✅ Pago de ${monto_pago:,.2f} registrado para {multa['nombre_completo']}")
                                    st.rerun()
                                    
                                except Exception as e:
                                    con.rollback()
                                    st.error(f"❌ Error al registrar pago: {e}")
                        else:
                            st.success("✅ Pagado completamente")
                    
                    st.divider()
            
            # Botón para pagar todas las multas pendientes
            st.subheader("Pago Masivo")
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("💳 Pagar Todas las Multas", type="primary", use_container_width=True):
                    try:
                        multas_pagadas = 0
                        total_pagado = 0
                        
                        for multa in multas_pendientes:
                            saldo_pendiente = float(multa['saldo_pendiente'])
                            if saldo_pendiente > 0:
                                # Pagar todo el saldo pendiente
                                monto_a_pagar = Decimal(str(multa['monto_a_pagar']))
                                
                                cursor.execute("""
                                    UPDATE MiembroxMulta 
                                    SET monto_pagado = %s 
                                    WHERE ID_Miembro = %s AND ID_Multa = %s
                                """, (monto_a_pagar, multa['ID_Miembro'], multa['ID_Multa']))
                                
                                multas_pagadas += 1
                                total_pagado += saldo_pendiente
                        
                        con.commit()
                        st.success(f"✅ Se pagaron {multas_pagadas} multas por un total de ${total_pagado:,.2f}")
                        st.rerun()
                        
                    except Exception as e:
                        con.rollback()
                        st.error(f"❌ Error al realizar pago masivo: {e}")
                        
        else:
            st.success("🎉 No hay multas pendientes de pago para esta reunión")
            st.info("💡 Las multas se generan automáticamente cuando registras ausentes en el módulo de Multas")
                
    except Exception as e:
        st.error(f"❌ Error: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'con' in locals():
            con.close()
