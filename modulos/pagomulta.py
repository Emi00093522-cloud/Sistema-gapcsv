import streamlit as st
from modulos.config.conexion import obtener_conexion
from datetime import datetime

def mostrar_pago_multas():
    st.header("💵 Pago de Multas")
    
    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        # Obtener grupos para filtrar
        cursor.execute("SELECT ID_Grupo, nombre FROM Grupo")
        grupos = cursor.fetchall()
        
        if not grupos:
            st.warning("No hay grupos registrados.")
            return
            
        grupo_options = {f"{g['nombre']}": g['ID_Grupo'] for g in grupos}
        grupo_seleccionado_nombre = st.selectbox("Seleccionar Grupo", list(grupo_options.keys()))
        grupo_seleccionado = grupo_options[grupo_seleccionado_nombre]
        
        if grupo_seleccionado:
            # Obtener multas pendientes del grupo
            cursor.execute("""
                SELECT 
                    mxm.ID_Miembro,
                    mxm.ID_Multa,
                    mxm.monto_a_pagar,
                    mxm.monto_pagado,
                    CONCAT(m.nombre, ' ', m.apellido) as nombre_completo,
                    mu.fecha as fecha_multa,
                    r.nombre as nombre_reunion,
                    (mxm.monto_a_pagar - mxm.monto_pagado) as saldo_pendiente
                FROM MiembroxMulta mxm
                JOIN Miembro m ON mxm.ID_Miembro = m.ID_Miembro
                JOIN Multa mu ON mxm.ID_Multa = mu.ID_Multa
                JOIN Reunion r ON mu.ID_Reunion = r.ID_Reunion
                WHERE m.ID_Grupo = %s 
                AND mxm.monto_pagado < mxm.monto_a_pagar
                ORDER BY m.nombre, mu.fecha
            """, (grupo_seleccionado,))
            
            multas_pendientes = cursor.fetchall()
            
            if multas_pendientes:
                st.subheader("📋 Multas Pendientes de Pago")
                
                total_pendiente = sum(multa['saldo_pendiente'] for multa in multas_pendientes)
                st.info(f"**Total pendiente por cobrar:** ${total_pendiente:,.2f}")
                
                for multa in multas_pendientes:
                    with st.expander(f"🧾 {multa['nombre_completo']} - ${multa['saldo_pendiente']:,.2f} pendientes", expanded=False):
                        col1, col2, col3 = st.columns([2, 2, 1])
                        
                        with col1:
                            st.write(f"**Reunión:** {multa['nombre_reunion']}")
                            st.write(f"**Fecha multa:** {multa['fecha_multa']}")
                            st.write(f"**Miembro:** {multa['nombre_completo']}")
                        
                        with col2:
                            st.write(f"**Monto total:** ${multa['monto_a_pagar']:,.2f}")
                            st.write(f"**Pagado:** ${multa['monto_pagado']:,.2f}")
                            st.write(f"**Saldo pendiente:** ${multa['saldo_pendiente']:,.2f}")
                        
                        with col3:
                            monto_pago = st.number_input(
                                f"Monto a pagar",
                                min_value=0.0,
                                max_value=float(multa['saldo_pendiente']),
                                value=float(multa['saldo_pendiente']),
                                step=10.0,
                                key=f"pago_{multa['ID_Miembro']}_{multa['ID_Multa']}"
                            )
                            
                            if st.button("💳 Registrar Pago", key=f"btn_{multa['ID_Miembro']}_{multa['ID_Multa']}"):
                                try:
                                    # Actualizar el monto pagado
                                    nuevo_monto_pagado = multa['monto_pagado'] + monto_pago
                                    
                                    cursor.execute("""
                                        UPDATE MiembroxMulta 
                                        SET monto_pagado = %s 
                                        WHERE ID_Miembro = %s AND ID_Multa = %s
                                    """, (nuevo_monto_pagado, multa['ID_Miembro'], multa['ID_Multa']))
                                    
                                    con.commit()
                                    st.success(f"✅ Pago de ${monto_pago:,.2f} registrado para {multa['nombre_completo']}")
                                    st.rerun()
                                    
                                except Exception as e:
                                    con.rollback()
                                    st.error(f"❌ Error al registrar pago: {e}")
            else:
                st.success("🎉 No hay multas pendientes de pago en este grupo")
                
    except Exception as e:
        st.error(f"❌ Error: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'con' in locals():
            con.close()
