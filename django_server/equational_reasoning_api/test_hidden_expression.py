"""
Tests for the hidden/visible definition expression feature (Steps 1-16).

Covers:
  - Definition model has expression_hidden field
  - DefinitionSerializer includes expression_hidden
  - proofs/views.py helper functions (create, get, edit, list)
  - validate_hidden_definition endpoint (ER): Case A match, Case A mismatch, Case B student-entry
  - get_proof_lines masks expression for students
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from django.core.cache import cache
from dill import dumps

from equational_reasoning_api.models import EquationalProof
from expression_tree.ERProofEngine import TwoSidedProof
from proofs.models import Definition
from proofs.serializers import DefinitionSerializer
from proofs.views import (
    create_user_definition,
    get_user_definitions,
    get_definition,
    edit_definition,
)

User = get_user_model()


def _make_cache_entry(proof_obj, proof_id):
    return {'proof_obj': dumps(proof_obj), 'proof_id': proof_id}


class DefinitionModelFieldTest(TestCase):
    """Step 1-2: expression_hidden field exists on Definition model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='fieldtest', email='fieldtest@test.com', password='pass'
        )

    def test_expression_hidden_default_false(self):
        d = Definition.objects.create(
            label='f', def_type='int', expression='(+ 1 1)', created_by=self.user
        )
        self.assertFalse(d.expression_hidden)

    def test_expression_hidden_can_be_true(self):
        d = Definition.objects.create(
            label='g', def_type='int', expression='(+ 2 2)',
            expression_hidden=True, created_by=self.user
        )
        self.assertTrue(d.expression_hidden)


class DefinitionSerializerTest(TestCase):
    """Step 3: DefinitionSerializer includes expression_hidden."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='sertest', email='sertest@test.com', password='pass'
        )

    def test_serializer_includes_expression_hidden(self):
        d = Definition.objects.create(
            label='h', def_type='int', expression='(+ 3 3)',
            expression_hidden=True, created_by=self.user
        )
        data = DefinitionSerializer(d).data
        self.assertIn('expression_hidden', data)
        self.assertTrue(data['expression_hidden'])

    def test_serializer_expression_hidden_false(self):
        d = Definition.objects.create(
            label='i', def_type='int', expression='(+ 4 4)', created_by=self.user
        )
        data = DefinitionSerializer(d).data
        self.assertIn('expression_hidden', data)
        self.assertFalse(data['expression_hidden'])


class DefinitionHelperFunctionsTest(TestCase):
    """Step 4: proofs/views.py helper functions handle expression_hidden."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='helpertest', email='helpertest@test.com', password='pass'
        )

    def test_create_user_definition_saves_expression_hidden_true(self):
        result = create_user_definition(self.user, {
            'label': 'myFunc',
            'type': 'int',
            'expression': '(+ 1 2)',
            'expression_hidden': True,
            'notes': '',
        })
        self.assertIsNotNone(result)
        db_def = Definition.objects.get(label='myFunc', created_by=self.user)
        self.assertTrue(db_def.expression_hidden)

    def test_create_user_definition_defaults_expression_hidden_false(self):
        result = create_user_definition(self.user, {
            'label': 'myFunc2',
            'type': 'int',
            'expression': '(+ 2 3)',
            'notes': '',
        })
        self.assertIsNotNone(result)
        db_def = Definition.objects.get(label='myFunc2', created_by=self.user)
        self.assertFalse(db_def.expression_hidden)

    def test_get_user_definitions_includes_expression_hidden(self):
        Definition.objects.create(
            label='visFunc', def_type='int', expression='(+ 5 5)',
            expression_hidden=False, created_by=self.user
        )
        Definition.objects.create(
            label='hidFunc', def_type='int', expression='(+ 6 6)',
            expression_hidden=True, created_by=self.user
        )
        defs = get_user_definitions(self.user)
        user_defs = [d for d in defs if not d.get('is_default')]
        labels = {d['label']: d for d in user_defs}
        self.assertIn('expression_hidden', labels['visFunc'])
        self.assertFalse(labels['visFunc']['expression_hidden'])
        self.assertIn('expression_hidden', labels['hidFunc'])
        self.assertTrue(labels['hidFunc']['expression_hidden'])

    def test_get_definition_includes_expression_hidden(self):
        Definition.objects.create(
            label='getFunc', def_type='int', expression='(+ 7 7)',
            expression_hidden=True, created_by=self.user
        )
        result = get_definition(self.user, 'getFunc')
        self.assertIsNotNone(result)
        self.assertIn('expression_hidden', result)
        self.assertTrue(result['expression_hidden'])

    def test_edit_definition_updates_expression_hidden(self):
        Definition.objects.create(
            label='editFunc', def_type='int', expression='(+ 8 8)',
            expression_hidden=False, created_by=self.user
        )
        result = edit_definition(self.user, 'editFunc', {
            'label': 'editFunc',
            'type': 'int',
            'expression': '(+ 8 8)',
            'expression_hidden': True,
            'notes': '',
        })
        self.assertIsNotNone(result)
        db_def = Definition.objects.get(label='editFunc', created_by=self.user)
        self.assertTrue(db_def.expression_hidden)


class ValidateHiddenDefinitionERTest(TestCase):
    """Steps 6-7: validate_hidden_definition endpoint for ER pipeline."""

    def setUp(self):
        self.student = User.objects.create_user(
            username='student_er', email='s@test.com', password='pass',
            is_instructor=False
        )
        self.token = Token.objects.create(user=self.student)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        # Create an EquationalProof in the DB with hidden definitions
        self.proof = EquationalProof.objects.create(
            user=self.student,
            lhs_goal='(+ 1 2)',
            rhs_goal='3',
            definition=[
                {
                    'label': 'double',
                    'type': 'int',
                    'expression': '(* 2 x)',
                    'expression_hidden': True,
                    'is_generic': False,
                    'applied': True,
                },
                {
                    'label': 'mystery',
                    'type': 'int',
                    'expression': '',
                    'expression_hidden': True,
                    'is_generic': False,
                    'applied': True,
                },
            ]
        )
        # Put a TwoSidedProof in cache pointing to this proof
        proof_obj = TwoSidedProof()
        cache.set(
            f'equational_obj_{self.student.username}',
            _make_cache_entry(proof_obj, self.proof.id),
            timeout=None
        )

    def tearDown(self):
        cache.delete(f'equational_obj_{self.student.username}')

    def test_case_a_correct_expression_returns_valid(self):
        """Case A: student enters the correct expression (tree match)."""
        response = self.client.post(
            '/api/v1/equational/validate-hidden-definition',
            {'label': 'double', 'student_expression': '(* 2 x)'},
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['isValid'])
        self.assertEqual(response.data['expression'], '(* 2 x)')

    def test_case_a_wrong_expression_returns_invalid(self):
        """Case A: student enters a wrong expression (tree mismatch)."""
        response = self.client.post(
            '/api/v1/equational/validate-hidden-definition',
            {'label': 'double', 'student_expression': '(+ x x)'},
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['isValid'])
        self.assertIn('does not match', response.data['message'])

    def test_case_b_student_entry_accepts_any_valid_expression(self):
        """Case B: definition has no expression; any valid parse is accepted."""
        response = self.client.post(
            '/api/v1/equational/validate-hidden-definition',
            {'label': 'mystery', 'student_expression': '(+ n 1)'},
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['isValid'])
        self.assertEqual(response.data['expression'], '(+ n 1)')
        # Check DB was updated
        self.proof.refresh_from_db()
        mystery_def = next(d for d in self.proof.definition if d['label'] == 'mystery')
        self.assertEqual(mystery_def['expression'], '(+ n 1)')

    def test_syntax_error_in_student_expression(self):
        """Invalid expression should return isValid=False."""
        response = self.client.post(
            '/api/v1/equational/validate-hidden-definition',
            {'label': 'double', 'student_expression': '(+ 1'},
            format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data['isValid'])

    def test_missing_parameters_returns_400(self):
        """Missing label or student_expression should return 400."""
        response = self.client.post(
            '/api/v1/equational/validate-hidden-definition',
            {'label': 'double'},
            format='json'
        )
        self.assertEqual(response.status_code, 400)

    def test_definition_not_found_returns_400(self):
        """Non-existent label should return 400."""
        response = self.client.post(
            '/api/v1/equational/validate-hidden-definition',
            {'label': 'nonexistent', 'student_expression': '(+ 1 2)'},
            format='json'
        )
        self.assertEqual(response.status_code, 400)


class GetProofLinesMaskingTest(TestCase):
    """Step 8: get_proof_lines masks expression for students but not instructors."""

    def setUp(self):
        self.instructor = User.objects.create_user(
            username='instr_mask', email='instr@test.com', password='pass',
            is_instructor=True
        )
        self.student = User.objects.create_user(
            username='stud_mask', email='stud@test.com', password='pass',
            is_instructor=False
        )
        hidden_def = {
            'label': 'secret',
            'type': 'int',
            'expression': '(* 3 x)',
            'expression_hidden': True,
            'is_generic': False,
            'applied': True,
        }
        # Student's proof
        self.stud_proof = EquationalProof.objects.create(
            user=self.student, lhs_goal='(+ 1 2)', rhs_goal='3',
            definition=[hidden_def]
        )
        # Instructor's own proof (same hidden def — instructor should see real expression)
        self.instr_proof = EquationalProof.objects.create(
            user=self.instructor, lhs_goal='(+ 1 2)', rhs_goal='3',
            definition=[hidden_def]
        )
        proof_obj = TwoSidedProof()
        cache.set(
            f'equational_obj_{self.student.username}',
            _make_cache_entry(proof_obj, self.stud_proof.id),
            timeout=None
        )
        cache.set(
            f'equational_obj_{self.instructor.username}',
            _make_cache_entry(proof_obj, self.instr_proof.id),
            timeout=None
        )
        self.stud_token = Token.objects.create(user=self.student)
        self.instr_token = Token.objects.create(user=self.instructor)

    def tearDown(self):
        cache.delete(f'equational_obj_{self.student.username}')
        cache.delete(f'equational_obj_{self.instructor.username}')

    def test_student_sees_masked_expression(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {self.stud_token.key}')
        response = client.get('/api/v1/equational/get-proof-lines')
        self.assertEqual(response.status_code, 200)
        defs = response.data.get('definitions', [])
        secret = next((d for d in defs if d.get('label') == 'secret'), None)
        self.assertIsNotNone(secret)
        self.assertEqual(secret['expression'], '****')

    def test_instructor_sees_real_expression(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {self.instr_token.key}')
        response = client.get('/api/v1/equational/get-proof-lines')
        self.assertEqual(response.status_code, 200)
        defs = response.data.get('definitions', [])
        secret = next((d for d in defs if d.get('label') == 'secret'), None)
        self.assertIsNotNone(secret)
        self.assertEqual(secret['expression'], '(* 3 x)')
