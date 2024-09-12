import unittest
from app import app
import os
import sqlite3

class FlaskAppTestCase(unittest.TestCase):

    def setUp(self):
        # Configuración antes de cada prueba
        app.config['TESTING'] = True
        self.app = app.test_client()

        # Establecer modo de prueba con SQLite
        os.environ['FLASK_ENV'] = 'testing'
        with sqlite3.connect('test.db') as connection:
            cursor = connection.cursor()
            # Crear la tabla de usuarios para pruebas
            cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                                id INTEGER PRIMARY KEY,
                                first_name TEXT NOT NULL,
                                last_name TEXT NOT NULL,
                                birth_date TEXT NOT NULL,
                                password TEXT NOT NULL
                             )''')

    def tearDown(self):
        # Eliminar la base de datos SQLite después de cada prueba
        with sqlite3.connect('test.db') as connection:
            cursor = connection.cursor()
            cursor.execute('DROP TABLE IF EXISTS usuarios')

    def test_register_user_success(self):
        # Simular los datos de un usuario para registrar
        user_data = {
            'firstName': 'Juan',
            'lastName': 'Perez',
            'birthDate': '1990-01-01',
            'password': 'securepassword123'
        }
        
        # Enviar una solicitud POST con los datos del usuario
        response = self.app.post('/register', json=user_data)
        
        # Verificar que la respuesta tenga un código de estado 201 (creado con éxito)
        self.assertEqual(response.status_code, 201)
        self.assertIn(b'Usuario registrado exitosamente', response.data)

    def test_register_user_missing_fields(self):
        # Simular datos incompletos para el registro de un usuario
        incomplete_user_data = {
            'firstName': 'Juan',
            'lastName': 'Perez'
            # Falta birthDate y password
        }
        
        # Enviar una solicitud POST con datos incompletos
        response = self.app.post('/register', json=incomplete_user_data)
        
        # Verificar que la respuesta tenga un código de estado 400 (petición incorrecta)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Todos los campos son requeridos', response.data)

if __name__ == '__main__':
    unittest.main()
