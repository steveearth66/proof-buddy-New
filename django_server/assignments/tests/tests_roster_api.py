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

class RosterAPITests(APITestCase):
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

        self.not_enrolled_student = User.objects.create_user(
            username='student2', 
            email='not_enrolled@gmail.com',
            password='password123', 
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
        
        # URLs for endpoints
        self.join_url = reverse('join-course')
        self.add_url = '/api/v1/assignments/add-student'
        self.remove_url = '/api/v1/assignments/remove-student'
        self.leave_url = reverse('leave-course') 

    def test_student_can_join_with_valid_code(self):
        """Test the end-to-end join course success path."""
        self.client.force_authenticate(user=self.not_enrolled_student)
        
        response = self.client.post(self.join_url, {"code": self.raw_code})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "Successfully joined the course!")
        self.assertIn(self.not_enrolled_student, self.course.students.all())

    @parameterized.expand([
        ("abc12345"),
        ("abcdefgh"),
        ("12345678"),
        ("WRONGCODE")
    ])
    def test_student_cannot_join_with_invalid_code(self, code):
        """Test that bad codes are rejected."""
        self.client.force_authenticate(user=self.not_enrolled_student)
        
        response = self.client.post(self.join_url, {"code": code})
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertNotIn(self.not_enrolled_student, self.course.students.all())

    def test_student_cannot_join_with_no_code(self):
        """Test that bad codes are rejected."""
        self.client.force_authenticate(user=self.not_enrolled_student)
        
        response = self.client.post(self.join_url, {})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn(self.not_enrolled_student, self.course.students.all())

    def test_instructor_can_add_student_by_username(self):
        """Test adding a student using their exact username."""
        self.client.force_authenticate(user=self.instructor)
        
        payload = {
            "course": self.course.id,
            "student": self.not_enrolled_student.username # Using username
        }
        
        response = self.client.post(self.add_url, payload)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.not_enrolled_student, self.course.students.all())

    def test_instructor_can_add_student_by_email(self):
        """Test adding a student using their email address."""
        self.client.force_authenticate(user=self.instructor)
        
        payload = {
            "course": self.course.id,
            "student": self.not_enrolled_student.email # Using email
        }
        
        response = self.client.post(self.add_url, payload)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.not_enrolled_student, self.course.students.all())

    def test_instructor_gets_conflict_if_more_than_one_student_has_email(self):
        """Test getting conflict message when adding a student using their 
        email address and finding more than 1."""
        self.client.force_authenticate(user=self.instructor)
        
        student_copy = User.objects.create_user(
            username='student_copy', 
            email='not_enrolled@gmail.com',
            password='password123!', 
            is_instructor=False
        )

        payload = {
            "course": self.course.id,
            "student": self.not_enrolled_student.email # Using email
        }
        
        response = self.client.post(self.add_url, payload)
        
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        candidates = response.data.get("candidates")
        self.assertEqual(len(candidates), 2)

        candidate_usernames = [c['username'] for c in candidates]
        self.assertIn(self.not_enrolled_student.username, candidate_usernames)
        self.assertIn(student_copy.username, candidate_usernames)
        self.assertNotIn(self.not_enrolled_student, self.course.students.all())
        self.assertNotIn(student_copy, self.course.students.all())


    def test_student_cannot_add_another_student(self):
        """Test that a 403 Forbidden is returned if a student tries to use this endpoint."""
        self.client.force_authenticate(user=self.student)
        
        payload = {"course": self.course.id, "student": self.not_enrolled_student.username}
        response = self.client.post(self.add_url, payload)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertNotIn(self.not_enrolled_student, self.course.students.all())

    def test_cannot_add_nonexistent_student(self):
        """Test that a 404 is returned for a bad username."""
        self.client.force_authenticate(user=self.instructor)
        
        payload = {"course": self.course.id, "student": "does_not_exist"}
        response = self.client.post(self.add_url, payload)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_instructor_can_remove_student(self):
        """Test that an instructor can manually drop a student."""
        self.client.force_authenticate(user=self.instructor)
        payload = {            
            "student": self.student.username,
            "course": self.course.id
        }
        
        response = self.client.post(self.remove_url, payload)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Verify the student is gone
        self.assertNotIn(self.student, self.course.students.all())

    def test_student_can_leave_course(self):
        """Test that a student can drop themselves from a course."""
        self.client.force_authenticate(user=self.student)
        payload = {
            "course": self.course.id
        }
        
        response = self.client.post(self.leave_url, payload)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify the student successfully removed themselves
        self.assertNotIn(self.student, self.course.students.all())

    def test_student_cannot_leave_course_not_enrolled_in(self):
        """Test that a student trying to drop themselves from a course does 
        nothing if they are not in the course."""
        self.client.force_authenticate(user=self.not_enrolled_student)

        payload = {
            "course": self.course.id
        }
        
        response = self.client.post(self.leave_url, payload)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
