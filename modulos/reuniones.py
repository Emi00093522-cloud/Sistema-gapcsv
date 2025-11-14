import streamlit as st
import datetime
from conexion import obtener_conexion


# ============================================
#   REGISTRAR ASISTENCIA POR MIEMBROS
# ============================================

def registrar_asistencia(id_reunion, id_grupo):
    st.subheader("Registro de asistencia por miembros")

    conn = obtener_conexion()
    cursor = conn.cursor(dictionary=True)

    # Obtener miembros del grupo
    cursor.execute("""
        SELECT id_miembro, nombre, apellido
        FROM miembros
        WHERE id_grupo = %s
    """, (id_grupo,))
    miembros = cursor.fetchall()

    if not miembros:
        st.info("Este grupo no tiene miembros registrados.")
        return

    # FORMULARIO
    with st.form(key="form_asistencia"):
        asistencia_data = []

        st.write("### Lista de miembros:")

        for miembro in miembros:

            col1, col2, col3 = st.columns([3, 2, 3])

            with col1:
                st.write(f"{miembro['nombre']} {miembro['apellido']}")

            with col2:
                asistio = st.checkbox(
                    "Asistió",
                    key=f"asistencia_{miembro['id_miembro']}",
                    value=False
                )

            with col3:
                if asistio:
                    hora_llegada = st.time_input(
                        "Hora de llegada",
                        value=datetime.time(18, 0),
                        key=f"hora_{miembro['id_miembro']}"
                    )
                else:
                    hora_llegada = None

            asistencia_data.append({
                'id_miembro': miembro['id_miembro'],
                'asistencia': 1 if asistio else 0,
                'hora': hora_llegada
            })

        submit = st.form_submit_button("Guardar asistencia")

    # GUARDAR EN BD
    if submit:
        for registro in asistencia_data:
            cursor.execute("""
                INSERT INTO MiembroXReunion (id_reunion, id_miembro, asistencia, hora_llegada)
                VALUES (%s, %s, %s, %s)
            """, (
                id_reunion,
                registro['id_miembro'],
                registro['asistencia'],
                registro['hora']
            ))

        conn.commit()
        st.success("Asistencia guardada correctamente.")


# ============================================
#     CREAR REUNIÓN
# ============================================

def crear_reunion():
    st.subheader("Crear una nueva reunión")

    conn = obtener_conexion()
    cursor = conn.cursor(dictionary=True)

    # Obtener grupos
    cursor.execute("SELECT id_grupo, nombre FROM grupos")
    grupos = cursor.fetchall()

    with st.form(key="form_crear_reunion"):
        fecha = st.date_input("Fecha de la reunión", datetime.date.today())
        hora = st.time_input("Hora", datetime.time(18, 0))
        tema = st.text_input("Tema de la reunión")
        id_grupo = st.selectbox(
            "Seleccione un grupo",
            [g["id_grupo"] for g in grupos],
            format_func=lambda x: next(g["nombre"] for g in grupos if g["id_grupo"] == x)
        )

        submit = st.form_submit_button("Guardar")

    if submit:
        cursor.execute("""
            INSERT INTO reuniones (fecha, hora, tema, id_grupo)
            VALUES (%s, %s, %s, %s)
        """, (fecha, hora, tema, id_grupo))
        conn.commit()
        st.success("Reunión creada exitosamente.")


# ============================================
#     LISTAR + EDITAR REUNIONES
# ============================================

def listar_reuniones():
    conn = obtener_conexion()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT r.id_reunion, r.fecha, r.hora, r.tema, g.nombre AS grupo
        FROM reuniones r
        INNER JOIN grupos g ON g.id_grupo = r.id_grupo
        ORDER BY r.fecha DESC
    """)
    reuniones = cursor.fetchall()

    st.subheader("Reuniones registradas")

    if not reuniones:
        st.info("No hay reuniones registradas.")
        return

    seleccion = st.selectbox(
        "Seleccione una reunión",
        reuniones,
        format_func=lambda r: f"{r['fecha']} - {r['tema']} ({r['grupo']})"
    )

    if seleccion:
        st.write("### Detalles de la reunión")
        st.write(f"**Fecha:** {seleccion['fecha']}")
        st.write(f"**Hora:** {seleccion['hora']}")
        st.write(f"**Tema:** {seleccion['tema']}")
        st.write(f"**Grupo:** {seleccion['grupo']}")

        if st.button("Registrar asistencia"):
            registrar_asistencia(
                id_reunion=seleccion['id_reunion'],
                id_grupo=next(
                    r["id_grupo"] for r in reuniones if r["id_reunion"] == seleccion["id_reunion"]
                )
            )


# ============================================
#      FUNCIÓN PRINCIPAL DEL MÓDULO
# ============================================

def mostrar_reuniones():
    st.title("Gestión de Reuniones")

    menu = ["Crear reunión", "Listado de reuniones"]
    opcion = st.radio("Seleccione una opción", menu)

    if opcion == "Crear reunión":
        crear_reunion()
    elif opcion == "Listado de reuniones":
        listar_reuniones()
