#!/bin/sh
set -e

echo "=== [PetMatch AI Backend Entrypoint] ==="

# Esperar a que PostgreSQL esté disponible si DB_HOST está definido
if [ "$DB_HOST" ]; then
    echo "Esperando conexión con la base de datos en $DB_HOST:${DB_PORT:-5432}..."
    while ! nc -z "$DB_HOST" "${DB_PORT:-5432}"; do
        sleep 1
    done
    echo "Base de datos disponible."
fi

# Aplicar migraciones
echo "Aplicando migraciones de base de datos..."
python manage.py migrate --noinput

# Cargar fixtures iniciales si la base de datos está vacía
echo "Verificando datos iniciales..."
python manage.py loaddata fixtures/initial_data.json || true

# Ejecutar el comando principal (gunicorn o comando pasado por docker)
echo "Iniciando servidor backend..."
exec "$@"
