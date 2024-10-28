import unittest
from unittest.mock import patch, MagicMock
from flask import json
from app import app

class TestFlaskApp(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = app.test_client()
        cls.app.testing = True

    @patch('main_app.athena_client.start_query_execution')
    @patch('main_app.athena_client.get_query_execution')
    @patch('main_app.athena_client.get_query_results')
    def test_get_movies_success(self, mock_get_query_results, mock_get_query_execution, mock_start_query_execution):
        # Simular la ejecución de la consulta en Athena
        mock_start_query_execution.return_value = {'QueryExecutionId': '1234'}

        # Simular el estado de ejecución de la consulta como 'SUCCEEDED'
        mock_get_query_execution.return_value = {
            'QueryExecution': {'Status': {'State': 'SUCCEEDED'}}
        }

        # Simular los resultados de la consulta
        mock_get_query_results.return_value = {
            'ResultSet': {
                'Rows': [
                    # Fila de datos simulada
                    {'Data': [{'VarCharValue': '5'}, {'VarCharValue': '1'}, {'VarCharValue': 'Inception'}, {'VarCharValue': '2024-10-24 14:30:00'}]}
                ]
            }
        }

        # Realizar la solicitud GET
        response = self.app.get('/get-movies/5')

        # Verificar que la respuesta sea exitosa y contenga un elemento
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.data)
        self.assertEqual(response_json['status'], 'success')
        self.assertEqual(len(response_json['data']), 1)
        self.assertEqual(response_json['data'][0]['title'], 'Inception')

    @patch('main_app.db.session')
    def test_add_rental_success(self, mock_session):
        # Simular la sesión de la base de datos
        mock_session.execute.return_value = MagicMock(scalar=MagicMock(return_value=1))

        # Datos de prueba para añadir una renta
        rental_data = {
            "rental_date": "2024-10-24 14:30:00",
            "customer_id": 5,
            "film_id": 1
        }

        # Realizar la solicitud POST
        response = self.app.post('/add-rental',
                                 data=json.dumps(rental_data),
                                 content_type='application/json')

        # Verificar que la respuesta sea exitosa
        self.assertEqual(response.status_code, 200)
        response_json = json.loads(response.data)
        self.assertEqual(response_json['status'], 'success')
        self.assertEqual(response_json['message'], 'Renta y registros relacionados añadidos con éxito')
        mock_session.execute.assert_called()
        mock_session.commit.assert_called()

if __name__ == '__main__':
    unittest.main()