def mostrar_prestamo():
    # ... código existente ...
    
    try:
        con = obtener_conexion()
        cursor = con.cursor()

        # CARGAR LISTA DE REUNIONES
        cursor.execute("SELECT ID_Reunion, fecha FROM Reunion ORDER BY fecha DESC")
        reuniones = cursor.fetchall()

        if not reuniones:
            st.warning("⚠️ No hay reuniones registradas.")
            return

        reuniones_dict = {f"Reunión {r[0]} - {r[1]}": r[0] for r in reuniones}

        # Seleccionar reunión primero
        reunion_sel = st.selectbox(
            "Selecciona la reunión:",
            list(reuniones_dict.keys())
        )
        id_reunion = reuniones_dict[reunion_sel]

        # CARGAR MIEMBROS QUE ASISTIERON A ESTA REUNIÓN
        cursor.execute("""
            SELECT m.ID_Miembro, m.nombre 
            FROM Miembro m
            JOIN Asistencia a ON m.ID_Miembro = a.ID_Miembro
            WHERE a.ID_Reunion = %s AND a.asistio = 1
            ORDER BY m.nombre
        """, (id_reunion,))
        
        miembros_presentes = cursor.fetchall()

        if not miembros_presentes:
            st.warning(f"⚠️ No hay miembros registrados como presentes en esta reunión.")
            return

        miembros_dict = {f"{m[1]} (ID {m[0]})": m[0] for m in miembros_presentes}

        # ... resto del código de préstamos usando miembros_dict ...
        
    except Exception as e:
        st.error(f"❌ Error: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'con' in locals():
            con.close()
