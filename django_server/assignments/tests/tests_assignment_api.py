from rest_framework.test import APITestCase
from rest_framework import status
from assignments.models import Course, Assignment
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()
due_date = timezone.now() + timedelta(days=30)

class AssignmentAPITests(APITestCase):
    def setUp(self):
        self.inst = User.objects.create_user(username='instructor', email='instructor@instructor.com', is_instructor=True)
        self.other_inst = User.objects.create_user(username='other', email='other@other.com', is_instructor=True)
        self.course = Course.objects.create(name="Math", instructor=self.inst, created_by=self.inst, is_active=True)
        self.assign = Assignment.objects.create(title="HW1", course=self.course, due_date=due_date, created_by=self.inst)

    def test_instructor_cannot_create_assignment_for_others_course(self):
        self.client.force_authenticate(user=self.other_inst)
        payload = {"title": "Hack", "course": self.course.id, "due_date": due_date}
        response = self.client.post('/api/v1/assignments/', payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_assignment_cascades(self):
        self.client.force_authenticate(user=self.inst)
        response = self.client.delete(f'/api/v1/assignments/assignments/detail/{self.assign.id}')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Assignment.objects.filter(id=self.assign.id).exists())