from flask import Flask, request, jsonify, CORS
import pymysql

app = Flask(__name__)
CORS(app)

# Configura los datos de conexión a la base de datos MySQL
db_config = {
    'host': 'ip_maquina_base_datos',  # La IP de la máquina donde está MySQL
    'user': 'usuario_flask',          # El usuario que creaste para la base de datos
    'password': 'tu_contraseña_segura',# La contraseña del usuario
    'database': 'nombre_de_tu_base_de_datos',  # El nombre de la base de datos
    'cursorclass': pymysql.cursors.DictCursor
}

# Ruta para recibir el registro de usuarios
@app.route('/register', methods=['POST'])
def register_user():
    # Obtener los datos enviados desde el frontend
    data = request.get_json()
    
    first_name = data.get('firstName')
    last_name = data.get('lastName')
    birth_date = data.get('birthDate')
    password = data.get('password')  # Recuerda que en producción no deberías almacenar contraseñas en texto plano

    # Verificar que los campos no estén vacíos
    if not first_name or not last_name or not birth_date or not password:
        return jsonify({'message': 'Todos los campos son requeridos'}), 400

    # Establecer la conexión con la base de datos
    connection = pymysql.connect(**db_config)

    try:
        with connection.cursor() as cursor:
            # Crear la consulta SQL para insertar el usuario
            sql = """
            INSERT INTO usuarios (first_name, last_name, birth_date, password)
            VALUES (%s, %s, %s, %s)
            """
            # Ejecutar la consulta SQL
            cursor.execute(sql, (first_name, last_name, birth_date, password))
            connection.commit()  # Guardar los cambios

        return jsonify({'message': 'Usuario registrado exitosamente'}), 201

    except Exception as e:
        print(f"Error al registrar el usuario: {e}")
        return jsonify({'message': 'Error al registrar el usuario'}), 500

    finally:
        connection.close()

# Ruta para obtener todos los usuarios registrados
@app.route('/users', methods=['GET'])
def get_users():
    connection = pymysql.connect(**db_config)

    try:
        with connection.cursor() as cursor:
            # Obtener todos los usuarios de la base de datos
            sql = "SELECT first_name, last_name, birth_date FROM usuarios"
            cursor.execute(sql)
            users = cursor.fetchall()

        return jsonify(users), 200

    except Exception as e:
        print(f"Error al obtener usuarios: {e}")
        return jsonify({'message': 'Error al obtener usuarios'}), 500

    finally:
        connection.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
