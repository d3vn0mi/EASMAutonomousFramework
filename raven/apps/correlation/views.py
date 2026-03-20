from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from apps.engagements.models import Engagement
from .models import CorrelationResult
from .tasks import run_correlation


@login_required
def run_correlation_view(request, engagement_pk):
    engagement = get_object_or_404(Engagement, pk=engagement_pk)
    if request.method == "POST":
        engine = request.POST.get("engine", "")
        run_correlation.delay(engagement.pk, engine_name=engine or None)
        messages.info(request, _("Correlation analysis started. Results will appear shortly."))
        return redirect("correlation:results", engagement_pk=engagement.pk)
    return render(request, "correlation/run_correlation.html", {"engagement": engagement})


@login_required
def correlation_results(request, engagement_pk):
    engagement = get_object_or_404(Engagement, pk=engagement_pk)
    results = CorrelationResult.objects.filter(engagement=engagement)
    return render(request, "correlation/results.html", {
        "engagement": engagement, "results": results,
    })
