FROM python:latest

WORKDIR /django_server

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /var/log/gunicorn.access.log

RUN mkdir -p /var/log/gunicorn.error.log

EXPOSE 8000

CMD ["sh", "./entrypoint.sh"]