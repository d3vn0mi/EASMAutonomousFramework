from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from core.mixins import TimestampMixin


class Report(TimestampMixin):
    class ReportType(models.TextChoices):
        EXECUTIVE = "executive", _("Executive Report")
        TECHNICAL = "technical", _("Technical Report")
        RETEST = "retest", _("Retest Report")

    class Status(models.TextChoices):
        DRAFT = "draft", _("Draft")
        GENERATED = "generated", _("Generated")
        REVIEW = "review", _("Under Review")
        APPROVED = "approved", _("Approved")
        DELIVERED = "delivered", _("Delivered")

    engagement = models.ForeignKey(
        "engagements.Engagement", related_name="reports", on_delete=models.CASCADE,
    )
    report_type = models.CharField(max_length=20, choices=ReportType.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    generated_file = models.FileField(upload_to="reports/%Y/%m/", blank=True)
    template_used = models.CharField(max_length=100, blank=True)
    generated_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="approved_reports",
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Report")
        verbose_name_plural = _("Reports")

    def __str__(self):
        return f"{self.get_report_type_display()} - {self.engagement}"
