import hashlib
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from parameterized import parameterized

# Import your Course model (adjust the path if needed)
from assignments.models import Course, CourseInvitation

User = get_user_model()

class PermissionTests(APITestCase):
    def setUp(self):
        """Run once before every single test to set up fresh database state."""
        # 1. Create an Instructor
        self.instructor = User.objects.create_user(
            username='instructor', 
            email='321cba@gmail.com',
            password='password', 
            is_instructor=True
        )
        
        # 2. Create Students
        self.student = User.objects.create_user(
            username='student', 
            email='abc123@gmail.com',
            password='password', 
            is_instructor=False
        )
        
        # 3. Create a Course with an active Join Code
        self.raw_code = "ABC12345"
        hashed_code = hashlib.sha256(self.raw_code.encode('utf-8')).hexdigest()
        
        self.course = Course.objects.create(
            name='Discrete Math 101',
            instructor=self.instructor,
            created_by=self.instructor,
            is_active=True,
            join_code_hash=hashed_code,
            join_code_expires_at=timezone.now() + timedelta(days=1)
        )
        self.course.students.add(self.student)

    def test_student_cannot_access_inactive_course(self):
        """Verify the 403 logic for students when a course is toggled off."""
        self.course.is_active = False
        self.course.save()
        
        self.client.force_authenticate(user=self.student)
        detail_url = f'/api/v1/assignments/courses/{self.course.id}'
        
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_instructor_can_access_inactive_course(self):
        """Verify instructor is NOT blocked by the 403 logic."""
        self.course.is_active = False
        self.course.save()
        
        self.client.force_authenticate(user=self.instructor)
        detail_url = f'/api/v1/assignments/courses/{self.course.id}'
        
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
