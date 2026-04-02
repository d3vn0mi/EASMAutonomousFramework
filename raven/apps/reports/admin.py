from django.contrib import admin
from .models import Report


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("engagement", "report_type", "status", "generated_at", "approved_by")
    list_filter = ("report_type", "status")
