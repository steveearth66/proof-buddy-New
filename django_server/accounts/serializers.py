import django.contrib.auth.password_validation as validators
from rest_framework import serializers
from .models import Account


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['email', 'username', 'password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate_password(self, value):
        try:
            validators.validate_password(value)
        except serializers.ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate_email(self, value):
        if Account.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already exists')
        return value

    def validate_username(self, value):
        if Account.objects.filter(username=value).exists():
            raise serializers.ValidationError('Username already exists')
        return value

    def validate_confirm_password(self, value):
        if self.initial_data['password'] != value:
            raise serializers.ValidationError('Passwords do not match')
        return value

    def create(self, validated_data):
        user = Account.objects.create_user(**validated_data)
        user.save()
        return user
