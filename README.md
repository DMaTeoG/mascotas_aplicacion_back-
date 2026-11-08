# mascotas_aplicacion_back-

Backend RESTful desarrollado en **Python 3.12** y **Django 5.2.6 / Django REST Framework** para la plataforma comunitaria inteligente **Huellitas & Rescate**.

## 🌟 Características Principales

1. **Gestión de Mascotas (`apps.pets`)**:
   - Reportes comunitarios de animales perdidos (`LOST`), encontrados (`FOUND`) y en adopción (`ADOPTION`).
   - Filtros avanzados por especie, tamaño, color, patrón, raza y geolocalización.
   - Flujo de reclamo de propiedad verificado (`PetClaim`) con pruebas privadas y marcas secretas.

2. **Motor de Inteligencia Artificial Explicable (`apps.ai_matching`)**:
   - Algoritmo probabilístico ponderado multivariado (Especie, Raza, Colorimetría, Distancia geográfica con fórmula de Haversine y Delta temporal).
   - Generación de reportes explicables de coincidencia (**XAI**) con desglose porcentual de factores.
   - Motor de Búsqueda Visual por Imagen mediante extracción de vectores y similitud de coseno.

3. **Módulo de Adopciones Responsables (`apps.adoptions`)**:
   - Solicitudes completas de postulación para adopción con validación de entorno y visitas domiciliarias.
   - Flujo de aprobación/rechazo y actualización atómica del estado del animal.

4. **Comunidad y Pistas (`apps.community`)**:
   - Comentarios comunitarios con flags de avistamiento y ubicación georreferenciada.
   - Bandeja de notificaciones y alertas en tiempo real sobre coincidencias del motor IA.

5. **Autenticación y Seguridad (`apps.accounts` & `core`)**:
   - Autenticación mediante tokens **JWT** (JSON Web Tokens) con SimpleJWT.
   - Middleware de registro de peticiones y auditoría.
   - Manejador centralizado de excepciones y CORS configurado.

## 🚀 Requisitos e Instalación

### Opción 1: Entorno Local

```bash
# 1. Crear y activar entorno virtual
python -m venv venv
# En Windows:
.\venv\Scripts\activate
# En Linux/macOS:
source venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Aplicar migraciones
python manage.py migrate

# 4. Cargar datos semilla de contingencia
python manage.py loaddata fixtures/initial_data.json

# 5. Iniciar servidor de desarrollo
python manage.py runserver
```

### Opción 2: Docker

```bash
docker build -t mascotas-back .
docker run -p 8000:8000 mascotas-back
```

## 🧪 Pruebas Unitarias

Para ejecutar la suite completa de pruebas automatizadas:

```bash
python manage.py test
```

## 📄 Licencia

Desarrollado para el proyecto académico de Programación Orientada a la Web.
