from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.pets.models import Pet, ReportType, Species
from apps.community.models import Comment, Notification

class CommunityAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.pet = Pet.objects.create(
            title="Gatita Angora Extraviada",
            report_type=ReportType.LOST,
            species=Species.CAT,
            breed="Angora",
            primary_color="blanco",
            zone_name="Cedritos",
            description="Lleva cascabel plateado"
        )

    def test_create_comment(self):
        data = {
            'pet': self.pet.id,
            'author_name': 'Vecino Juan',
            'content': 'La vi cerca de la panadería de la esquina ayer por la tarde',
            'is_sighting': True,
            'sighting_location': 'Calle 140 con Carrera 12'
        }
        response = self.client.post('/api/v1/community/comments/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['author_name'], 'Vecino Juan')
        self.assertTrue(response.data['is_sighting'])

    def test_list_comments_for_pet(self):
        Comment.objects.create(
            pet=self.pet,
            author_name='Vecina Ana',
            content='Ojalá aparezca pronto'
        )
        response = self.client.get(f'/api/v1/community/comments/?pet_id={self.pet.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['author_name'], 'Vecina Ana')

    def test_notification_creation_and_mark_read(self):
        notif = Notification.objects.create(
            title='Posible Coincidencia',
            message='Se ha detectado una mascota encontrada similar a tu reporte',
            notification_type='MATCH',
            pet=self.pet
        )
        response = self.client.post(f'/api/v1/community/notifications/{notif.id}/mark_read/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)
