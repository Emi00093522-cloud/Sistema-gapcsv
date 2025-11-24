import streamlit as st
from modulos.config.conexion import obtener_conexion
from datetime import datetime

def mostrar_movimiento_caja():
    st.header("💰 Movimientos de Caja")

    # Verificar si hay una reunión seleccionada
    if 'reunion_actual' not in st.session_state:
        st.warning("⚠️ Primero debes seleccionar una reunión en el módulo de Asistencia.")
        return

    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)

        # Obtener la reunión del session_state
        reunion_info = st.session_state.reunion_actual
        id_reunion = reunion_info['id_reunion']
        id_grupo = reunion_info['id_grupo']
        nombre_reunion = reunion_info['nombre_reunion']

        # Mostrar información de la reunión actual
        st.info(f"📅 **Reunión actual:** {nombre_reunion}")

        # Pestañas para diferentes funcionalidades
        tab1, tab2, tab3 = st.tabs(["📥 Registrar Movimiento", "📋 Ver Movimientos", "📊 Resumen de Caja"])

        with tab1:
            registrar_movimiento(cursor, con, id_reunion)

        with tab2:
            ver_movimientos(cursor, id_reunion)

        with tab3:
            resumen_caja(cursor, id_reunion)

    except Exception as e:
        st.error(f"❌ Error general: {e}")

    finally:
        if "cursor" in locals():
            cursor.close()
        if "con" in locals():
            con.close()

def registrar_movimiento(cursor, con, id_reunion):
    st.subheader("➕ Registrar Nuevo Movimiento")

    # Cargar tipos de movimiento desde tu tabla Tipo_de_movimiento
    cursor.execute("""
        SELECT ID_Tipo_movimiento, nombre_movimiento, tipo_ingreso_egreso 
        FROM Tipo_de_movimiento 
        WHERE estado = 1 
        ORDER BY tipo_ingreso_egreso, nombre_movimiento
    """)
    tipos_movimiento = cursor.fetchall()

    if not tipos_movimiento:
        st.error("❌ No hay tipos de movimiento configurados en el catálogo")
        return

    with st.form("form_movimiento_caja"):
        col1, col2 = st.columns(2)

        with col1:
            # Tipo de movimiento (Ingreso/Egreso)
            tipo_options = list(set([tm['tipo_ingreso_egreso'] for tm in tipos_movimiento]))
            tipo_seleccionado = st.selectbox("Tipo de movimiento *", tipo_options)

            # Filtrar categorías por tipo seleccionado
            categorias_filtradas = [tm for tm in tipos_movimiento if tm['tipo_ingreso_egreso'] == tipo_seleccionado]
            categoria_options = {f"{cat['nombre_movimiento']}": cat['ID_Tipo_movimiento'] for cat in categorias_filtradas}
            
            if categoria_options:
                categoria_seleccionada = st.selectbox("Categoría *", list(categoria_options.keys()))
                ID_Tipo_movimiento = categoria_options[categoria_seleccionada]
            else:
                st.error("❌ No hay categorías disponibles para este tipo")
                ID_Tipo_movimiento = None

            # Monto
            monto = st.number_input("Monto ($) *",
                                   min_value=0.01,
                                   value=100.00,
                                   step=50.00,
                                   format="%.2f")

        with col2:
            # Fecha
            fecha_movimiento = st.date_input("Fecha del movimiento *", value=datetime.now().date())

            # Categoría manual (para movimientos especiales)
            categoria_manual = st.text_input("Categoría personalizada (opcional)",
                                           placeholder="Ej: Donación, Gasto imprevisto...")

        # Descripción
        descripcion = st.text_area("Descripción del movimiento *",
                                 placeholder="Ej: Pago de préstamo de Juan Pérez, Ahorro semanal, Multa por tardanza...",
                                 max_chars=200,
                                 height=60)

        enviar = st.form_submit_button("💾 Registrar Movimiento")

        if enviar:
            errores = []

            if ID_Tipo_movimiento is None:
                errores.append("⚠ Debes seleccionar una categoría.")
            if monto <= 0:
                errores.append("⚠ El monto debe ser mayor a 0.")
            if not descripcion.strip():
                errores.append("⚠ La descripción es obligatoria.")

            if errores:
                for e in errores:
                    st.warning(e)
            else:
                try:
                    categoria_final = categoria_manual.strip() if categoria_manual.strip() else categoria_seleccionada

                    cursor.execute("""
                        INSERT INTO movimiento_caja 
                        (ID_Reunion, ID_Tipo_movimiento, monto, categoria, descripcion, fecha)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (id_reunion, ID_Tipo_movimiento, monto, categoria_final, descripcion.strip(), fecha_movimiento))

                    con.commit()

                    st.success("✅ Movimiento registrado correctamente!")
                    st.success(f"- Tipo: **{tipo_seleccionado}**")
                    st.success(f"- Categoría: **{categoria_final}**")
                    st.success(f"- Monto: **${monto:,.2f}**")

                    if st.button("🆕 Registrar otro movimiento", key="nuevo_movimiento"):
                        st.rerun()

                except Exception as e:
                    con.rollback()
                    st.error(f"❌ Error al registrar el movimiento: {e}")

def ver_movimientos(cursor, id_reunion):
    st.subheader("📋 Movimientos Registrados")

    col1, col2 = st.columns(2)
    
    with col1:
        filtro_tipo = st.selectbox("Filtrar por tipo", ["Todos", "Ingreso", "Egreso"], key="filtro_tipo")
    
    with col2:
        cursor.execute("""
            SELECT DISTINCT categoria 
            FROM movimiento_caja 
            WHERE ID_Reunion = %s 
            ORDER BY categoria
        """, (id_reunion,))
        categorias = cursor.fetchall()
        categorias_lista = ["Todas"] + [cat['categoria'] for cat in categorias]
        filtro_categoria = st.selectbox("Filtrar por categoría", categorias_lista)

    query = """
        SELECT mc.*, tm.tipo_ingreso_egreso as tipo, tm.nombre_movimiento
        FROM movimiento_caja mc
        JOIN Tipo_de_movimiento tm 
            ON mc.ID_Tipo_movimiento = tm.ID_Tipo_movimiento
        WHERE mc.ID_Reunion = %s
    """
    params = [id_reunion]

    if filtro_tipo != "Todos":
        query += " AND tm.tipo_ingreso_egreso = %s"
        params.append(filtro_tipo)

    if filtro_categoria != "Todas":
        query += " AND mc.categoria = %s"
        params.append(filtro_categoria)

    query += " ORDER BY mc.fecha DESC, mc.ID_Movimiento_caja DESC"

    cursor.execute(query, params)
    movimientos = cursor.fetchall()

    if not movimientos:
        st.info("📭 No hay movimientos registrados para esta reunión")
        return

    total_entradas = sum(mov['monto'] for mov in movimientos if mov['tipo'] == 'Ingreso')
    total_salidas = sum(mov['monto'] for mov in movimientos if mov['tipo'] == 'Egreso')
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("💰 Total Ingresos", f"${total_entradas:,.2f}")
    with col2:
        st.metric("💸 Total Egresos", f"${total_salidas:,.2f}")

    st.divider()

    for mov in movimientos:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                st.write(f"**{mov['descripcion']}**")
                st.caption(f"📁 {mov['categoria']} • 📅 {mov['fecha'].strftime('%d/%m/%Y %H:%M')}")

            with col2:
                tipo_color = "🟢" if mov['tipo'] == "Ingreso" else "🔴"
                st.write(f"{tipo_color} {mov['tipo']}")

            with col3:
                color = "color: green; font-weight: bold;" if mov['tipo'] == "Ingreso" else "color: red; font-weight: bold;"
                st.markdown(f"<p style='{color}'>${mov['monto']:,.2f}</p>", unsafe_allow_html=True)

            with col4:
                if st.button("🗑️", key=f"delete_{mov['ID_Movimiento_caja']}"):
                    eliminar_movimiento(cursor, con, mov['ID_Movimiento_caja'])
            
            st.divider()

def eliminar_movimiento(cursor, con, id_movimiento):
    try:
        cursor.execute("DELETE FROM movimiento_caja WHERE ID_Movimiento_caja = %s", (id_movimiento,))
        con.commit()
        st.success("✅ Movimiento eliminado correctamente")
        st.rerun()
    except Exception as e:
        con.rollback()
        st.error(f"❌ Error al eliminar el movimiento: {e}")

def resumen_caja(cursor, id_reunion):
    st.subheader("📊 Resumen de Caja")

    cursor.execute("""
        SELECT 
            tm.tipo_ingreso_egreso as tipo,
            mc.categoria,
            COUNT(*) as cantidad,
            SUM(mc.monto) as total
        FROM movimiento_caja mc
        JOIN Tipo_de_movimiento tm 
            ON mc.ID_Tipo_movimiento = tm.ID_Tipo_movimiento
        WHERE mc.ID_Reunion = %s
        GROUP BY tm.tipo_ingreso_egreso, mc.categoria
        ORDER BY tm.tipo_ingreso_egreso, total DESC
    """, (id_reunion,))
    
    resumen = cursor.fetchall()

    if not resumen:
        st.info("📭 No hay movimientos para mostrar en el resumen")
        return

    total_ingresos = sum(mov['total'] for mov in resumen if mov['tipo'] == 'Ingreso')
    total_egresos = sum(mov['total'] for mov in resumen if mov['tipo'] == 'Egreso')
    balance_final = total_ingresos - total_egresos

    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("💰 Total Ingresos", f"${total_ingresos:,.2f}")
    
    with col2:
        st.metric("💸 Total Egresos", f"${total_egresos:,.2f}")
    
    with col3:
        color = "normal" if balance_final >= 0 else "inverse"
        st.metric("⚖️ Balance Final", f"${balance_final:,.2f}", delta=None, delta_color=color)

    st.divider()

    st.subheader("📈 Detalle por Categoría")

    for tipo in ['Ingreso', 'Egreso']:
        movimientos_tipo = [mov for mov in resumen if mov['tipo'] == tipo]
        
        if movimientos_tipo:
            st.write(f"**{tipo.upper()}S**")
            
            for mov in movimientos_tipo:
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.write(f"📁 {mov['categoria']}")
                
                with col2:
                    st.write(f"${mov['total']:,.2f}")
                
                with col3:
                    st.write(f"({mov['cantidad']} movimientos)")
            
            st.divider()

def main():
    mostrar_movimiento_caja()

if __name__ == "__main__":
    main()
