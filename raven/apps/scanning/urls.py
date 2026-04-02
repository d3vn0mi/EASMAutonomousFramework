from django.urls import path
from . import views

app_name = "scanning"

urlpatterns = [
    path("<int:engagement_pk>/", views.scan_list, name="list"),
    path("<int:engagement_pk>/start/", views.start_scan, name="start"),
    path("progress/<int:scan_pk>/", views.scan_progress, name="progress"),
    path("results/<int:scan_pk>/", views.scan_results, name="results"),
]
