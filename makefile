# Makefile

.PHONY: up down build logs shell

# Build and start containers
init:
	docker compose -f docker-compose-local.yml up -d --build

# Stop and remove containers
down:
	docker compose down

# make python migrations
makemigrations:
	docker compose run django_server python manage.py makemigrations

# migrate changes to database
migrate:
	docker compose run django_server python manage.py migrate

