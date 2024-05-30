from django.urls import path
from . import views

urlpatterns = [
    path("signin", views.login),
    path("signup", views.signup),
    path("profile", views.get_user),
    path("activate-account", views.activate_account),
    path("forgot-password", views.forgot_password),
    path("reset-password", views.reset_password),
    path("resend-activation-email", views.resend_activation_email),
    path("logout", views.logout),
]
