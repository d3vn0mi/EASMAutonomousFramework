from django import forms
from django.utils.translation import gettext_lazy as _
from apps.accounts.models import User
from .models import Engagement, Retest, ScopeItem


class EngagementForm(forms.ModelForm):
    project_manager = forms.ModelChoiceField(
        queryset=User.objects.filter(role__in=["admin", "project_manager"]),
        required=False,
    )

    class Meta:
        model = Engagement
        fields = (
            "client", "name", "tier", "project_manager",
            "start_date", "end_date", "language", "notes",
        )
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }


class ScopeItemForm(forms.ModelForm):
    class Meta:
        model = ScopeItem
        fields = ("item_type", "value", "in_scope")


class ScopeBulkForm(forms.Form):
    item_type = forms.ChoiceField(choices=ScopeItem.ItemType.choices, label=_("Type"))
    values = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 8, "placeholder": _("One item per line")}),
        label=_("Values"),
    )
    in_scope = forms.BooleanField(initial=True, required=False, label=_("In Scope"))


class RetestForm(forms.ModelForm):
    class Meta:
        model = Retest
        fields = ("scheduled_date", "notes")
        widgets = {"scheduled_date": forms.DateInput(attrs={"type": "date"})}
