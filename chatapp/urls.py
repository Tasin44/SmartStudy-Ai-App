

# chatapp/urls.py

from django.urls import path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from .views import StartChatView, SendMessageView, ChatHistoryView, ChatSessionListView,AskAPIView

app_urlpatterns = [
    path('start/', StartChatView.as_view(), name='chat-start'),
    path('sessions/', ChatSessionListView.as_view(), name='chat-sessions'),
    path('<uuid:session_id>/message/', SendMessageView.as_view(), name='chat-message'),
    path('<uuid:session_id>/messages/', ChatHistoryView.as_view(), name='chat-history'),
    path('ask/', AskAPIView.as_view(), name='chat-ask'),
]

schema_view = get_schema_view(
    openapi.Info(
        title='Chat API',
        default_version='v1',
        description='Chat session and message endpoints.',
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
    patterns=app_urlpatterns,
)

urlpatterns = [
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='chat-swagger-ui'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='chat-swagger-json'),
] + app_urlpatterns
 














