from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from redis_monitor.models import RedisMetric
from redis_monitor.utils import get_redis_connection, calculate_derived_metrics
import time
import json
from datetime import timedelta

class Command(BaseCommand):
    help = 'Collect Redis metrics and prune old data'

    def add_arguments(self, parser):
        parser.add_argument('--loop', action='store_true', help='Run in loop mode for development')

    def handle(self, *args, **options):
        interval = settings.METRICS_COLLECTION_INTERVAL
        retention_days = settings.METRICS_RETENTION_DAYS
        if options['loop']:
            while True:
                self.collect_and_prune(retention_days)
                time.sleep(interval)
        else:
            self.collect_and_prune(retention_days)

    def collect_and_prune(self, retention_days):
        try:
            r = get_redis_connection()
            info = r.info()
            derived = calculate_derived_metrics(info)
            RedisMetric.objects.create(
                raw_info=info,
                memory_used=info.get('used_memory'),
                ops_per_sec=info.get('instantaneous_ops_per_sec'),
                hit_rate=derived['hit_rate'],
                rejected_connections=info.get('rejected_connections')
            )
            # Prune
            cutoff = timezone.now() - timedelta(days=retention_days)
            RedisMetric.objects.filter(timestamp__lt=cutoff).delete()
            self.stdout.write(self.style.SUCCESS('Metrics collected and pruned successfully'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error: {str(e)}'))