from rest_framework import serializers
from .models import RedisMetric

class RedisMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = RedisMetric
        fields = ['timestamp', 'memory_used', 'ops_per_sec', 'hit_rate', 'rejected_connections']

class KeysSerializer(serializers.Serializer):
    keys = serializers.ListField(child=serializers.CharField())
    next_cursor = serializers.CharField()

class ValueSerializer(serializers.Serializer):
    key = serializers.CharField()
    type = serializers.CharField()
    ttl = serializers.IntegerField()
    value = serializers.Field()  # Can be str, dict, list, etc.

class MetricsSerializer(serializers.Serializer):
    info = serializers.DictField()
    derived = serializers.DictField()

class StatusSerializer(serializers.Serializer):
    redis_reachable = serializers.BooleanField()
    last_metric = serializers.DateTimeField(allow_null=True)