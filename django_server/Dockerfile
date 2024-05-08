FROM python:latest

WORKDIR /django_server

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["sh", "./entrypoint.sh"]