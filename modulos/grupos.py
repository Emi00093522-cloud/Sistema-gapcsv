import streamlit as st
from modulos.config.conexion import obtener_conexion
from datetime import datetime, date

def mostrar_grupos():   # ⭐ ESTA ES LA FUNCIÓN QUE USARÁ EL PANEL DE SECRETARÍA
    st.header("👥 Registrar Grupo")

    # Estado para controlar el mensaje de éxito
    if 'grupo_registrado' not in st.session_state:
        st.session_state.grupo_registrado = False

    if st.session_state.grupo_registrado:
        st.success("🎉 ¡Grupo registrado con éxito!")
        
        if st.button("🆕 Registrar otro grupo"):
            st.session_state.grupo_registrado = False
            st.rerun()
        
        st.info("💡 **Para seguir navegando, selecciona una opción en el menú**")
        return

    try:
        con = obtener_conexion()
        cursor = con.cursor()

        # Obtener distritos
        cursor.execute("SELECT ID_Distrito, nombre FROM Distrito")
        distritos = cursor.fetchall()
        
        # Obtener promotoras
        cursor.execute("SELECT ID_Promotora, nombre FROM Promotora")
        promotoras = cursor.fetchall()

        # Formulario para registrar grupo
        with st.form("form_grupo"):
            st.subheader("Datos del Grupo")
            
            nombre = st.text_input("Nombre del grupo *", 
                                   placeholder="Ingrese el nombre del grupo",
                                   max_chars=100)

            # Distritos
            if distritos:
                distrito_options = {f"{d[1]} (ID: {d[0]})": d[0] for d in distritos}
                distrito_sel = st.selectbox("Distrito *", list(distrito_options.keys(_*_
