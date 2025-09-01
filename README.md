# RediLens Backend

## Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Set environment variables (e.g., in .env):
   - REDIS_URL: Redis connection URL (e.g., redis://localhost:6379, redis://:password@host:6379, rediss://host:6379 for TLS)
   - DJANGO_SECRET_KEY: Secret key for Django
   - METRICS_COLLECTION_INTERVAL: Seconds between collections (default 30)
   - METRICS_RETENTION_DAYS: Days to retain metrics (default 7)
3. Run migrations: `python manage.py makemigrations && python manage.py migrate`
4. Start server: `python manage.py runserver`
5. Collect metrics:
   - For dev: `python manage.py collect_metrics --loop` (runs periodically)
   - For prod: Schedule `python manage.py collect_metrics` via cron every 30s (or use django-crontab/Celery)

## REDIS_URL Examples
- Local: redis://localhost:6379
- With password: redis://:mypassword@host:6379
- TLS: rediss://host:6379 (for TLS; additional cert options via redis-py if needed)

## Notes
- API is open; add DRF permissions/JWT later.
- Large keys truncated to 100 items; paginate in future.
- SQLite for metrics; suitable for small/medium scale.