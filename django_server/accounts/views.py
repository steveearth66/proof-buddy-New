from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
import django.contrib.auth.password_validation as validators
from .serializers import AccountSerializer

User = get_user_model()


@api_view(['POST'])
def signup(request):
    serializer = AccountSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'Account created!'}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def login(request):
    try:
        user = User.objects.get(username=request.data['username'])
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    if user.check_password(request.data['password']):
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'accessToken': token.key, 'username': user.username}, status=status.HTTP_200_OK)
    return Response({'error': 'Invalid password'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def logout(request):
    try:
        user = User.objects.get(username=request.data['username'])
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    token = Token.objects.get(user=user)
    token.delete()
    return Response({'message': 'User logged out'}, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_user(request):
    print(request.user)
    try:
        user = User.objects.get(username=request.user)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    return Response({'username': user.username, 'email': user.email}, status=status.HTTP_200_OK)
