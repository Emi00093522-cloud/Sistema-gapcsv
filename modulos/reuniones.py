import streamlit as st
from modulos.config.conexion import obtener_conexion

def mostrar_reuniones():
    st.header("📅 Registro de Reuniones")
    st.subheader("📌 Registro de Reuniones por Distrito y Grupo")

    # Verificar rol (solo SECRETARIA puede entrar)
    if st.session_state.get("rol") != "Secretaria":
        st.warning("🔒 Acceso restringido: Solo la SECRETARIA puede ver y editar las reuniones.")
        return

    try:
        con = obtener_conexion()
        cursor = con.cursor()

        # ===============================
        # 1️⃣ CARGAR LISTADO DE DISTRITOS
        # ===============================
        cursor.execute("SELECT ID_Distrito, Nombre FROM Distrito ORDER BY Nombre")
        distritos = cursor.fetchall()

        if not distritos:
            st.error("❌ No hay distritos registrados.")
            return

        # Mostrar selector de distrito
        distrito_seleccionado = st.selectbox(
            "Selecciona un distrito",
            options=[(d[0], d[1]) for d in distritos],
            format_func=lambda x: x[1]
        )

        id_distrito = distrito_seleccionado[0]

        # ============================
        # 2️⃣ CARGAR GRUPOS DEL DISTRITO
        # ============================
        cursor.execute("""
            SELECT ID_Grupo, Codigo_Grupo 
            FROM Grupo 
            WHERE ID_Distrito = %s
            ORDER BY Codigo_Grupo
        """, (id_distrito,))
        grupos = cursor.fetchall()

        if not grupos:
            st.info("ℹ No hay grupos registrados en este distrito.")
            return

        grupo_seleccionado = st.selectbox(
            "Selecciona un grupo",
            options=[(g[0], g[1]) for g in grupos],
            format_func=lambda x: f"{x[0]} - {x[1]}"
        )

        id_grupo = grupo_seleccionado[0]

        st.write("---")

        # ==========================
        # 3️⃣ MOSTRAR/AGENDAR REUNIONES
        # ==========================
        st.subheader("📅 Reuniones registradas")

        cursor.execute("""
            SELECT ID_Reunion, Fecha, Tema, Lugar
            FROM Reunion
            WHERE ID_Grupo = %s
            ORDER BY Fecha DESC
        """, (id_grupo,))
        
        reuniones = cursor.fetchall()

        # Mostrar reuniones
        if not reuniones:
            st.info("No hay reuniones registradas para este grupo.")
        else:
            for r in reuniones:
                st.markdown(f"""
                ### 📌 Reunión #{r[0]}
                **Fecha:** {r[1]}  
                **Tema:** {r[2]}  
                **Lugar:** {r[3]}  
                ----
                """)

        # ============================
        # 4️⃣ FORMULARIO PARA CREAR REUNIONES
        # ============================
        st.subheader("📝 Registrar nueva reunión")

        with st.form("form_reunion"):
            fecha = st.date_input("Fecha de reunión")
            tema = st.text_input("Tema / Motivo")
            lugar = st.text_input("Lugar")
            guardar = st.form_submit_button("💾 Guardar reunión")

            if guardar:
                if tema.strip() == "" or lugar.strip() == "":
                    st.warning("⚠ Debes completar todos los campos.")
                else:
                    cursor.execute("""
                        INSERT INTO Reunion (ID_Grupo, Fecha, Tema, Lugar)
                        VALUES (%s, %s, %s, %s)
                    """, (id_grupo, fecha, tema, lugar))
                    con.commit()
                    st.success("✅ Reunión registrada correctamente.")
                    st.rerun()

    except Exception as e:
        st.error(f"❌ Error: {e}")

    finally:
        if 'cursor' in locals(): cursor.close()
        if 'con' in locals(): con.close()
