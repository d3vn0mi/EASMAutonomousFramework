from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from core.mixins import AuditMixin


class AssessmentStep(models.Model):
    """Reusable step definition seeded from the recon guides."""

    class AssessmentType(models.TextChoices):
        PASSIVE = "passive", _("Passive Recon")
        FULL = "full", _("Full Recon")

    assessment_type = models.CharField(
        max_length=10, choices=AssessmentType.choices, verbose_name=_("Assessment Type"),
    )
    phase_number = models.IntegerField(verbose_name=_("Phase Number"))
    phase_name = models.CharField(max_length=100, verbose_name=_("Phase Name"))
    step_number = models.CharField(max_length=10, verbose_name=_("Step Number"))
    title = models.CharField(max_length=200, verbose_name=_("Title"))
    description = models.TextField(verbose_name=_("Description"))
    commands = models.TextField(verbose_name=_("Commands"), blank=True)
    expected_input = models.TextField(verbose_name=_("Expected Input"), blank=True)
    expected_output = models.TextField(verbose_name=_("Expected Output"), blank=True)
    order = models.IntegerField(verbose_name=_("Order"))

    class Meta:
        ordering = ["order"]
        verbose_name = _("Assessment Step")
        verbose_name_plural = _("Assessment Steps")

    def __str__(self):
        return f"{self.step_number} - {self.title}"


class Assessment(AuditMixin):
    """A manual step-by-step assessment linked to an engagement."""

    class Status(models.TextChoices):
        DRAFT = "draft", _("Draft")
        IN_PROGRESS = "in_progress", _("In Progress")
        EXECUTED = "executed", _("Executed - Pending Report")
        PENDING_REVIEW = "pending_review", _("Pending Review")
        COMPLETED = "completed", _("Completed")

    name = models.CharField(max_length=200, verbose_name=_("Name"))
    assessment_type = models.CharField(
        max_length=10,
        choices=AssessmentStep.AssessmentType.choices,
        default=AssessmentStep.AssessmentType.PASSIVE,
        verbose_name=_("Assessment Type"),
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT,
        verbose_name=_("Status"),
    )
    scope_text = models.TextField(
        verbose_name=_("Scope"),
        help_text=_("Free-text scope: domains, IPs, CIDRs, emails, etc. One per line."),
    )
    engagement = models.ForeignKey(
        "engagements.Engagement",
        related_name="assessments",
        on_delete=models.CASCADE,
        verbose_name=_("Engagement"),
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_assessments",
        verbose_name=_("Assigned To"),
    )
    report_file = models.FileField(
        upload_to="assessment_reports/%Y/%m/",
        blank=True,
        verbose_name=_("Report File"),
    )
    report_uploaded_at = models.DateTimeField(null=True, blank=True)
    report_uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_assessment_reports",
    )
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Assessment")
        verbose_name_plural = _("Assessments")

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    @property
    def total_steps(self):
        return self.step_progress.count()

    @property
    def completed_steps(self):
        return self.step_progress.filter(completed=True).count()

    @property
    def progress_percent(self):
        total = self.total_steps
        if total == 0:
            return 0
        return int((self.completed_steps / total) * 100)


class AssessmentStepProgress(models.Model):
    """Tracks per-assessment completion of each step."""

    assessment = models.ForeignKey(
        Assessment, related_name="step_progress", on_delete=models.CASCADE,
    )
    step = models.ForeignKey(
        AssessmentStep, related_name="progress_records", on_delete=models.CASCADE,
    )
    completed = models.BooleanField(default=False, verbose_name=_("Completed"))
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="completed_assessment_steps",
    )
    notes = models.TextField(blank=True, verbose_name=_("Notes"))

    class Meta:
        ordering = ["step__order"]
        unique_together = [("assessment", "step")]
        verbose_name = _("Step Progress")
        verbose_name_plural = _("Step Progress")

    def __str__(self):
        status = "Done" if self.completed else "Pending"
        return f"{self.assessment.name} - {self.step} [{status}]"
