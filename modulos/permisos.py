import streamlit as st
from modulos.config.conexion import obtener_conexion

def obtener_permisos_usuario(id_usuario, tipo_usuario, cargo):
    """Obtiene los permisos y filtros específicos para cada usuario"""
    permisos = {
        "puede_ver_todo": False,
        "solo_sus_registros": False,
        "puede_registrar_distritos": False,
        "filtro_grupos": None,
        "filtro_usuario": None
    }
    
    # ADMINISTRADOR - Acceso total
    if cargo.lower() == "administrador" or tipo_usuario.lower() == "administrador":
        permisos["puede_ver_todo"] = True
        permisos["puede_registrar_distritos"] = True
    
    # SECRETARIA - Solo ve sus registros
    elif cargo.lower() == "secretaria" or tipo_usuario.lower() == "secretaria":
        permisos["solo_sus_registros"] = True
        permisos["filtro_usuario"] = id_usuario
    
    # PROMOTORA - Registra distritos y ve grupos asignados
    elif cargo.lower() == "promotora" or tipo_usuario.lower() == "promotora":
        permisos["puede_registrar_distritos"] = True
        permisos["filtro_grupos"] = obtener_grupos_asignados(id_usuario)
    
    return permisos

def obtener_grupos_asignados(id_usuario):
    """Obtiene los IDs de grupos asignados a un usuario promotora"""
    con = obtener_conexion()
    if not con:
        return None
    
    try:
        cursor = con.cursor()
        query = "SELECT ID_Grupo FROM Grupos_Asignados WHERE ID_Usuario = %s"
        cursor.execute(query, (id_usuario,))
        resultados = cursor.fetchall()
        
        # Retornar lista de IDs de grupos
        return [resultado[0] for resultado in resultados] if resultados else []
    
    except Exception as e:
        st.error(f"❌ Error al obtener grupos asignados: {e}")
        return []
    finally:
        con.close()

def aplicar_filtros_usuarios(query_base, permisos, params=None):
    """Aplica filtros según los permisos del usuario"""
    if params is None:
        params = []
    
    query_final = query_base
    params_final = params.copy()
    
    # Si es secretaria, filtrar por su ID de usuario
    if permisos["solo_sus_registros"] and permisos["filtro_usuario"]:
        if "WHERE" in query_base:
            query_final += " AND ID_Usuario_Registro = %s"
        else:
            query_final += " WHERE ID_Usuario_Registro = %s"
        params_final.append(permisos["filtro_usuario"])
    
    # Si es promotora, filtrar por grupos asignados
    elif permisos["filtro_grupos"]:
        if permisos["filtro_grupos"]:  # Si tiene grupos asignados
            placeholders = ",".join(["%s"] * len(permisos["filtro_grupos"]))
            if "WHERE" in query_base:
                query_final += f" AND ID_Grupo IN ({placeholders})"
            else:
                query_final += f" WHERE ID_Grupo IN ({placeholders})"
            params_final.extend(permisos["filtro_grupos"])
    
    # Administrador no necesita filtros adicionales
    
    return query_final, params_final

def verificar_permisos(accion_requerida):
    """
    Verifica si el usuario actual tiene permisos para una acción específica
    
    Args:
        accion_requerida (str): 'ver_todo', 'registrar_distritos', 'ver_sus_registros'
    
    Returns:
        bool: True si tiene permisos, False si no
    """
    if not st.session_state.get("sesion_iniciada", False):
        return False
    
    permisos = st.session_state.get("permisos_usuario", {})
    
    if accion_requerida == "ver_todo":
        return permisos.get("puede_ver_todo", False)
    elif accion_requerida == "registrar_distritos":
        return permisos.get("puede_registrar_distritos", False)
    elif accion_requerida == "ver_sus_registros":
        return permisos.get("solo_sus_registros", False)
    
    return False
