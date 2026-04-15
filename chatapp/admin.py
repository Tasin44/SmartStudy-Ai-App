from django.contrib import admin
from .models import ChatSession, ChatMessage, AskChatHistory

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
	list_display = ('id', 'user', 'subject', 'title', 'updated_at')
	search_fields = ('user__email', 'subject', 'title')
	list_filter = ('subject',)


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
	list_display = ('id', 'session', 'role', 'created_at')
	search_fields = ('session__user__email', 'content')
	list_filter = ('role',)


@admin.register(AskChatHistory)
class AskChatHistoryAdmin(admin.ModelAdmin):
	list_display = ('id', 'user', 'created_at')
	search_fields = ('user__email', 'prompt', 'ai_response')
