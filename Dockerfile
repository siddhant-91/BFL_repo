FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV DJANGO_DEBUG=false
RUN python manage.py collectstatic --noinput
CMD sh -c "python manage.py migrate && python manage.py setup_store && gunicorn bfl.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2"
