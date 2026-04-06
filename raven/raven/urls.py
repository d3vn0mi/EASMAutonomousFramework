from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.dashboard.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("clients/", include("apps.clients.urls")),
    path("engagements/", include("apps.engagements.urls")),
    path("assessments/", include("apps.assessments.urls")),
    path("scans/", include("apps.scanning.urls")),
    path("findings/", include("apps.findings.urls")),
    path("reports/", include("apps.reports.urls")),
    path("correlation/", include("apps.correlation.urls")),
    path("api/v1/", include("apps.api.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    try:
        import debug_toolbar  # noqa: F401
        urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]
    except ImportError:
        pass
