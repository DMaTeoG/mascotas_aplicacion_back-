import logging
from typing import Dict, Any, List, Optional
from apps.pets.models import Pet, ReportType, Status
from apps.ai_matching.models import MatchResult
from apps.ai_matching.rules import (
    WEIGHTS, THRESHOLDS,
    compute_species_similarity,
    compute_breed_similarity,
    compute_color_similarity,
    compute_size_gender_similarity,
    compute_geo_similarity,
    compute_time_similarity
)

logger = logging.getLogger('petmatch.ai_matching')


def evaluate_pair(lost_pet: Pet, found_pet: Pet) -> Optional[Dict[str, Any]]:
    """Evalúa la compatibilidad entre una mascota perdida y una encontrada."""
    # 1. Regla dura de especie
    s_species = compute_species_similarity(lost_pet.species, found_pet.species)
    if s_species == 0.0:
        return None  # No hay coincidencia entre especies distintas
        
    # 2. Similitud de Raza / Morfología
    s_breed = compute_breed_similarity(lost_pet.breed, found_pet.breed)
    
    # 3. Similitud de Color y Patrón
    s_color = compute_color_similarity(
        lost_pet.primary_color, lost_pet.secondary_color,
        found_pet.primary_color, found_pet.secondary_color,
        lost_pet.pattern, found_pet.pattern
    )
    
    # 4. Similitud de Tamaño y Sexo
    s_size = compute_size_gender_similarity(
        lost_pet.size, lost_pet.gender,
        found_pet.size, found_pet.gender
    )
    
    # 5. Proximidad Geográfica
    s_geo, dist_km = compute_geo_similarity(
        lost_pet.latitude, lost_pet.longitude,
        found_pet.latitude, found_pet.longitude,
        lost_pet.zone_name, found_pet.zone_name
    )
    
    # 6. Proximidad Temporal
    s_time, diff_hours = compute_time_similarity(lost_pet.event_date, found_pet.event_date)
    
    # Puntuación global ponderada
    total_score = (
        (WEIGHTS['SPECIES'] * s_species) +
        (WEIGHTS['BREED'] * s_breed) +
        (WEIGHTS['COLOR'] * s_color) +
        (WEIGHTS['SIZE_GENDER'] * s_size) +
        (WEIGHTS['GEO'] * s_geo) +
        (WEIGHTS['TIME'] * s_time)
    ) * 100.0
    
    total_score = round(min(100.0, max(0.0, total_score)), 1)
    
    # Nivel de confianza
    if total_score >= THRESHOLDS['HIGH_CONFIDENCE']:
        confidence = 'ALTA'
    elif total_score >= THRESHOLDS['MEDIUM_CONFIDENCE']:
        confidence = 'MEDIA'
    else:
        confidence = 'BAJA'
        
    # Construcción de la Explicación en Lenguaje Natural (XAI)
    motivos = []
    motivos.append(f"Misma especie ({lost_pet.get_species_display()})")
    
    if s_color >= 0.7:
        motivos.append(f"color muy coincidente ({lost_pet.primary_color})")
    if s_breed >= 0.75:
        motivos.append(f"raza/tipo compatible ({lost_pet.breed})")
    if s_geo >= 0.7:
        motivos.append(f"hallado a aprox. {dist_km:.1f} km de la zona de extravío")
    if s_time >= 0.8:
        motivos.append("concordancia cercana de fechas")
        
    explicacion = (
        f"{total_score}% de probabilidad de coincidencia ({confidence}): " +
        ", ".join(motivos) + "."
    )
    
    breakdown = {
        'species_score': s_species,
        'breed_score': round(s_breed, 2),
        'color_score': round(s_color, 2),
        'size_gender_score': round(s_size, 2),
        'geo_score': round(s_geo, 2),
        'distance_km': round(dist_km, 2),
        'time_score': round(s_time, 2),
        'diff_hours': round(diff_hours, 1)
    }
    
    return {
        'lost_pet': lost_pet,
        'found_pet': found_pet,
        'score_percent': total_score,
        'confidence_level': confidence,
        'explanation': explicacion,
        'factors_breakdown': breakdown
    }

def run_matching_for_pet(pet: Pet, min_threshold: float = 40.0) -> List[MatchResult]:
    """Ejecuta el motor de coincidencia para una mascota recién creada o actualizada."""
    results = []
    logger.info(f"[AI-RUN] Iniciando evaluación para Mascota #{pet.id} ({pet.report_type} - {pet.species} - '{pet.title}')")

    if pet.report_type == ReportType.LOST:
        candidates = Pet.objects.filter(
            report_type=ReportType.FOUND,
            status=Status.ACTIVE,
            species=pet.species
        )
        logger.debug(f"[AI-RUN] Encontrados {candidates.count()} candidatos FOUND compatibles por especie ({pet.species})")
        for found_pet in candidates:
            try:
                eval_data = evaluate_pair(pet, found_pet)
                if eval_data:
                    logger.debug(f"[AI-PAIR] Lost#{pet.id} vs Found#{found_pet.id} -> Score: {eval_data['score_percent']}% ({eval_data['confidence_level']})")
                    if eval_data['score_percent'] >= min_threshold:
                        match_obj, created = MatchResult.objects.update_or_create(
                            lost_pet=pet,
                            found_pet=found_pet,
                            defaults={
                                'score_percent': eval_data['score_percent'],
                                'confidence_level': eval_data['confidence_level'],
                                'explanation': eval_data['explanation'],
                                'factors_breakdown': eval_data['factors_breakdown'],
                            }
                        )
                        results.append(match_obj)
                        logger.info(f"[AI-MATCH] {'Nuevo' if created else 'Actualizado'} match #{match_obj.id}: Lost#{pet.id} <-> Found#{found_pet.id} con {eval_data['score_percent']}%")
            except Exception as e:
                logger.error(f"[AI-ERROR] Error evaluando pareja Lost#{pet.id} vs Found#{found_pet.id}: {str(e)}", exc_info=True)

    elif pet.report_type == ReportType.FOUND:
        candidates = Pet.objects.filter(
            report_type=ReportType.LOST,
            status=Status.ACTIVE,
            species=pet.species
        )
        logger.debug(f"[AI-RUN] Encontrados {candidates.count()} candidatos LOST compatibles por especie ({pet.species})")
        for lost_pet in candidates:
            try:
                eval_data = evaluate_pair(lost_pet, pet)
                if eval_data:
                    logger.debug(f"[AI-PAIR] Lost#{lost_pet.id} vs Found#{pet.id} -> Score: {eval_data['score_percent']}% ({eval_data['confidence_level']})")
                    if eval_data['score_percent'] >= min_threshold:
                        match_obj, created = MatchResult.objects.update_or_create(
                            lost_pet=lost_pet,
                            found_pet=pet,
                            defaults={
                                'score_percent': eval_data['score_percent'],
                                'confidence_level': eval_data['confidence_level'],
                                'explanation': eval_data['explanation'],
                                'factors_breakdown': eval_data['factors_breakdown'],
                            }
                        )
                        results.append(match_obj)
                        logger.info(f"[AI-MATCH] {'Nuevo' if created else 'Actualizado'} match #{match_obj.id}: Lost#{lost_pet.id} <-> Found#{pet.id} con {eval_data['score_percent']}%")
            except Exception as e:
                logger.error(f"[AI-ERROR] Error evaluando pareja Lost#{lost_pet.id} vs Found#{pet.id}: {str(e)}", exc_info=True)
                
    logger.info(f"[AI-END] Evaluación completada para Mascota #{pet.id}. {len(results)} matches generados >= {min_threshold}%.")
    return results

def run_global_matching(min_threshold: float = 50.0) -> int:
    """Evalúa todas las mascotas perdidas contra todas las encontradas."""
    logger.info("[AI-GLOBAL] Iniciando recálculo global de coincidencias en la base de datos.")
    lost_pets = Pet.objects.filter(report_type=ReportType.LOST, status=Status.ACTIVE)
    found_pets = Pet.objects.filter(report_type=ReportType.FOUND, status=Status.ACTIVE)
    count = 0
    for l_pet in lost_pets:
        for f_pet in found_pets:
            try:
                eval_data = evaluate_pair(l_pet, f_pet)
                if eval_data and eval_data['score_percent'] >= min_threshold:
                    match_obj, created = MatchResult.objects.update_or_create(
                        lost_pet=l_pet,
                        found_pet=f_pet,
                        defaults={
                            'score_percent': eval_data['score_percent'],
                            'confidence_level': eval_data['confidence_level'],
                            'explanation': eval_data['explanation'],
                            'factors_breakdown': eval_data['factors_breakdown'],
                        }
                    )
                    count += 1
            except Exception as e:
                logger.error(f"[AI-GLOBAL-ERROR] Error en Lost#{l_pet.id} vs Found#{f_pet.id}: {str(e)}", exc_info=True)
                
    logger.info(f"[AI-GLOBAL-END] Recálculo global completado. Total coincidencias activas: {count}.")
    return count


# XAI natural language summary
# Factors breakdown payload
# Query optimization
