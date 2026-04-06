from django import forms
from django.utils.translation import gettext_lazy as _
from apps.accounts.models import User
from .models import Assessment


class AssessmentCreateForm(forms.ModelForm):
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        label=_("Assigned To"),
    )

    class Meta:
        model = Assessment
        fields = ("name", "assessment_type", "engagement", "scope_text", "assigned_to")
        widgets = {
            "scope_text": forms.Textarea(attrs={
                "rows": 6,
                "placeholder": "example.com\n203.0.113.0/24\nadmin@example.com\nexample-corp (GitHub org)",
            }),
        }


class ReportUploadForm(forms.Form):
    report_file = forms.FileField(
        label=_("Report File"),
        help_text=_("Upload the completed assessment report (PDF, DOCX, or HTML)."),
    )
