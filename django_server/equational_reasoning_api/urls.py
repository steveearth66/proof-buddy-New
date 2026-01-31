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
]
