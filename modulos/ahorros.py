def obtener_prestamos_grupo():
    """
    Función para el módulo de cierre de ciclo
    Retorna todos los pagos de préstamos del grupo actual para consolidar en el cierre
    """
    try:
        # Tu código para conectar a la base de datos
        con = obtener_conexion()
        cursor = con.cursor()
        
        # Obtener el ID del grupo actual
        if 'reunion_actual' not in st.session_state:
            return []
        
        id_grupo = st.session_state.reunion_actual['id_grupo']
        
        # Consulta para obtener todos los pagos de préstamos del grupo
        cursor.execute("""
            SELECT 
                pp.ID_PagoPrestamo,
                pp.ID_Miembro,
                pp.monto,
                pp.fecha,
                pp.descripcion
            FROM PagoPrestamo pp
            JOIN Miembro m ON pp.ID_Miembro = m.ID_Miembro
            WHERE m.ID_Grupo = %s
            ORDER BY pp.fecha
        """, (id_grupo,))
        
        prestamos_data = cursor.fetchall()
        
        # Convertir a lista de diccionarios
        resultado = []
        for prestamo in prestamos_data:
            resultado.append({
                'id_pago_prestamo': prestamo[0],
                'id_miembro': prestamo[1],
                'monto': float(prestamo[2]),
                'fecha': prestamo[3],
                'descripcion': prestamo[4]
            })
        
        return resultado
        
    except Exception as e:
        st.error(f"❌ Error en obtener_prestamos_grupo: {e}")
        return []

def obtener_total_prestamos_ciclo():
    """
    Retorna la suma total de todos los pagos de préstamos del grupo
    """
    try:
        prestamos_data = obtener_prestamos_grupo()
        
        if not prestamos_data:
            return 0.00
        
        total_prestamos = sum(item['monto'] for item in prestamos_data)
        return total_prestamos
        
    except Exception as e:
        st.error(f"❌ Error calculando total de préstamos: {e}")
        return 0.00
