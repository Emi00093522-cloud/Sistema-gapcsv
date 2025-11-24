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
        nombre_reunion = reunion_info.get('nombre_reunion', 'Reunión')

        st.info(f"📅 **Reunión actual:** {nombre_reunion}")

        tab1, tab2, tab3 = st.tabs(["📥 Registrar Movimiento", "📋 Ver Movimientos", "📊 Resumen de Caja"])

        with tab1:
            registrar_movimiento(cursor, con, id_reunion)

        with tab2:
            ver_movimientos(cursor, con, id_reunion)  # paso 'con' para poder eliminar

        with tab3:
            resumen_caja(cursor, id_reunion)

    except Exception as e:
        st.error(f"❌ Error general: {e}")

    finally:
        if "cursor" in locals():
            try:
                cursor.close()
            except:
                pass
        if "con" in locals():
            try:
                con.close()
            except:
                pass

def registrar_movimiento(cursor, con, id_reunion):
    st.subheader("➕ Registrar Nuevo Movimiento")

    # Obtener los tipos (Ingreso/Egreso) desde el catálogo Tipo_de_movimiento
    cursor.execute("""
        SELECT ID_Tipo_movimiento, tipo_movimiento
        FROM Tipo_de_movimiento
        ORDER BY tipo_movimiento
    """)
    tipos = cursor.fetchall()

    if not tipos:
        st.error("❌ No hay tipos (Ingreso/Egreso) configurados en el catálogo Tipo_de_movimiento.")
        return

    # Preparar opciones de tipo (Ingreso/Egreso) y mapping ID
    tipo_options = [t['tipo_movimiento'] for t in tipos]
    tipo_to_id = {t['tipo_movimiento']: t['ID_Tipo_movimiento'] for t in tipos}

    with st.form("form_movimiento_caja"):
        col1, col2 = st.columns(2)

        with col1:
            tipo_seleccionado = st.selectbox("Tipo de movimiento *", tipo_options)
            # Categoría ahora: texto libre (porque el catálogo solo indica Ingreso/Egreso)
            categoria = st.text_input("Categoría *", placeholder="Ej: Cuotas, Donación, Compra material...")
            monto = st.number_input("Monto ($) *",
                                   min_value=0.01,
                                   value=100.00,
                                   step=10.00,
                                   format="%.2f")

        with col2:
            fecha_movimiento = st.date_input("Fecha del movimiento *", value=datetime.now().date())
            descripcion = st.text_area("Descripción (opcional)", placeholder="Notas adicionales...", max_chars=300, height=120)

        enviar = st.form_submit_button("💾 Registrar Movimiento")

        if enviar:
            errores = []
            if not categoria.strip():
                errores.append("⚠ Debes indicar una categoría.")
            if monto <= 0:
                errores.append("⚠ El monto debe ser mayor a 0.")

            if errores:
                for e in errores:
                    st.warning(e)
                return

            try:
                ID_Tipo_movimiento = tipo_to_id.get(tipo_seleccionado)
                categoria_final = categoria.strip()
                descripcion_final = descripcion.strip() if descripcion else None

                cursor.execute("""
                    INSERT INTO movimiento_caja
                    (ID_Reunion, ID_Tipo_movimiento, monto, categoria, descripcion, fecha)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (id_reunion, ID_Tipo_movimiento, monto, categoria_final, descripcion_final, fecha_movimiento))

                con.commit()

                st.success("✅ Movimiento registrado correctamente!")
                st.info(f"- Tipo: **{tipo_seleccionado}** — Categoría: **{categoria_final}** — Monto: **${monto:,.2f}**")

                if st.button("🆕 Registrar otro movimiento", key="nuevo_movimiento"):
                    st.rerun()

            except Exception as e:
                con.rollback()
                st.error(f"❌ Error al registrar el movimiento: {e}")

def ver_movimientos(cursor, con, id_reunion):
    """
    Mostrar movimientos y permitir eliminar.
    """
    st.subheader("📋 Movimientos Registrados")

    # Filtros
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
        categorias_lista = ["Todas"] + [c['categoria'] for c in categorias if c.get('categoria')]
        filtro_categoria = st.selectbox("Filtrar por categoría", categorias_lista)

    # Query principal: join con Tipo_de_movimiento para obtener 'tipo_movimiento'
    query = """
        SELECT mc.*, tm.tipo_movimiento as tipo
        FROM movimiento_caja mc
        LEFT JOIN Tipo_de_movimiento tm ON mc.ID_Tipo_movimiento = tm.ID_Tipo_movimiento
        WHERE mc.ID_Reunion = %s
    """
    params = [id_reunion]

    if filtro_tipo != "Todos":
        query += " AND tm.tipo_movimiento = %s"
        params.append(filtro_tipo)

    if filtro_categoria != "Todas":
        query += " AND mc.categoria = %s"
        params.append(filtro_categoria)

    query += " ORDER BY mc.fecha DESC, mc.ID_Movimiento_caja DESC"

    cursor.execute(query, tuple(params))
    movimientos = cursor.fetchall()

    if not movimientos:
        st.info("📭 No hay movimientos registrados para esta reunión")
        return

    # Totales calculados a partir del campo tipo (Ingreso/Egreso) obtenido del join
    total_entradas = sum(m['monto'] for m in movimientos if m.get('tipo') == 'Ingreso')
    total_salidas = sum(m['monto'] for m in movimientos if m.get('tipo') == 'Egreso')

    c1, c2 = st.columns(2)
    with c1:
        st.metric("💰 Total Ingresos", f"${total_entradas:,.2f}")
    with c2:
        st.metric("💸 Total Egresos", f"${total_salidas:,.2f}")

    st.divider()

    for mov in movimientos:
        with st.container():
            col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
            with col1:
                desc = mov.get('descripcion') or ""
                st.write(f"**{desc}**")
                fecha = mov.get('fecha')
                try:
                    # fecha puede venir como date/datetime/string
                    if hasattr(fecha, "strftime"):
                        fecha_str = fecha.strftime('%d/%m/%Y')
                    else:
                        fecha_str = str(fecha)
                    st.caption(f"📁 {mov.get('categoria','')} • 📅 {fecha_str}")
                except Exception:
                    st.caption(f"📁 {mov.get('categoria','')} • 📅 {fecha}")
            with col2:
                tipo_color = "🟢" if mov.get('tipo') == "Ingreso" else "🔴"
                st.write(f"{tipo_color} {mov.get('tipo') or 'N/A'}")
            with col3:
                monto_style = "color: green; font-weight: bold;" if mov.get('tipo') == "Ingreso" else "color: red; font-weight: bold;"
                st.markdown(f"<p style='{monto_style}'>${mov['monto']:,.2f}</p>", unsafe_allow_html=True)
            with col4:
                # botón de eliminar: llama a eliminar_movimiento con cursor y con disponibles
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
            tm.tipo_movimiento AS tipo,
            mc.categoria,
            COUNT(*) as cantidad,
            SUM(mc.monto) as total
        FROM movimiento_caja mc
        LEFT JOIN Tipo_de_movimiento tm ON mc.ID_Tipo_movimiento = tm.ID_Tipo_movimiento
        WHERE mc.ID_Reunion = %s
        GROUP BY tm.tipo_movimiento, mc.categoria
        ORDER BY tm.tipo_movimiento, total DESC
    """, (id_reunion,))

    resumen = cursor.fetchall()

    if not resumen:
        st.info("📭 No hay movimientos para mostrar en el resumen")
        return

    total_ingresos = sum(r['total'] for r in resumen if r.get('tipo') == 'Ingreso')
    total_egresos = sum(r['total'] for r in resumen if r.get('tipo') == 'Egreso')
    balance_final = (total_ingresos or 0) - (total_egresos or 0)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💰 Total Ingresos", f"${total_ingresos:,.2f}")
    with col2:
        st.metric("💸 Total Egresos", f"${total_egresos:,.2f}")
    with col3:
        delta_color = "normal" if balance_final >= 0 else "inverse"
        st.metric("⚖️ Balance Final", f"${balance_final:,.2f}", delta=None, delta_color=delta_color)

    st.divider()
    st.subheader("📈 Detalle por Categoría")

    # Agrupar y mostrar por tipo
    for tipo in ['Ingreso', 'Egreso']:
        filas = [r for r in resumen if r.get('tipo') == tipo]
        if filas:
            st.write(f"**{tipo}s**")
            for r in filas:
                col_a, col_b, col_c = st.columns([4,1,1])
                with col_a:
                    st.write(f"📁 {r.get('categoria') or 'Sin categoría'}")
                with col_b:
                    st.write(f"${r.get('total') or 0:,.2f}")
                with col_c:
                    st.write(f"({r.get('cantidad') or 0} movimientos)")
            st.divider()

def main():
    mostrar_movimiento_caja()

if __name__ == "__main__":
    main()
