#!/bin/bash
set -e

echo "Starting Celery Worker..."
echo "Waiting for PostgreSQL to be ready..."

# Aguardar PostgreSQL estar disponível
MAX_ATTEMPTS=60
ATTEMPT=0
while ! pg_isready -h postgres -p 5432 -U niochat_user -d niochat > /dev/null 2>&1; do
  ATTEMPT=$((ATTEMPT + 1))
  if [ $ATTEMPT -ge $MAX_ATTEMPTS ]; then
    echo "PostgreSQL failed to start after $MAX_ATTEMPTS attempts. Exiting."
    exit 1
  fi
  echo "PostgreSQL is unavailable - sleeping... (attempt $ATTEMPT/$MAX_ATTEMPTS)"
  sleep 5
done

echo "PostgreSQL is ready!"
echo "Starting Celery Worker with optimized settings..."

cd /app/backend
echo "Current directory: $(pwd)"
echo "Python path: $(which python)"
echo "Starting Celery worker (same as local)..."

# Executar apenas o Celery, sem criar superuser
exec python -m celery -A niochat worker -l info
