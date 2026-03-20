from django.db import models
from django.utils.translation import gettext_lazy as _
from core.mixins import TimestampMixin


class CorrelationResult(TimestampMixin):
    engagement = models.ForeignKey(
        "engagements.Engagement", related_name="correlations", on_delete=models.CASCADE,
    )
    engine_used = models.CharField(max_length=50, verbose_name=_("Engine"))
    input_summary = models.JSONField(default=dict, blank=True)
    output = models.TextField(verbose_name=_("Analysis Output"))
    attack_chains = models.JSONField(default=list, blank=True, verbose_name=_("Attack Chains"))
    patterns = models.JSONField(default=list, blank=True, verbose_name=_("Patterns"))
    risk_priorities = models.JSONField(default=list, blank=True, verbose_name=_("Risk Priorities"))
    executive_summary = models.TextField(blank=True, verbose_name=_("Executive Summary"))
    confidence_score = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("Correlation Result")

    def __str__(self):
        return f"Correlation for {self.engagement} ({self.engine_used})"
