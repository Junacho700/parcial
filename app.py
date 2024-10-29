from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import boto3
import time
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)

# Configura CORS
CORS(app)

# Configura la conexión a la base de datos RDS usando variables de entorno
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:3306/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

try:
    with app.app_context():
        db.session.execute(text("SELECT 1"))  # Ejecuta una consulta simple para verificar la conexión
    print("Conexión a la base de datos establecida con éxito.")
except Exception as e:
    print(f"Error al conectar a la base de datos: {e}")

# Configuración de credenciales de AWS para Athena usando variables de entorno
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_SESSION_TOKEN = os.getenv('AWS_SESSION_TOKEN')
REGION_NAME = 'us-east-1'  # Cambia la región si es necesario

# Inicializar el cliente de Athena con credenciales explícitas
athena_client = boto3.client(
    'athena',
    region_name=REGION_NAME,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    aws_session_token=AWS_SESSION_TOKEN
)

# Configuración de Athena
ATHENA_DATABASE = 's3_sakila'
ATHENA_OUTPUT_LOCATION = 's3://ruta-salida-athena/'  # Cambia esto a tu bucket de salida

# Ruta para obtener las películas rentadas por un cliente con el nombre de la película (GET)
@app.route('/get-movies/<int:id_customer>', methods=['GET'])
def get_movies(id_customer):
    # Consulta para obtener el nombre de la película desde fact_venta y film
    query = f"""
        SELECT fv.customer_id, fv.film_id, f.title, fv.rental_date
        FROM fact_rental fv
        JOIN film f ON fv.film_id = f.film_id
        WHERE fv.customer_id = {id_customer}
    """

    try:
        # Ejecutar la consulta en Athena
        response = athena_client.start_query_execution(
            QueryString=query,
            QueryExecutionContext={'Database': ATHENA_DATABASE},
            ResultConfiguration={'OutputLocation': ATHENA_OUTPUT_LOCATION}
        )
        
        # Obtener el ID de ejecución de la consulta
        query_execution_id = response['QueryExecutionId']

        # Esperar a que la consulta se complete
        status = 'RUNNING'
        while status in ['RUNNING', 'QUEUED']:
            response = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
            status = response['QueryExecution']['Status']['State']
            if status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                break
            time.sleep(1)

        if status == 'SUCCEEDED':
            # Obtener los resultados de la consulta
            results = athena_client.get_query_results(QueryExecutionId=query_execution_id)
            ventas = []
            for row in results['ResultSet']['Rows'][1:]:  # Ignorar la primera fila (cabecera)
                customer_id = row['Data'][0]['VarCharValue']
                film_id = row['Data'][1]['VarCharValue']
                title = row['Data'][2]['VarCharValue']
                rental_date = row['Data'][3]['VarCharValue']
                ventas.append({
                    'customer_id': customer_id,
                    'film_id': film_id,
                    'title': title,
                    'rental_date': rental_date,
                })

            return jsonify({
                "status": "success",
                "data": ventas
            })
        else:
            return jsonify({
                "status": "error",
                "message": "La consulta a Athena falló o fue cancelada"
            })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error al obtener datos de ventas: {e}"
        })

# Ruta para añadir una nueva renta en MySQL RDS (POST)
@app.route('/add-rental', methods=['POST'])
def add_rental():
    try:
        # Obtener datos del cuerpo de la solicitud
        rental_data = request.get_json()
        rental_date = rental_data.get('rental_date')
        customer_id = rental_data.get('customer_id')
        film_id = rental_data.get('film_id')

        # Validación básica de datos
        if not all([rental_date, customer_id, film_id]):
            return jsonify({
                "status": "error",
                "message": "Todos los campos son obligatorios (fecha, documento del cliente, película)"
            }), 400

        # Verificar que haya un inventory_id disponible para la película seleccionada
        inventory_query = text("SELECT inventory_id FROM inventory WHERE film_id = :film_id LIMIT 1")
        inventory = db.session.execute(inventory_query, {'film_id': film_id}).fetchone()
        if not inventory:
            return jsonify({
                "status": "error",
                "message": "No hay inventario disponible para esta película."
            }), 400

        inventory_id = inventory[0]

        # Inserción en la tabla rental
        rental_query = text("""
            INSERT INTO rental (rental_date, inventory_id, customer_id, staff_id)
            VALUES (:rental_date, :inventory_id, :customer_id, 1)  -- Asignando staff_id fijo por defecto
        """)
        db.session.execute(rental_query, {
            'rental_date': rental_date,
            'inventory_id': inventory_id,
            'customer_id': customer_id
        })
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Renta añadida con éxito"
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error al añadir la renta: {e}"
        })
        
# Ruta para obtener todas las películas (GET)
@app.route('/movies', methods=['GET'])
def get_all_movies():
    # Consulta SQL para obtener los títulos y IDs de las películas desde la tabla 'film'
    query = "SELECT film_id, title FROM film"

    try:
        movies = db.session.execute(text(query)).fetchall()
        movies_list = [{'film_id': film_id, 'title': title} for film_id, title in movies]

        return jsonify({
            "status": "success",
            "data": movies_list
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error al obtener las películas: {e}"
        })

if __name__ == '__main__':
    app.run(port=5000, host='0.0.0.0', debug=True)