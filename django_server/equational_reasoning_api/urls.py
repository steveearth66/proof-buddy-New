from django.urls import path
from . import views

app_name = 'equational_reasoning_api'

urlpatterns = [
    path("set-current-proof", views.set_current_proof, name="set_current_proof"),
    path("apply-rule", views.apply_rule, name="apply_rule"),
    path("substitution", views.substitution, name="substitution"),
    path("delete-line/<str:side>/<int:line_number>", views.delete_line, name="delete_line"),
    path("check-completion", views.check_completion, name="check_completion"),
    path("get-proof-lines", views.get_proof_lines, name="get_proof_lines"),
    path("toggle-visibility", views.toggle_visibility, name="toggle_visibility"),
    path("toggle-visibility-premise", views.toggle_visibility_premise, name="toggle_visibility_premise"),
    path("validate-hidden-field", views.validate_hidden_field, name="validate_hidden_field"),
    path("proofs", views.get_user_proofs, name="get_user_proofs"),
    path("get-user-proof", views.get_user_proof, name="get_user_proof"),
    path("clear-proof", views.clear_proof, name="clear_proof"),
    path("discard-proof", views.discard_proof, name="discard_proof"),
    path("save-proof", views.save_proof, name="save_proof"),
    path("delete-proof", views.delete_proof, name="delete_proof"),
    path("set-parameters", views.set_parameters, name="set_parameters"),
    path("download-proof", views.download_proof, name="download_proof"),
    path("upload-proof", views.upload_proof, name="upload_proof"),
]
