from django.urls import path

from .views import retrieve_etk, db_healthcheck

urlpatterns = [
    path("retrieve", retrieve_etk, name="retrieve_etk"),
    path("health/db", db_healthcheck, name="db_healthcheck"),
]
