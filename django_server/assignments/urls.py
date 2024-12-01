from django.urls import path
from . import views

urlpatterns = [
    path("terms", views.TermViewSet.as_view()),
    path("", views.AssignmentViewSet.as_view()),
]