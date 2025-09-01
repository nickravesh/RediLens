from django.db import models
from django.utils import timezone

class RedisMetric(models.Model):
    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    raw_info = models.JSONField(default=dict)
    memory_used = models.FloatField(null=True)
    ops_per_sec = models.IntegerField(null=True)
    hit_rate = models.FloatField(null=True)
    rejected_connections = models.IntegerField(null=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Metric at {self.timestamp}"