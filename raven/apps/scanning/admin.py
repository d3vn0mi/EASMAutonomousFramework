from django.contrib import admin
from .models import DiscoveredAsset, Scan, ToolExecution


@admin.register(Scan)
class ScanAdmin(admin.ModelAdmin):
    list_display = ("id", "engagement", "phase", "status", "progress", "created_at")
    list_filter = ("status", "phase")


@admin.register(ToolExecution)
class ToolExecutionAdmin(admin.ModelAdmin):
    list_display = ("tool_name", "target", "status", "started_at", "completed_at")
    list_filter = ("tool_name", "status")


@admin.register(DiscoveredAsset)
class DiscoveredAssetAdmin(admin.ModelAdmin):
    list_display = ("asset_type", "value", "source_tool", "engagement")
    list_filter = ("asset_type", "source_tool")
