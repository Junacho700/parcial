import pymysql

connection = pymysql.connect(
    host='ip_maquina_base_datos',
    user='usuario_flask',
    password='tu_contraseña_segura',
    database='nombre_de_tu_base_de_datos'
)

# Prueba de conexión
with connection.cursor() as cursor:
    cursor.execute("SELECT DATABASE();")
    result = cursor.fetchone()
    print("Conectado a:", result)