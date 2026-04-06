from django.urls import path
from . import views

app_name = "assessments"

urlpatterns = [
    path("", views.assessment_list, name="list"),
    path("create/", views.assessment_create, name="create"),
    path("<int:pk>/", views.assessment_detail, name="detail"),
    path("<int:pk>/execute/", views.assessment_execute, name="execute"),
    path("<int:pk>/upload-report/", views.assessment_upload_report, name="upload_report"),
    path("<int:pk>/mark-reviewed/", views.assessment_mark_reviewed, name="mark_reviewed"),
    path("report-template/", views.assessment_report_template, name="report_template"),
]
