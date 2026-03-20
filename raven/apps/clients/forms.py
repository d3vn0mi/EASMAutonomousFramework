from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Asset, Client, Contact


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ("name", "industry", "website", "status", "notes")


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ("name", "email", "phone", "role", "is_primary")


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ("asset_type", "value", "status")


class AssetBulkImportForm(forms.Form):
    """Import multiple assets at once, one per line."""
    asset_type = forms.ChoiceField(choices=Asset.AssetType.choices, label=_("Asset Type"))
    values = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 10, "placeholder": _("One asset per line")}),
        label=_("Values"),
    )
