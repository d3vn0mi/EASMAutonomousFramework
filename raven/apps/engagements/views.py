from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from apps.accounts.decorators import role_required
from .forms import EngagementForm, RetestForm, ScopeBulkForm, ScopeItemForm
from .models import Engagement, PreEngagementChecklist, Retest, ScopeItem


@login_required
def engagement_list(request):
    if request.user.is_tester:
        engagements = request.user.assigned_engagements.all()
    else:
        engagements = Engagement.objects.all()
    return render(request, "engagements/engagement_list.html", {"engagements": engagements})


@login_required
@role_required("admin", "project_manager")
def engagement_create(request):
    form = EngagementForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        eng = form.save(commit=False)
        eng.created_by = request.user
        eng.save()
        form.save_m2m()
        PreEngagementChecklist.objects.create(engagement=eng)
        messages.success(request, _("Engagement created: %(eid)s") % {"eid": eng.engagement_id})
        return redirect("engagements:detail", pk=eng.pk)
    return render(request, "engagements/engagement_form.html", {"form": form, "title": _("New Engagement")})


@login_required
def engagement_detail(request, pk):
    engagement = get_object_or_404(Engagement, pk=pk)
    scope_items = engagement.scope_items.all().order_by("item_type")
    scans = engagement.scans.all().order_by("-created_at")
    documents = engagement.documents.all()
    findings_qs = engagement.findings.all()
    retests = engagement.retests.all()
    checklist = getattr(engagement, "checklist", None)
    return render(request, "engagements/engagement_detail.html", {
        "engagement": engagement,
        "scope_items": scope_items,
        "scans": scans,
        "documents": documents,
        "findings": findings_qs,
        "retests": retests,
        "checklist": checklist,
    })


@login_required
@role_required("admin", "project_manager")
def engagement_edit(request, pk):
    engagement = get_object_or_404(Engagement, pk=pk)
    form = EngagementForm(request.POST or None, instance=engagement)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("Engagement updated."))
        return redirect("engagements:detail", pk=engagement.pk)
    return render(request, "engagements/engagement_form.html", {"form": form, "title": _("Edit Engagement")})


@login_required
@role_required("admin", "project_manager")
def engagement_status(request, pk):
    engagement = get_object_or_404(Engagement, pk=pk)
    new_status = request.POST.get("status")
    if new_status and new_status in dict(Engagement.Status.choices):
        engagement.status = new_status
        engagement.save(update_fields=["status"])
        messages.success(request, _("Status updated to %(s)s.") % {"s": engagement.get_status_display()})
    return redirect("engagements:detail", pk=engagement.pk)


@login_required
def scope_manage(request, pk):
    engagement = get_object_or_404(Engagement, pk=pk)
    item_form = ScopeItemForm(request.POST or None)
    bulk_form = ScopeBulkForm()
    if request.method == "POST":
        if "bulk_submit" in request.POST:
            bulk_form = ScopeBulkForm(request.POST)
            if bulk_form.is_valid():
                item_type = bulk_form.cleaned_data["item_type"]
                in_scope = bulk_form.cleaned_data["in_scope"]
                values = bulk_form.cleaned_data["values"].strip().splitlines()
                created = 0
                for val in values:
                    val = val.strip()
                    if val:
                        _, is_new = ScopeItem.objects.get_or_create(
                            engagement=engagement, item_type=item_type, value=val,
                            defaults={"in_scope": in_scope},
                        )
                        if is_new:
                            created += 1
                messages.success(request, _("%(count)d scope items added.") % {"count": created})
                return redirect("engagements:scope", pk=engagement.pk)
        elif item_form.is_valid():
            item = item_form.save(commit=False)
            item.engagement = engagement
            item.save()
            messages.success(request, _("Scope item added."))
            return redirect("engagements:scope", pk=engagement.pk)

    scope_items = engagement.scope_items.all().order_by("item_type")
    return render(request, "engagements/scope_manage.html", {
        "engagement": engagement,
        "scope_items": scope_items,
        "item_form": item_form,
        "bulk_form": bulk_form,
    })


@login_required
def scope_delete(request, pk, item_pk):
    item = get_object_or_404(ScopeItem, pk=item_pk, engagement__pk=pk)
    item.delete()
    messages.success(request, _("Scope item removed."))
    return redirect("engagements:scope", pk=pk)


@login_required
def checklist_view(request, pk):
    engagement = get_object_or_404(Engagement, pk=pk)
    checklist, _ = PreEngagementChecklist.objects.get_or_create(engagement=engagement)
    if request.method == "POST":
        items = checklist.items
        for i, item in enumerate(items):
            key = f"item_{i}"
            was_checked = item["checked"]
            is_checked = key in request.POST
            if is_checked and not was_checked:
                item["checked"] = True
                item["checked_by"] = request.user.username
                item["checked_at"] = timezone.now().isoformat()
            elif not is_checked and was_checked:
                item["checked"] = False
                item["checked_by"] = None
                item["checked_at"] = None
        checklist.items = items
        checklist.completed = all(item["checked"] for item in items)
        if checklist.completed:
            checklist.completed_at = timezone.now()
        checklist.save()
        messages.success(request, _("Checklist updated."))
        return redirect("engagements:checklist", pk=engagement.pk)
    return render(request, "engagements/checklist.html", {
        "engagement": engagement, "checklist": checklist,
    })


@login_required
@role_required("admin", "project_manager")
def assign_testers(request, pk):
    engagement = get_object_or_404(Engagement, pk=pk)
    if request.method == "POST":
        tester_ids = request.POST.getlist("testers")
        from apps.accounts.models import User
        testers = User.objects.filter(pk__in=tester_ids, role="tester")
        engagement.testers.set(testers)
        messages.success(request, _("Testers assigned."))
        return redirect("engagements:detail", pk=engagement.pk)
    from apps.accounts.models import User
    available_testers = User.objects.filter(role="tester", is_active=True)
    return render(request, "engagements/assign_testers.html", {
        "engagement": engagement, "available_testers": available_testers,
    })


@login_required
@role_required("admin", "project_manager")
def retest_create(request, pk):
    engagement = get_object_or_404(Engagement, pk=pk)
    form = RetestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        retest = form.save(commit=False)
        retest.engagement = engagement
        retest.save()
        messages.success(request, _("Retest scheduled."))
        return redirect("engagements:detail", pk=engagement.pk)
    return render(request, "engagements/retest_form.html", {"form": form, "engagement": engagement})


@login_required
@role_required("admin", "project_manager")
def generate_document(request, pk, doc_type):
    """Trigger document generation (SoW, RoE, etc.)."""
    engagement = get_object_or_404(Engagement, pk=pk)
    from .tasks import generate_engagement_document
    generate_engagement_document.delay(engagement.pk, doc_type, request.user.pk)
    messages.info(request, _("Document generation started. It will appear in the documents tab shortly."))
    return redirect("engagements:detail", pk=engagement.pk)
