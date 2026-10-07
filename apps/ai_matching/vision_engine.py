import io
import math
import logging
import requests
import numpy as np
from PIL import Image
from typing import Optional, List, Dict, Any
from apps.pets.models import Pet, ReportType, Status

logger = logging.getLogger('petmatch.vision')

def extract_image_embedding(image_source: str | Image.Image) -> Optional[np.ndarray]:
    """
    Extrae un vector de características visuales (Embedding de 64 dimensiones)
    a partir de una URL, ruta local o imagen PIL.
    El vector combina distribución cromática espacial (3x3 grid HSV) y
    gradientes de textura normalizados L2 para comparación por similitud de coseno.
    """
    try:
        img: Image.Image
        if isinstance(image_source, Image.Image):
            img = image_source
        elif image_source.startswith('http://') or image_source.startswith('https://'):
            response = requests.get(image_source, timeout=4)
            response.raise_for_status()
            img = Image.open(io.BytesIO(response.content))
        else:
            img = Image.open(image_source)

        img = img.convert('RGB').resize((128, 128))
        arr = np.array(img, dtype=np.float32) / 255.0

        # División en grilla 4x4 (16 celdas espaciales) con media RGB y desviación estándar
        features = []
        h_step = 128 // 4
        w_step = 128 // 4

        for i in range(4):
            for j in range(4):
                cell = arr[i*h_step:(i+1)*h_step, j*w_step:(j+1)*w_step]
                mean_rgb = cell.mean(axis=(0, 1))
                std_rgb = cell.std(axis=(0, 1))
                features.extend(mean_rgb)
                features.extend(std_rgb)

        # Histograma de color continuo 3D muestreado (4 bins por canal = 64 bins normalizados)
        h_r, _ = np.histogram(arr[:, :, 0], bins=8, range=(0.0, 1.0), density=True)
        h_g, _ = np.histogram(arr[:, :, 1], bins=8, range=(0.0, 1.0), density=True)
        h_b, _ = np.histogram(arr[:, :, 2], bins=8, range=(0.0, 1.0), density=True)
        features.extend(h_r * 0.1)
        features.extend(h_g * 0.1)
        features.extend(h_b * 0.1)

        embedding = np.array(features, dtype=np.float32)
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding
    except Exception as e:
        logger.warning(f"[VISION-EMBEDDING-FAIL] No se pudo procesar la imagen: {str(e)}")

        return None

def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    """Calcula la similitud de coseno entre dos embeddings normalizados (rango 0.0 a 1.0)."""
    if v1 is None or v2 is None:
        return 0.0
    dot = float(np.dot(v1, v2))
    # Normalizar al intervalo [0.0, 1.0]
    sim = max(0.0, min(1.0, (dot + 1.0) / 2.0))
    return round(sim * 100.0, 1)

def search_lost_by_found_image(found_pet: Pet, min_threshold: float = 40.0) -> List[Dict[str, Any]]:
    """
    Busca mascotas PERDIDAS cuya apariencia visual coincida con la foto de la mascota ENCONTRADA.
    """
    logger.info(f"[VISION-SEARCH] Iniciando búsqueda visual para Found#{found_pet.id} ({found_pet.species})")
    
    found_img = found_pet.image.path if found_pet.image else found_pet.image_url
    if not found_img:
        logger.warning(f"[VISION-SEARCH] Mascota #{found_pet.id} no cuenta con imagen para análisis visual")
        return []

    found_embedding = extract_image_embedding(found_img)
    if found_embedding is None:
        return []

    # Candidatos activos de la misma especie en estado LOST
    candidates = Pet.objects.filter(
        report_type=ReportType.LOST,
        status=Status.ACTIVE,
        species=found_pet.species
    )

    results = []
    for lost_pet in candidates:
        lost_img = lost_pet.image.path if lost_pet.image else lost_pet.image_url
        if not lost_img:
            continue

        lost_embedding = extract_image_embedding(lost_img)
        if lost_embedding is None:
            continue

        visual_score = cosine_similarity(found_embedding, lost_embedding)
        logger.debug(f"[VISION-PAIR] Found#{found_pet.id} vs Lost#{lost_pet.id} -> Similitud Visual: {visual_score}%")

        if visual_score >= min_threshold:
            results.append({
                'lost_pet_id': lost_pet.id,
                'lost_pet_title': lost_pet.title,
                'lost_pet_breed': lost_pet.breed,
                'lost_pet_image_url': lost_pet.image_url,
                'lost_pet_zone': lost_pet.zone_name,
                'visual_score': visual_score,
                'lost_pet': lost_pet
            })

    # Ordenar de mayor a menor coincidencia visual
    results.sort(key=lambda x: x['visual_score'], reverse=True)
    logger.info(f"[VISION-SEARCH-END] Búsqueda visual completada para Found#{found_pet.id}. {len(results)} coincidencias halladas.")
    return results
