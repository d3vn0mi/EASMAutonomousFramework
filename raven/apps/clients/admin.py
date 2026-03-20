from django.contrib import admin
from .models import Asset, Client, Contact


class ContactInline(admin.TabularInline):
    model = Contact
    extra = 0


class AssetInline(admin.TabularInline):
    model = Asset
    extra = 0


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "industry", "status", "created_at")
    list_filter = ("status", "industry")
    search_fields = ("name",)
    inlines = [ContactInline, AssetInline]
