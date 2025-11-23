import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import database as db  # Asumiendo que tienes un módulo para manejar la base de datos

def mostrar_informacion_ciclo():
    st.header("Gestión de Ciclo de Grupo")
    
    # Obtener información del ciclo actual
    ciclo_actual = db.obtener_ciclo_actual()
    
    if ciclo_actual:
        # Mostrar información en modo lectura
        st.subheader("Información del Ciclo Actual")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info(f"**Fecha de Inicio:** {ciclo_actual['fecha_inicio']}")
        
        with col2:
            if ciclo_actual['fecha_cierre']:
                st.info(f"**Fecha de Cierre:** {ciclo_actual['fecha_cierre']}")
            else:
                st.warning("**Fecha de Cierre:** Ciclo aún activo")
        
        with col3:
            if ciclo_actual['fecha_cierre']:
                duracion = (ciclo_actual['fecha_cierre'] - ciclo_actual['fecha_inicio']).days
                st.info(f"**Duración del Ciclo:** {duracion} días")
            else:
                duracion_actual = (datetime.now().date() - ciclo_actual['fecha_inicio']).days
                st.info(f"**Duración Actual:** {duracion_actual} días")
        
        # Botón para cerrar el ciclo (solo si está activo)
        if not ciclo_actual['fecha_cierre']:
            st.markdown("---")
            if st.button("¿Desea cerrar el ciclo? Sí", type="primary"):
                mostrar_resumen_cierre(ciclo_actual['ID_Ciclo'])
    else:
        st.warning("No hay un ciclo activo en este momento.")

def mostrar_resumen_cierre(id_ciclo):
    st.subheader("Resumen de Información para Cierre del Ciclo")
    
    # Obtener sumatorias de diferentes módulos
    total_ahorros = db.obtener_total_ahorros_por_ciclo(id_ciclo)
    total_multas = db.obtener_total_multas_por_ciclo(id_ciclo)
    total_prestamos = db.obtener_total_prestamos_por_ciclo(id_ciclo)
    
    # Calcular total de ingresos
    total_ingresos = total_ahorros + total_multas + total_prestamos
    
    # Crear tabla resumen
    resumen_data = {
        "Concepto": [
            "Total de Ahorros", 
            "Total de Multas", 
            "Total de Pagos de Préstamos",
            "TOTAL DE INGRESOS"
        ],
        "Monto": [
            f"${total_ahorros:,.2f}",
            f"${total_multas:,.2f}",
            f"${total_prestamos:,.2f}",
            f"${total_ingresos:,.2f}"
        ]
    }
    
    df_resumen = pd.DataFrame(resumen_data)
    
    # Mostrar tabla con estilo
    st.dataframe(df_resumen, use_container_width=True, hide_index=True)
    
    # Botones de acción
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        if st.button("Confirmar Cierre del Ciclo", type="primary"):
            # Actualizar fecha de cierre en la base de datos
            fecha_cierre = datetime.now().date()
            if db.actualizar_fecha_cierre_ciclo(id_ciclo, fecha_cierre):
                st.success("¡Ciclo cerrado exitosamente!")
                st.rerun()
            else:
                st.error("Error al cerrar el ciclo. Por favor, intente nuevamente.")

# Ejemplo de funciones de base de datos (debes implementarlas según tu estructura)
"""
# En tu módulo database.py, necesitarás implementar estas funciones:

def obtener_ciclo_actual():
    # Consulta para obtener el ciclo actual (sin fecha de cierre)
    query = "SELECT * FROM ciclo WHERE fecha_cierre IS NULL ORDER BY fecha_inicio DESC LIMIT 1"
    # Ejecutar query y retornar resultado
    pass

def obtener_total_ahorros_por_ciclo(id_ciclo):
    # Consulta para sumar todos los ahorros del ciclo
    query = "SELECT SUM(monto) FROM ahorros WHERE ID_Ciclo = %s"
    # Ejecutar query y retornar resultado
    pass

def obtener_total_multas_por_ciclo(id_ciclo):
    # Consulta para sumar todas las multas del ciclo
    query = "SELECT SUM(monto) FROM pagomulta WHERE ID_Ciclo = %s"
    # Ejecutar query y retornar resultado
    pass

def obtener_total_prestamos_por_ciclo(id_ciclo):
    # Consulta para sumar todos los pagos de préstamos del ciclo
    query = "SELECT SUM(monto) FROM pagoprestamos WHERE ID_Ciclo = %s"
    # Ejecutar query y retornar resultado
    pass

def actualizar_fecha_cierre_ciclo(id_ciclo, fecha_cierre):
    # Actualizar la fecha de cierre del ciclo
    query = "UPDATE ciclo SET fecha_cierre = %s WHERE ID_Ciclo = %s"
    # Ejecutar query y retornar si fue exitoso
    pass
"""

if __name__ == "__main__":
    mostrar_informacion_ciclo()
