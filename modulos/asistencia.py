import streamlit as st
from config.conexion import obtener_conexion

def mostrar_asistencia():
    st.title("📝 Registro de Asistencia")

    # 1️⃣ Verificar si tenemos la reunión seleccionada
    id_reunion = st.session_state.get("id_reunion_asistencia", None)

    if id_reunion is None:
        st.error("No se seleccionó ninguna reunión.")
        return

    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)

    # 2️⃣ Obtener el grupo al que pertenece esta reunión
    cursor.execute("SELECT ID_Grupo, Tema FROM Reunion WHERE ID_Reunion=%s", (id_reunion,))
    reunion = cursor.fetchone()

    if not reunion:
        st.error("Reunión no encontrada.")
        return

    id_grupo = reunion["ID_Grupo"]

    st.subheader(f"Reunión #{id_reunion} - {reunion['Tema']}")

    # 3️⃣ Listar los miembros del grupo
    cursor.execute("SELECT * FROM Miembro WHERE ID_Grupo=%s", (id_grupo,))
    miembros = cursor.fetchall()

    st.write(f"Miembros del grupo: **{len(miembros)}**")

    # 4️⃣ Mostrar checkboxes de asistencia
    asistencia_check = {}

    for m in miembros:
        asistencia_check[m["ID_Miembro"]] = st.checkbox(
            f"{m['Nombre']} {m['Apellido']}",
            key=f"as_{m['ID_Miembro']}"
        )

    # 5️⃣ Botón para guardar asistencia
    if st.button("💾 Guardar asistencia"):
        # Borrar asistencia previa
        cursor.execute("DELETE FROM MiembroxReunion WHERE ID_Reunion=%s", (id_reunion,))

        # Insertar asistencia nueva
        insert = """
            INSERT INTO MiembroxReunion (ID_Reunion, ID_Miembro, Asistencia)
            VALUES (%s, %s, %s)
        """

        for id_miembro, asistio in asistencia_check.items():
            cursor.execute(insert, (id_reunion, id_miembro, 1 if asistio else 0))

        conexion.commit()
        st.success("Asistencia registrada correctamente 🎉")

        # Regresar a reuniones
        st.switch_page("modulos/reuniones.py")

    conexion.close()


# Ejecutar función
mostrar_asistencia()

