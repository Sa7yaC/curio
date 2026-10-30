#!/bin/sh
set -e

# Apply database migrations
echo "==> Running database migrations..."
python manage.py migrate --noinput

# Collect static files for WhiteNoise
echo "==> Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn server binding to Render's dynamic PORT
PORT="${PORT:-8000}"
echo "==> Starting Gunicorn server on 0.0.0.0:${PORT}..."
exec gunicorn ecommerce_platform.wsgi:application \
    --bind "0.0.0.0:${PORT}" \
    --workers "${GUNICORN_WORKERS:-3}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    --access-logfile - \
    --error-logfile -

