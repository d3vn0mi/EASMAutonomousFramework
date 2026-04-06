from django.contrib import admin
from .models import Assessment, AssessmentStep, AssessmentStepProgress


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ("name", "assessment_type", "status", "engagement", "assigned_to", "created_at")
    list_filter = ("status", "assessment_type")
    search_fields = ("name", "scope_text")


@admin.register(AssessmentStep)
class AssessmentStepAdmin(admin.ModelAdmin):
    list_display = ("step_number", "title", "assessment_type", "phase_number", "phase_name", "order")
    list_filter = ("assessment_type", "phase_number")
    ordering = ("order",)


@admin.register(AssessmentStepProgress)
class AssessmentStepProgressAdmin(admin.ModelAdmin):
    list_display = ("assessment", "step", "completed", "completed_by", "completed_at")
    list_filter = ("completed",)
