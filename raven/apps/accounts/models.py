from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", _("Admin")
        PROJECT_MANAGER = "project_manager", _("Project Manager")
        TESTER = "tester", _("Tester")

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.TESTER,
        verbose_name=_("Role"),
    )
    language = models.CharField(
        max_length=2,
        choices=[("en", "English"), ("el", "Ελληνικά")],
        default="en",
        verbose_name=_("Preferred Language"),
    )
    phone = models.CharField(max_length=30, blank=True, verbose_name=_("Phone"))

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_project_manager(self):
        return self.role == self.Role.PROJECT_MANAGER

    @property
    def is_tester(self):
        return self.role == self.Role.TESTER


class AuditLog(models.Model):
    """Persistent audit trail for compliance."""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=10)
    path = models.CharField(max_length=500)
    status_code = models.IntegerField()
    ip_address = models.GenericIPAddressField(null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = _("Audit Log")
        verbose_name_plural = _("Audit Logs")

    def __str__(self):
        return f"{self.user} {self.action} {self.path} @ {self.timestamp}"
