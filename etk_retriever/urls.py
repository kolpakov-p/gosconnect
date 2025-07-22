from django.urls import path

from .views import retrieve_etk

urlpatterns = [
    path("retrieve", retrieve_etk, name="retrieve_etk"),
]
