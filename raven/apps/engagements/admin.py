from django.contrib import admin
from .models import Engagement, EngagementDocument, PreEngagementChecklist, Retest, ScopeItem


class ScopeItemInline(admin.TabularInline):
    model = ScopeItem
    extra = 0


@admin.register(Engagement)
class EngagementAdmin(admin.ModelAdmin):
    list_display = ("engagement_id", "name", "client", "tier", "status", "created_at")
    list_filter = ("tier", "status")
    search_fields = ("engagement_id", "name", "client__name")
    inlines = [ScopeItemInline]


@admin.register(EngagementDocument)
class EngagementDocumentAdmin(admin.ModelAdmin):
    list_display = ("engagement", "doc_type", "version", "created_at")


@admin.register(Retest)
class RetestAdmin(admin.ModelAdmin):
    list_display = ("engagement", "scheduled_date", "status")
