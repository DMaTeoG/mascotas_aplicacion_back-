#!/usr/bin/env bash
# Exit on error
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

# Asegurar que el Schema exista si se conecta a PostgreSQL
python -c "
import os
db_url = os.getenv('DATABASE_URL')
schema = os.getenv('DB_SCHEMA', 'mascotas')

if db_url and schema:
    try:
        import psycopg2
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(f'CREATE SCHEMA IF NOT EXISTS {schema};')
        cur.close()
        conn.close()
        print(f'✅ Schema [{schema}] verificado o creado con éxito en PostgreSQL.')
    except Exception as e:
        print(f'ℹ️ Aviso schema: {e}')
" || true

python manage.py collectstatic --no-input || true
python manage.py migrate --no-input
python manage.py loaddata fixtures/initial_data.json || true
