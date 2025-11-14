# --- IMPORTS NECESARIOS (CON FIX PARA LA CARPETA CONFIG) ---
import sys
import os
sys.path.append(os.path.abspath("config"))

from conexion import obtener_conexion
import streamlit as st


def obtener_reuniones():
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("""
        SELECT r.ID_Reunion, r.Fecha, r.Hora, g.Nombre AS Grupo, r.ID_Grupo
        FROM Reunion r
        INNER JOIN Grupo g ON r.ID_Grupo = g.ID_Grupo
        ORDER BY r.Fecha DESC
    """)
    datos = cursor.fetchall()
    conexion.close()
    return datos


def obtener_miembros_por_grupo(id_grupo):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("""
        SELECT ID_Miembro, Nombre, Apellido
        FROM Miembro
        WHERE ID_Grupo = %s
        ORDER BY Nombre
    """, (id_grupo,))
    datos = cursor.fetchall()
    conexion.close()
    return datos


def guardar_asistencia(id_reunion, asistencias):
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    # Limpia asistencias existentes
    cursor.execute("DELETE FROM MiembroxReunion WHERE ID_Reunion = %s", (id_reunion,))

    # Inserta nuevas asistencias
    for id_miembro, presente in asistencias.items():
        cursor.execute("""
            INSERT INTO MiembroxReunion (ID_Miembro, ID_Reunion, Presente)
            VALUES (%s, %s, %s)
        """, (id_miembro, id_reunion, presente))

    # Calcula total presentes
    total_presentes = sum(1 for p in asistencias.values() if p == 1)

    cursor.execute("""
        UPDATE Reunion SET Total_Presentes = %s
        WHERE ID_Reunion = %s
    """, (total_presentes, id_reunion))

    conexion.commit()
    conexion.close()
    return total_presentes


def obtener_asistencia_guardada(id_reunion):
    conexion = obtener_conexion()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("""
        SELECT ID_Miembro, Presente
        FROM MiembroxReunion
        WHERE ID_Reunion = %s
    """, (id_reunion,))
    datos = cursor.fetchall()
    conexion.close()

    return {fila["ID_Miembro"]: fila["Presente"] for fila in datos}


# ============================
#     📌 INTERFAZ PRINCIPAL
# ============================
def mostrar_asistencia():
    st.title("📋 Control de Asistencia por Reunión")

    reuniones = obtener_reuniones()
    if not reuniones:
        st.warning("⚠️ No hay reuniones registradas.")
        return

    # Selector de reunión
    nombres = [
        f"Reunión {r['ID_Reunion']} - {r['Fecha']} - {r['Grupo']}"
        for r in reuniones
    ]

    seleccion = st.selectbox("Seleccione una reunión:", nombres)
    idx = nombres.index(seleccion)
    reunion = reuniones[idx]

    st.subheader(f"📅 Reunión del {reunion['Fecha']} - Grupo: {reunion['Grupo']}")

    # Obtener miembros del grupo
    miembros = obtener_miembros_por_grupo(reunion["ID_Grupo"])

    if not miembros:
        st.warning("⚠️ No hay miembros registrados en este grupo.")
        return

    # Obtener asistencias guardadas
    asistencia_guardada = obtener_asistencia_guardada(reunion["ID_Reunion"])

    st.write("### 👉 Marque asistencia:")

    asistencias = {}

    with st.form("form_asistencia"):
        for m in miembros:
            key_check = f"asis_{m['ID_Miembro']}"
            presente = asistencia_guardada.get(m["ID_Miembro"], 0) == 1

            asistencias[m["ID_Miembro"]] = st.checkbox(
                f"{m['Nombre']} {m['Apellido']}",
                value=presente,
                key=key_check
            )

        btn_guardar = st.form_submit_button("💾 Guardar asistencia")

        if btn_guardar:
            # Convertir booleanos a enteros 1/0
            asistencias_db = {mid: (1 if pres else 0) for mid, pres in asistencias.items()}

            total = guardar_asistencia(reunion["ID_Reunion"], asistencias_db)

            st.success(f"✔️ Asistencia guardada correctamente. Total presentes: {total}")
            st.rerun()


