# Docker For Deployment
### Database Deployment

To deploy Proof Buddy database run the following commands. <br>
This should be done from a unix system. <br>
Before running theres commands ensure you have docker and it's dependencies installed.

Create an `.env` with the database configurations.

```
# MariaDB configurations.
MYSQL_DATABASE=proofbuddy_production # whatever name you want
MYSQL_ROOT_PASSWORD=password # choose a strong password
MYSQL_USER=root # can be whatever you want
MYSQL_PASSWORD=password # choose a strong password
```
```
cd database
sudo docker compose up --build -d
```

### Application Deployment
To deploy Proof Buddy create a `.env` file is created with the necessary environment variables.
```
# Database configurations.
DB_NAME=proofbuddy_production # the name you choose for your database
DB_HOST=localhost # where is your database running?
DB_USER=root # can be whatever you want
DB_PASSWORD=password # choose a strong password
DB_PORT=3306 

# Email configurations.
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=email@example.com
EMAIL_HOST_PASSWORD=django_app_password

# Django configurations.
DJANGO_SUPERUSER_PASSWORD=password # choose a strong password
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=email@example.com
DEBUG=False # True when in dev
SECRET_KEY=SOME_SECRET_KEY # use this: https://django-secret-key-generator.netlify.app/
FRONTEND_URL=http://localhost:3000 # the domain name of where the frontend is hosted
BACKEND_URL=http://localhost:8000 # the domain name of where the backend is hosted
```
This is an example change the values to match your configurations.

To deploy Proof Buddy Server run the following commands.
```
sudo docker compose up --build -d
```