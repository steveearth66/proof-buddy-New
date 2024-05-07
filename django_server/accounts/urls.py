from django.urls import path
from .views import login, signup, get_user

urlpatterns = [
    path('signin', login),
    path('signup', signup),
    path('profile', get_user)
]
