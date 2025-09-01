from django.test import TestCase
from rest_framework.test import APITestCase, APIRequestFactory
from rest_framework import status
from django.core.management import call_command
from django.conf import settings
from .models import RedisMetric
from .views import KeyViewSet, ValueViewSet, MetricViewSet, StatusViewSet
import redis
from datetime import timedelta
from django.utils import timezone

class RedisMonitorTests(APITestCase):
    def setUp(self):
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.redis.flushdb()  # Clear for tests
        self.redis.set('test_string', 'value')
        self.redis.hset('test_hash', mapping={'field': 'val'})
        self.redis.lpush('test_list', 'item1', 'item2')
        self.redis.sadd('test_set', 'member1', 'member2')
        self.redis.zadd('test_zset', {'score1': 1, 'score2': 2})
        # For stream
        self.redis.xadd('test_stream', {'data': 'val'})

    def test_keys_endpoint_scan_pagination(self):
        response = self.client.get('/api/keys/?cursor=0&count=10')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('keys', response.data)
        self.assertIn('next_cursor', response.data)

    def test_values_endpoint_types_strings_hashes_lists_sets_zsets(self):
        for key, typ in [
            ('test_string', 'string'),
            ('test_hash', 'hash'),
            ('test_list', 'list'),
            ('test_set', 'set'),
            ('test_zset', 'zset'),
            ('test_stream', 'stream')
        ]:
            response = self.client.get(f'/api/values/{key}/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['type'], typ)
            self.assertIn('value', response.data)

    def test_metrics_endpoint_info_parsing(self):
        response = self.client.get('/api/metrics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('info', response.data)
        self.assertIn('derived', response.data)
        self.assertIn('hit_rate', response.data['derived'])

    def test_metrics_history_time_range_query(self):
        call_command('collect_metrics')
        start = (timezone.now() - timedelta(days=1)).isoformat()
        end = timezone.now().isoformat()
        response = self.client.get(f'/api/metrics/history/?start={start}&end={end}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)  # Assuming pagination

    def test_redis_unreachable_returns_503(self):
        original_url = settings.REDIS_URL
        settings.REDIS_URL = 'redis://invalid:9999'  # Invalid
        response = self.client.get('/api/metrics/')
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        settings.REDIS_URL = original_url  # Restore