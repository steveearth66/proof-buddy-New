from django.urls import path
from . import views

urlpatterns = [
    path("start-induction-proof", views.start_induction_proof),
    path("clear-induction", views.clear_induction),
    path("add-definitions", views.add_definitions),
    path("substitution", views.substitution),
]
