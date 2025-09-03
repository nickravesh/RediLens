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
    """
    search for keys like:
    http://localhost:8000/api/keys/search/?q=[key-name]
    """
    @action(detail=False, methods=['get'])
    def total(self, request):
        """Return total number of keys in Redis"""
        try:
            r = get_redis_connection()
            total_keys = r.dbsize()
            return Response({"total_keys": total_keys})
        except Exception as e:
            return Response(
                {"detail": "Error getting total keys", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search keys by partial match and return type + ttl"""
        query = request.query_params.get('q', None)
        limit = int(request.query_params.get('count', 100))

        if not query:
            return Response(
                {"detail": "Missing query parameter 'q'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            r = get_redis_connection()
            cursor = 0
            matched_keys = []

            # Keep scanning until done or enough matches
            while True:
                cursor, keys = r.scan(cursor=cursor, match=f"*{query}*", count=limit)
                matched_keys.extend(keys)
                if cursor == 0 or len(matched_keys) >= limit:
                    break

            # Enrich keys with type + ttl
            pipe = r.pipeline()
            for key in matched_keys:
                k = key.decode("utf-8") if isinstance(key, bytes) else key
                pipe.type(k)
                pipe.ttl(k)
            results = pipe.execute()

            key_info = []
            for i, key in enumerate(matched_keys[:limit]):
                key_str = key.decode("utf-8") if isinstance(key, bytes) else key
                ktype = results[i*2].decode("utf-8") if isinstance(results[i*2], bytes) else results[i*2]
                ttl = results[i*2 + 1]
                key_info.append({
                    "name": key_str,
                    "type": ktype,
                    "ttl": ttl
                })

            return Response({"keys": key_info})
        except Exception as e:
            return Response(
                {"detail": "Error searching keys", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    def list(self, request):
        cursor = request.query_params.get('cursor', '0')
        count = int(request.query_params.get('count', 100))
        try:
            r = get_redis_connection()
            next_cursor, keys = r.scan(cursor=cursor, count=count)

            key_info = []

            # Use pipeline to reduce round-trips (faster)
            pipe = r.pipeline()
            for key in keys:
                k = key.decode("utf-8") if isinstance(key, bytes) else key
                pipe.type(k)
                pipe.ttl(k)

            results = pipe.execute()

            for i, key in enumerate(keys):
                key_str = key.decode("utf-8") if isinstance(key, bytes) else key
                ktype = results[i*2].decode("utf-8") if isinstance(results[i*2], bytes) else results[i*2]
                ttl = results[i*2 + 1]  # already int (-1 no expiry, -2 no key)

                key_info.append({
                    "name": key_str,
                    "type": ktype,
                    "ttl": ttl
                })

            data = {
                "keys": key_info,
                "next_cursor": str(next_cursor)
            }
            return Response(data)
        except APIException as e:
            return Response(e.detail, status=e.status_code)
        except Exception as e:
            return Response(
                {"detail": "Error scanning keys", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    
    def create(self, request):
        """
        Create a new Redis key.
        Body:
        {
          "name": "user:123",
          "type": "string" | "hash",
          "value": "some_value" OR { "field": "val" },
          "ttl": 60   # optional, in seconds
        }
        """
        try:
            r = get_redis_connection()
            name = request.data.get("name")
            key_type = request.data.get("type", "string")
            value = request.data.get("value")
            ttl = request.data.get("ttl", None)

            if not name or value is None:
                return Response({"detail": "Both 'name' and 'value' are required"}, status=status.HTTP_400_BAD_REQUEST)

            if key_type == "string":
                r.set(name, value)
            elif key_type == "hash":
                if not isinstance(value, dict):
                    return Response({"detail": "'value' must be a JSON object for hash type"}, status=status.HTTP_400_BAD_REQUEST)
                r.hset(name, mapping=value)
            else:
                return Response({"detail": f"Unsupported type '{key_type}'"}, status=status.HTTP_400_BAD_REQUEST)

            if ttl is not None:
                r.expire(name, int(ttl))

            return Response({"detail": "Key created successfully"}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"detail": "Error creating key", "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def destroy(self, request, pk=None):
        """
        Delete a Redis key by name (pk).
        Example: DELETE /api/keys/user:123
        """
        try:
            r = get_redis_connection()
            deleted = r.delete(pk)
            if deleted == 0:
                return Response({"detail": f"Key '{pk}' not found"}, status=status.HTTP_404_NOT_FOUND)
            return Response({"detail": f"Key '{pk}' deleted successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"detail": "Error deleting key", "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def retrieve(self, request, pk=None):
        """
        Get the value of a Redis key.
        - For string keys: return the string value
        - For hash keys: return the entire hash as a dictionary
        Example: GET /api/keys/user:123
        """
        try:
            r = get_redis_connection()

            if not r.exists(pk):
                return Response({"detail": f"Key '{pk}' not found"}, status=404)

            key_type = r.type(pk).decode("utf-8") if isinstance(r.type(pk), bytes) else r.type(pk)
            ttl = r.ttl(pk)

            if key_type == "string":
                value = r.get(pk)
                if isinstance(value, bytes):
                    value = value.decode("utf-8")
            elif key_type == "hash":
                value = r.hgetall(pk)
                # decode bytes to str
                value = {k.decode("utf-8"): v.decode("utf-8") for k, v in value.items()}
            else:
                value = f"<unsupported key type: {key_type}>"

            return Response({
                "name": pk,
                "type": key_type,
                "ttl": ttl,
                "value": value
            })

        except Exception as e:
            return Response({"detail": "Error retrieving key", "error": str(e)}, status=500)
             
            
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