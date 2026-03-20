import datetime
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from core.mixins import AuditMixin, TimestampMixin


class Engagement(AuditMixin):
    class Tier(models.TextChoices):
        BRONZE = "bronze", _("Bronze")
        SILVER = "silver", _("Silver")
        GOLD = "gold", _("Gold")

    class Status(models.TextChoices):
        DRAFT = "draft", _("Draft")
        SCOPING = "scoping", _("Scoping")
        ACTIVE = "active", _("Active")
        REPORTING = "reporting", _("Reporting")
        REVIEW = "review", _("Review")
        DELIVERED = "delivered", _("Delivered")
        RETEST = "retest", _("Retest")
        CLOSED = "closed", _("Closed")

    engagement_id = models.CharField(
        max_length=30, unique=True, verbose_name=_("Engagement ID"),
        help_text=_("Format: RAVEN-EASM-YYYY-NNN"),
    )
    client = models.ForeignKey(
        "clients.Client", related_name="engagements", on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=255, verbose_name=_("Engagement Name"))
    tier = models.CharField(max_length=10, choices=Tier.choices, verbose_name=_("Tier"))
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT,
    )
    project_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="managed_engagements",
        on_delete=models.SET_NULL, null=True, blank=True,
    )
    testers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="assigned_engagements", blank=True,
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    language = models.CharField(
        max_length=2, choices=[("en", "English"), ("el", "Ελληνικά")], default="en",
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Engagement")
        verbose_name_plural = _("Engagements")

    def __str__(self):
        return f"{self.engagement_id} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.engagement_id:
            year = datetime.date.today().year
            last = Engagement.objects.filter(
                engagement_id__startswith=f"RAVEN-EASM-{year}-"
            ).count()
            self.engagement_id = f"RAVEN-EASM-{year}-{last + 1:03d}"
        super().save(*args, **kwargs)


class ScopeItem(TimestampMixin):
    class ItemType(models.TextChoices):
        DOMAIN = "domain", _("Domain")
        IP = "ip", _("IP Address")
        CIDR = "cidr", _("CIDR Range")
        EMAIL = "email", _("Email")
        NAME = "name", _("Person Name")

    engagement = models.ForeignKey(
        Engagement, related_name="scope_items", on_delete=models.CASCADE,
    )
    item_type = models.CharField(max_length=20, choices=ItemType.choices)
    value = models.CharField(max_length=500)
    in_scope = models.BooleanField(default=True, verbose_name=_("In Scope"))

    class Meta:
        verbose_name = _("Scope Item")
        verbose_name_plural = _("Scope Items")
        unique_together = ("engagement", "item_type", "value")

    def __str__(self):
        prefix = "" if self.in_scope else "[EXCLUDED] "
        return f"{prefix}{self.get_item_type_display()}: {self.value}"


class PreEngagementChecklist(TimestampMixin):
    CHECKLIST_ITEMS = [
        "Statement of Work signed",
        "Rules of Engagement signed",
        "Engagement ID assigned",
        "Project workspace created",
        "Seed information collected",
        "Domains confirmed",
        "IP ranges confirmed",
        "Exclusions documented",
        "Tier confirmed",
        "Testing window confirmed",
        "VPS provisioned",
        "Tools updated",
        "Templates prepared",
        "VPN configured",
        "Source IPs documented",
        "Comms channel established",
        "Client contacts confirmed",
        "Emergency contacts confirmed",
        "Escalation matrix reviewed",
        "Final sign-off obtained",
    ]

    engagement = models.OneToOneField(
        Engagement, related_name="checklist", on_delete=models.CASCADE,
    )
    items = models.JSONField(default=list)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Pre-Engagement Checklist")

    def save(self, *args, **kwargs):
        if not self.items:
            self.items = [
                {"item": item, "checked": False, "checked_by": None, "checked_at": None}
                for item in self.CHECKLIST_ITEMS
            ]
        super().save(*args, **kwargs)


class EngagementDocument(TimestampMixin):
    class DocType(models.TextChoices):
        SOW = "sow", _("Statement of Work")
        ROE = "roe", _("Rules of Engagement")
        CHECKLIST = "checklist", _("Pre-Engagement Checklist")
        REPORT_EXEC = "report_exec", _("Executive Report")
        REPORT_TECH = "report_tech", _("Technical Report")
        RETEST = "retest", _("Retest Report")
        ESCALATION = "escalation", _("Escalation Form")
        BOARD_DECK = "board_deck", _("Board Deck")

    engagement = models.ForeignKey(
        Engagement, related_name="documents", on_delete=models.CASCADE,
    )
    doc_type = models.CharField(max_length=30, choices=DocType.choices)
    file = models.FileField(upload_to="documents/%Y/%m/")
    version = models.PositiveIntegerField(default=1)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True,
    )

    class Meta:
        verbose_name = _("Engagement Document")
        verbose_name_plural = _("Engagement Documents")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_doc_type_display()} v{self.version} - {self.engagement}"


class Retest(TimestampMixin):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", _("Scheduled")
        IN_PROGRESS = "in_progress", _("In Progress")
        COMPLETED = "completed", _("Completed")

    engagement = models.ForeignKey(
        Engagement, related_name="retests", on_delete=models.CASCADE,
    )
    scheduled_date = models.DateField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.SCHEDULED,
    )
    findings = models.ManyToManyField("findings.Finding", blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Retest")
        verbose_name_plural = _("Retests")
        ordering = ["-scheduled_date"]
