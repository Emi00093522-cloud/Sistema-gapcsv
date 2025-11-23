import streamlit as st
from modulos.config.conexion import obtener_conexion
from modulos.permisos import aplicar_filtros_usuarios

# CONSULTAS PARA GRUPOS
def obtener_grupos():
    """Obtiene todos los grupos con filtros según permisos"""
    if not st.session_state.get("sesion_iniciada", False):
        return []
    
    permisos = st.session_state.get("permisos_usuario", {})
    
    query = """
        SELECT g.*, d.Nombre as Distrito, u.Usuario as Responsable
        FROM Grupos g
        LEFT JOIN Distritos d ON g.ID_Distrito = d.ID_Distrito
        LEFT JOIN Usuario u ON g.ID_Usuario_Responsable = u.ID_Usuario
    """
    
    query_filtrada, params = aplicar_filtros_usuarios(query, permisos)
    query_filtrada += " ORDER BY g.Nombre_Grupo"
    
    con = obtener_conexion()
    if not con:
        return []
    
    try:
        cursor = con.cursor(dictionary=True)
        cursor.execute(query_filtrada, params)
        return cursor.fetchall()
    except Exception as e:
        st.error(f"❌ Error al obtener grupos: {e}")
        return []
    finally:
        con.close()

# CONSULTAS PARA REGISTROS/ACTIVIDADES
def obtener_registros_actividades():
    """Obtiene registros de actividades con filtros según permisos"""
    if not st.session_state.get("sesion_iniciada", False):
        return []
    
    permisos = st.session_state.get("permisos_usuario", {})
    
    query = """
        SELECT ra.*, u.Usuario as Registrado_Por, g.Nombre_Grupo
        FROM Registros_Actividades ra
        LEFT JOIN Usuario u ON ra.ID_Usuario_Registro = u.ID_Usuario
        LEFT JOIN Grupos g ON ra.ID_Grupo = g.ID_Grupo
    """
    
    query_filtrada, params = aplicar_filtros_usuarios(query, permisos)
    query_filtrada += " ORDER BY ra.Fecha_Registro DESC"
    
    con = obtener_conexion()
    if not con:
        return []
    
    try:
        cursor = con.cursor(dictionary=True)
        cursor.execute(query_filtrada, params)
        return cursor.fetchall()
    except Exception as e:
        st.error(f"❌ Error al obtener registros: {e}")
        return []
    finally:
        con.close()

# CONSULTAS PARA DISTRITOS
def obtener_distritos():
    """Obtiene todos los distritos (todos los usuarios pueden ver)"""
    query = "SELECT * FROM Distritos ORDER BY Nombre"
    
    con = obtener_conexion()
    if not con:
        return []
    
    try:
        cursor = con.cursor(dictionary=True)
        cursor.execute(query)
        return cursor.fetchall()
    except Exception as e:
        st.error(f"❌ Error al obtener distritos: {e}")
        return []
    finally:
        con.close()

# CONSULTAS PARA MIEMBROS
def obtener_miembros():
    """Obtiene miembros con filtros según permisos"""
    if not st.session_state.get("sesion_iniciada", False):
        return []
    
    permisos = st.session_state.get("permisos_usuario", {})
    
    query = """
        SELECT m.*, g.Nombre_Grupo, u.Usuario as Registrado_Por
        FROM Miembros m
        LEFT JOIN Grupos g ON m.ID_Grupo = g.ID_Grupo
        LEFT JOIN Usuario u ON m.ID_Usuario_Registro = u.ID_Usuario
    """
    
    query_filtrada, params = aplicar_filtros_usuarios(query, permisos)
    query_filtrada += " ORDER BY m.Nombre"
    
    con = obtener_conexion()
    if not con:
        return []
    
    try:
        cursor = con.cursor(dictionary=True)
        cursor.execute(query_filtrada, params)
        return cursor.fetchall()
    except Exception as e:
        st.error(f"❌ Error al obtener miembros: {e}")
        return []
    finally:
        con.close()

# CONSULTAS PARA AHORROS
def obtener_ahorros():
    """Obtiene registros de ahorros con filtros según permisos"""
    if not st.session_state.get("sesion_iniciada", False):
        return []
    
    permisos = st.session_state.get("permisos_usuario", {})
    
    query = """
        SELECT a.*, m.Nombre as Miembro, g.Nombre_Grupo, u.Usuario as Registrado_Por
        FROM Ahorros a
        LEFT JOIN Miembros m ON a.ID_Miembro = m.ID_Miembro
        LEFT JOIN Grupos g ON m.ID_Grupo = g.ID_Grupo
        LEFT JOIN Usuario u ON a.ID_Usuario_Registro = u.ID_Usuario
    """
    
    query_filtrada, params = aplicar_filtros_usuarios(query, permisos)
    query_filtrada += " ORDER BY a.Fecha_Registro DESC"
    
    con = obtener_conexion()
    if not con:
        return []
    
    try:
        cursor = con.cursor(dictionary=True)
        cursor.execute(query_filtrada, params)
        return cursor.fetchall()
    except Exception as e:
        st.error(f"❌ Error al obtener ahorros: {e}")
        return []
    finally:
        con.close()
