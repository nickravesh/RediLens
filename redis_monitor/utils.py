import redis
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from rest_framework.exceptions import APIException
from rest_framework import status

def get_redis_connection():
    try:
        r = redis.from_url(settings.REDIS_URL, decode_responses=True)
        r.ping()  # Test connection
        return r
    except redis.ConnectionError as e:
        raise APIException(detail={"detail": "Redis unreachable", "error": str(e)}, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

def calculate_derived_metrics(info):
    hits = info.get('keyspace_hits', 0)
    misses = info.get('keyspace_misses', 0)
    total = hits + misses
    hit_rate = hits / total if total > 0 else 0.0
    return {'hit_rate': hit_rate}