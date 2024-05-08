from django.urls import path
from .views import login, signup, get_user, activate_account

urlpatterns = [
    path('signin', login),
    path('signup', signup),
    path('profile', get_user),
    path('activate-account', activate_account),
]
