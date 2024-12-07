from .models import Assignment, AssignmentSubmission, Term
from .serializers import AssignmentSerializer, AssignmentSubmissionSerializer, TermSerializer, CreateTermSerializer, CreateAssignmentSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth import get_user_model

User = get_user_model()

# Create your views here.

class TermViewSet(APIView):
    permission_classes = [permissions.IsAuthenticated]
    # GET /terms/term_id
    # GET /terms/
    """
        [
            {
                "id": 42,
                "name": "Test 2",
                "instructor": {
                    "id": 3,
                    "email": "testmail@mail.com",
                    "username": "int566",
                    "first_name": "John",
                    "last_name": "Instructor"
                },
                "students": [
                    {
                        "id": 4,
                        "email": "teststu@mail.com",
                        "username": "test22",
                        "first_name": "John",
                        "last_name": "Test"
                    }
                ],
                "created_by": {
                    "id": 3,
                    "email": "testmail@mail.com",
                    "username": "int566",
                    "first_name": "John",
                    "last_name": "Instructor"
                }
            }
        ]
    """
    def get(self, request, *args, **kwargs):
        user = request.user

        if kwargs.get("term_id"):
            try:
                term = Term.objects.get(id=kwargs.get("term_id"))
            except Term.DoesNotExist:
                return Response({"message": "Term not found"}, status=status.HTTP_404_NOT_FOUND)

            if not (user.is_instructor and term.instructor == user) and user not in term.students.all() and not user.is_superuser:
                return Response({"message": "You are not authorized to view this term."}, status=status.HTTP_403_FORBIDDEN)

            serializer = TermSerializer(term, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        terms = Term.objects.filter(instructor=user) if user.is_instructor else Term.objects.filter(students=user)
        serializer = TermSerializer(terms, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # POST /terms/
    # e.g. post data
    """
        {
            "name": "Test 4",
            "students": ["pryceja"] # a list of students username or email
        }
    """
    def post(self, request):
        if not (request.user.is_instructor or request.user.is_superuser):
            return Response({"message": "You are not authorized to create a term"}, status=status.HTTP_403_FORBIDDEN)

        serializer = CreateTermSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            term = serializer.save(request.data)
            return Response(term, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AssignmentViewSet(APIView):
    permission_classes = [permissions.IsAuthenticated]
    # GET /assignments/term_id
    """
        [
            {
                "id": 6,
                "title": "Test 2",
                "description": "Lorem ipsum dolor sit amet, consectetur",
                "due_date": "2024-12-12T00:00:00-05:00",
                "submissions": [
                    {
                        "id": 5,
                        "student": {
                            "id": 1,
                            "email": "javanpryce1@gmail.com",
                            "username": "pryceja",
                            "first_name": "Javan",
                            "last_name": "Test"
                        },
                        "submission_date": "2024-12-01T20:13:42.764919-05:00",
                        "proofs": [
                            14,
                            30,
                            33
                        ],
                        "grade": 0.0
                    }
                ],
                "created_by": {
                    "id": 2,
                    "email": "admin@localhost",
                    "username": "admin",
                    "first_name": "",
                    "last_name": ""
                }
            }
        ]
    """
    def get(self, request, term_id):
        user = request.user

        try:
            term = Term.objects.get(id=term_id)
        except Term.DoesNotExist:
            return Response({"message": "Term not found"}, status=status.HTTP_404_NOT_FOUND)

        if not (user.is_instructor and term.instructor == user) and user not in term.students.all() and not user.is_superuser:
            return Response({"message": "You are not authorized to view any assignments for this term."}, status=status.HTTP_403_FORBIDDEN)

        assignments = Assignment.objects.filter(term=term)
        serializer = AssignmentSerializer(assignments, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    # POST /assignments/
    # e.g. post data
    """
    {
        "title": "Test 7",
        "description": "test assignment",
        "due_date": "2024-12-12",
        "term": 55
    }
    """
    def post(self, request):
        if not (request.user.is_instructor or not request.user.is_superuser):
            return Response({"message": "You are not authorized to create an assignment"}, status=status.HTTP_403_FORBIDDEN)

        serializer = CreateAssignmentSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def check_user(request):
    data = request.data
    student = data.get("student")

    try:
        User.objects.get(username=student) if "@" not in student else User.objects.get(email=student)
        return Response(status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
