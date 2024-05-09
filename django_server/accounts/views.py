from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from .serializers import AccountSerializer
from .models import ActivateAccount, ResetPassword, send_activation_email

User = get_user_model()


@api_view(['POST'])
def signup(request):
    serializer = AccountSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'Account created!'}, status=status.HTTP_201_CREATED)

    error_messages = [str(error)
                      for errors in serializer.errors.values() for error in errors]

    error_message_string = ', '.join(error_messages).replace(
        '[', '').replace(']', '').replace("'", "")

    return Response({'message': error_message_string}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def login(request):
    try:
        user = User.objects.get(username=request.data['username'])
    except User.DoesNotExist:
        return Response({'message': 'Invalid username/password'}, status=status.HTTP_404_NOT_FOUND)
    if user.check_password(request.data['password']):
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'accessToken': token.key, 'username': user.username}, status=status.HTTP_200_OK)
    return Response({'message': 'Invalid username/password'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_user(request):
    try:
        user = User.objects.get(username=request.user)
    except User.DoesNotExist:
        return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    return Response({'username': user.username, 'email': user.email}, status=status.HTTP_200_OK)


@api_view(['POST'])
def activate_account(request):
    activation_key = request.data['activation_key']
    try:
        account = ActivateAccount.objects.get(activation_key=activation_key)
    except ActivateAccount.DoesNotExist:
        return Response({'message': 'Invalid activation key'}, status=status.HTTP_404_NOT_FOUND)
    account.user.is_active = True
    account.user.save()
    account.delete()
    return Response({'message': 'Account activated'}, status=status.HTTP_200_OK)


@api_view(['POST'])
def forgot_password(request):
    try:
        user = User.objects.get(email=request.data['email'])
    except User.DoesNotExist:
        return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    try:
        ResetPassword.objects.get(user=user).delete()
    except ResetPassword.DoesNotExist:
        ResetPassword.objects.create(user=user)

    return Response({'message': 'Email sent'}, status=status.HTTP_200_OK)


@api_view(['POST'])
def reset_password(request):
    try:
        reset = ResetPassword.objects.get(reset_key=request.data['reset_key'])
    except ResetPassword.DoesNotExist:
        return Response({'message': 'Invalid activation key'}, status=status.HTTP_404_NOT_FOUND)
    user = reset.user
    user.set_password(request.data['password'])
    user.save()
    reset.delete()
    return Response({'message': 'Password reset'}, status=status.HTTP_200_OK)

@api_view(['POST'])
def resend_activation_email(request):
    try:
        user = User.objects.get(email=request.data['email'])
    except User.DoesNotExist:
        return Response({'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    try:
        activation = ActivateAccount.objects.get(user=user)
        email = user.email
        username = user.username
        key = activation.activation_key
        
        send_activation_email(email, username, key)
    except ActivateAccount.DoesNotExist:
        ActivateAccount.objects.create(user=user)
    return Response({'message': 'Email sent'}, status=status.HTTP_200_OK)