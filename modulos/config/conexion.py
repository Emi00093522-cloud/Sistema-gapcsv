import mysql.connector
from mysql.connector import Error

def obtener_conexion():
    try:
        conexion = mysql.connector.connect(
            host='bxdoosqjcoa8senn4bzt-mysql.services.clever-cloud.com',
            user='uew98fb7s6o8aam5',
            password='E9LAVdpxhYFonyDcjRl0',
            database='bxdoosqjcoa8senn4bzt',
            port=3306
        )
        if conexion.is_connected():
            print("✅ Conexión establecida")
            return conexion
        else:
            print("❌ Conexión fallida (is_connected = False)")
            return None
    except mysql.connector.Error as e:
        print(f"❌ Error al conectar: {e}")
        return None

