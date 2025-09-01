FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py makemigrations
RUN python manage.py migrate

EXPOSE 8000

# For production: CMD ["gunicorn", "--bind", "0.0.0.0:8000", "redilens.wsgi:application"]
# For dev: 
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]