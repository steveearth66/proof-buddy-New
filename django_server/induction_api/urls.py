from django.urls import path
from . import views

urlpatterns = [
    path("start-induction-proof", views.start_induction_proof, name="start_induction_proof"),
    path("clear-induction", views.clear_induction, name="clear_induction"),
    path("create-induction-proof/", views.create_induction_proof, name="create_induction_proof"),
    path("get-induction-proofs/", views.get_induction_proofs, name="get_induction_proofs"),
    path("proof/<int:proof_id>/", views.get_induction_proof, name="get_induction_proof"),
    # ER engine wiring endpoints (mirroring racket_api pattern)
    path("set-current-proof", views.set_current_proof, name="set_current_proof"),
    path("apply-rule", views.apply_rule, name="apply_rule"),
    path("delete-line/<str:case>/<str:side>", views.delete_line, name="delete_line"),
    path("check-goal", views.check_goal, name="check_goal"),
    path("substitution", views.substitution, name="substitution"),
    path("check-completion", views.check_completion, name="check_completion"),
]