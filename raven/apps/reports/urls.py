from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path("<int:engagement_pk>/", views.report_list, name="list"),
    path("<int:engagement_pk>/generate/", views.generate_report_view, name="generate"),
    path("<int:pk>/approve/", views.approve_report, name="approve"),
    path("<int:pk>/deliver/", views.deliver_report, name="deliver"),
]
