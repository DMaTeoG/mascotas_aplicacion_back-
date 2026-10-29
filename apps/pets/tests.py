from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from apps.pets.models import Pet, ReportType, Species, Status, PetClaim, ClaimStatus

class PetAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_rescuer = User.objects.create_user(
            username='rescatista_juan',
            email='juan@rescates.org',
            password='Password123!'
        )
        self.user_owner = User.objects.create_user(
            username='dueno_carlos',
            email='carlos@owner.com',
            password='Password123!'
        )
        self.user_stranger = User.objects.create_user(
            username='extrano_pedro',
            email='pedro@otro.com',
            password='Password123!'
        )

        self.pet1 = Pet.objects.create(
            author=self.user_rescuer,
            title="Max Labrador",
            report_type=ReportType.LOST,
            species=Species.DOG,
            breed="Labrador",
            primary_color="negro",
            zone_name="Zona Norte",
            description="Perro amigable"
        )
        self.pet_found = Pet.objects.create(
            author=self.user_rescuer,
            title="Golden Encontrado en el Parque",
            report_type=ReportType.FOUND,
            species=Species.DOG,
            breed="Golden Retriever",
            primary_color="dorado",
            zone_name="Parque Virrey",
            description="Encontrado con collar rojo sin placa"
        )

    def test_list_pets(self):
        response = self.client.get('/api/v1/pets/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_filter_by_report_type(self):
        response = self.client.get('/api/v1/pets/?report_type=LOST')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(all(p['report_type'] == 'LOST' for p in response.data))

    def test_create_pet(self):
        data = {
            'title': 'Gato Siames Encontrado',
            'report_type': 'FOUND',
            'species': 'cat',
            'breed': 'Siames',
            'primary_color': 'crema',
            'zone_name': 'Chapinero',
            'description': 'Encontrado en un tejado'
        }
        response = self.client.post('/api/v1/pets/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Gato Siames Encontrado')

    def test_like_pet(self):
        initial_likes = self.pet1.likes_count
        response = self.client.post(f'/api/v1/pets/{self.pet1.id}/like/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.pet1.refresh_from_db()
        self.assertEqual(self.pet1.likes_count, initial_likes + 1)

    def test_search_pets(self):
        response = self.client.get('/api/v1/pets/?search=labrador')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.pet1.id)

    # --- TESTS DE RECLAMOS DE PROPIEDAD (PetClaim) ---

    def test_create_claim_authenticated(self):
        """Un usuario autenticado puede presentar reclamo con pruebas de propiedad"""
        self.client.force_authenticate(user=self.user_owner)
        data = {
            'pet': self.pet_found.id,
            'proof_description': 'Tiene una cicatriz debajo de la pata izquierda y responde a Toby',
            'proof_image_url': 'https://example.com/foto_antigua_con_toby.jpg'
        }
        response = self.client.post('/api/v1/pets/claims/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], ClaimStatus.PENDING)
        self.assertEqual(response.data['claimant_detail']['username'], 'dueno_carlos')

    def test_create_claim_unauthenticated_fails(self):
        """Reclamar sin estar autenticado retorna 401"""
        data = {
            'pet': self.pet_found.id,
            'proof_description': 'Es mi perro'
        }
        response = self.client.post('/api/v1/pets/claims/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cannot_claim_own_post(self):
        """El mismo usuario que publicó la mascota no puede reclamarla"""
        self.client.force_authenticate(user=self.user_rescuer)
        data = {
            'pet': self.pet_found.id,
            'proof_description': 'Es mi propia mascota'
        }
        response = self.client.post('/api/v1/pets/claims/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_approve_claim_by_rescuer_resolves_pet(self):
        """Al aprobar el reclamo, el estado del reclamo es APPROVED y la mascota pasa a RESOLVED"""
        claim = PetClaim.objects.create(
            pet=self.pet_found,
            claimant=self.user_owner,
            proof_description='Prueba fidedigna'
        )
        self.client.force_authenticate(user=self.user_rescuer)
        response = self.client.post(
            f'/api/v1/pets/claims/{claim.id}/approve/',
            {'notes': 'Identidad verificada, mascota entregada'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        claim.refresh_from_db()
        self.pet_found.refresh_from_db()
        self.assertEqual(claim.status, ClaimStatus.APPROVED)
        self.assertEqual(self.pet_found.status, Status.RESOLVED)

    def test_stranger_cannot_approve_claim(self):
        """Un usuario ajeno no puede aprobar un reclamo sobre la mascota de otro"""
        claim = PetClaim.objects.create(
            pet=self.pet_found,
            claimant=self.user_owner,
            proof_description='Prueba fidedigna'
        )
        self.client.force_authenticate(user=self.user_stranger)
        response = self.client.post(f'/api/v1/pets/claims/{claim.id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_resolved_pet_not_in_active_feed(self):
        """Una mascota resuelta no debe aparecer en el feed por defecto de mascotas activas"""
        self.pet_found.status = Status.RESOLVED
        self.pet_found.save()
        response = self.client.get('/api/v1/pets/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids_in_feed = [p['id'] for p in response.data]
        self.assertNotIn(self.pet_found.id, ids_in_feed)

# Pet claim assertions
