import streamlit as st
from datetime import datetime, date
from modulos.config.conexion import obtener_conexion


def mostrar_grupos():   # ⭐ Función para registrar grupos
    st.header("👥 Registrar Grupo")

    # Estado para controlar el mensaje de éxito
    if "grupo_registrado" not in st.session_state:
        st.session_state.grupo_registrado = False

    # Si ya se registró un grupo, mostramos mensaje y opción de registrar otro
    if st.session_state.grupo_registrado:
        st.success("🎉 ¡Grupo registrado con éxito!")
        
        if st.button("🆕 Registrar otro grupo"):
            st.session_state.grupo_registrado = False
            st.rerun()
        
        st.info("💡 **Para seguir navegando, selecciona una opción en el menú**")
        return

    # 🔐 VALIDACIÓN: debe haber un usuario logueado
    if "id_usuario" not in st.session_state:
        st.error("⚠️ Debes iniciar sesión para registrar un grupo.")
        return

    # 👤 ID del usuario que está creando el grupo (viene del login)
    id_usuario = st.session_state["id_usuario"]
    
    # 👉 VERIFICAR SI ES USUARIO PROMOTORA
    es_promotora = st.session_state.get("acceso_total_promotora", False)
    cargo_usuario = st.session_state.get("cargo_de_usuario", "")
    
    if es_promotora:
        st.info("🔓 **Modo Promotora**: Tienes acceso completo a todos los grupos")

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


def obtener_id_grupo_por_usuario(id_usuario: int):
    """
    Devuelve el ID_Grupo asociado a un usuario.
    Si el usuario tiene varios grupos, devuelve el último creado.
    Si no tiene grupos, devuelve None.
    """
    # 👉 VERIFICAR SI ES USUARIO PROMOTORA
    es_promotora = st.session_state.get("acceso_total_promotora", False)
    
    if es_promotora:
        # Para promotora, no retornamos un grupo específico (se manejará en otros módulos)
        return "TODOS_LOS_GRUPOS"
    
    # Para otros usuarios, comportamiento normal
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


def obtener_grupos_por_usuario():
    """
    Función auxiliar para obtener grupos según el tipo de usuario
    Útil para usar en otros módulos
    """
    # 👉 VERIFICAR SI ES USUARIO PROMOTORA
    es_promotora = st.session_state.get("acceso_total_promotora", False)
    id_usuario = st.session_state.get("id_usuario")
    
    if not id_usuario:
        return None
    
    con = obtener_conexion()
    if not con:
        return None

    try:
        cursor = con.cursor(dictionary=True)
        
        if es_promotora:
            # Promotora ve TODOS los grupos
            cursor.execute("""
                SELECT ID_Grupo, nombre, fecha_inicio, ID_Estado
                FROM Grupo
                ORDER BY ID_Grupo DESC
            """)
        else:
            # Otros usuarios ven solo sus grupos
            cursor.execute("""
                SELECT ID_Grupo, nombre, fecha_inicio, ID_Estado
                FROM Grupo
                WHERE ID_Usuario = %s
                ORDER BY ID_Grupo DESC
            """, (id_usuario,))
        
        grupos = cursor.fetchall()
        return grupos

    except Exception as e:
        st.error(f"❌ Error al obtener grupos: {e}")
        return None

    finally:
        con.close()
