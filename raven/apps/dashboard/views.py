from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from apps.clients.models import Client
from apps.engagements.models import Engagement
from apps.findings.models import Finding
from apps.scanning.models import Scan


@login_required
def dashboard(request):
    user = request.user

    # Base querysets
    if user.is_tester:
        engagements = user.assigned_engagements.all()
    else:
        engagements = Engagement.objects.all()

    active_engagements = engagements.filter(
        status__in=["active", "scoping", "reporting", "review", "retest"]
    )

    # Stats
    total_clients = Client.objects.count()
    total_engagements = engagements.count()
    active_count = active_engagements.count()

    # Findings by severity
    findings_qs = Finding.objects.filter(engagement__in=engagements)
    severity_stats = findings_qs.values("severity").annotate(count=Count("id")).order_by("severity")
    severity_dict = {s["severity"]: s["count"] for s in severity_stats}

    # Recent scans
    recent_scans = Scan.objects.filter(engagement__in=engagements).order_by("-created_at")[:10]

    # Open findings count
    open_findings = findings_qs.filter(
        remediation_status="open", is_false_positive=False
    ).count()

    context = {
        "total_clients": total_clients,
        "total_engagements": total_engagements,
        "active_engagements": active_count,
        "open_findings": open_findings,
        "severity_critical": severity_dict.get("critical", 0),
        "severity_high": severity_dict.get("high", 0),
        "severity_medium": severity_dict.get("medium", 0),
        "severity_low": severity_dict.get("low", 0),
        "severity_info": severity_dict.get("info", 0),
        "recent_scans": recent_scans,
        "active_engagement_list": active_engagements[:10],
    }
    return render(request, "dashboard/index.html", context)
