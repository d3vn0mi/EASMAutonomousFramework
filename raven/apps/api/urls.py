from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import views

app_name = "api"

router = DefaultRouter()
router.register(r"clients", views.ClientViewSet, basename="client")
router.register(r"engagements", views.EngagementViewSet, basename="engagement")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "clients/<int:client_pk>/contacts/",
        views.ContactViewSet.as_view({"get": "list", "post": "create"}),
        name="client-contacts",
    ),
    path(
        "clients/<int:client_pk>/assets/",
        views.AssetViewSet.as_view({"get": "list", "post": "create"}),
        name="client-assets",
    ),
    path(
        "engagements/<int:engagement_pk>/scope/",
        views.ScopeItemViewSet.as_view({"get": "list", "post": "create"}),
        name="engagement-scope",
    ),
    path(
        "engagements/<int:engagement_pk>/findings/",
        views.FindingViewSet.as_view({"get": "list", "post": "create"}),
        name="engagement-findings",
    ),
    path(
        "engagements/<int:engagement_pk>/scans/",
        views.ScanViewSet.as_view({"get": "list"}),
        name="engagement-scans",
    ),
    path(
        "engagements/<int:engagement_pk>/discovered-assets/",
        views.DiscoveredAssetViewSet.as_view({"get": "list"}),
        name="engagement-discovered-assets",
    ),
    path(
        "engagements/<int:engagement_pk>/reports/",
        views.ReportViewSet.as_view({"get": "list"}),
        name="engagement-reports",
    ),
]
