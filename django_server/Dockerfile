FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
EXPOSE 80
CMD ["gunicorn", "-w", "3", "--bind", "0.0.0.0:80", "django_server.wsgi:application"]