from django.contrib import admin
from .models import BreachRecord, EscalationRecord, Finding


@admin.register(Finding)
class FindingAdmin(admin.ModelAdmin):
    list_display = ("title", "severity", "engagement", "remediation_status", "created_at")
    list_filter = ("severity", "remediation_status", "is_false_positive")
    search_fields = ("title", "description")


@admin.register(EscalationRecord)
class EscalationRecordAdmin(admin.ModelAdmin):
    list_display = ("finding", "escalated_by", "method", "acknowledged", "created_at")


@admin.register(BreachRecord)
class BreachRecordAdmin(admin.ModelAdmin):
    list_display = ("breach_name", "email_or_domain", "breach_date", "pwn_count", "is_verified")
    list_filter = ("source", "is_verified")
    search_fields = ("breach_name", "email_or_domain")
