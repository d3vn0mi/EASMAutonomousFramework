from django import forms
from django.utils.translation import gettext_lazy as _
from .models import EscalationRecord, Finding


class FindingForm(forms.ModelForm):
    class Meta:
        model = Finding
        fields = (
            "title", "severity", "cvss_score", "cve_id", "description",
            "evidence", "recommendation", "references", "is_false_positive",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "evidence": forms.Textarea(attrs={"rows": 5}),
            "recommendation": forms.Textarea(attrs={"rows": 3}),
        }


class RemediationForm(forms.ModelForm):
    class Meta:
        model = Finding
        fields = ("remediation_status", "remediation_notes", "remediation_deadline")
        widgets = {
            "remediation_deadline": forms.DateInput(attrs={"type": "date"}),
        }


class EscalationForm(forms.ModelForm):
    class Meta:
        model = EscalationRecord
        fields = ("escalated_to_contact", "method", "notes")
