import unittest
from app import app

class FlaskAppTestCase(unittest.TestCase):

    def setUp(self):
        # Configuración antes de cada prueba
        self.app = app.test_client()
        self.app.testing = True

    def test_register_user_empty(self):
        # Enviar una solicitud POST con campos vacíos
        response = self.app.post('/register', json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'Todos los campos son requeridos', response.data)

    def test_get_users(self):
        # Probar la obtención de todos los usuarios
        response = self.app.get('/users')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()