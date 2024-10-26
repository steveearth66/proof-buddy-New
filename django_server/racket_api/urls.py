from django.urls import path
from . import views

urlpatterns = [
    path("er-generate", views.apply_rule),
    path("check-goal", views.check_goal),
    path("er-definitions", views.add_definitions),
    path("er-complete", views.complete_proof),
    path("er-clear", views.clear_proof),
    path("er-substitution", views.substitution),
    path("er-save", views.save_proof),
    path("proofs", views.get_user_proofs),
    path("proofs/<int:proof_id>", views.get_proof),
    path("get-definitions", views.get_definitions),
    path("use-definition/<int:id>", views.use_definition),
    path("edit-definition/", views.update_definition),
    path("delete-definition/<int:id>/", views.delete_definition_api),
    path("remove-definition/<int:id>/", views.remove_definition),
]
