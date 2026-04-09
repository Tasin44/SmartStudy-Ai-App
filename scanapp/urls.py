

from django.urls import path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from .views import ScanView, ScanHistoryView

app_urlpatterns = [
    path('', ScanView.as_view(), name='scan'),
    path('history/', ScanHistoryView.as_view(), name='scan-history'),
]

schema_view = get_schema_view(
    openapi.Info(
        title='Scan API',
        default_version='v1',
        description='Scan and scan history endpoints.',
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    patterns=app_urlpatterns,
)

urlpatterns = [
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='scan-swagger-ui'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='scan-swagger-json'),
] + app_urlpatterns

















