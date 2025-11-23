import streamlit as st
from modulos.config.conexion import obtener_conexion
from datetime import datetime, date

from modulos.consultas_db import obtener_grupos
from modulos.permisos import verificar_permisos

def mostrar_grupos():
    grupos = obtener_grupos()  # ✅ Ya existe en consultas_db.py
    # ... tu código actual

# Para crear nuevos grupos
if verificar_permisos("ver_todo") or verificar_permisos("registrar_distritos"):
    st.button("Crear Nuevo Grupo")


#def mostrar_grupos():   # ⭐ ESTA ES LA FUNCIÓN QUE USARÁ EL PANEL DE SECRETARÍA
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
                distrito_sel = st.selectbox("Distrito *", list(distrito_options.keys()))
                ID_Distrito = distrito_options[distrito_sel]
            else:
                st.error("❌ No hay distritos registrados.")
                ID_Distrito = None
            
            # Fecha
            fecha_inicio = st.date_input(
                "Fecha de inicio *",
                value=datetime.now().date(),
                min_value=date(1990,1,1),
                max_value=date(2100,12,31)
            )

            # Promotora
            if promotoras:
                promotora_options = {f"{p[1]} (ID: {p[0]})": p[0] for p in promotoras}
                promotora_sel = st.selectbox("Promotora *", list(promotora_options.keys()))
                ID_Promotora = promotora_options[promotora_sel]
            else:
                st.error("❌ No hay promotoras registradas.")
                ID_Promotora = None

            ID_Estado = st.selectbox(
                "Estado",
                options=[1,2],
                format_func=lambda x: "Activo" if x == 1 else "Inactivo"
            )

            enviar = st.form_submit_button("✅ Guardar Grupo")

            if enviar:
                errores = []

                if nombre.strip() == "":
                    errores.append("⚠ El nombre no puede estar vacío.")
                if ID_Distrito is None:
                    errores.append("⚠ Selecciona un distrito.")
                if ID_Promotora is None:
                    errores.append("⚠ Selecciona una promotora.")

                if errores:
                    for e in errores:
                        st.warning(e)
                else:
                    try:
                        # INSERT sin duracion_ciclo
                        cursor.execute("""
                            INSERT INTO Grupo 
                            (nombre, ID_Distrito, fecha_inicio, ID_Promotora, ID_Estado)
                            VALUES (%s,%s,%s,%s,%s)
                        """, (nombre, ID_Distrito, fecha_inicio, ID_Promotora, ID_Estado))

                        con.commit()

                        cursor.execute("SELECT LAST_INSERT_ID()")
                        id_grupo = cursor.fetchone()[0]

                        st.session_state.grupo_registrado = True
                        st.session_state.id_grupo_creado = id_grupo
                        st.session_state.nombre_grupo_creado = nombre
                        st.rerun()

                    except Exception as e:
                        con.rollback()
                        st.error(f"❌ Error al registrar el grupo: {e}")

    except Exception as e:
        st.error(f"❌ Error de conexión: {e}")

    finally:
        try:
            cursor.close()
            con.close()
        except:
            pass
