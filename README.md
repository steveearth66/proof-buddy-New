# Proof Buddy

A web application for verifying mathematical proofs using Truth-Functional Logic (TFL) and First Order Logic (FOL), currently utilized by professors and students in courses at Drexel University.

## Prerequisites

Ensure you have the following installed before attempting to build or run.

- [NodeJS](https://nodejs.org/en/download/)
- [Python](https://www.python.org/downloads/release/python-3122/)
- [Docker](https://www.docker.com/products/docker-desktop/)

## Building

Build the static assets (`.html`, `.css`, `.js`, etc.) of Proof Buddy.

### Frontend

The `client/` directory contains the frontend of Proof Buddy. It is written in JavaScript using React and managed with [create-react-app](https://create-react-app.dev/). With a recent version of NodeJS installed, run

```bash
cd client
npm install
```

to install the dependencies of the frontend. Then run

```bash
npm run build
```

to build the application into `dist/` at the root of the project. The `dist/` directory now contains assets that can served by a web server.

Alternatively, if you are currently working on the frontend, you may want to use `npm run watch`. This will watch for changes made to the frontend code, and rebuild the project into `dist/`.

### Backend

The `django_server/` directory contains the backend of Proof Buddy. It is written in Python using Django. With a recent version of Python installed, run

```bash
cd ../django_server
python -m pip install -r requirements.txt
```

to install the dependencies of the backend. The Django project has a few static files that should be served along with the React app. Run

```bash
python manage.py collectstatic
```

to collect these static assets into `dist/`.

## Environment Variables

To use Proof Buddy, you will need to set some environment variables. Create `.env` file inside `django_server/` with the following contents.

```ini
DEBUG=true
SECRET_KEY=
EMAIL_HOST=
EMAIL_PORT=
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
PUBLIC_URL=http://localhost:8000
```

The [secret key](https://docs.djangoproject.com/en/5.0/ref/settings/#secret-key) can be anything, but it should be secret. [This site](http://www.unit-conversion.info/texttools/random-string-generator/) might be useful for generating one. For help setting the `EMAIL_` variables see [EMAIL.md](docs/EMAIL.md).

## Database

You need a database to use Proof Buddy. If you don't already have one, create one by running

```bash
python manage.py migrate
python manage.py createcachetable
```

This will create a database at `django_server/db.sqlite3`. You should also create a superuser account to be able to use the website.

```bash
python manage.py createsuperuser
```

You may set the username, email, and password of this account to whatever you would like.

## Running

Once you have the static assets built into `dist/` and have created the `.env` and `db.sqlite3` files, you can start the project using Docker Compose.

```bash
cd ..
docker-compose up --build
```

In a web browser, visit <http://localhost:8000> to use Proof Buddy.

## Deploying

Running Proof Buddy in a production environment is about the same as running it locally. Just make sure you update the `DEBUG` and `PUBLIC_URL` of the .env file before running. For example if you were using [EC2](https://aws.amazon.com/ec2/), it might looks something like this:

```ini
DEBUG=false
PUBLIC_URL=http://ec2-3-16-213-196.us-east-2.compute.amazonaws.com
```

You also probably want to change the `ports` of the `nginx` service in `compose.yaml` to `80:80` so users can access your site in a web browser without specifying the port.

Now you can run

```bash
docker-compose up -d --build
```

which will start it in a detached state. You can look at the logs by running

```bash
docker-compose logs -f
```

Or stop the server by running

```bash
docker-compose down
```
