#!/bin/sh

python manage.py migrate --no-input
python manage.py collectstatic --no-input
python manage.py createsuperuser --no-input

gunicorn django_server.wsgi:application -c gunicorn.conf.py