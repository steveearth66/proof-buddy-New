# Docker For Deployment
### Client Deployment

To deploy Proof Buddy client run the following commands.
This should be done from a unix system.
Before running theres commands ensure you have docker and it's dependencies installed.
```
cd client
sudo docker compose up --build -d
```

### Server Deployment
In order to deploy Proof Buddy Server a few things must be in place first.
```
cd django_server
```
1. Ensure a .env file is created with the necessary environment variables.
```
# Database configurations.
DB_NAME=proofbuddy_development
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=password
DB_PORT=3306

# Email configurations.
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=email@example.com
EMAIL_HOST_PASSWORD=django_app_password

# Django configurations.
DJANGO_SUPERUSER_PASSWORD=password
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=email@example.com
DEBUG=True
SECRET_KEY=SOME_SECRET_KEY
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
```
This is an example change the values to match your configurations.
2. Ensure a .db.env file is created with the necessary environment variables.
```
MYSQL_DATABASE=proofbuddy_production
MYSQL_USER=root
MYSQL_PASSWORD=password
MYSQL_ROOT_PASSWORD=password
```
This is an example change the values to match your configurations.

To deploy Proof Buddy Server run the following commands.
```
sudo docker compose up --build -d
```