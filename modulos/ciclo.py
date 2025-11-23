import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def mostrar_informacion_ciclo():
    st.header("🔒 Cierre de Ciclo - Resumen Financiero")
    
    # Datos de ejemplo del ciclo actual (simulando la base de datos)
    ciclo_actual = {
        'ID_Ciclo': 1,
        'fecha_inicio': datetime(2024, 1, 1).date(),
        'fecha_cierre': None,  # Ciclo aún activo
        'ID_Estado_ciclo': 1
    }
    
    if ciclo_actual:
        # Mostrar información en modo lectura
        st.subheader("📊 Información del Ciclo Actual")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info(f"**📅 Fecha de Inicio:** {ciclo_actual['fecha_inicio']}")
        
        with col2:
            if ciclo_actual['fecha_cierre']:
                st.info(f"**🔚 Fecha de Cierre:** {ciclo_actual['fecha_cierre']}")
            else:
                st.warning("**⏳ Fecha de Cierre:** Ciclo aún activo")
        
        with col3:
            if ciclo_actual['fecha_cierre']:
                duracion = (ciclo_actual['fecha_cierre'] - ciclo_actual['fecha_inicio']).days
                st.info(f"**⏰ Duración del Ciclo:** {duracion} días")
            else:
                duracion_actual = (datetime.now().date() - ciclo_actual['fecha_inicio']).days
                st.info(f"**⏰ Duración Actual:** {duracion_actual} días")
        
        # Botón para cerrar el ciclo (solo si está activo)
        if not ciclo_actual['fecha_cierre']:
            st.markdown("---")
            
            # Inicializar el estado en session_state si no existe
            if 'mostrar_resumen' not in st.session_state:
                st.session_state.mostrar_resumen = False
            
            # Botón principal - ¿Desea cerrar el ciclo?
            if st.button("🚀 ¿Desea cerrar el ciclo? Sí", type="primary", use_container_width=True):
                st.session_state.mostrar_resumen = True
            
            # Solo mostrar el resumen si el usuario presionó "Sí"
            if st.session_state.mostrar_resumen:
                mostrar_resumen_cierre(ciclo_actual['ID_Ciclo'])
    else:
        st.warning("No hay un ciclo activo en este momento.")

def calcular_totales_financieros(id_ciclo):
    """
    Calcula los totales financieros del ciclo
    En un sistema real, estos datos vendrían de la base de datos
    """
    
    # DATOS DE EJEMPLO - Simulando lo que vendría de tus módulos
    
    # Simulación de datos del módulo ahorros.py
    ahorros_data = [
        {'monto': 1500.00, 'fecha': '2024-01-15'},
        {'monto': 2000.00, 'fecha': '2024-02-10'},
        {'monto': 1800.00, 'fecha': '2024-03-05'},
        {'monto': 2200.00, 'fecha': '2024-04-12'},
    ]
    
    # Simulación de datos del módulo pagomulta.py
    multas_data = [
        {'monto': 50.00, 'fecha': '2024-01-20'},
        {'monto': 75.00, 'fecha': '2024-02-15'},
        {'monto': 100.00, 'fecha': '2024-03-22'},
        {'monto': 25.00, 'fecha': '2024-04-08'},
    ]
    
    # Simulación de datos del módulo pagoprestamos.py
    prestamos_data = [
        {'monto': 500.00, 'fecha': '2024-01-25'},
        {'monto': 750.00, 'fecha': '2024-02-18'},
        {'monto': 600.00, 'fecha': '2024-03-30'},
        {'monto': 450.00, 'fecha': '2024-04-14'},
    ]
    
    # CÁLCULOS REALES
    ahorros_totales = sum(item['monto'] for item in ahorros_data)
    multas_totales = sum(item['monto'] for item in multas_data)
    prestamos_totales = sum(item['monto'] for item in prestamos_data)
    
    return ahorros_totales, multas_totales, prestamos_totales

def mostrar_resumen_cierre(id_ciclo):
    st.subheader("💰 Resumen Financiero del Ciclo")
    
    st.success("✅ Has seleccionado cerrar el ciclo. Aquí está el resumen:")
    
    # Obtener sumatorias calculadas
    ahorros_totales, multas_totales, prestamos_totales = calcular_totales_financieros(id_ciclo)
    
    # Calcular total de ingresos
    total_ingresos = ahorros_totales + multas_totales + prestamos_totales
    
    # Crear tabla resumen consolidada - MODO LECTURA
    st.write("### 📋 Tabla de Consolidado - Modo Lectura")
    
    resumen_data = {
        "Concepto": [
            "💰 Total de Ahorros del Grupo", 
            "⚖️ Total de Multas Aplicadas", 
            "🏦 Total de Pagos de Préstamos",
            "💵 **TOTAL DE INGRESOS DEL CICLO**"
        ],
        "Monto": [
            f"${ahorros_totales:,.2f}",
            f"${multas_totales:,.2f}",
            f"${prestamos_totales:,.2f}",
            f"**${total_ingresos:,.2f}**"
        ],
        "Descripción": [
            "Suma total de todos los ahorros registrados en el módulo de ahorros.py",
            "Suma total de todas las multas registradas en el módulo de pagomulta.py", 
            "Suma total de todos los pagos de préstamos en pagoprestamos.py",
            "Consolidado general de todos los ingresos del ciclo"
        ]
    }
    
    df_resumen = pd.DataFrame(resumen_data)
    
    # Mostrar tabla con estilo mejorado - SOLO LECTURA
    st.dataframe(
        df_resumen, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "Concepto": st.column_config.TextColumn("Concepto", width="medium"),
            "Monto": st.column_config.TextColumn("Monto", width="small"),
            "Descripción": st.column_config.TextColumn("Descripción del Cálculo", width="large")
        }
    )
    
    # Mostrar detalles adicionales en modo lectura
    st.write("### 🔍 Detalles de los Cálculos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**📊 Ahorros Totales:**")
        st.write(f"- Calculado desde: módulo `ahorros.py`")
        st.write(f"- Método: Suma de todos los registros de ahorro")
        st.write(f"- Resultado: **${ahorros_totales:,.2f}**")
        
        st.write("**⚖️ Multas Totales:**")
        st.write(f"- Calculado desde: módulo `pagomulta.py`")
        st.write(f"- Método: Suma de todas las multas aplicadas")
        st.write(f"- Resultado: **${multas_totales:,.2f}**")
    
    with col2:
        st.write("**🏦 Préstamos Totales:**")
        st.write(f"- Calculado desde: módulo `pagoprestamos.py`")
        st.write(f"- Método: Suma de todos los pagos de préstamos")
        st.write(f"- Resultado: **${prestamos_totales:,.2f}**")
        
        st.write("**💵 Total Consolidado:**")
        st.write(f"- Fórmula: Ahorros + Multas + Préstamos")
        st.write(f"- Cálculo: ${ahorros_totales:,.2f} + ${multas_totales:,.2f} + ${prestamos_totales:,.2f}")
        st.write(f"- Resultado: **${total_ingresos:,.2f}**")
    
    # Botón para confirmar el cierre definitivo
    st.markdown("---")
    st.write("### ✅ Confirmar Cierre Definitivo")
    
    if st.button("🔐 Confirmar Cierre del Ciclo", type="primary", use_container_width=True):
        # Aquí iría la lógica para guardar en la base de datos
        st.success("🎉 ¡Ciclo cerrado exitosamente!")
        st.balloons()
        
        # Resetear el estado
        st.session_state.mostrar_resumen = False
        st.rerun()

if __name__ == "__main__":
    mostrar_informacion_ciclo()
