from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from apps.engagements.models import Engagement
from .models import Scan, ToolExecution


@login_required
def start_scan(request, engagement_pk):
    engagement = get_object_or_404(Engagement, pk=engagement_pk)
    if request.method == "POST":
        phase = request.POST.get("phase", "discovery")
        scan = Scan.objects.create(
            engagement=engagement,
            phase=phase,
            started_by=request.user,
        )
        from .tasks import run_scan_workflow
        run_scan_workflow.delay(scan.pk)
        messages.info(request, _("Scan started. You can monitor progress below."))
        return redirect("scanning:progress", scan_pk=scan.pk)
    return render(request, "scanning/start_scan.html", {"engagement": engagement})


@login_required
def scan_progress(request, scan_pk):
    scan = get_object_or_404(Scan, pk=scan_pk)
    tool_executions = scan.tool_executions.all()
    return render(request, "scanning/scan_progress.html", {
        "scan": scan, "tool_executions": tool_executions,
    })


@login_required
def scan_results(request, scan_pk):
    scan = get_object_or_404(Scan, pk=scan_pk)
    tool_executions = scan.tool_executions.all()
    discovered_assets = scan.discovered_assets.all()
    return render(request, "scanning/scan_results.html", {
        "scan": scan,
        "tool_executions": tool_executions,
        "discovered_assets": discovered_assets,
    })


@login_required
def scan_list(request, engagement_pk):
    engagement = get_object_or_404(Engagement, pk=engagement_pk)
    scans = engagement.scans.all()
    return render(request, "scanning/scan_list.html", {
        "engagement": engagement, "scans": scans,
    })
