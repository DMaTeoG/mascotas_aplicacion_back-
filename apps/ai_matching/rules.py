"""
Reglas Claras y Ponderaciones del Motor de Inteligencia Artificial (Matching Engine).
"""
import math

# Ponderación de pesos (debe sumar 1.0)
WEIGHTS = {
    'SPECIES': 0.30,   # Regla dura (si difiere, score = 0)
    'BREED': 0.20,     # Similitud morfológica o de raza
    'COLOR': 0.20,     # Similitud de paleta y patrón
    'SIZE_GENDER': 0.10, # Tamaño relativo y sexo
    'GEO': 0.15,       # Proximidad geográfica (distancia Haversine)
    'TIME': 0.05       # Proximidad temporal
}

# Umbrales Operativos
THRESHOLDS = {
    'HIGH_CONFIDENCE': 80.0,   # Notificación inmediata + Side-by-Side prioritario
    'MEDIUM_CONFIDENCE': 60.0, # Notificación informativa
    'LOW_CONFIDENCE': 40.0     # Umbral de descarte
}

# Familias de colores de pelaje canino / felino
COLOR_GROUPS = {
    'dorado': {'dorado', 'rubio', 'amarillo', 'miel', 'crema', 'arena'},
    'marron': {'marron', 'cafe', 'chocolate', 'canela', 'rojizo'},
    'negro': {'negro', 'azabache', 'oscuro'},
    'blanco': {'blanco', 'marfil', 'nieve'},
    'gris': {'gris', 'plata', 'ceniza', 'humo', 'azul'},
    'atigrado': {'atigrado', 'carey', 'barcino', 'tricolor'}
}

# Escala ordinal de tamaños
SIZE_SCALE = {
    'small': 1,
    'medium': 2,
    'large': 3,
    'extra_large': 4
}

def normalize_text(text: str) -> str:
    if not text:
        return ''
    return text.strip().lower()

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula la distancia ortodrómica en kilómetros entre dos puntos geográficos."""
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return 5.0 # Distancia por defecto neutra si no hay coordenadas
    R = 6371.0 # Radio medio de la Tierra en km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def compute_species_similarity(p1_species: str, p2_species: str) -> float:
    """Regla dura: si la especie no coincide (perro vs gato), anula el score."""
    if normalize_text(p1_species) != normalize_text(p2_species):
        return 0.0
    return 1.0

def compute_breed_similarity(b1: str, b2: str) -> float:
    b1_norm = normalize_text(b1)
    b2_norm = normalize_text(b2)
    if not b1_norm or not b2_norm:
        return 0.6
    if b1_norm == b2_norm:
        return 1.0
    if 'mestizo' in b1_norm or 'criollo' in b1_norm or 'mestizo' in b2_norm or 'criollo' in b2_norm:
        return 0.75 # Flexibilidad ética para animales mestizos
    if b1_norm in b2_norm or b2_norm in b1_norm:
        return 0.85
    return 0.25

def get_color_family(color: str) -> str:
    color_norm = normalize_text(color)
    for family, members in COLOR_GROUPS.items():
        if color_norm in members or any(m in color_norm for m in members):
            return family
    return color_norm

def compute_color_similarity(c1_prim: str, c1_sec: str, c2_prim: str, c2_sec: str, pat1: str, pat2: str) -> float:
    fam1 = get_color_family(c1_prim)
    fam2 = get_color_family(c2_prim)
    
    # Similitud de color primario
    prim_score = 1.0 if fam1 == fam2 else 0.2
    
    # Similitud de color secundario
    sec1 = get_color_family(c1_sec) if c1_sec else None
    sec2 = get_color_family(c2_sec) if c2_sec else None
    sec_score = 0.5
    if sec1 and sec2:
        sec_score = 1.0 if sec1 == sec2 else 0.3
    elif not sec1 and not sec2:
        sec_score = 0.8
        
    # Patrón
    pat_score = 1.0 if normalize_text(pat1) == normalize_text(pat2) else 0.5
    
    return (0.6 * prim_score) + (0.2 * sec_score) + (0.2 * pat_score)

def compute_size_gender_similarity(size1: str, gender1: str, size2: str, gender2: str) -> float:
    s1 = SIZE_SCALE.get(size1, 2)
    s2 = SIZE_SCALE.get(size2, 2)
    diff = abs(s1 - s2)
    size_sim = max(0.0, 1.0 - (0.35 * diff))
    
    # Penalización si el sexo es conocido y es opuesto
    g1 = normalize_text(gender1)
    g2 = normalize_text(gender2)
    gender_mult = 1.0
    if g1 in ['male', 'female'] and g2 in ['male', 'female'] and g1 != g2:
        gender_mult = 0.5
        
    return size_sim * gender_mult

def compute_geo_similarity(lat1, lon1, lat2, lon2, zone1: str, zone2: str) -> tuple[float, float]:
    dist_km = haversine_distance_km(lat1, lon1, lat2, lon2)
    
    # Decaimiento gaussiano para la distancia geográfica
    sigma = 3.5 # km
    geo_score = math.exp(-(dist_km ** 2) / (2.0 * (sigma ** 2)))
    
    # Bonificación si el nombre de zona o barrio coincide textualmente
    z1 = normalize_text(zone1)
    z2 = normalize_text(zone2)
    if z1 and z2 and (z1 in z2 or z2 in z1):
        geo_score = min(1.0, geo_score + 0.2)
        
    return geo_score, dist_km

def compute_time_similarity(date1, date2) -> tuple[float, float]:
    if not date1 or not date2:
        return 0.7, 48.0
    diff_seconds = abs((date1 - date2).total_seconds())
    diff_hours = diff_seconds / 3600.0
    diff_days = diff_hours / 24.0
    
    # Si ocurrió dentro de 7 días, similitud muy alta; luego decae suavemente
    if diff_days <= 3:
        time_score = 1.0
    elif diff_days <= 10:
        time_score = 0.85
    elif diff_days <= 30:
        time_score = 0.6
    else:
        time_score = 0.3
        
    return time_score, diff_hours

# Haversine distance formula
# Breed compatibility matrix
