from flask import Flask, jsonify, request
import boto3
import mysql.connector
from mysql.connector import Error
from flask_cors import CORS
import time
from dotenv import load_dotenv
import os

# Cargar variables de entorno desde el archivo .env
load_dotenv()

app = Flask(__name__)

# Configura CORS
CORS(app, resources={r"/": {"origins": ""}}, supports_credentials=True)

# Configuración de credenciales de AWS para Athena
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
AWS_SESSION_TOKEN = os.getenv('AWS_SESSION_TOKEN')
REGION_NAME = os.getenv('REGION_NAME')

# Inicializar el cliente de Athena con credenciales explícitas
athena_client = boto3.client(
    'athena',
    region_name=REGION_NAME,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    aws_session_token=AWS_SESSION_TOKEN
)

# Configuración de Athena
ATHENA_DATABASE = 's3-sakila'
ATHENA_OUTPUT_LOCATION = 's3://s3-sakila/'  # Cambia a tu bucket de salida

# Credenciales de la RDS de MySQL
DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

@app.route('/get-movies/<int:id_customer>', methods=['GET'])
def get_movies(id_customer):
    # Consulta para obtener el nombre de la película desde fact_venta y film
    query = f"""
        SELECT fv.customer_id, fv.film_id, f.title, fv.rental_id, fv.store_id, fv.rental_date, fv.date_sales_id, fv.amount
        FROM fact_venta fv
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
                rental_id = row['Data'][3]['VarCharValue']
                store_id = row['Data'][4]['VarCharValue']
                rental_date = row['Data'][5]['VarCharValue']
                date_sales_id = row['Data'][6]['VarCharValue']
                amount = row['Data'][7]['VarCharValue']
                ventas.append({
                    'customer_id': customer_id,
                    'film_id': film_id,
                    'title': title,
                    'rental_id': rental_id,
                    'store_id': store_id,
                    'rental_date': rental_date,
                    'date_sales_id': date_sales_id,
                    'amount': amount
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

if __name__ == '__main__':
    app.run(port=5000, host='0.0.0.0', debug=True)
