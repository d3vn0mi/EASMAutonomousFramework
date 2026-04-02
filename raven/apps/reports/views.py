from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from apps.accounts.decorators import role_required
from apps.engagements.models import Engagement
from .models import Report
from .tasks import generate_report


@login_required
def report_list(request, engagement_pk):
    engagement = get_object_or_404(Engagement, pk=engagement_pk)
    reports = Report.objects.filter(engagement=engagement)
    return render(request, "reports/report_list.html", {
        "engagement": engagement, "reports": reports,
    })


@login_required
def generate_report_view(request, engagement_pk):
    engagement = get_object_or_404(Engagement, pk=engagement_pk)
    if request.method == "POST":
        report_type = request.POST.get("report_type", "technical")
        generate_report.delay(engagement.pk, report_type, request.user.pk)
        messages.info(request, _("Report generation started."))
        return redirect("reports:list", engagement_pk=engagement.pk)
    return render(request, "reports/generate_report.html", {"engagement": engagement})


@login_required
@role_required("admin", "project_manager")
def approve_report(request, pk):
    report = get_object_or_404(Report, pk=pk)
    report.status = "approved"
    report.approved_by = request.user
    report.approved_at = timezone.now()
    report.save(update_fields=["status", "approved_by", "approved_at"])
    messages.success(request, _("Report approved."))
    return redirect("reports:list", engagement_pk=report.engagement.pk)


@login_required
@role_required("admin", "project_manager")
def deliver_report(request, pk):
    report = get_object_or_404(Report, pk=pk)
    report.status = "delivered"
    report.save(update_fields=["status"])
    messages.success(request, _("Report marked as delivered."))
    return redirect("reports:list", engagement_pk=report.engagement.pk)
