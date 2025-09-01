from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import KeyViewSet, ValueViewSet, StatusViewSet, HistoryMetricViewSet, CurrentMetricViewSet

router = DefaultRouter()
router.register(r'metrics/history', HistoryMetricViewSet, basename='metrics-history')
router.register(r'metrics', CurrentMetricViewSet, basename='metrics')
router.register(r'keys', KeyViewSet, basename='keys')
router.register(r'values', ValueViewSet, basename='values')
router.register(r'status', StatusViewSet, basename='status')

urlpatterns = [
    path('', include(router.urls)),
]