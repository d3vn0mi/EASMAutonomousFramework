from django.urls import path
from . import views

app_name = "findings"

urlpatterns = [
    path("<int:engagement_pk>/", views.finding_list, name="list"),
    path("<int:engagement_pk>/create/", views.finding_create, name="create"),
    path("detail/<int:pk>/", views.finding_detail, name="detail"),
    path("detail/<int:pk>/edit/", views.finding_edit, name="edit"),
    path("detail/<int:pk>/remediation/", views.remediation_update, name="remediation"),
    path("detail/<int:pk>/escalate/", views.escalate_finding, name="escalate"),
    path("<int:engagement_pk>/import/<int:scan_pk>/", views.import_from_scan, name="import_from_scan"),
]
