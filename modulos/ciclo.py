import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Agregar la ruta de tus módulos (por si este archivo está en otra carpeta)
sys.path.append(os.path.dirname(__file__))

# =============================================
#  UTILIDADES DE MÓDULOS
# =============================================

def verificar_modulos():
    """Solo muestra en el sidebar si los otros módulos están accesibles (no afecta cálculos)."""
    st.sidebar.write("### 🔧 Verificación de Módulos")
    
    try:
        from ahorros import obtener_ahorros_grupo
        st.sidebar.success("✅ ahorros.py - CONECTADO")
    except ImportError as e:
        st.sidebar.error(f"❌ ahorros.py - ERROR: {e}")
    
    try:
        from pagomulta import obtener_multas_grupo
        st.sidebar.success("✅ pagomulta.py - CONECTADO")  
    except ImportError as e:
        st.sidebar.error(f"❌ pagomulta.py - ERROR: {e}")
    
    try:
        from pagoprestamo import mostrar_pago_prestamo
        st.sidebar.success("✅ pagoprestamo.py - CONECTADO (usando mostrar_pago_prestamo)")
    except ImportError as e:
        st.sidebar.error(f"❌ pagoprestamo.py - ERROR: {e}")

# =============================================
#  IDENTIFICACIÓN DE GRUPO DEL USUARIO
# =============================================

def obtener_id_grupo_usuario():
    """Obtiene el ID del grupo del usuario logueado desde session_state."""
    return st.session_state.get("id_grupo")

def verificar_grupo_usuario():
    """Verifica que el usuario tenga un grupo asociado."""
    id_grupo = obtener_id_grupo_usuario()
    if id_grupo is None:
        st.error("⚠️ No tienes un grupo asociado. Crea primero un grupo en el módulo 'Grupos'.")
        return False
    return True

# =============================================
#  AHORROS - FUNCIÓN CORREGIDA
# =============================================

def obtener_ahorros_por_miembro_ciclo(fecha_inicio=None, fecha_fin=None):
    """
    Obtiene los ahorros totales por miembro dentro del rango de fechas
    PARA EL GRUPO DEL USUARIO. El filtro se hace por Reunion.fecha.
    """
    try:
        from modulos.config.conexion import obtener_conexion
        
        if not verificar_grupo_usuario():
            return []
            
        id_grupo = obtener_id_grupo_usuario()
        
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        query = """
            SELECT 
                m.ID_Miembro,
                m.nombre AS nombre_miembro,
                COALESCE(SUM(a.monto_ahorro), 0)                 AS total_ahorros,
                COALESCE(SUM(a.monto_otros), 0)                  AS total_otros,
                COALESCE(SUM(a.monto_ahorro + a.monto_otros), 0) AS total_general
            FROM Miembro m
            LEFT JOIN Ahorro a ON m.ID_Miembro = a.ID_Miembro
            LEFT JOIN Reunion r ON a.ID_Reunion = r.ID_Reunion
            WHERE m.ID_Grupo = %s
              AND m.ID_Estado = 1
        """
        
        params = [id_grupo]
        
        # 🔎 Filtro por rango de fechas del CICLO (fecha de la REUNIÓN)
        if fecha_inicio and fecha_fin:
            query += " AND r.fecha BETWEEN %s AND %s"
            params.extend([fecha_inicio, fecha_fin])
        
        query += """
            GROUP BY m.ID_Miembro, m.nombre
            ORDER BY m.nombre
        """
        
        cursor.execute(query, tuple(params))
        ahorros_miembros = cursor.fetchall()
        
        resultado = []
        for row in ahorros_miembros:
            resultado.append({
                "miembro":       row["nombre_miembro"],
                "total_ahorros": float(row["total_ahorros"]),
                "total_otros":   float(row["total_otros"]),
                "total_general": float(row["total_general"]),
            })
        
        cursor.close()
        con.close()
        return resultado

    except Exception as e:
        st.error(f"❌ Error obteniendo ahorros por miembro: {e}")
        return []

def obtener_total_miembros_activos():
    """
    Obtiene el total de miembros activos (ID_Estado = 1) del grupo DEL USUARIO.
    """
    try:
        from modulos.config.conexion import obtener_conexion
        
        if not verificar_grupo_usuario():
            return 0
            
        id_grupo = obtener_id_grupo_usuario()
        
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT COUNT(*) AS total_miembros
            FROM Miembro 
            WHERE ID_Grupo = %s AND ID_Estado = 1
        """, (id_grupo,))
        
        resultado = cursor.fetchone()
        total_miembros = resultado["total_miembros"] if resultado else 0
        
        cursor.close()
        con.close()
        
        return total_miembros
        
    except Exception as e:
        st.error(f"❌ Error obteniendo miembros activos: {e}")
        return 0

# =============================================
#  PRÉSTAMOS
# =============================================

def obtener_datos_prestamos_desde_bd(fecha_inicio=None, fecha_fin=None):
    """
    Obtiene datos de préstamos directamente desde la base de datos
    con filtro opcional de fechas PARA EL GRUPO DEL USUARIO.
    """
    try:
        from modulos.config.conexion import obtener_conexion
        
        if not verificar_grupo_usuario():
            return []
            
        id_grupo = obtener_id_grupo_usuario()
        
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        query = """
            SELECT 
                p.ID_Prestamo,
                p.monto,
                p.total_interes,
                p.monto_total_pagar,
                p.ID_Estado_prestamo,
                p.fecha_desembolso,
                m.nombre AS nombre_miembro
            FROM Prestamo p
            JOIN Miembro m ON p.ID_Miembro = m.ID_Miembro
            WHERE m.ID_Grupo = %s 
              AND p.ID_Estado_prestamo != 3  -- Excluir cancelados/rechazados
        """
        
        params = [id_grupo]
        
        # Filtro por fecha de desembolso
        if fecha_inicio and fecha_fin:
            query += " AND p.fecha_desembolso BETWEEN %s AND %s"
            params.extend([fecha_inicio, fecha_fin])
        
        cursor.execute(query, tuple(params))
        prestamos = cursor.fetchall()
        
        resultado = []
        for p in prestamos:
            monto_capital   = p.get("monto", 0) or 0
            monto_intereses = p.get("total_interes", 0) or 0
            monto_total     = p.get("monto_total_pagar")
            
            if monto_total is None:
                monto_total = monto_capital + monto_intereses
                
            resultado.append({
                "monto_capital":   float(monto_capital),
                "monto_intereses": float(monto_intereses),
                "monto_total":     float(monto_total),
                "estado":          p["ID_Estado_prestamo"],
                "nombre_miembro":  p["nombre_miembro"],
            })
        
        cursor.close()
        con.close()
        
        return resultado
        
    except Exception as e:
        st.error(f"❌ Error obteniendo préstamos desde BD: {e}")
        return []

# =============================================
#  MULTAS
# =============================================

def obtener_datos_multas_desde_bd(fecha_inicio=None, fecha_fin=None):
    """
    Obtiene datos de multas directamente desde la base de datos
    con filtro opcional de fechas PARA EL GRUPO DEL USUARIO.
    """
    try:
        from modulos.config.conexion import obtener_conexion
        
        if not verificar_grupo_usuario():
            return []
            
        id_grupo = obtener_id_grupo_usuario()
        
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        query = """
            SELECT 
                pm.ID_PagoMulta,
                pm.monto_pagado,
                pm.fecha_pago,
                m.nombre AS nombre_miembro
            FROM PagoMulta pm
            JOIN Multa mult  ON pm.ID_Multa   = mult.ID_Multa
            JOIN Miembro m   ON pm.ID_Miembro = m.ID_Miembro
            WHERE m.ID_Grupo = %s
        """
        
        params = [id_grupo]
        
        # Filtro por fecha de pago
        if fecha_inicio and fecha_fin:
            query += " AND pm.fecha_pago BETWEEN %s AND %s"
            params.extend([fecha_inicio, fecha_fin])
        
        cursor.execute(query, tuple(params))
        multas = cursor.fetchall()
        
        resultado = []
        for multa in multas:
            resultado.append({
                "monto_pagado":  float(multa.get("monto_pagado", 0) or 0),
                "fecha_pago":    multa["fecha_pago"],
                "nombre_miembro": multa["nombre_miembro"],
                "descripcion":   multa["descripcion"],
            })
        
        cursor.close()
        con.close()
        
        return resultado
        
    except Exception as e:
        st.error(f"❌ Error obteniendo multas desde BD: {e}")
        return []

# =============================================
#  CONSOLIDADO DE DATOS REALES
# =============================================

def obtener_datos_reales(fecha_inicio=None, fecha_fin=None):
    """
    Obtiene datos REALES con filtro opcional de fechas
    PARA EL GRUPO DEL USUARIO.
    """
    if not verificar_grupo_usuario():
        return [], [], []
        
    ahorros_data, multas_data, prestamos_data = [], [], []
    
    # 🔹 AHORROS (a partir de ahorros_por_miembro con rango de fechas)
    try:
        ahorros_por_miembro = obtener_ahorros_por_miembro_ciclo(fecha_inicio, fecha_fin)
        for m in ahorros_por_miembro:
            ahorros_data.append({
                "monto_ahorro": m["total_ahorros"],
                "monto_otros":  m["total_otros"],
            })
    except Exception as e:
        st.error(f"❌ Error en ahorros: {e}")
    
    # 🔹 MULTAS
    try:
        multas_data = obtener_datos_multas_desde_bd(fecha_inicio, fecha_fin) or []
    except Exception as e:
        st.error(f"❌ Error en multas: {e}")
    
    # 🔹 PRÉSTAMOS
    try:
        prestamos_data = obtener_datos_prestamos_desde_bd(fecha_inicio, fecha_fin) or []
    except Exception as e:
        st.error(f"❌ Error en préstamos: {e}")
    
    return ahorros_data, multas_data, prestamos_data

def calcular_totales_reales(fecha_inicio=None, fecha_fin=None):
    """
    Calcula los totales con datos REALES - separa capital e intereses
    con filtro opcional de fechas PARA EL GRUPO DEL USUARIO.
    """
    if not verificar_grupo_usuario():
        return 0.00, 0.00, 0.00, 0.00
        
    ahorros_data, multas_data, prestamos_data = obtener_datos_reales(fecha_inicio, fecha_fin)
    
    # Si no hay datos, puedes devolver 0 o valores de ejemplo
    if not ahorros_data and not multas_data and not prestamos_data:
        st.warning("⚠️ No se encontraron datos en el rango seleccionado.")
        return 0.00, 0.00, 0.00, 0.00
    
    # 🔹 Ahorros
    ahorros_totales = 0.0
    for ahorro in ahorros_data:
        ahorros_totales += float(ahorro.get("monto_ahorro", 0) or 0) \
                         + float(ahorro.get("monto_otros", 0) or 0)
    
    # 🔹 Multas
    multas_totales = 0.0
    for multa in multas_data:
        multas_totales += float(multa.get("monto_pagado", 0) or 0)
    
    # 🔹 Préstamos (capital e intereses separados)
    prestamos_capital   = 0.0
    prestamos_intereses = 0.0
    for prestamo in prestamos_data:
        prestamos_capital   += float(prestamo.get("monto_capital", 0) or 0)
        prestamos_intereses += float(prestamo.get("monto_intereses", 0) or 0)
    
    return ahorros_totales, multas_totales, prestamos_capital, prestamos_intereses

# =============================================
#  SESSION STATE Y FILTRO DE FECHAS
# =============================================

def inicializar_session_state():
    """Inicializa el estado de la sesión para las pestañas."""
    if "ciclos_cerrados" not in st.session_state:
        st.session_state.ciclos_cerrados = []
    if "mostrar_resumen" not in st.session_state:
        st.session_state.mostrar_resumen = False
    if "ciclo_actual_numero" not in st.session_state:
        st.session_state.ciclo_actual_numero = 1
    if "filtro_fechas" not in st.session_state:
        st.session_state.filtro_fechas = {
            "fecha_inicio": datetime.now().date() - timedelta(days=30),
            "fecha_fin": datetime.now().date(),
        }

def mostrar_filtro_fechas():
    """Muestra el filtro de fechas para seleccionar el rango del ciclo."""
    st.subheader("📅 Seleccionar Rango del Ciclo")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fecha_inicio = st.date_input(
            "Fecha de Inicio del Ciclo",
            value=st.session_state.filtro_fechas["fecha_inicio"],
            max_value=datetime.now().date(),
        )
    
    with col2:
        fecha_fin = st.date_input(
            "Fecha de Fin del Ciclo",
            value=st.session_state.filtro_fechas["fecha_fin"],
            max_value=datetime.now().date(),
        )
    
    if fecha_inicio > fecha_fin:
        st.error("❌ La fecha de inicio no puede ser mayor que la fecha de fin")
        return None, None
    
    st.session_state.filtro_fechas = {
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
    }
    
    dias_ciclo = (fecha_fin - fecha_inicio).days
    st.info(f"**📊 Rango seleccionado:** {fecha_inicio} a {fecha_fin} ({dias_ciclo} días)")
    
    return fecha_inicio, fecha_fin

# =============================================
#  RESUMEN DEL CICLO
# =============================================

def mostrar_resumen_completo(fecha_inicio, fecha_fin):
    """Muestra el resumen completo del ciclo con filtro de fechas PARA EL GRUPO DEL USUARIO."""
    
    if not verificar_grupo_usuario():
        return None
        
    st.subheader(f"💰 Resumen Financiero del Ciclo: {fecha_inicio} a {fecha_fin}")
    
    st.success("✅ Calculando datos para el rango seleccionado...")
    
    with st.spinner("🔍 Calculando datos financieros..."):
        ahorros_totales, multas_totales, prestamos_capital, prestamos_intereses = \
            calcular_totales_reales(fecha_inicio, fecha_fin)
    
    prestamos_total = prestamos_capital + prestamos_intereses
    total_ingresos  = ahorros_totales + multas_totales + prestamos_total
    
    # Tabla resumen
    st.write("### 📋 Tabla de Consolidado")
    
    resumen_data = {
        "Concepto": [
            "💰 Total de Ahorros",
            "⚖️ Total de Multas",
            "🏦 Total Préstamos (Capital)",
            "📈 Total Intereses",
            "💵 **TOTAL INGRESOS**",
        ],
        "Monto": [
            f"${ahorros_totales:,.2f}",
            f"${multas_totales:,.2f}",
            f"${prestamos_capital:,.2f}",
            f"${prestamos_intereses:,.2f}",
            f"**${total_ingresos:,.2f}**",
        ],
    }
    
    df_resumen = pd.DataFrame(resumen_data)
    st.dataframe(df_resumen, use_container_width=True, hide_index=True)
    
    # Métricas
    st.write("### 📈 Métricas del Ciclo")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Ahorros", f"${ahorros_totales:,.2f}")
    with col2:
        st.metric("Multas", f"${multas_totales:,.2f}")
    with col3:
        st.metric("Préstamos", f"${prestamos_capital:,.2f}")
    with col4:
        st.metric("Intereses", f"${prestamos_intereses:,.2f}")
    
    # Ahorros por miembro
    st.write("### 📊 Ahorros por Miembro (Ciclo Completo)")
    
    ahorros_por_miembro = obtener_ahorros_por_miembro_ciclo(fecha_inicio, fecha_fin)
    
    if ahorros_por_miembro:
        tabla_data = {
            "Miembro":       [m["miembro"] for m in ahorros_por_miembro],
            "Total Ahorros": [f"${m['total_ahorros']:,.2f}" for m in ahorros_por_miembro],
            "Total Otros":   [f"${m['total_otros']:,.2f}" for m in ahorros_por_miembro],
            "TOTAL":         [f"${m['total_general']:,.2f}" for m in ahorros_por_miembro],
        }
        
        df_tabla = pd.DataFrame(tabla_data)
        st.dataframe(df_tabla, use_container_width=True, hide_index=True)
        
        total_general_miembros = sum(item["total_general"] for item in ahorros_por_miembro)
        st.info(f"**💵 Total general de ahorros de todos los miembros: ${total_general_miembros:,.2f}**")
    else:
        st.info("ℹ️ No se encontraron datos de ahorros por miembro dentro del rango.")
    
    # Distribución de beneficios (intereses)
    st.write("### 📊 Distribución de Beneficios")
    
    total_miembros_activos = obtener_total_miembros_activos()
    
    distribucion_por_miembro = 0
    if total_miembros_activos > 0 and prestamos_intereses > 0:
        distribucion_por_miembro = prestamos_intereses / total_miembros_activos
        
        distribucion_data = {
            "Concepto": [
                "Total de Miembros Activos",
                "Total de Intereses a Distribuir",
                "Distribución por Miembro",
            ],
            "Valor": [
                f"{total_miembros_activos}",
                f"${prestamos_intereses:,.2f}",
                f"${distribucion_por_miembro:,.2f}",
            ],
        }
        
        df_distribucion = pd.DataFrame(distribucion_data)
        st.dataframe(df_distribucion, use_container_width=True, hide_index=True)
        
        st.success(f"**🎯 A cada miembro activo le corresponde: ${distribucion_por_miembro:,.2f}**")
        
        with st.expander("🔍 Ver Cálculo Detallado"):
            st.write(f"""
            **Fórmula de distribución:**
            - Total Intereses: ${prestamos_intereses:,.2f}
            - Total Miembros Activos: {total_miembros_activos}
            - Distribución: ${prestamos_intereses:,.2f} ÷ {total_miembros_activos} = **${distribucion_por_miembro:,.2f} por miembro**
            """)
    
    elif total_miembros_activos == 0:
        st.warning("⚠️ No se encontraron miembros activos en el grupo.")
    
    elif prestamos_intereses == 0:
        st.info("ℹ️ No hay intereses para distribuir en este ciclo.")
    
    # Detalles de préstamos
    with st.expander("📊 Ver Detalles de Préstamos"):
        try:
            prestamos_detalle = obtener_datos_prestamos_desde_bd(fecha_inicio, fecha_fin)
            if prestamos_detalle:
                df_prestamos = pd.DataFrame(prestamos_detalle)
                st.dataframe(
                    df_prestamos[
                        ["nombre_miembro", "monto_capital", "monto_intereses", "monto_total"]
                    ],
                    use_container_width=True,
                )
            else:
                st.info("No hay datos detallados de préstamos en el rango.")
        except Exception:
            st.info("No se pudieron cargar los detalles de préstamos.")
    
    return {
        "ahorros_totales":         ahorros_totales,
        "multas_totales":          multas_totales,
        "prestamos_capital":       prestamos_capital,
        "prestamos_intereses":     prestamos_intereses,
        "total_ingresos":          total_ingresos,
        "total_miembros_activos":  total_miembros_activos,
        "distribucion_por_miembro": distribucion_por_miembro,
        "ahorros_por_miembro":     ahorros_por_miembro,
        "fecha_inicio":            fecha_inicio.strftime("%Y-%m-%d"),
        "fecha_fin":               fecha_fin.strftime("%Y-%m-%d"),
        "fecha_cierre":            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

# =============================================
#  PESTAÑAS
# =============================================

def pestaña_ciclo_activo():
    """Pestaña 1: Ciclo Activo - Donde se calcula y cierra el ciclo actual DEL GRUPO DEL USUARIO."""
    st.header("🔒 Cierre de Ciclo - Resumen Financiero")
    
    if not verificar_grupo_usuario():
        return
    
    fecha_inicio, fecha_fin = mostrar_filtro_fechas()
    if fecha_inicio is None or fecha_fin is None:
        return
    
    st.markdown("---")
    
    if st.button("🚀 Generar Resumen del Ciclo", type="primary", use_container_width=True):
        st.session_state.mostrar_resumen = True
    
    if st.session_state.mostrar_resumen:
        datos_ciclo = mostrar_resumen_completo(fecha_inicio, fecha_fin)
        if datos_ciclo is None:
            return
        
        st.markdown("---")
        st.write("### ✅ Confirmar Cierre Definitivo")
        
        if st.button("🔐 CONFIRMAR CIERRE DEL CICLO", type="primary", use_container_width=True):
            ciclo_cerrado = {
                "numero_ciclo": st.session_state.ciclo_actual_numero,
                "datos":        datos_ciclo,
                "fecha_cierre": datos_ciclo["fecha_cierre"],
                "rango_fechas": f"{datos_ciclo['fecha_inicio']} a {datos_ciclo['fecha_fin']}",
            }
            st.session_state.ciclos_cerrados.append(ciclo_cerrado)
            st.session_state.ciclo_actual_numero += 1
            st.session_state.mostrar_resumen = False
            
            st.success("🎉 ¡Ciclo cerrado exitosamente! Se ha iniciado un nuevo ciclo.")
            st.balloons()
            st.info("📁 Puedes ver el historial en la pestaña 'Registro de Ciclos Cerrados'.")

def pestaña_ciclos_cerrados():
    """Pestaña 2: Registro de Ciclos Cerrados - Historial del grupo del usuario."""
    st.header("📁 Registro de Ciclos Cerrados")
    
    if not verificar_grupo_usuario():
        return
    
    if not st.session_state.ciclos_cerrados:
        st.info("ℹ️ No hay ciclos cerrados registrados. Los ciclos cerrados aparecerán aquí.")
        return
    
    for i, ciclo in enumerate(st.session_state.ciclos_cerrados):
        with st.expander(
            f"📊 Ciclo {ciclo['numero_ciclo']} - {ciclo['rango_fechas']} - {ciclo['fecha_cierre']}",
            expanded=(i == 0),
        ):
            datos = ciclo["datos"]
            
            st.write(
                f"**Ciclo {ciclo['numero_ciclo']} - Rango: {ciclo['rango_fechas']} - Cerrado el: {ciclo['fecha_cierre']}**"
            )
            
            # Consolidado
            st.write("#### 📋 Tabla de Consolidado")
            resumen_data = {
                "Concepto": [
                    "💰 Total de Ahorros",
                    "⚖️ Total de Multas",
                    "🏦 Total Préstamos (Capital)",
                    "📈 Total Intereses",
                    "💵 **TOTAL INGRESOS**",
                ],
                "Monto": [
                    f"${datos['ahorros_totales']:,.2f}",
                    f"${datos['multas_totales']:,.2f}",
                    f"${datos['prestamos_capital']:,.2f}",
                    f"${datos['prestamos_intereses']:,.2f}",
                    f"**${datos['total_ingresos']:,.2f}**",
                ],
            }
            df_resumen = pd.DataFrame(resumen_data)
            st.dataframe(df_resumen, use_container_width=True, hide_index=True)
            
            # Métricas
            st.write("#### 📈 Métricas del Ciclo")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Ahorros", f"${datos['ahorros_totales']:,.2f}")
            with col2:
                st.metric("Multas", f"${datos['multas_totales']:,.2f}")
            with col3:
                st.metric("Préstamos", f"${datos['prestamos_capital']:,.2f}")
            with col4:
                st.metric("Intereses", f"${datos['prestamos_intereses']:,.2f}")
            
            # Ahorros por miembro
            if datos["ahorros_por_miembro"]:
                st.write("#### 📊 Ahorros por Miembro")
                tabla_data = {
                    "Miembro":       [m["miembro"] for m in datos["ahorros_por_miembro"]],
                    "Total Ahorros": [f"${m['total_ahorros']:,.2f}" for m in datos["ahorros_por_miembro"]],
                    "Total Otros":   [f"${m['total_otros']:,.2f}" for m in datos["ahorros_por_miembro"]],
                    "TOTAL":         [f"${m['total_general']:,.2f}" for m in datos["ahorros_por_miembro"]],
                }
                df_tabla = pd.DataFrame(tabla_data)
                st.dataframe(df_tabla, use_container_width=True, hide_index=True)
            
            # Distribución de beneficios
            if datos["distribucion_por_miembro"] > 0:
                st.write("#### 📊 Distribución de Beneficios")
                st.info(f"**Distribución por miembro: ${datos['distribucion_por_miembro']:,.2f}**")

# =============================================
#  FUNCIÓN PRINCIPAL
# =============================================

def mostrar_ciclo():
    """Función principal que llama app.py - SOLO PARA EL GRUPO DEL USUARIO."""
    if not verificar_grupo_usuario():
        return
        
    verificar_modulos()
    inicializar_session_state()
    
    tab1, tab2 = st.tabs(
        ["🔒 Cierre de Ciclo Activo", "📁 Registro de Ciclos Cerrados"]
    )
    
    with tab1:
        pestaña_ciclo_activo()
    
    with tab2:
        pestaña_ciclos_cerrados()

if __name__ == "__main__":
    mostrar_ciclo()
