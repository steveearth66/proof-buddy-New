from .models import Assignment, AssignmentSubmission, Term
from .serializers import AssignmentSerializer, AssignmentSubmissionSerializer, TermSerializer, CreateTermSerializer
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# Create your views here.

class TermViewSet(APIView):
    def get(self, request):
        terms = Term.objects.all()
        serializer = TermSerializer(terms, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        if not request.user.is_instructor:
            return Response({"message": "You are not authorized to create a term"}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = CreateTermSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            term = serializer.save(request.data)
            return Response(term, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AssignmentViewSet(APIView):
    def get(self, request):
        assignments = Assignment.objects.all()
        serializer = AssignmentSerializer(assignments, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        if not request.user.is_instructor:
            return Response({"message": "You are not authorized to create an assignment"}, status=status.HTTP_403_FORBIDDEN)

        serializer = AssignmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)