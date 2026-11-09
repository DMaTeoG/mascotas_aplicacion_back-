#!/usr/bin/env bash
# Exit on error
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

# Asegurar que el Schema de PostgreSQL exista si se comparte base de datos con otro proyecto
python -c "
import os
import psycopg2

db_url = os.getenv('DATABASE_URL')
schema = os.getenv('DB_SCHEMA', 'mascotas')

if db_url and schema:
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(f'CREATE SCHEMA IF NOT EXISTS {schema};')
        cur.close()
        conn.close()
        print(f'✅ Schema [{schema}] verificado o creado con éxito en PostgreSQL.')
    except Exception as e:
        print(f'ℹ️ Nota sobre schema: {e}')
" || true

python manage.py collectstatic --no-input
python manage.py migrate
python manage.py loaddata fixtures/initial_data.json || true
