from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from core.mixins import TimestampMixin


class Finding(TimestampMixin):
    class Severity(models.TextChoices):
        CRITICAL = "critical", _("Critical")
        HIGH = "high", _("High")
        MEDIUM = "medium", _("Medium")
        LOW = "low", _("Low")
        INFO = "info", _("Informational")

    class RemediationStatus(models.TextChoices):
        OPEN = "open", _("Open")
        IN_PROGRESS = "in_progress", _("In Progress")
        REMEDIATED = "remediated", _("Remediated")
        ACCEPTED_RISK = "accepted_risk", _("Accepted Risk")
        WONT_FIX = "wont_fix", _("Won't Fix")

    engagement = models.ForeignKey(
        "engagements.Engagement", related_name="findings", on_delete=models.CASCADE,
    )
    scan = models.ForeignKey(
        "scanning.Scan", related_name="findings", on_delete=models.SET_NULL, null=True, blank=True,
    )
    title = models.CharField(max_length=500, verbose_name=_("Title"))
    severity = models.CharField(max_length=10, choices=Severity.choices, verbose_name=_("Severity"))
    cvss_score = models.FloatField(null=True, blank=True, verbose_name=_("CVSS Score"))
    cve_id = models.CharField(max_length=20, blank=True, verbose_name=_("CVE ID"))
    description = models.TextField(verbose_name=_("Description"))
    affected_assets = models.ManyToManyField("scanning.DiscoveredAsset", blank=True)
    evidence = models.TextField(blank=True, verbose_name=_("Evidence"))
    recommendation = models.TextField(blank=True, verbose_name=_("Recommendation"))
    references = models.JSONField(default=list, blank=True, verbose_name=_("References"))
    tool_source = models.CharField(max_length=50, blank=True)
    raw_tool_output = models.TextField(blank=True)
    is_false_positive = models.BooleanField(default=False, verbose_name=_("False Positive"))
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
    )
    remediation_status = models.CharField(
        max_length=20, choices=RemediationStatus.choices, default=RemediationStatus.OPEN,
    )
    remediation_notes = models.TextField(blank=True)
    remediation_deadline = models.DateField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-severity", "-created_at"]
        verbose_name = _("Finding")
        verbose_name_plural = _("Findings")

    def __str__(self):
        return f"[{self.get_severity_display()}] {self.title}"


class EscalationRecord(TimestampMixin):
    finding = models.ForeignKey(Finding, related_name="escalations", on_delete=models.CASCADE)
    escalated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
    )
    escalated_to_contact = models.ForeignKey(
        "clients.Contact", on_delete=models.SET_NULL, null=True, blank=True,
    )
    method = models.CharField(max_length=50, verbose_name=_("Method"))
    acknowledged = models.BooleanField(default=False)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Escalation Record")

    def __str__(self):
        return f"Escalation for {self.finding.title}"
