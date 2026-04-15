from django.contrib import admin
from .models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
	list_display = (
		'id', 'user', 'name', 'problems_solved', 'study_minutes',
		'active_days', 'two_factor_enabled', 'updated_at'
	)
	search_fields = ('user__email', 'name')
	list_filter = ('two_factor_enabled',)
