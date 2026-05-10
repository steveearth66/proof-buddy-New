from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from assignments.models import Course, Assignment, StudentProofMapping, AssignmentProof
from equational_reasoning_api.models import EquationalProof, EquationalProofLine
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from datetime import timedelta

User = get_user_model()
due_date = timezone.now() + timedelta(days=30)

class ProofCloningTests(APITestCase):
    def setUp(self):
        self.student = User.objects.create_user(username='student', email='student@student.com')
        self.inst = User.objects.create_user(username='instructor', email='instructor@instructor.com', is_instructor=True)
        self.course = Course.objects.create(name="Logic", instructor=self.inst, created_by=self.inst, is_active=True)
        self.course.students.add(self.student)

        # Create a Template Proof with lines
        self.template = EquationalProof.objects.create(name="Template", user=None)
        EquationalProofLine.objects.create(proof=self.template, rule='PREMISE', racket='LHS = RHS', line_number=0)
        
        self.assignment = Assignment.objects.create(title="Proof HW", course=self.course, due_date=due_date, created_by=self.inst)
        self.assignmentProof = AssignmentProof.objects.create(assignment=self.assignment, content_type=ContentType.objects.get(app_label='equational_reasoning_api', model='equationalproof'), object_id=self.template.id)

    def test_start_proof_creates_deep_clone_and_mapping(self):
        self.client.force_authenticate(user=self.student)
        payload = {
            "proof_id": self.template.id,
            "proof_type": "equationalproof"
        }
        response = self.client.post(f'/api/v1/assignments/assignments/{self.assignment.id}/start-assignment-proof', payload)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_id = response.data['new_proof_id']
        
        # Verify Clone Existence
        clone = EquationalProof.objects.get(id=new_id)
        self.assertEqual(clone.user, self.student)
        self.assertIn("(Assignment Copy)", clone.name)
        
        # Verify Lines Cloned
        self.assertEqual(clone.proof_lines.count(), 1)
        
        # Verify Mapping
        self.assertTrue(StudentProofMapping.objects.filter(assignment=self.assignment, student=self.student).exists())

    def test_restarting_proof_returns_existing_clone(self):
        # Run once to create clone
        self.client.force_authenticate(user=self.student)
        payload = {"proof_id": self.template.id, "proof_type": "equationalproof"}
        first_resp = self.client.post(f'/api/v1/assignments/assignments/{self.assignment.id}/start-assignment-proof', payload)
        
        # Run again
        second_resp = self.client.post(f'/api/v1/assignments/assignments/{self.assignment.id}/start-assignment-proof', payload)
        self.assertEqual(second_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(first_resp.data['new_proof_id'], second_resp.data['new_proof_id'])