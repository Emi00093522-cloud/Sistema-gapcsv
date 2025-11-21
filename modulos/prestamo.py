import streamlit as st
from modulos.config.conexion import obtener_conexion
from datetime import datetime

def mostrar_prestamo():
    st.header("💰 Gestión de Préstamos")
    
    # Crear pestañas para diferentes formas de registrar préstamos
    tab1, tab2 = st.tabs(["📋 Por Grupo", "✏️ Formulario Directo"])
    
    with tab1:
        _mostrar_prestamo_por_grupo()
    
    with tab2:
        _mostrar_formulario_directo()

def _mostrar_prestamo_por_grupo():
    """Muestra la interfaz para seleccionar grupo y luego miembros"""
    st.subheader("📋 Seleccionar Grupo y Miembro")
    
    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        # Cargar grupos disponibles
        cursor.execute("""
            SELECT g.ID_Grupo, g.nombre as grupo_nombre, d.nombre as distrito_nombre
            FROM Grupo g
            JOIN Distrito d ON g.ID_Distrito = d.ID_Distrito
            ORDER BY d.nombre, g.nombre
        """)
        grupos = cursor.fetchall()
        
        if not grupos:
            st.warning("No hay grupos registrados en el sistema.")
            return
        
        # Seleccionar grupo
        grupo_options = {f"{g['grupo_nombre']} - {g['distrito_nombre']}": g['ID_Grupo'] for g in grupos}
        grupo_seleccionado = st.selectbox("Selecciona un grupo:", list(grupo_options.keys()))
        id_grupo_seleccionado = grupo_options[grupo_seleccionado]
        
        # Cargar miembros del grupo seleccionado
        cursor.execute("""
            SELECT ID_Miembro, nombre, apellido, telefono, correo
            FROM Miembro 
            WHERE ID_Grupo = %s AND ID_Estado = 1
            ORDER BY nombre, apellido
        """, (id_grupo_seleccionado,))
        miembros = cursor.fetchall()
        
        if not miembros:
            st.info("Este grupo no tiene miembros activos.")
            return
        
        st.subheader(f"👥 Miembros del Grupo ({len(miembros)})")
        
        # Mostrar lista de miembros con información y botón para agregar préstamo
        for miembro in miembros:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Información del miembro
                st.write(f"**{miembro['nombre']} {miembro.get('apellido', '')}**")
                if miembro.get('telefono'):
                    st.caption(f"📞 {miembro['telefono']}")
                if miembro.get('correo'):
                    st.caption(f"📧 {miembro['correo']}")
            
            with col2:
                # Botón para agregar préstamo a este miembro
                if st.button("💰 Agregar Préstamo", key=f"btn_{miembro['ID_Miembro']}"):
                    st.session_state['miembro_seleccionado'] = {
                        'id': miembro['ID_Miembro'],
                        'nombre': f"{miembro['nombre']} {miembro.get('apellido', '')}",
                        'grupo_id': id_grupo_seleccionado
                    }
                    st.rerun()
        
        # Línea separadora
        st.markdown("---")
        
        # Si hay un miembro seleccionado, mostrar el formulario de préstamo
        if 'miembro_seleccionado' in st.session_state:
            miembro = st.session_state['miembro_seleccionado']
            st.subheader(f"✏️ Nuevo Préstamo para: {miembro['nombre']}")
            _mostrar_formulario_prestamo(
                id_miembro_predefinido=miembro['id'],
                miembro_nombre_predefinido=miembro['nombre']
            )
            
            # Botón para cancelar y volver a la lista
            if st.button("❌ Cancelar y volver a la lista"):
                del st.session_state['miembro_seleccionado']
                st.rerun()
    
    except Exception as e:
        st.error(f"❌ Error al cargar grupos y miembros: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'con' in locals():
            con.close()

def _mostrar_formulario_directo():
    """Muestra el formulario tradicional de préstamo"""
    st.subheader("✏️ Formulario de Préstamo")
    
    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)

        # Cargar todos los miembros activos
        cursor.execute("SELECT ID_Miembro, nombre, apellido FROM Miembro WHERE ID_Estado = 1 ORDER BY nombre, apellido")
        miembros = cursor.fetchall()

        cursor.execute("SELECT ID_Estado_prestamo, estado_prestamo FROM Estado_prestamo")
        estados_prestamo = cursor.fetchall()

        with st.form("form_prestamo_directo"):
            # MIEMBRO
            if miembros:
                miembro_options = {f"{m['nombre']} {m.get('apellido', '')} (ID: {m['ID_Miembro']})": m['ID_Miembro'] for m in miembros}
                miembro_seleccionado = st.selectbox("Miembro *", list(miembro_options.keys()))
                ID_Miembro = miembro_options[miembro_seleccionado]
            else:
                st.error("❌ No hay miembros disponibles")
                ID_Miembro = None

            # FECHA
            fecha_desembolso = st.date_input("Fecha de desembolso *", value=datetime.now().date())

            # MONTO
            monto = st.number_input("Monto del préstamo ($) *",
                                    min_value=0.01,
                                    value=1000.00,
                                    step=100.00,
                                    format="%.2f")

            # TASA DE INTERÉS MENSUAL
            tasa_mensual = st.number_input("Tasa de interés MENSUAL (%) *",
                                           min_value=0.00,
                                           max_value=100.00,
                                           value=5.00,
                                           step=0.10,
                                           format="%.2f")

            # ESTADO PRÉSTAMO
            if estados_prestamo:
                estado_options = {e["estado_prestamo"]: e["ID_Estado_prestamo"] for e in estados_prestamo}
                estado_seleccionado = st.selectbox("Estado del préstamo *", list(estado_options.keys()))
                ID_Estado_prestamo = estado_options[estado_seleccionado]
            else:
                st.error("❌ No hay estados de préstamo disponibles")
                ID_Estado_prestamo = None

            # PLAZO
            plazo = st.number_input("Plazo (meses) *", min_value=1, max_value=120, value=6, step=1)

            # PROPÓSITO
            proposito = st.text_area("Propósito del préstamo (opcional)",
                                     placeholder="Ej: Compra de materiales, gastos médicos…",
                                     max_chars=200,
                                     height=80)

            # ================================
            # CÁLCULOS DE INTERÉS MENSUAL SIMPLE
            # ================================
            if monto > 0 and plazo > 0:
                # Convertir tasa mensual a decimal
                tasa_decimal = tasa_mensual / 100

                # Interés de un mes
                interes_mensual = monto * tasa_decimal

                # Interés total
                interes_total = interes_mensual * plazo

                # Total a pagar
                monto_total = monto + interes_total

                # Cuota fija mensual simple
                cuota_mensual = monto_total / plazo

                st.info("📊 **Resumen del préstamo:**")
                st.write(f"- Tasa mensual: **{tasa_mensual:.2f}%**")
                st.write(f"- Interés mensual: **${interes_mensual:,.2f}**")
                st.write(f"- Interés total a pagar: **${interes_total:,.2f}**")
                st.write(f"- Monto total a pagar: **${monto_total:,.2f}**")
                st.write(f"- 💵 **Cuota mensual: ${cuota_mensual:,.2f}**")

            enviar = st.form_submit_button("✅ Registrar Préstamo")

            if enviar:
                errores = []

                if ID_Miembro is None:
                    errores.append("⚠ Debes seleccionar un miembro.")
                if monto <= 0:
                    errores.append("⚠ El monto debe ser mayor a 0.")
                if tasa_mensual < 0:
                    errores.append("⚠ La tasa mensual no puede ser negativa.")
                if plazo <= 0:
                    errores.append("⚠ El plazo debe ser mayor a 0.")
                if ID_Estado_prestamo is None:
                    errores.append("⚠ Debes seleccionar un estado del préstamo.")

                if errores:
                    for e in errores:
                        st.warning(e)
                else:
                    try:
                        proposito_val = proposito.strip() if proposito.strip() else None

                        cursor.execute("""
                            INSERT INTO Prestamo
                            (ID_Miembro, fecha_desembolso, monto, total_interes,
                             ID_Estado_prestamo, plazo, proposito)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (ID_Miembro, fecha_desembolso, monto, tasa_mensual,
                              ID_Estado_prestamo, plazo, proposito_val))

                        con.commit()

                        st.success("✅ Préstamo registrado correctamente!")
                        st.success(f"- Interés total: ${interes_total:,.2f}")
                        st.success(f"- Cuota mensual: ${cuota_mensual:,.2f}")

                        if st.button("🆕 Registrar otro préstamo"):
                            st.rerun()

                    except Exception as e:
                        con.rollback()
                        st.error(f"❌ Error al registrar el préstamo: {e}")

    except Exception as e:
        st.error(f"❌ Error general: {e}")
    finally:
        if "cursor" in locals():
            cursor.close()
        if "con" in locals():
            con.close()

def _mostrar_formulario_prestamo(id_miembro_predefinido=None, miembro_nombre_predefinido=None):
    """Muestra el formulario de préstamo con miembro predefinido"""
    
    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)

        # Cargar estados de préstamo
        cursor.execute("SELECT ID_Estado_prestamo, estado_prestamo FROM Estado_prestamo")
        estados_prestamo = cursor.fetchall()

        with st.form("form_prestamo_miembro"):
            # Mostrar miembro predefinido
            if id_miembro_predefinido and miembro_nombre_predefinido:
                st.success(f"**Miembro seleccionado:** {miembro_nombre_predefinido}")
                ID_Miembro = id_miembro_predefinido
            else:
                st.error("No se ha seleccionado un miembro válido")
                ID_Miembro = None

            # FECHA
            fecha_desembolso = st.date_input("Fecha de desembolso *", value=datetime.now().date())

            # MONTO
            monto = st.number_input("Monto del préstamo ($) *",
                                    min_value=0.01,
                                    value=1000.00,
                                    step=100.00,
                                    format="%.2f")

            # TASA DE INTERÉS MENSUAL
            tasa_mensual = st.number_input("Tasa de interés MENSUAL (%) *",
                                           min_value=0.00,
                                           max_value=100.00,
                                           value=5.00,
                                           step=0.10,
                                           format="%.2f")

            # ESTADO PRÉSTAMO
            if estados_prestamo:
                estado_options = {e["estado_prestamo"]: e["ID_Estado_prestamo"] for e in estados_prestamo}
                estado_seleccionado = st.selectbox("Estado del préstamo *", list(estado_options.keys()))
                ID_Estado_prestamo = estado_options[estado_seleccionado]
            else:
                st.error("❌ No hay estados de préstamo disponibles")
                ID_Estado_prestamo = None

            # PLAZO
            plazo = st.number_input("Plazo (meses) *", min_value=1, max_value=120, value=6, step=1)

            # PROPÓSITO
            proposito = st.text_area("Propósito del préstamo (opcional)",
                                     placeholder="Ej: Compra de materiales, gastos médicos…",
                                     max_chars=200,
                                     height=80)

            # ================================
            # CÁLCULOS DE INTERÉS MENSUAL SIMPLE
            # ================================
            if monto > 0 and plazo > 0:
                # Convertir tasa mensual a decimal
                tasa_decimal = tasa_mensual / 100

                # Interés de un mes
                interes_mensual = monto * tasa_decimal

                # Interés total
                interes_total = interes_mensual * plazo

                # Total a pagar
                monto_total = monto + interes_total

                # Cuota fija mensual simple
                cuota_mensual = monto_total / plazo

                st.info("📊 **Resumen del préstamo:**")
                st.write(f"- Tasa mensual: **{tasa_mensual:.2f}%**")
                st.write(f"- Interés mensual: **${interes_mensual:,.2f}**")
                st.write(f"- Interés total a pagar: **${interes_total:,.2f}**")
                st.write(f"- Monto total a pagar: **${monto_total:,.2f}**")
                st.write(f"- 💵 **Cuota mensual: ${cuota_mensual:,.2f}**")

            enviar = st.form_submit_button("✅ Registrar Préstamo")

            if enviar:
                errores = []

                if ID_Miembro is None:
                    errores.append("⚠ Debes seleccionar un miembro.")
                if monto <= 0:
                    errores.append("⚠ El monto debe ser mayor a 0.")
                if tasa_mensual < 0:
                    errores.append("⚠ La tasa mensual no puede ser negativa.")
                if plazo <= 0:
                    errores.append("⚠ El plazo debe ser mayor a 0.")
                if ID_Estado_prestamo is None:
                    errores.append("⚠ Debes seleccionar un estado del préstamo.")

                if errores:
                    for e in errores:
                        st.warning(e)
                else:
                    try:
                        proposito_val = proposito.strip() if proposito.strip() else None

                        cursor.execute("""
                            INSERT INTO Prestamo
                            (ID_Miembro, fecha_desembolso, monto, total_interes,
                             ID_Estado_prestamo, plazo, proposito)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """, (ID_Miembro, fecha_desembolso, monto, tasa_mensual,
                              ID_Estado_prestamo, plazo, proposito_val))

                        con.commit()

                        st.success("✅ Préstamo registrado correctamente!")
                        st.success(f"- Interés total: ${interes_total:,.2f}")
                        st.success(f"- Cuota mensual: ${cuota_mensual:,.2f}")

                        # Limpiar selección después de guardar
                        if 'miembro_seleccionado' in st.session_state:
                            del st.session_state['miembro_seleccionado']
                        
                        if st.button("🆕 Registrar otro préstamo"):
                            st.rerun()

                    except Exception as e:
                        con.rollback()
                        st.error(f"❌ Error al registrar el préstamo: {e}")

    except Exception as e:
        st.error(f"❌ Error general: {e}")
    finally:
        if "cursor" in locals():
            cursor.close()
        if "con" in locals():
            con.close()
