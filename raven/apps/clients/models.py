from django.db import models
from django.utils.translation import gettext_lazy as _
from core.mixins import AuditMixin, TimestampMixin


class Client(AuditMixin):
    class Status(models.TextChoices):
        ACTIVE = "active", _("Active")
        INACTIVE = "inactive", _("Inactive")
        PROSPECT = "prospect", _("Prospect")

    name = models.CharField(max_length=255, verbose_name=_("Client Name"))
    industry = models.CharField(max_length=100, blank=True, verbose_name=_("Industry"))
    website = models.URLField(blank=True, verbose_name=_("Website"))
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    notes = models.TextField(blank=True, verbose_name=_("Notes"))

    class Meta:
        ordering = ["name"]
        verbose_name = _("Client")
        verbose_name_plural = _("Clients")

    def __str__(self):
        return self.name


class Contact(TimestampMixin):
    client = models.ForeignKey(Client, related_name="contacts", on_delete=models.CASCADE)
    name = models.CharField(max_length=255, verbose_name=_("Name"))
    email = models.EmailField(verbose_name=_("Email"))
    phone = models.CharField(max_length=30, blank=True, verbose_name=_("Phone"))
    role = models.CharField(max_length=100, verbose_name=_("Role"))
    is_primary = models.BooleanField(default=False, verbose_name=_("Primary Contact"))

    class Meta:
        verbose_name = _("Contact")
        verbose_name_plural = _("Contacts")

    def __str__(self):
        return f"{self.name} ({self.client.name})"


class Asset(TimestampMixin):
    """Per-client asset inventory."""
    class AssetType(models.TextChoices):
        DOMAIN = "domain", _("Domain")
        IP = "ip", _("IP Address")
        CIDR = "cidr", _("CIDR Range")
        EMAIL = "email", _("Email")
        NAME = "name", _("Person Name")
        URL = "url", _("URL")

    client = models.ForeignKey(Client, related_name="assets", on_delete=models.CASCADE)
    asset_type = models.CharField(max_length=20, choices=AssetType.choices, verbose_name=_("Type"))
    value = models.CharField(max_length=500, verbose_name=_("Value"))
    status = models.CharField(max_length=20, default="active", verbose_name=_("Status"))
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Metadata"))

    class Meta:
        verbose_name = _("Asset")
        verbose_name_plural = _("Assets")
        unique_together = ("client", "asset_type", "value")

    def __str__(self):
        return f"{self.get_asset_type_display()}: {self.value}"
