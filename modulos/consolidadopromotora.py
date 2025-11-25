import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def mostrar_consolidado_promotora():
    """Función principal del módulo de consolidado - VERSIÓN SUPER SIMPLE"""
    
    st.title("🏦 Consolidado Promotora")
    st.success("✅ ¡El módulo se está ejecutando correctamente!")
    
    # Información de debug
    st.subheader("🔍 Información de Sesión")
    st.write("Valores en session_state:")
    for key, value in st.session_state.items():
        st.write(f"- **{key}:** {value}")
    
    # Datos de ejemplo para demostrar que funciona
    st.subheader("📊 Datos de Ejemplo")
    
    # Crear datos de ejemplo
    datos_ejemplo = [
        {'grupo': 'Grupo A', 'mes': '2024-01', 'ingresos': 15000, 'egresos': 8000, 'balance': 7000},
        {'grupo': 'Grupo A', 'mes': '2024-02', 'ingresos': 18000, 'egresos': 9000, 'balance': 9000},
        {'grupo': 'Grupo B', 'mes': '2024-01', 'ingresos': 12000, 'egresos': 6000, 'balance': 6000},
        {'grupo': 'Grupo B', 'mes': '2024-02', 'ingresos': 14000, 'egresos': 7000, 'balance': 7000},
    ]
    
    df = pd.DataFrame(datos_ejemplo)
    st.dataframe(df, use_container_width=True)
    
    # Gráfica simple
    st.subheader("📈 Gráfica de Ejemplo")
    fig = px.bar(
        df, 
        x='mes', 
        y='ingresos', 
        color='grupo',
        title='Ingresos por Grupo (Datos de Ejemplo)',
        barmode='group'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Métricas
    st.subheader("🎯 Métricas de Ejemplo")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Ingresos", "$62,000")
    with col2:
        st.metric("Total Egresos", "$30,000")
    with col3:
        st.metric("Balance Total", "$32,000")
    
    st.info("""
    **Próximos pasos:**
    1. ✅ Módulo cargado correctamente
    2. 🔄 Conectando con base de datos
    3. 📊 Generando reportes reales
    """)

# Si el archivo se ejecuta directamente
if __name__ == "__main__":
    mostrar_consolidado_promotora()
