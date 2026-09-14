from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

class AuthJWTTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_data = {
            'username': 'juanperez',
            'email': 'juan@example.com',
            'password': 'Password123*',
            'first_name': 'Juan',
            'last_name': 'Pérez'
        }

    def test_user_registration_success(self):
        response = self.client.post('/api/v1/auth/register/', self.register_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertEqual(response.data['user']['username'], 'juanperez')
        self.assertTrue(User.objects.filter(username='juanperez').exists())

    def test_user_duplicate_email_rejected(self):
        self.client.post('/api/v1/auth/register/', self.register_data, format='json')
        # Intentar registrar otro usuario con el mismo email
        duplicate_data = self.register_data.copy()
        duplicate_data['username'] = 'juan2'
        response = self.client.post('/api/v1/auth/register/', duplicate_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_jwt_login_success(self):
        User.objects.create_user(username='anita', password='SecurePassword123', email='anita@example.com')
        login_data = {
            'username': 'anita',
            'password': 'SecurePassword123'
        }
        response = self.client.post('/api/v1/auth/login/', login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

        # Probar endpoint protegido /me/
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        me_response = self.client.get('/api/v1/auth/me/')
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertEqual(me_response.data['username'], 'anita')
