import streamlit as st
from datetime import datetime
from modulos.config.conexion import obtener_conexion
import pandas as pd

# ==========================================================
#   FUNCIONES INTERNAS
# ==========================================================

def _get_cargo_detectado():
    return st.session_state.get("cargo_de_usuario", "").strip().upper()

def _tiene_rol_secretaria():
    return _get_cargo_detectado() == "SECRETARIA"

# ==========================================================
#   MÓDULO PRINCIPAL
# ==========================================================

def mostrar_reuniones():
    st.header("📅 Gestión de Reuniones")

    if not _tiene_rol_secretaria():
        st.warning("🔒 Acceso restringido: Solo la SECRETARIA puede ver y editar las reuniones.")
        return

    # Pestañas principales (igual que reglamentos)
    tab1, tab2 = st.tabs(["📝 Registrar Nueva Reunión", "✏️ Editar Reuniones Existentes"])

    with tab1:
        _mostrar_registro_reuniones()

    with tab2:
        _mostrar_edicion_reuniones()

# ==========================================================
#   FUNCIÓN PARA REGISTRAR NUEVA REUNIÓN
# ==========================================================

def _mostrar_registro_reuniones():
    st.subheader("Registrar Nueva Reunión")

    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
    except Exception as e:
        st.error(f"❌ Error de conexión: {e}")
        return

    # 1. SELECCIONAR DISTRITO
    try:
        cursor.execute("SELECT ID_Distrito, nombre FROM Distrito ORDER BY nombre")
        distritos = cursor.fetchall()
    except Exception:
        distritos = []

    if not distritos:
        st.error("⚠️ No existen Distritos registrados.")
        cursor.close()
        con.close()
        return

    mapa_distritos = {f"{d['ID_Distrito']} - {d['nombre']}": d['ID_Distrito'] for d in distritos}
    distrito_label = st.selectbox("Seleccione Distrito", options=list(mapa_distritos.keys()))
    id_distrito = mapa_distritos[distrito_label]

    # 2. SELECCIONAR GRUPO SEGÚN DISTRITO
    cursor.execute(
        "SELECT ID_Grupo, nombre FROM Grupo WHERE ID_Distrito = %s ORDER BY nombre",
        (id_distrito,)
    )
    grupos = cursor.fetchall()

    if not grupos:
        st.warning("⚠️ Este distrito no tiene grupos registrados.")
        cursor.close()
        con.close()
        return

    mapa_grupos = {f"{g['ID_Grupo']} - {g['nombre']}": g['ID_Grupo'] for g in grupos}
    grupo_label = st.selectbox("Seleccione Grupo", list(mapa_grupos.keys()))
    id_grupo = mapa_grupos[grupo_label]

    st.markdown("---")
    st.markdown("### 📋 Formulario de Reunión")

    # PESTAÑAS DENTRO DEL FORMULARIO (igual que reglamentos)
    reunion_tab1, reunion_tab2 = st.tabs(["💰 Préstamo", "✅ Asistencia"])

    with reunion_tab1:
        st.markdown("#### Información de Préstamos")
        
        col_prest1, col_prest2, col_prest3 = st.columns(3)
        
        with col_prest1:
            st.markdown("**Monto total prestado:**")
            monto_prestado = st.number_input(
                "Monto ($):",
                min_value=0.00,
                value=0.00,
                step=10.00,
                format="%.2f",
                key="monto_prestado_reunion"
            )
        
        with col_prest2:
            st.markdown("**Nuevos préstamos aprobados:**")
            nuevos_prestamos = st.number_input(
                "Cantidad:",
                min_value=0,
                value=0,
                step=1,
                key="nuevos_prestamos_reunion"
            )
        
        with col_prest3:
            st.markdown("**Préstamos pagados:**")
            prestamos_pagados = st.number_input(
                "Cantidad:",
                min_value=0,
                value=0,
                step=1,
                key="prestamos_pagados_reunion"
            )
        
        st.markdown("**Observaciones de préstamos:**")
        observaciones_prestamos = st.text_area(
            "Notas sobre préstamos:",
            placeholder="Ej: Se aprobaron 2 nuevos préstamos, se recibieron 3 pagos...",
            height=80,
            key="observaciones_prestamos"
        )

    with reunion_tab2:
        st.markdown("#### Gestión de Asistencia")
        
        # Información básica de la reunión
        col_fecha, col_hora = st.columns(2)
        
        with col_fecha:
            fecha_reunion = st.date_input(
                "Fecha de reunión:",
                datetime.now().date(),
                key="fecha_reunion"
            )
        
        with col_hora:
            hora_reunion = st.time_input(
                "Hora de reunión:",
                datetime.now().time().replace(second=0, microsecond=0),
                key="hora_reunion"
            )
        
        lugar_reunion = st.text_input(
            "Lugar de reunión:",
            placeholder="Ej: Casa comunal, Salón parroquial...",
            key="lugar_reunion"
        )
        
        # Configuración de asistencia
        col_asist1, col_asist2 = st.columns(2)
        
        with col_asist1:
            st.markdown("**Total de miembros presentes:**")
            total_presentes = st.number_input(
                "Miembros presentes:",
                min_value=0,
                value=0,
                step=1,
                key="total_presentes"
            )
        
        with col_asist2:
            st.markdown("**Porcentaje de asistencia:**")
            porcentaje_asistencia = st.number_input(
                "Porcentaje (%):",
                min_value=0,
                max_value=100,
                value=0,
                key="porcentaje_asistencia_reunion"
            )
        
        st.markdown("**Observaciones de asistencia:**")
        observaciones_asistencia = st.text_area(
            "Notas sobre asistencia:",
            placeholder="Ej: 15 miembros presentes, 3 ausentes con justificación...",
            height=80,
            key="observaciones_asistencia"
        )

    # Otras observaciones generales
    st.markdown("---")
    st.markdown("#### Otras observaciones de la reunión")
    observaciones_generales = st.text_area(
        "Puntos tratados y acuerdos:",
        placeholder="Describa los principales puntos tratados en la reunión, acuerdos tomados, etc...",
        height=120,
        key="observaciones_generales"
    )

    # Botón para guardar TODO el registro de reunión
    st.markdown("---")
    if st.button("💾 Guardar Registro Completo de Reunión", use_container_width=True, type="primary"):
        # Validar campos obligatorios
        if not lugar_reunion:
            st.error("❌ El campo 'Lugar de reunión' es obligatorio.")
            return

        try:
            # Convertir hora a string
            if hasattr(hora_reunion, "strftime"):
                hora_str_full = hora_reunion.strftime("%H:%M:%S")
            else:
                hora_str_full = str(hora_reunion)

            # Guardar la reunión principal
            cursor.execute("""
                INSERT INTO Reunion 
                (ID_Grupo, fecha, Hora, lugar, total_presentes, observaciones)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                id_grupo, fecha_reunion, hora_str_full, lugar_reunion, 
                total_presentes, observaciones_generales
            ))
            
            # Obtener el ID de la reunión recién insertada
            id_reunion = cursor.lastrowid
            
            # Guardar información específica de préstamos (si existe la tabla)
            try:
                cursor.execute("""
                    INSERT INTO ReunionPrestamos 
                    (ID_Reunion, monto_prestado, nuevos_prestamos, prestamos_pagados, observaciones)
                    VALUES (%s, %s, %s, %s, %s)
                """, (id_reunion, monto_prestado, nuevos_prestamos, prestamos_pagados, observaciones_prestamos))
            except:
                # Si no existe la tabla, continuar sin error
                pass
            
            con.commit()
            st.success("✅ Reunión guardada exitosamente!")
            st.balloons()
            
        except Exception as e:
            con.rollback()
            st.error(f"❌ Error al guardar la reunión: {e}")

    # Cerrar conexión
    cursor.close()
    con.close()

# ==========================================================
#   FUNCIÓN PARA EDITAR REUNIONES EXISTENTES
# ==========================================================

def _mostrar_edicion_reuniones():
    st.subheader("Editar Reuniones Existentes")

    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
    except Exception as e:
        st.error(f"❌ Error de conexión: {e}")
        return

    # Cargar reuniones existentes
    cursor.execute("""
        SELECT r.ID_Reunion, r.fecha, r.Hora, r.lugar, r.total_presentes, 
               g.nombre as grupo_nombre, d.nombre as distrito_nombre
        FROM Reunion r
        JOIN Grupo g ON r.ID_Grupo = g.ID_Grupo
        JOIN Distrito d ON g.ID_Distrito = d.ID_Distrito
        ORDER BY r.fecha DESC, r.Hora DESC
    """)
    reuniones_existentes = cursor.fetchall()

    if not reuniones_existentes:
        st.info("📝 No hay reuniones registradas aún.")
        cursor.close()
        con.close()
        return

    st.write("### 📋 Reuniones Registradas")
    
    for reunion in reuniones_existentes:
        with st.expander(f"📅 {reunion['grupo_nombre']} - {reunion['distrito_nombre']} - {reunion['fecha']}"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Lugar:** {reunion['lugar']}")
                st.write(f"**Hora:** {reunion['Hora']}")
                st.write(f"**Asistentes:** {reunion['total_presentes']}")
            
            with col2:
                if st.button(f"✏️ Editar", key=f"editar_{reunion['ID_Reunion']}"):
                    st.session_state.reunion_a_editar = reunion['ID_Reunion']
                    st.rerun()

    # TODO: Implementar la funcionalidad de edición completa
    if 'reunion_a_editar' in st.session_state:
        st.write("---")
        st.subheader("✏️ Editando Reunión")
        st.info("🔧 Funcionalidad de edición en desarrollo...")
        
        if st.button("❌ Cancelar Edición"):
            del st.session_state.reunion_a_editar
            st.rerun()

    cursor.close()
    con.close()
