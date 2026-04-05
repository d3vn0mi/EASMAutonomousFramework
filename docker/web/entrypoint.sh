#!/bin/bash
set -e

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput 2>/dev/null || true

echo "Starting Daphne ASGI server..."
exec daphne -b 0.0.0.0 -p 8000 raven.asgi:application
