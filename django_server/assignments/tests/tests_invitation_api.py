from rest_framework.test import APITestCase
from assignments.models import Course, CourseInvitation
from django.contrib.auth import get_user_model

User = get_user_model()

class InvitationTests(APITestCase):
    def setUp(self):
        self.inst = User.objects.create_user(username='instructor', email='instructor@instructor.com', is_instructor=True)
        self.stu = User.objects.create_user(username='student', email='student@student.com')
        self.course = Course.objects.create(
            name="Calc", 
            instructor=self.inst, 
            created_by=self.inst, 
            is_active=True)
        self.invite = CourseInvitation.objects.create(course=self.course, student=self.stu)

    def test_student_can_accept_invitation(self):
        self.client.force_authenticate(user=self.stu)
        response = self.client.post('/api/v1/assignments/invitations/me', {
            "invitation_id": self.invite.id,
            "action": "accept"
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.stu, self.course.students.all())
        self.assertFalse(CourseInvitation.objects.filter(id=self.invite.id).exists())

    def test_student_can_reject_invitation(self):
        self.client.force_authenticate(user=self.stu)
        self.client.post('/api/v1/assignments/invitations/me', {
            "invitation_id": self.invite.id,
            "action": "reject"
        })
        self.invite.refresh_from_db()
        self.assertEqual(self.invite.status, 'rejected')