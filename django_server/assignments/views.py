from .models import Assignment, AssignmentSubmission, Term
from .serializers import AssignmentSerializer, AssignmentSubmissionSerializer, TermSerializer, CreateTermSerializer
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

# Create your views here.

class TermViewSet(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        terms = Term.objects.filter(instructor=user) if user.is_instructor else Term.objects.filter(students=user)
        serializer = TermSerializer(terms, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        if not request.user.is_instructor or not request.user.is_superuser:
            return Response({"message": "You are not authorized to create a term"}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = CreateTermSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            term = serializer.save(request.data)
            return Response(term, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AssignmentViewSet(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, term_id):
        user = request.user

        try:
            term = Term.objects.get(id=term_id)
        except Term.DoesNotExist:
            return Response({"message": "Term not found"}, status=status.HTTP_404_NOT_FOUND)

        if not (user.is_instructor and term.instructor == user) and user not in term.students.all() and not user.is_superuser:
            return Response({"message": "You are not authorized to view this assignment"}, status=status.HTTP_403_FORBIDDEN)
        
        assignments = Assignment.objects.filter(term=term)
        serializer = AssignmentSerializer(assignments, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        if not request.user.is_instructor or not request.user.is_superuser:
            return Response({"message": "You are not authorized to create an assignment"}, status=status.HTTP_403_FORBIDDEN)

        serializer = AssignmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)