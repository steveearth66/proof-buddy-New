from django.urls import path
from . import views

urlpatterns = [
    path("delete-proof/<int:id>", views.delete_proof),
    path("edit=proof/<int:id>", views.edit_proof)
]