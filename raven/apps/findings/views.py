from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from apps.engagements.models import Engagement
from .forms import EscalationForm, FindingForm, RemediationForm
from .models import EscalationRecord, Finding


@login_required
def finding_list(request, engagement_pk):
    engagement = get_object_or_404(Engagement, pk=engagement_pk)
    findings = engagement.findings.all()
    severity_filter = request.GET.get("severity")
    if severity_filter:
        findings = findings.filter(severity=severity_filter)
    return render(request, "findings/finding_list.html", {
        "engagement": engagement, "findings": findings,
    })


@login_required
def finding_create(request, engagement_pk):
    engagement = get_object_or_404(Engagement, pk=engagement_pk)
    form = FindingForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        finding = form.save(commit=False)
        finding.engagement = engagement
        finding.added_by = request.user
        finding.save()
        messages.success(request, _("Finding added."))
        return redirect("findings:list", engagement_pk=engagement.pk)
    return render(request, "findings/finding_form.html", {
        "form": form, "engagement": engagement, "title": _("Add Finding"),
    })


@login_required
def finding_detail(request, pk):
    finding = get_object_or_404(Finding, pk=pk)
    escalations = finding.escalations.all()
    return render(request, "findings/finding_detail.html", {
        "finding": finding, "escalations": escalations,
    })


@login_required
def finding_edit(request, pk):
    finding = get_object_or_404(Finding, pk=pk)
    form = FindingForm(request.POST or None, instance=finding)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("Finding updated."))
        return redirect("findings:detail", pk=finding.pk)
    return render(request, "findings/finding_form.html", {
        "form": form, "engagement": finding.engagement, "title": _("Edit Finding"),
    })


@login_required
def remediation_update(request, pk):
    finding = get_object_or_404(Finding, pk=pk)
    form = RemediationForm(request.POST or None, instance=finding)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("Remediation status updated."))
        return redirect("findings:detail", pk=finding.pk)
    return render(request, "findings/remediation_form.html", {
        "form": form, "finding": finding,
    })


@login_required
def escalate_finding(request, pk):
    finding = get_object_or_404(Finding, pk=pk)
    form = EscalationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        esc = form.save(commit=False)
        esc.finding = finding
        esc.escalated_by = request.user
        esc.save()
        messages.success(request, _("Finding escalated."))
        return redirect("findings:detail", pk=finding.pk)
    client_contacts = finding.engagement.client.contacts.all()
    form.fields["escalated_to_contact"].queryset = client_contacts
    return render(request, "findings/escalation_form.html", {
        "form": form, "finding": finding,
    })


@login_required
def import_from_scan(request, engagement_pk, scan_pk):
    """Auto-import findings from scan tool results (e.g., Nuclei)."""
    from apps.scanning.models import Scan, ToolExecution

    engagement = get_object_or_404(Engagement, pk=engagement_pk)
    scan = get_object_or_404(Scan, pk=scan_pk)

    imported = 0
    for te in scan.tool_executions.filter(tool_name="nuclei", status="completed"):
        for vuln in te.parsed_results.get("findings", []):
            if isinstance(vuln, dict):
                title = vuln.get("template-id", vuln.get("name", "Unknown"))
                severity = vuln.get("info", {}).get("severity", "info") if isinstance(vuln.get("info"), dict) else "info"
                if severity not in dict(Finding.Severity.choices):
                    severity = "info"
                _, created = Finding.objects.get_or_create(
                    engagement=engagement,
                    title=title,
                    tool_source="nuclei",
                    defaults={
                        "severity": severity,
                        "description": vuln.get("info", {}).get("description", "") if isinstance(vuln.get("info"), dict) else str(vuln),
                        "scan": scan,
                        "raw_tool_output": str(vuln)[:5000],
                        "added_by": request.user,
                    },
                )
                if created:
                    imported += 1

    messages.success(request, _("%(count)d findings imported.") % {"count": imported})
    return redirect("findings:list", engagement_pk=engagement.pk)
