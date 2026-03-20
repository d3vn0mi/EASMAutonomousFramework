from django.db import models


class TimestampMixin(models.Model):
    """Adds created_at / updated_at to any model."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AuditMixin(TimestampMixin):
    """Adds created_by tracking on top of timestamps."""

    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_created",
    )

    class Meta:
        abstract = True
