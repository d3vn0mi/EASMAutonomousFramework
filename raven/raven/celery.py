import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "raven.settings.development")

app = Celery("raven")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Route scanning tasks to the scanner container
app.conf.task_routes = {
    "apps.scanning.tasks.*": {"queue": "scanning"},
    "apps.correlation.tasks.*": {"queue": "default"},
    "apps.reports.tasks.*": {"queue": "default"},
    "apps.engagements.tasks.*": {"queue": "default"},
}
