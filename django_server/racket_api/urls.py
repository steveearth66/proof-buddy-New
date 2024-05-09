from django.urls import path
from .views import apply_rule, check_goal, add_definitions, complete_proof, clear_proof

urlpatterns = [
    path('er-generate', apply_rule),
    path('check-goal', check_goal),
    path('er-definitions', add_definitions),
    path('er-complete', complete_proof),
    path('er-clear', clear_proof)
]
