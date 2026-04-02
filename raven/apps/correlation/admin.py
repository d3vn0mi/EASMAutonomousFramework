from django.contrib import admin
from .models import CorrelationResult


@admin.register(CorrelationResult)
class CorrelationResultAdmin(admin.ModelAdmin):
    list_display = ("engagement", "engine_used", "confidence_score", "created_at")
    list_filter = ("engine_used",)
