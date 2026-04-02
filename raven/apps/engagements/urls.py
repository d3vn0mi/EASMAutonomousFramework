from django.urls import path
from . import views

app_name = "engagements"

urlpatterns = [
    path("", views.engagement_list, name="list"),
    path("create/", views.engagement_create, name="create"),
    path("<int:pk>/", views.engagement_detail, name="detail"),
    path("<int:pk>/edit/", views.engagement_edit, name="edit"),
    path("<int:pk>/status/", views.engagement_status, name="status"),
    path("<int:pk>/scope/", views.scope_manage, name="scope"),
    path("<int:pk>/scope/<int:item_pk>/delete/", views.scope_delete, name="scope_delete"),
    path("<int:pk>/checklist/", views.checklist_view, name="checklist"),
    path("<int:pk>/testers/", views.assign_testers, name="assign_testers"),
    path("<int:pk>/retest/", views.retest_create, name="retest_create"),
    path("<int:pk>/generate/<str:doc_type>/", views.generate_document, name="generate_document"),
]
