from django.urls import path
from .views import apply_rule, check_goal, add_definitions

urlpatterns = [
    path('er-generate', apply_rule),
    path('check-goal', check_goal),
    path('add-definitions', add_definitions),
]
