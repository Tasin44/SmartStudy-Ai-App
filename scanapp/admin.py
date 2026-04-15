from django.contrib import admin
from .models import ScanHistory, AiPersonalization

@admin.register(ScanHistory)
class ScanHistoryAdmin(admin.ModelAdmin):
	list_display = ('id', 'user', 'subject', 'created_at')
	search_fields = ('user__email', 'subject', 'question')
	list_filter = ('subject',)


@admin.register(AiPersonalization)
class AiPersonalizationAdmin(admin.ModelAdmin):
	list_display = (
		'id', 'user', 'model', 'response_sytel',
		'dificulty_level', 'language', 'subject_focus_area', 'created_at'
	)
	search_fields = ('user__email', 'model', 'language', 'subject_focus_area')
	list_filter = ('model', 'language', 'dificulty_level')
