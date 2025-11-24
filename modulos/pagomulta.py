import streamlit as st
from modulos.config.conexion import obtener_conexion
from datetime import date

# ------------------------------------------------------------
# FUNCION AUXILIAR: Obtener la fecha de la siguiente reunión
# ------------------------------------------------------------
def obtener_fecha_limite_pago(id_reunion_actual):
    con = obtener_conexion()
    cursor = con.cursor()

    # 1. Obtener el grupo de la reunión actual
    cursor.execute("""
        SELECT ID_Grupo, fecha 
        FROM Reunion 
        WHERE ID_Reunion = %s
    """, (id_reunion_actual,))
    datos = cursor.fetchone()

    if not datos:
        return None

    id_grupo, fecha_reunion = datos

    # 2. Buscar la próxima reunión del MISMO grupo
    cursor.execute("""
        SELECT fecha 
        FROM Reunion
        WHERE ID_Grupo = %s
          AND fecha > %s
        ORDER BY fecha ASC
        LIMIT 1
    """, (id_grupo, fecha_reunion))

    siguiente = cursor.fetchone()

    return siguiente[0] if siguiente else None


# ------------------------------------------------------------
# MÓDULO PRINCIPAL
# ------------------------------------------------------------
def mostrar_pago_multas():

    st.header("💰 Registro de Pago de Multas")

    con = obtener_conexion()
    cursor = con.cursor()

    # --------------------------------------------------------
    # 1. Cargar multas pendientes de pago
    # --------------------------------------------------------
    cursor.execute("""
        SELECT 
            m.ID_Multa,
            m.fecha,
            m.ID_Reunion,
            mem.ID_Miembro,
            CONCAT(mem.nombre, ' ', mem.apellido) AS nombre_completo,
            re.lugar,
            re.fecha AS fecha_reunion
        FROM Multa m
        INNER JOIN Miembro mem ON mem.ID_Miembro = m.ID_Miembro
        INNER JOIN Reunion re ON re.ID_Reunion = m.ID_Reunion
        WHERE m.ID_Estado_multa = 1
        ORDER BY m.fecha DESC
    """)

    multas = cursor.fetchall()

    if not multas:
        st.info("No hay multas pendientes.")
        return

    # --------------------------------------------------------
    # 2. Seleccionar una multa
    # --------------------------------------------------------
    opciones = {
        f"Multa #{m[0]} - {m[4]} - Fecha: {m[1]} (Reunión: {m[6]})": m
        for m in multas
    }

    seleccion = st.selectbox("Selecciona una multa para registrar su pago:", list(opciones.keys()))

    multa = opciones[seleccion]

    id_multa = multa[0]
    fecha_multa = multa[1]
    id_reunion_multa = multa[2]
    id_miembro = multa[3]
    nombre_completo = multa[4]

    st.subheader("📄 Detalles de la Multa Seleccionada")

    st.write(f"👤 Miembro: **{nombre_completo}**")
    st.write(f"📅 Fecha de la multa: **{fecha_multa}**")

    # --------------------------------------------------------
    # 3. Calcular FECHA LÍMITE según la lógica real
    # --------------------------------------------------------
    fecha_limite = obtener_fecha_limite_pago(id_reunion_multa)

    if fecha_limite is None:
        st.error("⚠ No existe una reunión futura registrada para este grupo. No se puede fijar fecha límite.")
        return

    st.write(f"⏳ Fecha límite de pago (próxima reunión): **{fecha_limite}**")

    monto = st.number_input("Monto pagado:", min_value=0.00, step=0.25)

    if st.button("Registrar pago"):

        cursor.execute("""
            INSERT INTO Pago_Multa (ID_Miembro, ID_Multa, monto_pagado, fecha_pago, fecha_limite_pago)
            VALUES (%s, %s, %s, CURDATE(), %s)
        """, (id_miembro, id_multa, monto, fecha_limite))

        # Cambiar estado de multa a pagada
        cursor.execute("""
            UPDATE Multa SET ID_Estado_multa = 2
            WHERE ID_Multa = %s
        """, (id_multa,))

        con.commit()

        st.success(f"Pago registrado correctamente. Fecha límite: {fecha_limite}")
        st.rerun()
