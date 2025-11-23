# 4. Comité de Dirección (SOLO cargos de directiva en orden específico)
st.markdown("#### 4. Comité de Dirección")
try:
    cursor.execute("""
        SELECT m.nombre, m.apellido, r.nombre_rol as cargo
        FROM Miembro m
        INNER JOIN Rol r ON m.ID_Rol = r.ID_Rol
        WHERE m.ID_Grupo = %s
          AND r.nombre_rol IN ('PRESIDENTE', 'SECRETARIA', 'TESORERA', 'ENCARGADA_LLAVE')
        ORDER BY 
            CASE r.nombre_rol
                WHEN 'PRESIDENTE' THEN 1
                WHEN 'SECRETARIA' THEN 2
                WHEN 'TESORERA' THEN 3
                WHEN 'ENCARGADA_LLAVE' THEN 4
                ELSE 5
            END
    """, (reglamento['ID_Grupo'],))
    directiva = cursor.fetchall()
    
    if directiva:
        st.markdown("**Integrantes de la Directiva:**")
        
        # Mostrar en el orden específico
        for cargo_orden in ['PRESIDENTE', 'SECRETARIA', 'TESORERA', 'ENCARGADA_LLAVE']:
            # Buscar si existe este cargo en los resultados
            miembro_cargo = next((m for m in directiva if m['cargo'] == cargo_orden), None)
            
            if miembro_cargo:
                nombre_completo = f"{miembro_cargo['nombre']} {miembro_cargo['apellido']}"
                st.markdown(f"**| {cargo_orden.title()} | {nombre_completo} |**")
            else:
                st.markdown(f"**| {cargo_orden.title()} | (Vacante) |**")
    else:
        st.info("ℹ️ No se han registrado miembros de directiva para este grupo.")
except Exception as e:
    st.error(f"❌ Error al cargar el comité de dirección: {e}")
