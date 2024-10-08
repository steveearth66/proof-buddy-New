#!/bin/sh

set -e  # Exit immediately if a command exits with a non-zero status.

echo "Running database migrations..."
python manage.py migrate --no-input

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Creating cache table..."
python manage.py createcachetable

# Automate superuser creation if required variables are set
if [ "$DJANGO_SUPERUSER_USERNAME" ] && [ "$DJANGO_SUPERUSER_PASSWORD" ] && [ "$DJANGO_SUPERUSER_EMAIL" ]; then
    echo "Creating superuser..."
    python manage.py createsuperuser \
        --no-input \
        --username "$DJANGO_SUPERUSER_USERNAME" \
        --email "$DJANGO_SUPERUSER_EMAIL"
else
    echo "Superuser credentials not provided. Skipping superuser creation."
fi

# Check if the environment is local
if [ "$DJANGO_ENV" = "dev" ]; then
    echo "Running in local environment. Starting Django development server..."
    exec python manage.py runserver 0.0.0.0:8000
else
    echo "Starting Gunicorn server..."
    exec gunicorn django_server.wsgi:application -c gunicorn.conf.py
fi
