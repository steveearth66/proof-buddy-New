#!/bin/sh

python manage.py migrate --no-input
python manage.py collectstatic --no-input
python manage.py createsuperuser --no-input
python manage.py createcachetable --no-input

gunicorn django_server.wsgi:application -c gunicorn.conf.py