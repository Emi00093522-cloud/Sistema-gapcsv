import streamlit as st
from datetime import datetime, date
from modulos.config.conexion import obtener_conexion
from dateutil.relativedelta import relativedelta

def inicializar_session_state():
    """Inicializa el estado de la sesión para grupos"""
    if 'mostrar_formulario_grupo' not in st.session_state:
        st.session_state.mostrar_formulario_grupo = True
    if 'grupo_seleccionado' not in st.session_state:
        st.session_state.grupo_seleccionado = None
    if 'creando_nuevo_ciclo' not in st.session_state:
        st.session_state.creando_nuevo_ciclo = None

def obtener_grupos_por_usuario(id_usuario: int):
    """
    Obtiene todos los grupos asociados a un usuario
    """
    con = obtener_conexion()
    if not con:
        return []

    try:
        cursor = con.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                g.ID_Grupo,
                g.nombre,
                g.fecha_inicio,
                d.nombre as distrito,
                p.nombre as promotora,
                CASE 
                    WHEN g.ID_Estado = 1 THEN 'Activo'
                    ELSE 'Inactivo'
                END as estado
            FROM Grupo g
            LEFT JOIN Distrito d ON g.ID_Distrito = d.ID_Distrito
            LEFT JOIN Promotora p ON g.ID_Promotora = p.ID_Promotora
            WHERE g.ID_Usuario = %s
            ORDER BY g.ID_Grupo DESC
        """, (id_usuario,))
        
        grupos = cursor.fetchall()
        return grupos

    except Exception as e:
        st.error(f"❌ Error al obtener grupos: {e}")
        return []

    finally:
        con.close()

def obtener_ciclos_del_grupo(id_grupo: int):
    """
    Obtiene todos los ciclos asociados a un grupo
    """
    con = obtener_conexion()
    if not con:
        return []

    try:
        cursor = con.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                ID_Ciclo,
                numero_ciclo,
                fecha_inicio,
                fecha_cierre,
                duracion_meses,
                CASE 
                    WHEN ID_Estado_ciclo = 1 THEN 'Activo'
                    ELSE 'Inactivo'
                END as estado
            FROM Ciclo
            WHERE ID_Grupo = %s
            ORDER BY numero_ciclo DESC
        """, (id_grupo,))
        
        ciclos = cursor.fetchall()
        return ciclos

    except Exception as e:
        # Si hay error, probablemente porque no existen las columnas nuevas
        return []

    finally:
        con.close()

def obtener_proximo_numero_ciclo(id_grupo: int):
    """
    Obtiene el próximo número de ciclo para un grupo
    """
    con = obtener_conexion()
    if not con:
        return 1

    try:
        cursor = con.cursor()
        cursor.execute("""
            SELECT MAX(numero_ciclo) as ultimo_ciclo
            FROM Ciclo
            WHERE ID_Grupo = %s
        """, (id_grupo,))
        
        resultado = cursor.fetchone()
        ultimo_ciclo = resultado[0] if resultado[0] is not None else 0
        return ultimo_ciclo + 1

    except Exception as e:
        # Si hay error, empezar desde 1
        return 1

    finally:
        con.close()

def crear_nuevo_ciclo(id_grupo: int, numero_ciclo: int, fecha_inicio: date, duracion_meses: int):
    """
    Crea un nuevo ciclo en la base de datos
    """
    con = obtener_conexion()
    if not con:
        return False

    try:
        cursor = con.cursor()
        
        # Calcular fecha de cierre basada en la duración
        fecha_cierre = fecha_inicio + relativedelta(months=duracion_meses)
        
        # Insertar nuevo ciclo con estado Activo (1)
        cursor.execute("""
            INSERT INTO Ciclo 
                (ID_Grupo, numero_ciclo, fecha_inicio, fecha_cierre, duracion_meses, 
                 ID_Estado_ciclo, total_multas_utilizadas, ID_Reglamento, 
                 total_ahorros, total_pago_prestamos)
            VALUES 
                (%s, %s, %s, %s, %s, 1, 0.00, 1, 0.00, 0.00)
        """, (id_grupo, numero_ciclo, fecha_inicio, fecha_cierre, duracion_meses))
        
        con.commit()
        return True

    except Exception as e:
        con.rollback()
        st.error(f"❌ Error al crear nuevo ciclo: {e}")
        return False

    finally:
        con.close()

def pestaña_registrar_grupo():
    """Pestaña 1: Registrar nuevo grupo"""
    st.header("👥 Registrar Nuevo Grupo")

    # 🔐 VALIDACIÓN: debe haber un usuario logueado
    if "id_usuario" not in st.session_state:
        st.error("⚠️ Debes iniciar sesión para registrar un grupo.")
        return

    # 👤 ID del usuario que está creando el grupo
    id_usuario = st.session_state["id_usuario"]

    try:
        con = obtener_conexion()
        if not con:
            st.error("❌ No se pudo conectar a la base de datos.")
            return

        cursor = con.cursor()

        # Obtener distritos
        cursor.execute("SELECT ID_Distrito, nombre FROM Distrito")
        distritos = cursor.fetchall()
        
        # Obtener promotoras
        cursor.execute("SELECT ID_Promotora, nombre FROM Promotora")
        promotoras = cursor.fetchall()

        # 📝 Formulario para registrar grupo
        with st.form("form_grupo"):
            st.subheader("Datos del Grupo")
            
            nombre = st.text_input(
                "Nombre del grupo *", 
                placeholder="Ingrese el nombre del grupo",
                max_chars=100
            )

            # Distritos
            if distritos:
                distrito_options = {f"{d[1]} (ID: {d[0]})": d[0] for d in distritos}
                distrito_sel = st.selectbox("Distrito *", list(distrito_options.keys()))
                ID_Distrito = distrito_options[distrito_sel]
            else:
                st.error("❌ No hay distritos registrados.")
                ID_Distrito = None
            
            # Fecha de inicio
            fecha_inicio = st.date_input(
                "Fecha de inicio *",
                value=datetime.now().date(),
                min_value=date(1990, 1, 1),
                max_value=date(2100, 12, 31)
            )

            # Promotora
            if promotoras:
                promotora_options = {f"{p[1]} (ID: {p[0]})": p[0] for p in promotoras}
                promotora_sel = st.selectbox("Promotora *", list(promotora_options.keys()))
                ID_Promotora = promotora_options[promotora_sel]
            else:
                st.error("❌ No hay promotoras registradas.")
                ID_Promotora = None

            # Estado (1 = Activo, 2 = Inactivo)
            ID_Estado = st.selectbox(
                "Estado",
                options=[1, 2],
                format_func=lambda x: "Activo" if x == 1 else 'Inactivo'
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
                        # 🔥 INSERT: ahora también guarda ID_Usuario automáticamente
                        cursor.execute("""
                            INSERT INTO Grupo 
                                (nombre, ID_Distrito, fecha_inicio, ID_Promotora, ID_Estado, ID_Usuario)
                            VALUES 
                                (%s, %s, %s, %s, %s, %s)
                        """, (nombre, ID_Distrito, fecha_inicio, ID_Promotora, ID_Estado, id_usuario))

                        con.commit()

                        # Obtener el ID_Grupo recién creado
                        cursor.execute("SELECT LAST_INSERT_ID()")
                        id_grupo = cursor.fetchone()[0]

                        st.success("🎉 ¡Grupo registrado con éxito!")
                        st.info(f"**ID del grupo creado:** {id_grupo}")
                        
                        # Mostrar opción para ver en la otra pestaña
                        st.info("📁 **Puedes ver y gestionar este grupo en la pestaña 'Mis Grupos Registrados'**")

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

def mostrar_formulario_nuevo_ciclo(grupo):
    """Muestra el formulario para crear un nuevo ciclo"""
    st.header(f"🔄 Crear Nuevo Ciclo")
    st.subheader(f"Grupo: {grupo['nombre']}")
    
    with st.form(f"form_nuevo_ciclo_{grupo['ID_Grupo']}"):
        # Obtener próximo número de ciclo
        proximo_ciclo = obtener_proximo_numero_ciclo(grupo['ID_Grupo'])
        
        st.info(f"**Número del ciclo:** Ciclo {proximo_ciclo}")
        
        # Fecha de inicio del ciclo
        fecha_inicio = st.date_input(
            "Fecha de inicio del ciclo *",
            value=datetime.now().date(),
            min_value=date(1990, 1, 1),
            max_value=date(2100, 12, 31)
        )
        
        # Duración del ciclo
        duracion = st.selectbox(
            "Duración del ciclo *",
            options=[6, 12],
            format_func=lambda x: f"{x} meses"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            crear_ciclo = st.form_submit_button("✅ Crear Nuevo Ciclo", use_container_width=True)
        
        with col2:
            cancelar = st.form_submit_button("❌ Cancelar", use_container_width=True)
        
        if crear_ciclo:
            # Crear el nuevo ciclo en la base de datos
            if crear_nuevo_ciclo(grupo['ID_Grupo'], proximo_ciclo, fecha_inicio, duracion):
                st.success(f"🎉 ¡Ciclo {proximo_ciclo} creado exitosamente!")
                st.info("📊 **Ya puedes comenzar a registrar datos en este nuevo ciclo**")
                st.session_state.creando_nuevo_ciclo = None
                st.rerun()
        
        if cancelar:
            st.session_state.creando_nuevo_ciclo = None
            st.rerun()

def pestaña_mis_grupos():
    """Pestaña 2: Mostrar grupos registrados (editable) con opción de crear nuevo ciclo"""
    st.header("📋 Mis Grupos Registrados")

    # 🔐 VALIDACIÓN: debe haber un usuario logueado
    if "id_usuario" not in st.session_state:
        st.error("⚠️ Debes iniciar sesión para ver tus grupos.")
        return

    id_usuario = st.session_state["id_usuario"]
    
    # Obtener grupos del usuario
    grupos = obtener_grupos_por_usuario(id_usuario)
    
    if not grupos:
        st.info("ℹ️ No tienes grupos registrados. Crea tu primer grupo en la pestaña 'Registrar Grupo'.")
        return

    # VERIFICAR SI ESTAMOS CREANDO UN NUEVO CICLO - ESTA ES LA PARTE CLAVE
    if st.session_state.creando_nuevo_ciclo is not None:
        grupo_creando_ciclo = next((g for g in grupos if g['ID_Grupo'] == st.session_state.creando_nuevo_ciclo), None)
        if grupo_creando_ciclo:
            mostrar_formulario_nuevo_ciclo(grupo_creando_ciclo)
            return

    # Mostrar cada grupo en una tarjeta editable
    for grupo in grupos:
        with st.container():
            st.subheader(f"🏢 {grupo['nombre']}")
            
            # Información del grupo en columnas
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**📅 Fecha inicio:** {grupo['fecha_inicio']}")
                st.write(f"**📍 Distrito:** {grupo['distrito']}")
            
            with col2:
                st.write(f"**👤 Promotora:** {grupo['promotora']}")
                st.write(f"**📊 Estado:** {grupo['estado']}")
            
            with col3:
                st.write(f"**🔢 ID Grupo:** {grupo['ID_Grupo']}")
            
            # Mostrar ciclos existentes del grupo
            ciclos = obtener_ciclos_del_grupo(grupo['ID_Grupo'])
            if ciclos:
                st.write("**📈 Ciclos del grupo:**")
                for ciclo in ciclos:
                    estado_emoji = "🟢" if ciclo['estado'] == 'Activo' else "🔴"
                    st.write(f"{estado_emoji} Ciclo {ciclo['numero_ciclo']} - {ciclo['duracion_meses']} meses - Inicio: {ciclo['fecha_inicio']}")
            else:
                st.info("ℹ️ Este grupo no tiene ciclos creados aún.")
            
            # Botones de acción
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                # Botón para crear nuevo ciclo - ESTE ES EL QUE DEBE FUNCIONAR
                if st.button(f"🔄 Crear Nuevo Ciclo", key=f"nuevo_ciclo_{grupo['ID_Grupo']}", use_container_width=True):
                    st.session_state.creando_nuevo_ciclo = grupo['ID_Grupo']
                    st.rerun()
            
            with col_btn2:
                # Botón para editar grupo
                if st.button(f"✏️ Editar Grupo", key=f"editar_{grupo['ID_Grupo']}", use_container_width=True):
                    st.session_state.grupo_seleccionado = grupo['ID_Grupo']
                    st.info(f"✏️ Editando grupo: {grupo['nombre']}")

            # Línea separadora
            st.markdown("---")

def mostrar_grupos():
    """Función principal que muestra las dos pestañas"""
    inicializar_session_state()
    
    # Crear pestañas
    tab1, tab2 = st.tabs([
        "📝 Registrar Grupo", 
        "📋 Mis Grupos Registrados"
    ])
    
    with tab1:
        pestaña_registrar_grupo()
    
    with tab2:
        pestaña_mis_grupos()

def obtener_id_grupo_por_usuario(id_usuario: int):
    """
    Devuelve el ID_Grupo asociado a un usuario.
    Si el usuario tiene varios grupos, devuelve el último creado.
    Si no tiene grupos, devuelve None.
    """
    con = obtener_conexion()
    if not con:
        return None

    try:
        cursor = con.cursor(dictionary=True)
        cursor.execute("""
            SELECT ID_Grupo
            FROM Grupo
            WHERE ID_Usuario = %s
            ORDER BY ID_Grupo DESC
            LIMIT 1
        """, (id_usuario,))
        fila = cursor.fetchone()
        return fila["ID_Grupo"] if fila else None

    except Exception:
        return None

    finally:
        con.close()

# Para usar individualmente (si necesitas alguna función específica)
if __name__ == "__main__":
    mostrar_grupos()
