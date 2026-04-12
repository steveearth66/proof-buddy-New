from .models import Assignment, AssignmentSubmission, Course
from .serializers import AssignmentSerializer, AssignmentSubmissionSerializer, CourseSerializer, CreateCourseSerializer, CreateAssignmentSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth import get_user_model
import hashlib
import secrets
import string
from datetime import timedelta
from django.utils import timezone

User = get_user_model()

# Create your views here.

class CourseViewSet(APIView):
    permission_classes = [permissions.IsAuthenticated]
    # GET /courses/course_id
    # GET /courses/
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

        if kwargs.get("course_id"):
            try:
                course = Course.objects.get(id=kwargs.get("course_id"))
            except Course.DoesNotExist:
                return Response({"message": "Course not found"}, status=status.HTTP_404_NOT_FOUND)

            if not (user.is_instructor and course.instructor == user) and user not in course.students.all() and not user.is_superuser:
                return Response({"message": "You are not authorized to view this course."}, status=status.HTTP_403_FORBIDDEN)

            serializer = CourseSerializer(course, context={"request": request})
            return Response(serializer.data, status=status.HTTP_200_OK)

        courses = Course.objects.filter(instructor=user) if user.is_instructor else Course.objects.filter(students=user)
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # POST /courses/
    # e.g. post data
    """
        {
            "name": "Test 4",
            "students": ["pryceja"] # a list of students username or email
        }
    """
    def post(self, request):
        if not (request.user.is_instructor or request.user.is_superuser):
            return Response({"message": "You are not authorized to create a course"}, status=status.HTTP_403_FORBIDDEN)

        serializer = CreateCourseSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            course = serializer.save()
            return Response(course, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, *args, **kwargs):
        course_id = kwargs.get("course_id")
        
        if not course_id:
            return Response({"message": "Course ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response({"message": "Course not found"}, status=status.HTTP_404_NOT_FOUND)

        if not request.user.is_superuser and course.instructor != request.user:
            return Response({"message": "You are not authorized to manage this course."}, status=status.HTTP_403_FORBIDDEN)

        # ROUTE 1: Regenerate Join Code
        if request.data.get("action") == "regenerate_code":
            raw_code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            course.join_code_hash = hashlib.sha256(raw_code.encode('utf-8')).hexdigest()
            course.join_code_expires_at = timezone.now() + timedelta(days=7)
            course.save()
            return Response({
                "join_code": raw_code,
                "join_code_expires_at": course.join_code_expires_at
            }, status=status.HTTP_200_OK)

        # ROUTE 2: Standard Field Updates (like is_active)
        if "is_active" in request.data:
            course.is_active = request.data.get("is_active")
            course.save()
            
        # Return the updated course data for standard updates
        serializer = CourseSerializer(course, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

class AssignmentViewSet(APIView):
    permission_classes = [permissions.IsAuthenticated]
    # GET /assignments/course_id
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
    def get(self, request, course_id):
        user = request.user

        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response({"message": "Course not found"}, status=status.HTTP_404_NOT_FOUND)

        if not (user.is_instructor and course.instructor == user) and user not in course.students.all() and not user.is_superuser:
            return Response({"message": "You are not authorized to view any assignments for this course."}, status=status.HTTP_403_FORBIDDEN)

        assignments = Assignment.objects.filter(course=course)
        serializer = AssignmentSerializer(assignments, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    # POST /assignments/
    # e.g. post data
    """
    {
        "title": "Test 7",
        "description": "test assignment",
        "due_date": "2024-12-12",
        "course": 55
    }
    """
    def post(self, request):
        if not (request.user.is_instructor or request.user.is_superuser):
            return Response({"message": "You are not authorized to create an assignment"}, status=status.HTTP_403_FORBIDDEN)

        course_id = request.data.get("course")
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response({"message": "Course not found"}, status=status.HTTP_404_NOT_FOUND)
        
        if not request.user.is_superuser and course.instructor != request.user:
            return Response({"message": "You can only create assignments for your own courses."}, status=status.HTTP_403_FORBIDDEN)

        serializer = CreateAssignmentSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            assignment = AssignmentSerializer(
                serializer.instance, context={"request": request}
            ).data
            return Response(assignment, status=status.HTTP_201_CREATED)
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


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def remove_student(request):
    data = request.data
    course = data.get("course")
    student = data.get("student")

    try:
        course = Course.objects.get(id=course)
    except Course.DoesNotExist:
        return Response({"message": "Course not found"}, status=status.HTTP_404_NOT_FOUND)

    if (
        not (request.user.is_instructor and course.instructor == request.user)
        and not request.user.is_superuser
    ):
        return Response(
            {"message": "You are not authorized to remove a student from this course."},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        student = (
            User.objects.get(username=student)
            if "@" not in student
            else User.objects.get(email=student)
        )
    except User.DoesNotExist:
        return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    course.students.remove(student)
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def add_student(request):
    data = request.data
    course = data.get("course")
    student = data.get("student")

    try:
        course = Course.objects.get(id=course)
    except Course.DoesNotExist:
        return Response({"message": "Course not found"}, status=status.HTTP_404_NOT_FOUND)

    if (
        not (request.user.is_instructor and course.instructor == request.user)
        and not request.user.is_superuser
    ):
        return Response(
            {"message": "You are not authorized to add a student to this course."},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        student = (
            User.objects.get(username=student)
            if "@" not in student
            else User.objects.get(email=student)
        )
    except User.DoesNotExist:
        return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    course.students.add(student)
    data = CourseSerializer(course).data
    return Response(data, status=status.HTTP_200_OK)
