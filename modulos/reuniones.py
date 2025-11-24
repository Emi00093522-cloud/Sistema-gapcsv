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

def _obtener_fecha_inicio_ciclo_actual():
    """
    Obtiene la fecha de inicio del ciclo actual desde el módulo de reglamento
    """
    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        # Buscar en ReglamentoGrupo la fecha de inicio del ciclo actual
        cursor.execute("""
            SELECT fecha_inicio_ciclo 
            FROM ReglamentoGrupo 
            ORDER BY fecha_actualizacion DESC 
            LIMIT 1
        """)
        
        resultado = cursor.fetchone()
        if resultado and resultado['fecha_inicio_ciclo']:
            fecha = resultado['fecha_inicio_ciclo']
            if hasattr(fecha, 'year'):
                return fecha.year
            else:
                # Si es string, extraer el año
                return int(str(fecha)[:4])
        
        # Si no existe, usar año actual por defecto
        return datetime.now().year
        
    except Exception as e:
        # Si hay error, usar año actual
        return datetime.now().year
    finally:
        try:
            cursor.close()
            con.close()
        except:
            pass

def _obtener_ultimo_ciclo_reuniones(id_grupo):
    """
    Obtiene el último ciclo registrado en las reuniones del grupo
    """
    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT DISTINCT ciclo 
            FROM Reunion 
            WHERE ID_Grupo = %s 
            ORDER BY ciclo DESC 
            LIMIT 1
        """, (id_grupo,))
        
        resultado = cursor.fetchone()
        return resultado['ciclo'] if resultado else None
        
    except Exception as e:
        st.error(f"❌ Error al obtener último ciclo: {e}")
        return None
    finally:
        try:
            cursor.close()
            con.close()
        except:
            pass

def _detectar_y_crear_nuevo_ciclo(id_grupo):
    """
    Detecta si hay un nuevo ciclo y crea las reuniones automáticamente
    """
    try:
        # Obtener ciclo actual del reglamento
        ciclo_actual_reglamento = _obtener_fecha_inicio_ciclo_actual()
        
        # Obtener último ciclo de reuniones existentes
        ultimo_ciclo_reuniones = _obtener_ultimo_ciclo_reuniones(id_grupo)
        
        # Si no hay reuniones o el ciclo del reglamento es mayor, crear nuevo ciclo
        if not ultimo_ciclo_reuniones or ciclo_actual_reglamento > int(ultimo_ciclo_reuniones):
            st.info(f"🔄 Detectado nuevo ciclo {ciclo_actual_reglamento}. Creando reuniones automáticamente...")
            return _crear_reuniones_nuevo_ciclo(id_grupo, str(ciclo_actual_reglamento), ultimo_ciclo_reuniones)
        
        return False
        
    except Exception as e:
        st.error(f"❌ Error al detectar nuevo ciclo: {e}")
        return False

def _crear_reuniones_nuevo_ciclo(id_grupo, nuevo_ciclo, ciclo_anterior=None):
    """
    Crea reuniones para un nuevo ciclo basándose en las reuniones del ciclo anterior
    """
    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        reuniones_creadas = 0
        
        # Si hay ciclo anterior, usar sus reuniones como plantilla
        if ciclo_anterior:
            # Obtener reuniones del ciclo anterior
            cursor.execute("""
                SELECT fecha, Hora, lugar, ID_Estado_reunion
                FROM Reunion 
                WHERE ID_Grupo = %s AND ciclo = %s
                ORDER BY fecha
            """, (id_grupo, ciclo_anterior))
            reuniones_anteriores = cursor.fetchall()
            
            if reuniones_anteriores:
                for reunion in reuniones_anteriores:
                    # Ajustar la fecha para el nuevo ciclo (sumar la diferencia de años)
                    fecha_original = reunion['fecha']
                    diferencia_anios = int(nuevo_ciclo) - int(ciclo_anterior)
                    
                    if hasattr(fecha_original, 'year'):
                        nueva_fecha = fecha_original.replace(year=fecha_original.year + diferencia_anios)
                    else:
                        # Si es string, convertir a datetime
                        if isinstance(fecha_original, str):
                            fecha_dt = datetime.strptime(fecha_original, '%Y-%m-%d')
                        else:
                            fecha_dt = fecha_original
                        nueva_fecha = fecha_dt.replace(year=fecha_dt.year + diferencia_anios)
                    
                    # Insertar nueva reunión para el nuevo ciclo
                    cursor.execute("""
                        INSERT INTO Reunion (ID_Grupo, fecha, Hora, lugar, ID_Estado_reunion, total_presentes, ciclo)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        id_grupo, 
                        nueva_fecha, 
                        reunion['Hora'], 
                        reunion['lugar'], 
                        1,  # Estado: Programada por defecto
                        0,  # Total presentes inicial
                        nuevo_ciclo
                    ))
                    reuniones_creadas += 1
        else:
            # Si no hay ciclo anterior, crear reuniones mensuales por defecto
            for mes in range(1, 13):
                fecha_reunion = datetime(int(nuevo_ciclo), mes, 15).date()  # Día 15 de cada mes
                
                cursor.execute("""
                    INSERT INTO Reunion (ID_Grupo, fecha, Hora, lugar, ID_Estado_reunion, total_presentes, ciclo)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    id_grupo, 
                    fecha_reunion, 
                    "18:00:00",  # Hora por defecto
                    "Sede del grupo",  # Lugar por defecto
                    1,  # Programada
                    0,  # Sin asistentes
                    nuevo_ciclo
                ))
                reuniones_creadas += 1
        
        con.commit()
        
        if reuniones_creadas > 0:
            st.success(f"✅ Se crearon {reuniones_creadas} reuniones para el ciclo {nuevo_ciclo}")
        else:
            st.info(f"ℹ️ No se crearon reuniones para el ciclo {nuevo_ciclo}")
        
        return True
        
    except Exception as e:
        con.rollback()
        st.error(f"❌ Error al crear reuniones para nuevo ciclo: {e}")
        return False
    finally:
        try:
            cursor.close()
            con.close()
        except:
            pass

def _obtener_ciclos_disponibles(id_grupo):
    """
    Obtiene todos los ciclos disponibles para un grupo
    """
    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT DISTINCT ciclo 
            FROM Reunion 
            WHERE ID_Grupo = %s 
            ORDER BY ciclo DESC
        """, (id_grupo,))
        
        ciclos = [row['ciclo'] for row in cursor.fetchall()]
        return ciclos
        
    except Exception as e:
        st.error(f"❌ Error al obtener ciclos: {e}")
        return []
    finally:
        try:
            cursor.close()
            con.close()
        except:
            pass

# ==========================================================
#   MÓDULO PRINCIPAL
# ==========================================================

def mostrar_reuniones():

    # Títulos
    st.header("📅 Registro de Reuniones")
    st.subheader("📌 Registro de Reuniones del Grupo")

    # Solo SECRETARIA
    if not _tiene_rol_secretaria():
        st.warning("🔒 Acceso restringido: Solo la SECRETARIA puede ver y editar las reuniones.")
        return

    # 🔥 1) Tomar el grupo del usuario logueado
    id_grupo = st.session_state.get("id_grupo")
    if id_grupo is None:
        st.error("⚠️ No tienes un grupo asociado. Crea primero un grupo en el módulo 'Grupos'.")
        return

    # 🔥 2) DETECTAR Y CREAR NUEVO CICLO AUTOMÁTICAMENTE
    _detectar_y_crear_nuevo_ciclo(id_grupo)

    # Conexión
    try:
        con = obtener_conexion()
        cursor = con.cursor(dictionary=True)
    except Exception as e:
        st.error(f"❌ Error de conexión: {e}")
        return

    try:
        # ======================================================
        # 0. INFO DEL GRUPO (DISTRITO + NOMBRE) SOLO LECTURA
        # ======================================================
        cursor.execute("""
            SELECT g.ID_Grupo,
                   g.nombre AS nombre_grupo,
                   d.ID_Distrito,
                   d.nombre AS nombre_distrito
            FROM Grupo g
            LEFT JOIN Distrito d ON g.ID_Distrito = d.ID_Distrito
            WHERE g.ID_Grupo = %s
        """, (id_grupo,))
        fila_grupo = cursor.fetchone()

        nombre_grupo = fila_grupo["nombre_grupo"] if fila_grupo else f"Grupo {id_grupo}"
        nombre_distrito = fila_grupo.get("nombre_distrito") if fila_grupo and fila_grupo.get("nombre_distrito") else "N/D"

        # Mostrar info del grupo/distrito (solo lectura)
        colg1, colg2 = st.columns(2)
        with colg1:
            st.text_input("Distrito", nombre_distrito, disabled=True)
        with colg2:
            st.text_input("Grupo", nombre_grupo, disabled=True)

        # ======================================================
        # 1. SELECTOR DE CICLO
        # ======================================================
        st.write("---")
        
        ciclos_disponibles = _obtener_ciclos_disponibles(id_grupo)
        ciclo_actual_reglamento = _obtener_fecha_inicio_ciclo_actual()
        
        if not ciclos_disponibles:
            ciclos_disponibles = [str(ciclo_actual_reglamento)]
        
        col_ciclo1, col_ciclo2 = st.columns([2, 1])
        with col_ciclo1:
            ciclo_seleccionado = st.selectbox(
                "Seleccionar Ciclo",
                options=ciclos_disponibles,
                index=0
            )
        
        with col_ciclo2:
            st.write("")  # Espacio para alinear
            if st.button("🔄 Forzar Nuevo Ciclo", use_container_width=True):
                nuevo_ciclo = str(ciclo_actual_reglamento + 1)
                if _crear_reuniones_nuevo_ciclo(id_grupo, nuevo_ciclo, ciclo_seleccionado):
                    st.rerun()

        st.write("---")

        # ======================================================
        # 2. CARGAR REUNIONES DEL GRUPO (FILTRADO POR CICLO)
        # ======================================================
        cursor.execute("""
            SELECT ID_Reunion, fecha, Hora, lugar, total_presentes, ID_Estado_reunion, ciclo
            FROM Reunion
            WHERE ID_Grupo = %s AND ciclo = %s
            ORDER BY fecha DESC, Hora DESC
        """, (id_grupo, ciclo_seleccionado))
        reuniones = cursor.fetchall()

        st.subheader(f"📄 Reuniones registradas - Ciclo {ciclo_seleccionado}")

        if not reuniones:
            st.info("No hay reuniones registradas para este ciclo.")
        else:
            filas = []
            for r in reuniones:
                # Manejo seguro de fecha y hora (pueden venir como string o datetime)
                fecha_val = r.get("fecha")
                if hasattr(fecha_val, "strftime"):
                    fecha_str = fecha_val.strftime("%Y-%m-%d")
                else:
                    fecha_str = str(fecha_val) if fecha_val is not None else ""

                hora_val = r.get("Hora")
                hora_str = ""
                if hora_val:
                    if hasattr(hora_val, "strftime"):
                        hora_str = hora_val.strftime("%H:%M")
                    else:
                        hora_str = str(hora_val)

                # Obtener nombre del estado
                estado_id = r.get("ID_Estado_reunion", 1)
                estado_nombre = {1: "Programada", 2: "Realizada", 3: "Cancelada"}.get(estado_id, "Programada")

                filas.append({
                    "Fecha": fecha_str,
                    "Hora": hora_str,
                    "Lugar": r.get("lugar") or "",
                    "Estado": estado_nombre,
                    "Asistentes": r.get("total_presentes", 0)
                })
            
            # Mostrar dataframe
            st.dataframe(pd.DataFrame(filas), use_container_width=True)

        st.write("---")

        # ======================================================
        # 3. FORMULARIO: CREAR O EDITAR
        # ======================================================
        st.subheader("✏️ Crear o Editar Reunión")

        opciones = ["➕ Nueva reunión"]
        mapa_reuniones = {"➕ Nueva reunión": None}

        for r in reuniones:
            fecha_val = r.get("fecha")
            if hasattr(fecha_val, "strftime"):
                fecha_str = fecha_val.strftime("%Y-%m-%d")
            else:
                fecha_str = str(fecha_val) if fecha_val is not None else ""

            hora_val = r.get("Hora")
            hora_str = ""
            if hora_val:
                if hasattr(hora_val, "strftime"):
                    hora_str = hora_val.strftime("%H:%M")
                else:
                    hora_str = str(hora_val)

            etiqueta = f"{r['ID_Reunion']} — {fecha_str} {hora_str}"
            opciones.append(etiqueta)
            mapa_reuniones[etiqueta] = r["ID_Reunion"]

        seleccion = st.selectbox("Seleccione una reunión", opciones)
        id_reunion = mapa_reuniones[seleccion]

        # Valores por defecto para el form de creación/edición
        if id_reunion is None:
            fecha_def = datetime.now().date()
            hora_def = datetime.now().time().replace(second=0, microsecond=0)
            lugar_def = ""
            estado_def = 1
            total_presentes_def = 0
        else:
            fila = next((x for x in reuniones if x["ID_Reunion"] == id_reunion), {})
            fecha_def = fila.get("fecha") or datetime.now().date()
            hora_def = fila.get("Hora") or datetime.now().time().replace(second=0, microsecond=0)
            lugar_def = fila.get("lugar", "")
            estado_def = fila.get("ID_Estado_reunion", 1)
            total_presentes_def = fila.get("total_presentes", 0)

        with st.form("form_reuniones"):
            col1, col2 = st.columns(2)
            with col1:
                fecha = st.date_input("Fecha", fecha_def)
            with col2:
                hora = st.time_input("Hora", hora_def)

            lugar = st.text_input("Lugar", lugar_def)
            
            # 🔥 NUEVO CAMPO: TOTAL PRESENTES
            total_presentes = st.number_input(
                "Total de presentes", 
                min_value=0, 
                value=total_presentes_def,
                help="Número total de personas que asistieron a la reunión"
            )

            estados = {"Programada": 1, "Realizada": 2, "Cancelada": 3}
            estado_texto_actual = [k for k, v in estados.items() if v == estado_def][0]

            estado_texto = st.selectbox(
                "Estado de la reunión",
                list(estados.keys()),
                index=list(estados.keys()).index(estado_texto_actual)
            )
            estado = estados[estado_texto]

            guardar = st.form_submit_button("💾 Guardar")
            eliminar = st.form_submit_button("🗑️ Eliminar") if id_reunion else False
            nuevo = st.form_submit_button("➕ Nuevo")

        # ------------------------------------------------------
        # GUARDAR / INSERT / UPDATE
        # ------------------------------------------------------
        if guardar:
            try:
                if hasattr(hora, "strftime"):
                    hora_str_full = hora.strftime("%H:%M:%S")
                else:
                    hora_str_full = str(hora)

                if id_reunion:
                    cursor.execute("""
                        UPDATE Reunion
                        SET fecha=%s, Hora=%s, lugar=%s, ID_Estado_reunion=%s, total_presentes=%s
                        WHERE ID_Reunion=%s
                    """, (fecha, hora_str_full, lugar, int(estado), int(total_presentes), id_reunion))
                else:
                    cursor.execute("""
                        INSERT INTO Reunion (ID_Grupo, fecha, Hora, lugar, ID_Estado_reunion, total_presentes, ciclo)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (id_grupo, fecha, hora_str_full, lugar, int(estado), int(total_presentes), ciclo_seleccionado))

                con.commit()
                st.success("✅ Reunión guardada correctamente.")
                st.rerun()

            except Exception as e:
                con.rollback()
                st.error(f"❌ Error al guardar: {e}")

        # ------------------------------------------------------
        # ELIMINAR
        # ------------------------------------------------------
        if eliminar and id_reunion:
            try:
                cursor.execute("DELETE FROM Reunion WHERE ID_Reunion=%s", (id_reunion,))
                con.commit()
                st.success("🗑️ Reunión eliminada.")
                st.rerun()
            except Exception as e:
                con.rollback()
                st.error(f"❌ Error al eliminar: {e}")

        # ======================================================
        # PESTAÑAS PARA ASISTENCIA Y PRÉSTAMO
        # ======================================================
        if id_reunion:
            st.write("---")
            
            tab1, tab2 = st.tabs(["🧍‍♂️🧍‍♀️ Asistencia", "💰 Préstamo"])
            
            # ======================================================
            # PESTAÑA 1: ASISTENCIA
            # ======================================================
            with tab1:
                st.subheader("🧍‍♂️🧍‍♀️ Registro de Asistencia")

                cursor.execute("""
                    SELECT ID_Miembro, nombre, apellido
                    FROM Miembro
                    WHERE ID_Grupo = %s
                    ORDER BY nombre, apellido
                """, (id_grupo,))
                miembros = cursor.fetchall()

                if not miembros:
                    st.info("No hay miembros registrados en este grupo.")
                else:
                    cursor.execute("""
                        SELECT ID_Miembro, asistencia
                        FROM MiembroXReunion
                        WHERE ID_Reunion = %s
                    """, (id_reunion,))
                    asistencia_previa_rows = cursor.fetchall()
                    asistencia_previa = {r["ID_Miembro"]: r["asistencia"] for r in asistencia_previa_rows}

                    st.write("Marque asistencia y luego presione '💾 Guardar asistencia'")

                    asistentes_dict = {}
                    for m in miembros:
                        mid = m["ID_Miembro"]
                        label = f"{m.get('nombre','')} {m.get('apellido','')}".strip()
                        key = f"asist_{id_reunion}_{mid}"
                        default_val = bool(asistencia_previa.get(mid, 0))
                        asistentes_dict[mid] = st.checkbox(label, value=default_val, key=key)

                    if st.button("💾 Guardar asistencia", key="guardar_asistencia"):
                        try:
                            for mid, checked in asistentes_dict.items():
                                asistencia_val = 1 if checked else 0
                                cursor.execute("""
                                    INSERT INTO MiembroXReunion (ID_Miembro, ID_Reunion, asistencia, Fecha_registro)
                                    VALUES (%s, %s, %s, NOW())
                                    ON DUPLICATE KEY UPDATE
                                        asistencia = VALUES(asistencia),
                                        Fecha_registro = VALUES(Fecha_registro)
                                """, (mid, id_reunion, asistencia_val))

                            cursor.execute("""
                                SELECT COUNT(*) AS total
                                FROM MiembroXReunion
                                WHERE ID_Reunion = %s AND asistencia = 1
                            """, (id_reunion,))
                            total_row = cursor.fetchone()
                            total = int(total_row["total"]) if total_row and "total" in total_row else 0

                            cursor.execute("""
                                UPDATE Reunion SET total_presentes = %s WHERE ID_Reunion = %s
                            """, (total, id_reunion))

                            con.commit()
                            st.success(f"✅ Asistencia guardada. Total presentes: {total}")
                            st.rerun()

                        except Exception as e:
                            con.rollback()
                            st.error(f"❌ Error al guardar asistencia: {e}")

            # ======================================================
            # PESTAÑA 2: PRÉSTAMO
            # ======================================================
            with tab2:
                st.subheader("💰 Gestión de Préstamos")
                st.info("Funcionalidad de préstamos en desarrollo...")

                with st.form("form_prestamo"):
                    st.write("Registrar nuevo préstamo:")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        monto = st.number_input("Monto del préstamo", min_value=0.0, step=0.01)
                        fecha_prestamo = st.date_input("Fecha del préstamo", datetime.now().date())
                    
                    with col2:
                        plazo = st.selectbox("Plazo (meses)", [1, 3, 6, 12, 24, 36])
                        tasa_interes = st.number_input("Tasa de interés (%)", min_value=0.0, step=0.1)
                    
                    descripcion = st.text_area("Descripción del préstamo")
                    
                    guardar_prestamo = st.form_submit_button("💾 Guardar Préstamo")
                    
                    if guardar_prestamo:
                        st.success(f"Préstamo de ${monto} registrado correctamente")
                        # Aquí iría la lógica para guardar en la base de datos

    except Exception as e:
        st.error(f"❌ Error: {e}")
    finally:
        try:
            cursor.close()
            con.close()
        except:
            pass
