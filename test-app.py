import unittest
from app import app

class FlaskAppTestCase(unittest.TestCase):

    def setUp(self):
        # Configuración antes de cada prueba
        self.app = app.test_client()
        self.app.testing = True

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
