

# chatapp/urls.py
 
from django.urls import path
from .views import StartChatView, SendMessageView, ChatHistoryView, ChatSessionListView
 
urlpatterns = [
    path('start/', StartChatView.as_view(), name='chat-start'),
    path('sessions/', ChatSessionListView.as_view(), name='chat-sessions'),
    path('<uuid:session_id>/message/', SendMessageView.as_view(), name='chat-message'),
    path('<uuid:session_id>/messages/', ChatHistoryView.as_view(), name='chat-history'),
]
 














