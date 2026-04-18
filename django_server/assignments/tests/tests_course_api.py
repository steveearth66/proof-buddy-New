import hashlib
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from parameterized import parameterized

# Import your Course model (adjust the path if needed)
from assignments.models import Course 

User = get_user_model()

class CourseAPITests(APITestCase):
    def setUp(self):
        """Run once before every single test to set up fresh database state."""
        # 1. Create an Instructor
        self.instructor = User.objects.create_user(
            username='instructor', 
            email='321cba@gmail.com',
            password='password', 
            is_instructor=True
        )
        
        # 2. Create a Student
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
        
        # URLs for endpoints
        self.course_detail_url = f'/api/v1/assignments/courses/{self.course.id}' 

    @parameterized.expand([
        ("valid_winter", "Winter 2026"),
        ("valid_summer", "Summer 2099"),
        ("valid_spring", "Spring 2024"),
        ("valid_fall", "Fall 2015")
    ])
    def test_instructor_can_update_course_term(self, name, term):
        """Test the partial update logic using the serializer."""
        self.client.force_authenticate(user=self.instructor)
        
        response = self.client.patch(self.course_detail_url, {"term": term})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.course.refresh_from_db()
        self.assertEqual(self.course.term, term)

    @parameterized.expand([
        ("invalid_season", "Autumn 2026"),
        ("double_space", "Spring  2026"),
        ("short_year", "Fall 26"),
        ("missing_space", "Winter2026"),
        ("lowercase", "summer 2026"),
    ])
    def test_course_patch_rejects_bad_term(self, name, term):
        """Test that formatting protects the database."""
        self.client.force_authenticate(user=self.instructor)
        
        response = self.client.patch(self.course_detail_url, {"term": term})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("term", response.data)