from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from apps.pets.models import Pet, ReportType, Species, Size, Gender
from apps.ai_matching.rules import (
    compute_species_similarity,
    compute_breed_similarity,
    compute_color_similarity,
    haversine_distance_km
)
from apps.ai_matching.engine import evaluate_pair, run_matching_for_pet

class AIMatchingRulesTestCase(TestCase):
    def test_species_hard_rule(self):
        """Regla dura: Si la especie no coincide, la similitud es 0.0"""
        self.assertEqual(compute_species_similarity('dog', 'cat'), 0.0)
        self.assertEqual(compute_species_similarity('dog', 'dog'), 1.0)
        self.assertEqual(compute_species_similarity('cat', 'cat'), 1.0)

    def test_breed_similarity(self):
        """Validar similitud de razas y flexibilidad con mestizos"""
        self.assertEqual(compute_breed_similarity('Golden Retriever', 'Golden Retriever'), 1.0)
        self.assertEqual(compute_breed_similarity('Mestizo Criollo', 'Criollo'), 0.75)

    def test_color_family_matching(self):
        """Colores sinónimos (dorado, miel, rubio) deben dar alta similitud"""
        score = compute_color_similarity('dorado', 'blanco', 'miel', 'blanco', 'solido', 'solido')
        self.assertGreaterEqual(score, 0.9)

    def test_haversine_distance(self):
        """Distancia entre dos puntos cercanos debe ser coherente (< 2km)"""
        # Puntos en Bogotá cercanos al Simón Bolívar
        dist = haversine_distance_km(4.6580, -74.0930, 4.6570, -74.0880)
        self.assertLess(dist, 1.5)

    def test_evaluate_pair_high_match(self):
        """Mascotas compatibles deben generar score alto y explicación en lenguaje natural"""
        now = timezone.now()
        lost = Pet.objects.create(
            title="Toby Perdido",
            report_type=ReportType.LOST,
            species=Species.DOG,
            breed="Golden Retriever",
            size=Size.LARGE,
            gender=Gender.MALE,
            primary_color="dorado",
            zone_name="Salitre",
            latitude=4.6580,
            longitude=-74.0930,
            event_date=now - timedelta(hours=10),
            description="Perro perdido"
        )
        found = Pet.objects.create(
            title="Golden Encontrado",
            report_type=ReportType.FOUND,
            species=Species.DOG,
            breed="Golden Retriever",
            size=Size.LARGE,
            gender=Gender.MALE,
            primary_color="dorado",
            zone_name="Salitre",
            latitude=4.6570,
            longitude=-74.0880,
            event_date=now - timedelta(hours=2),
            description="Perro encontrado"
        )

        result = evaluate_pair(lost, found)
        self.assertIsNotNone(result)
        self.assertGreaterEqual(result['score_percent'], 80.0)
        self.assertEqual(result['confidence_level'], 'ALTA')
        self.assertIn("Misma especie", result['explanation'])

    def test_evaluate_pair_null_coordinates(self):
        """Si alguna mascota no tiene coordenadas GPS, el motor no debe lanzar excepción y debe usar zona textual"""
        lost_no_geo = Pet.objects.create(
            title="Gato Perdido sin GPS",
            report_type=ReportType.LOST,
            species=Species.CAT,
            breed="Criollo",
            primary_color="negro",
            zone_name="Chapinero Central",
            latitude=None,
            longitude=None
        )
        found_no_geo = Pet.objects.create(
            title="Gato Encontrado sin GPS",
            report_type=ReportType.FOUND,
            species=Species.CAT,
            breed="Criollo",
            primary_color="negro",
            zone_name="Chapinero Central",
            latitude=None,
            longitude=None
        )
        result = evaluate_pair(lost_no_geo, found_no_geo)
        self.assertIsNotNone(result)
        self.assertGreater(result['score_percent'], 50.0)
        self.assertEqual(result['factors_breakdown']['geo_score'], 0.56)


    def test_dismiss_match_action(self):
        """Verificar descarte de coincidencias para silenciar alertas"""
        from apps.ai_matching.models import MatchResult
        from rest_framework.test import APIClient
        client = APIClient()
        lost = Pet.objects.create(title="P1", report_type=ReportType.LOST, species=Species.DOG, primary_color="blanco")
        found = Pet.objects.create(title="P2", report_type=ReportType.FOUND, species=Species.DOG, primary_color="blanco")
        match = MatchResult.objects.create(
            lost_pet=lost,
            found_pet=found,
            score_percent=85.0,
            confidence_level='ALTA',
            explanation='Match de prueba'
        )
        response = client.post(f'/api/v1/ai/matches/{match.id}/dismiss/')
        self.assertEqual(response.status_code, 200)
        match.refresh_from_db()
        self.assertTrue(match.is_dismissed)

    def test_vision_embedding_extraction(self):
        """Verificar extracción de embeddings y cálculo de similitud de coseno con imágenes sintéticas"""
        from PIL import Image
        from apps.ai_matching.vision_engine import extract_image_embedding, cosine_similarity

        # Crear dos imágenes PIL simples (una roja y otra casi roja)
        img1 = Image.new('RGB', (100, 100), color=(255, 0, 0))
        img2 = Image.new('RGB', (100, 100), color=(240, 10, 10))
        img_blue = Image.new('RGB', (100, 100), color=(0, 0, 255))

        emb1 = extract_image_embedding(img1)
        emb2 = extract_image_embedding(img2)
        emb_blue = extract_image_embedding(img_blue)

        self.assertIsNotNone(emb1)
        self.assertEqual(len(emb1), 120) # 4*4*(3+3) + 24 = 120

        sim_high = cosine_similarity(emb1, emb2)
        sim_low = cosine_similarity(emb1, emb_blue)

        self.assertGreater(sim_high, 90.0)
        self.assertLess(sim_low, 70.0)


    def test_visual_search_endpoint(self):
        """Probar endpoint POST /api/v1/ai/matches/visual-search/"""
        from rest_framework.test import APIClient
        client = APIClient()
        found_dog = Pet.objects.create(
            title="Perro Encontrado",
            report_type=ReportType.FOUND,
            species=Species.DOG,
            primary_color="negro"
        )
        response = client.post('/api/v1/ai/matches/visual-search/', {'found_pet_id': found_dog.id}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.data)



# Additional threshold assertions

# Visual search assertions
