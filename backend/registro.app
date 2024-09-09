from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
import mysql.connector
from datetime import datetime

app = Flask(__name__)
bcrypt = Bcrypt(app)

# Configuración de MySQL
db_config = {
    'user': 'tu_usuario',
    'password': 'tu_password',
    'host': 'localhost',
    'database': 'nombre_de_tu_base_de_datos'
}

# Ruta para registrar un nuevo usuario
@app.route('/register', methods=['POST'])
def register():
    data = request.json

    nombres = data.get('nombres')
    apellidos = data.get('apellidos')
    fecha_nacimiento = data.get('fecha_nacimiento')
    password = data.get('password')

    # Validar que todos los campos existan
    if not nombres or not apellidos or not fecha_nacimiento or not password:
        return jsonify({'error': 'Faltan datos'}), 400

    # Cifrar la contraseña
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    # Convertir la fecha de nacimiento a formato datetime
    try:
        fecha_nac = datetime.strptime(fecha_nacimiento, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Formato de fecha incorrecto. Use YYYY-MM-DD.'}), 400

    # Conectar a la base de datos
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # Insertar el nuevo usuario en la base de datos
    try:
        cursor.execute(
            "INSERT INTO usuarios (nombres, apellidos, fecha_nacimiento, password) VALUES (%s, %s, %s, %s)",
            (nombres, apellidos, fecha_nac, hashed_password)
        )
        conn.commit()
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({'error': str(err)}), 500
    finally:
        cursor.close()
        conn.close()

    return jsonify({'message': 'Usuario registrado con éxito'}), 201

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

