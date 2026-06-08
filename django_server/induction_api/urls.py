from django.urls import path
from . import views

urlpatterns = [
    path("start-induction-proof", views.start_induction_proof, name="start_induction_proof"),
    path("clear-induction", views.clear_induction, name="clear_induction"),
    path("new-proof", views.new_proof, name="new_proof"),
    path("create-induction-proof/", views.create_induction_proof, name="create_induction_proof"),
    path("get-induction-proofs/", views.get_induction_proofs, name="get_induction_proofs"),
    path("proof/<int:proof_id>/", views.get_induction_proof, name="get_induction_proof"),
    # ER engine wiring endpoints (mirroring racket_api pattern)
    path("set-current-proof", views.set_current_proof, name="set_current_proof"),
    path("apply-rule", views.apply_rule, name="apply_rule"),
    path("delete-line/<str:case>/<str:side>/<int:line_number>", views.delete_line, name="delete_line"),
    path("check-goal", views.check_goal, name="check_goal"),
    path("substitution", views.substitution, name="substitution"),
    path("check-completion", views.check_completion, name="check_completion"),
    path("get-proof-lines", views.get_proof_lines, name="get_proof_lines"),
    path("get-current-proof", views.get_current_proof, name="get_current_proof"),
    path("clear-all-proof-lines", views.clear_all_proof_lines, name="clear_all_proof_lines"),
    path("set-induction-session-by-id", views.set_induction_session_by_id, name="set_induction_session_by_id"),
    path("delete-proof", views.delete_proof, name="delete_proof"),
    path("check-name-conflict", views.check_name_conflict, name="check_name_conflict"),
    path("set-parameters", views.set_parameters, name="set_parameters"),
    path("download-proof", views.download_proof, name="download_proof"),
    path("upload-proof", views.upload_proof, name="upload_proof"),
    path("validate-hidden-field", views.validate_hidden_field, name="validate_hidden_field"),
    path("validate-hidden-definition", views.validate_hidden_definition, name="validate_hidden_definition"),
    path("toggle-visibility", views.toggle_visibility, name="toggle_visibility"),
    path("save-comment", views.save_comment, name="save_comment"),
    path("get-comments", views.get_comments, name="get_comments"),
    path("get-comment-status", views.get_comment_status, name="get_comment_status"),
]