from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from apps.accounts.decorators import role_required
from .forms import AssetBulkImportForm, AssetForm, ClientForm, ContactForm
from .models import Asset, Client, Contact


@login_required
def client_list(request):
    clients = Client.objects.all()
    return render(request, "clients/client_list.html", {"clients": clients})


@login_required
@role_required("admin", "project_manager")
def client_create(request):
    form = ClientForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        client = form.save(commit=False)
        client.created_by = request.user
        client.save()
        messages.success(request, _("Client created."))
        return redirect("clients:detail", pk=client.pk)
    return render(request, "clients/client_form.html", {"form": form, "title": _("New Client")})


@login_required
def client_detail(request, pk):
    client = get_object_or_404(Client, pk=pk)
    contacts = client.contacts.all()
    assets = client.assets.all()
    engagements = client.engagements.all().order_by("-created_at")
    return render(request, "clients/client_detail.html", {
        "client": client, "contacts": contacts, "assets": assets, "engagements": engagements,
    })


@login_required
@role_required("admin", "project_manager")
def client_edit(request, pk):
    client = get_object_or_404(Client, pk=pk)
    form = ClientForm(request.POST or None, instance=client)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("Client updated."))
        return redirect("clients:detail", pk=client.pk)
    return render(request, "clients/client_form.html", {"form": form, "title": _("Edit Client")})


@login_required
@role_required("admin", "project_manager")
def contact_create(request, client_pk):
    client = get_object_or_404(Client, pk=client_pk)
    form = ContactForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        contact = form.save(commit=False)
        contact.client = client
        contact.save()
        messages.success(request, _("Contact added."))
        return redirect("clients:detail", pk=client.pk)
    return render(request, "clients/contact_form.html", {"form": form, "client": client})


@login_required
@role_required("admin", "project_manager")
def contact_edit(request, pk):
    contact = get_object_or_404(Contact, pk=pk)
    form = ContactForm(request.POST or None, instance=contact)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("Contact updated."))
        return redirect("clients:detail", pk=contact.client.pk)
    return render(request, "clients/contact_form.html", {"form": form, "client": contact.client})


@login_required
def asset_list(request, client_pk):
    client = get_object_or_404(Client, pk=client_pk)
    assets = client.assets.all().order_by("asset_type", "value")
    return render(request, "clients/asset_list.html", {"client": client, "assets": assets})


@login_required
@role_required("admin", "project_manager")
def asset_create(request, client_pk):
    client = get_object_or_404(Client, pk=client_pk)
    form = AssetForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        asset = form.save(commit=False)
        asset.client = client
        asset.save()
        messages.success(request, _("Asset added."))
        return redirect("clients:asset_list", client_pk=client.pk)
    return render(request, "clients/asset_form.html", {"form": form, "client": client})


@login_required
@role_required("admin", "project_manager")
def asset_bulk_import(request, client_pk):
    client = get_object_or_404(Client, pk=client_pk)
    form = AssetBulkImportForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        asset_type = form.cleaned_data["asset_type"]
        values = form.cleaned_data["values"].strip().splitlines()
        created = 0
        for val in values:
            val = val.strip()
            if val:
                _, is_new = Asset.objects.get_or_create(
                    client=client, asset_type=asset_type, value=val,
                )
                if is_new:
                    created += 1
        messages.success(request, _("%(count)d assets imported.") % {"count": created})
        return redirect("clients:asset_list", client_pk=client.pk)
    return render(request, "clients/asset_bulk_import.html", {"form": form, "client": client})
