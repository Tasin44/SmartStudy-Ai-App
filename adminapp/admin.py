from django.contrib import admin

from .models import TermsConditionSection


@admin.register(TermsConditionSection)
class TermsConditionSectionAdmin(admin.ModelAdmin):
    list_display = ("section_name", "order", "created_by", "created_at")
    search_fields = ("section_name", "description")
    ordering = ("order", "created_at")
