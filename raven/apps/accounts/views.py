from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from .decorators import role_required
from .forms import LoginForm, RavenUserChangeForm, RavenUserCreationForm
from .models import AuditLog, User


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:index")
    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data["username"],
            password=form.cleaned_data["password"],
        )
        if user is not None:
            login(request, user)
            return redirect(request.GET.get("next", "dashboard:index"))
        messages.error(request, _("Invalid username or password."))
    return render(request, "accounts/login.html", {"form": form})


@login_required
def logout_view(request):
    logout(request)
    return redirect("accounts:login")


@login_required
@role_required("admin")
def user_list(request):
    users = User.objects.all().order_by("username")
    return render(request, "accounts/user_list.html", {"users": users})


@login_required
@role_required("admin")
def user_create(request):
    form = RavenUserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("User created successfully."))
        return redirect("accounts:user_list")
    return render(request, "accounts/user_form.html", {"form": form, "title": _("Create User")})


@login_required
@role_required("admin")
def user_edit(request, pk):
    user = get_object_or_404(User, pk=pk)
    form = RavenUserChangeForm(request.POST or None, instance=user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("User updated successfully."))
        return redirect("accounts:user_list")
    return render(request, "accounts/user_form.html", {"form": form, "title": _("Edit User")})


@login_required
@role_required("admin")
def audit_log(request):
    logs = AuditLog.objects.select_related("user").all()[:500]
    return render(request, "accounts/audit_log.html", {"logs": logs})


@login_required
def profile(request):
    if request.method == "POST":
        request.user.language = request.POST.get("language", "en")
        request.user.phone = request.POST.get("phone", "")
        request.user.save(update_fields=["language", "phone"])
        messages.success(request, _("Profile updated."))
        return redirect("accounts:profile")
    return render(request, "accounts/profile.html")
