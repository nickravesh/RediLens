from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, APIException
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from .models import RedisMetric
from .serializers import (
    RedisMetricSerializer, KeysSerializer, ValueSerializer,
    MetricsSerializer, StatusSerializer
)
from .utils import get_redis_connection, calculate_derived_metrics
import json

class HistoryMetricViewSet(viewsets.ModelViewSet):
    queryset = RedisMetric.objects.all()
    serializer_class = RedisMetricSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['timestamp']

    def get_queryset(self):
        queryset = super().get_queryset()
        start = self.request.query_params.get('start')
        end = self.request.query_params.get('end')
        if start:
            queryset = queryset.filter(timestamp__gte=start)
        if end:
            queryset = queryset.filter(timestamp__lte=end)
        return queryset

class CurrentMetricViewSet(viewsets.ViewSet):
    def list(self, request):
        try:
            r = get_redis_connection()
            info = r.info()
            derived = calculate_derived_metrics(info)
            data = {'info': info, 'derived': derived}
            serializer = MetricsSerializer(data)
            return Response(serializer.data)
        except APIException as e:
            return Response(e.detail, status=e.status_code)
        except Exception as e:
            return Response({"detail": "Error fetching metrics", "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class KeyViewSet(viewsets.ViewSet):
    def list(self, request):
        cursor = request.query_params.get('cursor', '0')
        count = request.query_params.get('count', 100)
        try:
            r = get_redis_connection()
            next_cursor, keys = r.scan(cursor=cursor, count=count)
            data = {'keys': keys, 'next_cursor': str(next_cursor)}
            serializer = KeysSerializer(data)
            return Response(serializer.data)
        except APIException as e:
            return Response(e.detail, status=e.status_code)
        except Exception as e:
            return Response({"detail": "Error scanning keys", "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ValueViewSet(viewsets.ViewSet):
    def retrieve(self, request, pk=None):
        if not pk:
            raise NotFound({"detail": "Key not provided"})
        try:
            r = get_redis_connection()
            key_type = r.type(pk)
            if key_type == 'none':
                raise NotFound({"detail": "Key not found"})
            ttl = r.ttl(pk)
            value = None
            if key_type == 'string':
                value = r.get(pk)
            elif key_type == 'hash':
                value = r.hgetall(pk)
            elif key_type == 'list':
                value = r.lrange(pk, 0, 99)  # Truncate to first 100
            elif key_type == 'set':
                value = list(r.smembers(pk))[:100]  # Truncate to first 100
            elif key_type == 'zset':
                value = r.zrange(pk, 0, 99, withscores=True)  # Truncate to first 100
            elif key_type == 'stream':
                value = r.xrevrange(pk, '+', '-', count=100)  # Last 100 entries
            else:
                raise APIException({"detail": f"Unsupported type: {key_type}"}, status=status.HTTP_400_BAD_REQUEST)
            data = {'key': pk, 'type': key_type, 'ttl': ttl, 'value': value}
            serializer = ValueSerializer(data)
            return Response(serializer.data)
        except APIException as e:
            return Response(e.detail, status=e.status_code)
        except Exception as e:
            return Response({"detail": "Error fetching value", "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class StatusViewSet(viewsets.ViewSet):
    def list(self, request):
        reachable = True
        last_metric = None
        try:
            get_redis_connection()
            latest = RedisMetric.objects.first()
            if latest:
                last_metric = latest.timestamp
        except APIException:
            reachable = False
        data = {'redis_reachable': reachable, 'last_metric': last_metric}
        serializer = StatusSerializer(data)
        return Response(serializer.data)