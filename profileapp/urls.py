# profileapp/urls.py

from django.urls import path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from .views import ProfileView, ProfileSetupView, ActivityUpdateView

app_urlpatterns = [
    path('setup/', ProfileSetupView.as_view(), name='profile-setup'),
    path('', ProfileView.as_view(), name='profile'),
    path('activity/', ActivityUpdateView.as_view(), name='profile-activity'),
]

schema_view = get_schema_view(
    openapi.Info(
        title='Profile API',
        default_version='v1',
        description='Profile setup and activity endpoints.',
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    patterns=app_urlpatterns,
)

urlpatterns = [
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='profile-swagger-ui'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='profile-swagger-json'),
] + app_urlpatterns