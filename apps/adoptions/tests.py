from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from apps.pets.models import Pet, ReportType, Species, Size, Gender, Status
from apps.adoptions.models import AdoptionApplication, ApplicationStatus

class AdoptionAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_rescuer = User.objects.create_user(
            username='rescatista_ana',
            email='ana@refugio.org',
            password='Password123!'
        )
        self.user_applicant = User.objects.create_user(
            username='adoptante_juan',
            email='juan@hogar.com',
            password='Password123!'
        )
        self.user_stranger = User.objects.create_user(
            username='otro_usuario',
            email='otro@test.com',
            password='Password123!'
        )

        self.pet_adoption = Pet.objects.create(
            author=self.user_rescuer,
            title="Luna Mestiza en Adopción",
            report_type=ReportType.ADOPTION,
            species=Species.DOG,
            breed="Criollo",
            size=Size.MEDIUM,
            gender=Gender.FEMALE,
            primary_color="caramelo",
            zone_name="Suba",
            description="Perrita rescatada, sociable y esterilizada"
        )
        self.pet_lost = Pet.objects.create(
            author=self.user_rescuer,
            title="Max Perdido",
            report_type=ReportType.LOST,
            species=Species.DOG,
            breed="Labrador",
            primary_color="negro",
            zone_name="Usaquén",
            description="Extraviado recientemente"
        )

    def test_create_adoption_application_success(self):
        self.client.force_authenticate(user=self.user_applicant)
        data = {
            'pet': self.pet_adoption.id,
            'applicant_name': 'Carlos Mendoza',
            'applicant_email': 'carlos.mendoza@example.com',
            'applicant_phone': '+57 300 123 4567',
            'city': 'Bogotá',
            'housing_type': 'Casa con patio cerrado',
            'has_other_pets': True,
            'other_pets_description': 'Un gato de 3 años vacunado',
            'has_children': False,
            'time_dedicated': '4 a 6 horas',
            'experience_description': 'He convivido con perros toda mi vida',
            'agree_to_home_visit': True
        }
        response = self.client.post('/api/v1/adoptions/applications/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['applicant_name'], 'Carlos Mendoza')
        self.assertEqual(response.data['status'], ApplicationStatus.PENDING)

    def test_list_applications_filter_by_pet(self):
        AdoptionApplication.objects.create(
            pet=self.pet_adoption,
            applicant_name='Laura Gómez',
            applicant_email='laura@example.com',
            applicant_phone='3110000000',
            housing_type='Apartamento',
            experience_description='Amante de los animales'
        )
        response = self.client.get(f'/api/v1/adoptions/applications/?pet_id={self.pet_adoption.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['applicant_name'], 'Laura Gómez')

    def test_update_application_status_to_approved_updates_pet(self):
        """Aprobar la solicitud actualiza el estado de la mascota a ADOPTED"""
        app = AdoptionApplication.objects.create(
            pet=self.pet_adoption,
            applicant_user=self.user_applicant,
            applicant_name='Laura Gómez',
            applicant_email='laura@example.com',
            applicant_phone='3110000000',
            housing_type='Apartamento',
            experience_description='Amante de los animales'
        )
        self.client.force_authenticate(user=self.user_rescuer)
        response = self.client.post(
            f'/api/v1/adoptions/applications/{app.id}/update_status/',
            {'status': ApplicationStatus.APPROVED, 'notes': 'Familia ideal para Luna'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        app.refresh_from_db()
        self.pet_adoption.refresh_from_db()
        self.assertEqual(app.status, ApplicationStatus.APPROVED)
        self.assertEqual(self.pet_adoption.status, Status.ADOPTED)

    def test_stranger_cannot_update_application_status(self):
        """Un usuario ajeno no puede aprobar ni rechazar solicitudes"""
        app = AdoptionApplication.objects.create(
            pet=self.pet_adoption,
            applicant_user=self.user_applicant,
            applicant_name='Laura Gómez',
            applicant_email='laura@example.com',
            applicant_phone='3110000000',
            housing_type='Apartamento',
            experience_description='Amante de los animales'
        )
        self.client.force_authenticate(user=self.user_stranger)
        response = self.client.post(
            f'/api/v1/adoptions/applications/{app.id}/update_status/',
            {'status': ApplicationStatus.APPROVED},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_reject_adoption_for_lost_pet(self):
        """Regla de negocio: Rechazar adopción si el animal está marcado como LOST"""
        data = {
            'pet': self.pet_lost.id,
            'applicant_name': 'Mario Duarte',
            'applicant_email': 'mario@example.com',
            'applicant_phone': '3109998877',
            'housing_type': 'Casa',
            'experience_description': 'Deseo adoptar'
        }
        response = self.client.post('/api/v1/adoptions/applications/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('pet', response.data)

# Adoption approval assertion
# E2E workflow assertions
