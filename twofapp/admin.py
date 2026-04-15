from django.contrib import admin
from .models import ParentalControl

@admin.register(ParentalControl)
class ParentalControlAdmin(admin.ModelAdmin):
	list_display = ('id', 'user', 'related_email', 'relation_type', 'created_at')
	search_fields = ('user__email', 'related_email')
	list_filter = ('relation_type',)
