from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from dotenv import load_dotenv
import string
import random
import os


load_dotenv()

class AccountManager(BaseUserManager):
    def create_user(self, email, username, password=None, **other_fields):
        if not email:
            raise ValueError('Users must have an email address')
        if not username:
            raise ValueError('Users must have a username')

        user = self.model(
            email=self.normalize_email(email),
            username=username,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password):
        user = self.create_user(
            email=self.normalize_email(email),
            password=password,
            username=username,
        )
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class Account(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(verbose_name='email', max_length=60, unique=True)
    username = models.CharField(max_length=30, unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    date_joined = models.DateTimeField(
        verbose_name='date joined', auto_now_add=True)
    last_login = models.DateTimeField(verbose_name='last login', auto_now=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_instructor = models.BooleanField(default=False)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    objects = AccountManager()

    def __str__(self):
        return self.username


def generate_key():
    key = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
    return key


class ActivateAccount(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    activation_key = models.CharField(
        max_length=20, unique=True, default=generate_key)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


class ResetPassword(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    reset_key = models.CharField(
        max_length=20, unique=True, default=generate_key)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=Account)
def create_activation_key(sender, instance, created, **kwargs):
    if created:
        activation = ActivateAccount.objects.create(user=instance)
        email = instance.email
        username = instance.username
        key = activation.activation_key
        send_activation_email(email, username, key)


def send_activation_email(email, username, key):
    html_content = f'''
<p>Hello {username}!</p>
<p>Thank you for signing up to Proof Buddy! To get started please confirm your email address by visiting the following link:</p>
<a href="{os.getenv('FRONTEND_URL')}/verify-success?token={key}" target="_blank">{os.getenv('FRONTEND_URL')}/verify-success?token={key}</a>
<p>Thank you,<br/>Proof Buddy Team</p>
'''
    text_content = ""
    subject = "Proof Buddy - Confirm Your Email"
    from_email = os.getenv('EMAIL_HOST_USER')
    to = email
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
    msg.attach_alternative(html_content, "text/html")
    msg.send()


@receiver(post_save, sender=ResetPassword)
def send_reset_password_email(sender, instance, created, **kwargs):
    if created:
        print('sending email')
        email = instance.user.email
        username = instance.user.username
        key = instance.reset_key
        send_reset_email(email, username, key)


def send_reset_email(email, username, key):
    html_content = f'''
<p>Hello {username}!</p>
<p>It seems you've forgotten your password. To reset your password please visit the following link:</p>
<a href="{os.getenv('FRONTEND_URL')}/reset-password?token={key}" target="_blank">{os.getenv('FRONTEND_URL')}/reset-password?token={key}</a>
'''
    text_content = ""
    subject = "Proof Buddy - Reset Your Password"
    from_email = os.getenv('EMAIL_HOST_USER')
    to = email
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
    msg.attach_alternative(html_content, "text/html")
    msg.send()
