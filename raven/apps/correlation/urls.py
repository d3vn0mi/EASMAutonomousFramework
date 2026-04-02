from django.urls import path
from . import views

app_name = "correlation"

urlpatterns = [
    path("<int:engagement_pk>/run/", views.run_correlation_view, name="run"),
    path("<int:engagement_pk>/results/", views.correlation_results, name="results"),
]
