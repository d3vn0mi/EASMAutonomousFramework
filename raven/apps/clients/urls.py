from django.urls import path
from . import views

app_name = "clients"

urlpatterns = [
    path("", views.client_list, name="list"),
    path("create/", views.client_create, name="create"),
    path("<int:pk>/", views.client_detail, name="detail"),
    path("<int:pk>/edit/", views.client_edit, name="edit"),
    path("<int:client_pk>/contacts/create/", views.contact_create, name="contact_create"),
    path("contacts/<int:pk>/edit/", views.contact_edit, name="contact_edit"),
    path("<int:client_pk>/assets/", views.asset_list, name="asset_list"),
    path("<int:client_pk>/assets/create/", views.asset_create, name="asset_create"),
    path("<int:client_pk>/assets/import/", views.asset_bulk_import, name="asset_bulk_import"),
]
