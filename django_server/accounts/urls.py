from django.urls import path
from .views import login, signup, get_user, activate_account, forgot_password, reset_password, resend_verification_email

urlpatterns = [
    path('signin', login),
    path('signup', signup),
    path('profile', get_user),
    path('activate-account', activate_account),
    path('forgot-password', forgot_password),
    path('reset-password', reset_password),
    path('resend-verification-email', resend_verification_email),
]
