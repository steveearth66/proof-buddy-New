from django.urls import path
from . import views

urlpatterns = [
    path("start-induction-proof", views.start_induction_proof, name="start_induction_proof"),
    path("clear-induction", views.clear_induction, name="clear_induction"),
    path("create-induction-proof/", views.create_induction_proof, name="create_induction_proof"),
    path("get-induction-proofs/", views.get_induction_proofs, name="get_induction_proofs"),
    path("proof/<int:proof_id>/", views.get_induction_proof, name="get_induction_proof"),
]