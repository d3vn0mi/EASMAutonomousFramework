from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.accounts.decorators import role_required
from .forms import AssessmentCreateForm, ReportUploadForm
from .models import Assessment, AssessmentStep, AssessmentStepProgress


@login_required
def assessment_list(request):
    if request.user.is_tester:
        assessments = Assessment.objects.filter(assigned_to=request.user)
    else:
        assessments = Assessment.objects.all()
    return render(request, "assessments/assessment_list.html", {"assessments": assessments})


@login_required
@role_required("admin", "project_manager")
def assessment_create(request):
    form = AssessmentCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        assessment = form.save(commit=False)
        assessment.created_by = request.user
        assessment.save()
        # Create progress records for all steps of the chosen type
        steps = AssessmentStep.objects.filter(assessment_type=assessment.assessment_type)
        AssessmentStepProgress.objects.bulk_create([
            AssessmentStepProgress(assessment=assessment, step=step)
            for step in steps
        ])
        messages.success(request, _("Assessment created: %(name)s") % {"name": assessment.name})
        return redirect("assessments:detail", pk=assessment.pk)
    return render(request, "assessments/assessment_form.html", {
        "form": form, "title": _("New Assessment"),
    })


@login_required
def assessment_detail(request, pk):
    assessment = get_object_or_404(Assessment, pk=pk)
    progress = assessment.step_progress.select_related("step", "completed_by").all()
    return render(request, "assessments/assessment_detail.html", {
        "assessment": assessment,
        "progress": progress,
    })


@login_required
def assessment_execute(request, pk):
    assessment = get_object_or_404(Assessment, pk=pk)

    if assessment.status == Assessment.Status.DRAFT:
        assessment.status = Assessment.Status.IN_PROGRESS
        assessment.save(update_fields=["status"])

    progress_qs = assessment.step_progress.select_related("step", "completed_by").all()

    if request.method == "POST":
        for sp in progress_qs:
            key = f"step_{sp.pk}"
            notes_key = f"notes_{sp.pk}"
            was_completed = sp.completed
            is_completed = key in request.POST
            sp.notes = request.POST.get(notes_key, sp.notes)

            if is_completed and not was_completed:
                sp.completed = True
                sp.completed_at = timezone.now()
                sp.completed_by = request.user
            elif not is_completed and was_completed:
                sp.completed = False
                sp.completed_at = None
                sp.completed_by = None
            sp.save()

        # Check if all steps are done
        all_done = not assessment.step_progress.filter(completed=False).exists()
        if all_done and assessment.status == Assessment.Status.IN_PROGRESS:
            assessment.status = Assessment.Status.EXECUTED
            assessment.save(update_fields=["status"])
            messages.success(request, _("All steps completed! You can now upload your report."))
            return redirect("assessments:detail", pk=assessment.pk)

        messages.success(request, _("Progress saved."))
        return redirect("assessments:execute", pk=assessment.pk)

    # Group progress by phase for template rendering
    phases = {}
    for sp in progress_qs:
        phase_key = sp.step.phase_number
        if phase_key not in phases:
            phases[phase_key] = {
                "number": sp.step.phase_number,
                "name": sp.step.phase_name,
                "steps": [],
            }
        phases[phase_key]["steps"].append(sp)
    phases_list = sorted(phases.values(), key=lambda p: p["number"])

    return render(request, "assessments/assessment_execute.html", {
        "assessment": assessment,
        "phases": phases_list,
    })


@login_required
def assessment_upload_report(request, pk):
    assessment = get_object_or_404(Assessment, pk=pk)
    form = ReportUploadForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        assessment.report_file = form.cleaned_data["report_file"]
        assessment.report_uploaded_at = timezone.now()
        assessment.report_uploaded_by = request.user
        assessment.status = Assessment.Status.PENDING_REVIEW
        assessment.save()
        messages.success(request, _("Report uploaded. Assessment is now pending review."))
        return redirect("assessments:detail", pk=assessment.pk)
    return render(request, "assessments/assessment_upload_report.html", {
        "assessment": assessment,
        "form": form,
    })


@login_required
@role_required("admin", "project_manager")
def assessment_mark_reviewed(request, pk):
    assessment = get_object_or_404(Assessment, pk=pk)
    if request.method == "POST":
        assessment.status = Assessment.Status.COMPLETED
        assessment.completed_at = timezone.now()
        assessment.save(update_fields=["status", "completed_at"])
        messages.success(request, _("Assessment marked as completed."))
    return redirect("assessments:detail", pk=assessment.pk)


@login_required
def assessment_report_template(request):
    return render(request, "assessments/report_template_view.html")
