"""
Tests for the Set Parameters feature on InductionProof.

Covers:
  Step 1: Model has 6 support param fields with BooleanField(default=True)
  Step 2: PATCH /api/v1/induction/set-parameters endpoint access control and behaviour

DO NOT register in proofs/tests.py until Steps 1 and 2 are implemented.

Run individually:
  $env:PYTHONIOENCODING="utf-8"; py manage.py test induction_api.test_set_parameters
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from induction_api.models import InductionProof

User = get_user_model()

PARAM_FIELDS = [
    'support_errors',
    'support_current_lhs_rhs',
    'support_ih',
    'support_premise',
    'support_rule_set',
    'support_value_mapping',
]

PROOF_DEFAULTS = dict(
    induction_variable='n',
    anchor_value='0',
    leap_variable='k',
    lhs_anchor_goal='(f 0)',
    rhs_anchor_goal='0',
)


# ===========================================================
# Step 1: Model field defaults
# ===========================================================

class InductionProofParamModelTests(TestCase):
    """Verify InductionProof model has all 6 support param fields defaulting to True."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def _make_proof(self, **kwargs):
        params = dict(user=self.user, **PROOF_DEFAULTS)
        params.update(kwargs)
        return InductionProof.objects.create(**params)

    def test_all_param_fields_default_to_true(self):
        """All 6 support fields should default to True (high support)."""
        proof = self._make_proof()
        for field in PARAM_FIELDS:
            value = getattr(proof, field, 'MISSING')
            self.assertIs(
                value, True,
                f"Expected {field} to default to True; got {value!r}"
            )

    def test_param_fields_can_be_set_low(self):
        """All 6 support fields can be set to False and persisted."""
        proof = self._make_proof()
        for field in PARAM_FIELDS:
            setattr(proof, field, False)
        proof.save()
        proof.refresh_from_db()
        for field in PARAM_FIELDS:
            self.assertFalse(
                getattr(proof, field),
                f"{field} should persist as False after save"
            )

    def test_param_fields_are_independent(self):
        """Setting one field low does not affect the others."""
        proof = self._make_proof(support_errors=False)
        self.assertFalse(proof.support_errors)
        for field in PARAM_FIELDS:
            if field != 'support_errors':
                self.assertTrue(
                    getattr(proof, field),
                    f"{field} should still be True when only support_errors was set False"
                )

    def test_mixed_creation_persists_correctly(self):
        """Mixed high/low values set at creation time persist correctly."""
        proof = self._make_proof(
            support_errors=False,
            support_current_lhs_rhs=False,
            support_ih=True,
            support_premise=True,
            support_rule_set=False,
            support_value_mapping=True,
        )
        proof.refresh_from_db()
        self.assertFalse(proof.support_errors)
        self.assertFalse(proof.support_current_lhs_rhs)
        self.assertTrue(proof.support_ih)
        self.assertTrue(proof.support_premise)
        self.assertFalse(proof.support_rule_set)
        self.assertTrue(proof.support_value_mapping)


# ===========================================================
# Step 2: API endpoint
# ===========================================================

class InductionSetParametersAPITests(TestCase):
    """Verify PATCH /api/v1/induction/set-parameters endpoint."""

    def setUp(self):
        # Instructor user
        self.instructor = User.objects.create_user(
            username='instructor',
            email='instructor@test.com',
            password='testpass123',
            is_instructor=True
        )
        self.instr_token = Token.objects.create(user=self.instructor)
        self.instr_client = APIClient()
        self.instr_client.credentials(HTTP_AUTHORIZATION=f'Token {self.instr_token.key}')

        # Student user
        self.student = User.objects.create_user(
            username='student',
            email='student@test.com',
            password='testpass123',
            is_instructor=False
        )
        self.student_token = Token.objects.create(user=self.student)
        self.student_client = APIClient()
        self.student_client.credentials(HTTP_AUTHORIZATION=f'Token {self.student_token.key}')

        # Proof owned by instructor
        self.proof = InductionProof.objects.create(
            user=self.instructor,
            name='Test Proof',
            tag='test',
            **PROOF_DEFAULTS
        )

    def _payload(self, **overrides):
        """Build a complete set-parameters payload."""
        base = {
            'proof_id': self.proof.id,
            'support_errors': True,
            'support_current_lhs_rhs': True,
            'support_ih': True,
            'support_premise': True,
            'support_rule_set': True,
            'support_value_mapping': True,
        }
        base.update(overrides)
        return base

    def test_instructor_can_set_all_fields_low(self):
        """Instructor sets all 6 fields to False; DB is updated."""
        payload = self._payload(**{f: False for f in PARAM_FIELDS})
        response = self.instr_client.patch(
            '/api/v1/induction/set-parameters', payload, format='json'
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.proof.refresh_from_db()
        for field in PARAM_FIELDS:
            self.assertFalse(getattr(self.proof, field), f"{field} should be False in DB")

    def test_instructor_can_set_mixed_values(self):
        """Instructor can independently set a subset of fields."""
        payload = self._payload(support_errors=False, support_rule_set=False)
        response = self.instr_client.patch(
            '/api/v1/induction/set-parameters', payload, format='json'
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.proof.refresh_from_db()
        self.assertFalse(self.proof.support_errors)
        self.assertFalse(self.proof.support_rule_set)
        self.assertTrue(self.proof.support_ih)
        self.assertTrue(self.proof.support_premise)
        self.assertTrue(self.proof.support_current_lhs_rhs)
        self.assertTrue(self.proof.support_value_mapping)

    def test_student_is_forbidden(self):
        """Students receive 403 when trying to call set-parameters."""
        student_proof = InductionProof.objects.create(
            user=self.student,
            **PROOF_DEFAULTS
        )
        payload = self._payload(proof_id=student_proof.id, support_errors=False)
        response = self.student_client.patch(
            '/api/v1/induction/set-parameters', payload, format='json'
        )
        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_is_rejected(self):
        """Unauthenticated requests receive 401."""
        unauth = APIClient()
        response = unauth.patch(
            '/api/v1/induction/set-parameters', self._payload(), format='json'
        )
        self.assertEqual(response.status_code, 401)

    def test_proof_not_found_returns_404(self):
        """Non-existent or other-user proof_id returns 404."""
        payload = self._payload(proof_id=99999)
        response = self.instr_client.patch(
            '/api/v1/induction/set-parameters', payload, format='json'
        )
        self.assertEqual(response.status_code, 404)

    def test_response_includes_all_param_fields(self):
        """Successful response body includes all 6 support param fields."""
        response = self.instr_client.patch(
            '/api/v1/induction/set-parameters', self._payload(), format='json'
        )
        self.assertEqual(response.status_code, 200)
        for field in PARAM_FIELDS:
            self.assertIn(field, response.data, f"Response missing field: {field}")

    def test_response_values_match_db(self):
        """Response param values match what was actually saved to DB."""
        payload = self._payload(support_errors=False, support_ih=False)
        response = self.instr_client.patch(
            '/api/v1/induction/set-parameters', payload, format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.proof.refresh_from_db()
        for field in PARAM_FIELDS:
            self.assertEqual(
                response.data[field], getattr(self.proof, field),
                f"Response value for {field} does not match DB"
            )
