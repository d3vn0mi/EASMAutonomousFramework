from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from core.mixins import TimestampMixin


class Scan(TimestampMixin):
    class Phase(models.TextChoices):
        DISCOVERY = "discovery", _("Phase 1 - Discovery")
        ENUMERATION = "enumeration", _("Phase 2 - Enumeration")
        VULN_ASSESS = "vuln_assess", _("Phase 3 - Vulnerability Assessment")

    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        RUNNING = "running", _("Running")
        COMPLETED = "completed", _("Completed")
        FAILED = "failed", _("Failed")
        CANCELLED = "cancelled", _("Cancelled")

    engagement = models.ForeignKey(
        "engagements.Engagement", related_name="scans", on_delete=models.CASCADE,
    )
    phase = models.CharField(max_length=20, choices=Phase.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    started_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    celery_task_id = models.CharField(max_length=255, blank=True)
    progress = models.PositiveIntegerField(default=0)
    error_log = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Scan")
        verbose_name_plural = _("Scans")

    def __str__(self):
        return f"Scan {self.pk} - {self.get_phase_display()} ({self.get_status_display()})"


class ToolExecution(TimestampMixin):
    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        RUNNING = "running", _("Running")
        COMPLETED = "completed", _("Completed")
        FAILED = "failed", _("Failed")
        SKIPPED = "skipped", _("Skipped")

    scan = models.ForeignKey(Scan, related_name="tool_executions", on_delete=models.CASCADE)
    tool_name = models.CharField(max_length=50)
    target = models.CharField(max_length=500)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    command = models.TextField(blank=True)
    output_file = models.FileField(upload_to="scan_output/%Y/%m/", blank=True)
    raw_output = models.TextField(blank=True)
    parsed_results = models.JSONField(default=dict, blank=True)
    exit_code = models.IntegerField(null=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = _("Tool Execution")

    def __str__(self):
        return f"{self.tool_name} -> {self.target} ({self.get_status_display()})"


class DiscoveredAsset(TimestampMixin):
    scan = models.ForeignKey(Scan, related_name="discovered_assets", on_delete=models.CASCADE)
    engagement = models.ForeignKey(
        "engagements.Engagement", related_name="discovered_assets", on_delete=models.CASCADE,
    )
    asset_type = models.CharField(max_length=20)
    value = models.CharField(max_length=500)
    source_tool = models.CharField(max_length=50)
    metadata = models.JSONField(default=dict, blank=True)
    technology_stack = models.JSONField(default=list, blank=True, verbose_name=_("Technology Stack"))
    ssl_info = models.JSONField(default=dict, blank=True, verbose_name=_("SSL/TLS Info"))
    whois_data = models.JSONField(default=dict, blank=True, verbose_name=_("WHOIS Data"))
    screenshot = models.ImageField(upload_to="screenshots/%Y/%m/", blank=True, verbose_name=_("Screenshot"))

    class Meta:
        verbose_name = _("Discovered Asset")
        verbose_name_plural = _("Discovered Assets")
        unique_together = ("engagement", "asset_type", "value")

    def __str__(self):
        return f"{self.asset_type}: {self.value} (via {self.source_tool})"
