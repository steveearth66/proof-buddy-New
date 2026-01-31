from django.urls import path
from . import views

urlpatterns = [
    path("terms", views.TermViewSet.as_view()),
    path("terms/<int:term_id>", views.TermViewSet.as_view()),
    path("<int:term_id>", views.AssignmentViewSet.as_view()),
    path("", views.AssignmentViewSet.as_view()),
    path("check-user", views.check_user),
    path("remove-student", views.remove_student),
    path("add-student", views.add_student),
]
