import pymysql

connection = pymysql.connect(
    host='172.31.83.172',
    user='user',
    password='123456789',
    database='bigdata'
)

# Prueba de conexión
with connection.cursor() as cursor:
    cursor.execute("SELECT DATABASE();")
    result = cursor.fetchone()
    print("Conectado a:", result)