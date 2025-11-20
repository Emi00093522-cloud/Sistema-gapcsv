import streamlit as st
from modulos.config.conexion import obtener_conexion
from datetime import datetime

def mostrar_prestamo():
    st.header("💰 Registrar Préstamo")

    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)

        # Cargar miembros
        cursor.execute("SELECT ID_Miembro, nombre FROM Miembro WHERE ID_Estado = 1")
        miembros = cursor.fetchall()
        
        # Cargar estados de préstamo
        cursor.execute("SELECT ID_Estado_prestamo, estado_prestamo FROM Estado_prestamo")
        estados_prestamo = cursor.fetchall()

        # Formulario para registrar el préstamo
        with st.form("form_prestamo"):
            st.subheader("Datos del Préstamo")
            
            # Campo 2: ID_Miembro
            if miembros:
                miembro_options = {f"{miembro['nombre']} (ID: {miembro['ID_Miembro']})": miembro['ID_Miembro'] for miembro in miembros}
                miembro_seleccionado = st.selectbox("Miembro *", options=list(miembro_options.keys()))
                ID_Miembro = miembro_options[miembro_seleccionado]
            else:
                st.error("❌ No hay miembros disponibles")
                ID_Miembro = None
            
            # Campo 3: fecha_desembolso
            fecha_desembolso = st.date_input("Fecha de desembolso *", value=datetime.now().date())
            
            # Campo 4: monto
            monto = st.number_input("Monto del préstamo ($) *", 
                                  min_value=0.01, 
                                  value=1000.00, 
                                  step=100.00,
                                  format="%.2f")
            
            # Campo 5: total_interes (%)
            total_interes = st.number_input("Tasa de interés (%) *", 
                                          min_value=0.00, 
                                          max_value=100.00,
                                          value=10.00, 
                                          step=0.5,
                                          format="%.2f",
                                          help="Porcentaje de interés anual")
            
            # Campo 6: ID_Estado_prestamo
            if estados_prestamo:
                estado_options = {f"{estado['estado_prestamo']}": estado['ID_Estado_prestamo'] for estado in estados_prestamo}
                estado_seleccionado = st.selectbox("Estado del préstamo *", options=list(estado_options.keys()))
                ID_Estado_prestamo = estado_options[estado_seleccionado]
            else:
                st.error("❌ No hay estados de préstamo disponibles")
                ID_Estado_prestamo = None
            
            # Campo 7: plazo
            plazo = st.number_input("Plazo (meses) *", 
                                  min_value=1, 
                                  max_value=120, 
                                  value=12, 
                                  step=1)
            
            # Campo 8: proposito
            proposito = st.text_area("Propósito del préstamo (opcional)", 
                                   placeholder="Ej: Compra de materiales, Gastos médicos, Educación...",
                                   max_chars=200,
                                   height=80)
            
            # Resumen
            if monto > 0 and total_interes > 0 and plazo > 0:
                interes_mensual = (monto * (total_interes / 100)) / 12
                interes_total = interes_mensual * plazo
                monto_total = monto + interes_total
                
                st.info(f"**📊 Resumen del préstamo:**")
                st.write(f"- Interés mensual: ${interes_mensual:,.2f}")
                st.write(f"- Interés total a pagar: ${interes_total:,.2f}")
                st.write(f"- Monto total a pagar: ${monto_total:,.2f}")
            
            enviar = st.form_submit_button("✅ Registrar Préstamo")

            if enviar:
                errores = []
                
                if ID_Miembro is None:
                    errores.append("⚠ Debes seleccionar un miembro.")
                if fecha_desembolso is None:
                    errores.append("⚠ Debes seleccionar una fecha de desembolso.")
                if monto <= 0:
                    errores.append("⚠ El monto debe ser mayor a 0.")
                if total_interes < 0:
                    errores.append("⚠ La tasa de interés no puede ser negativa.")
                if plazo <= 0:
                    errores.append("⚠ El plazo debe ser mayor a 0.")
                if ID_Estado_prestamo is None:
                    errores.append("⚠ Debes seleccionar un estado del préstamo.")
                
                if errores:
                    for error in errores:
                        st.warning(error)
                else:
                    try:
                        proposito_val = proposito.strip() if proposito.strip() else None
                        
                        cursor.execute(
                            """INSERT INTO Prestamo 
                            (ID_Miembro, fecha_desembolso, monto, total_interes, 
                             ID_Estado_prestamo, plazo, proposito) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                            (ID_Miembro, fecha_desembolso, monto, total_interes,
                             ID_Estado_prestamo, plazo, proposito_val)
                        )
                        
                        con.commit()

                        st.success("¡Préstamo registrado correctamente!")
                        st.info("Si deseas registrar otro préstamo, usa el botón de abajo.")

        # 🔵 Segundo formulario solo para reiniciar
        with st.form("nuevo_prestamo"):
            nuevo = st.form_submit_button("🆕 Registrar otro préstamo")
            if nuevo:
                st.rerun()

    except Exception as e:
        st.error(f"❌ Error general: {e}")

    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'con' in locals():
            con.close()
