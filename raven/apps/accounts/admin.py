from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import AuditLog, User


@admin.register(User)
class RavenUserAdmin(UserAdmin):
    list_display = ("username", "email", "role", "language", "is_active")
    list_filter = ("role", "is_active", "language")
    fieldsets = UserAdmin.fieldsets + (
        ("RAVEN", {"fields": ("role", "language", "phone")}),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "user", "action", "path", "status_code", "ip_address")
    list_filter = ("action", "timestamp")
    readonly_fields = ("user", "action", "path", "status_code", "ip_address", "timestamp", "details")
