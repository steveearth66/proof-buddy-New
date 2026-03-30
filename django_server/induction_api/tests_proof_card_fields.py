"""
Tests verifying that the get-induction-proofs endpoint returns the goal fields
needed for the proof card display feature (lhs_leap_goal, rhs_leap_goal, is_complete).

Run with:
    $env:PYTHONIOENCODING="utf-8"; py manage.py test induction_api.tests_proof_card_fields
"""

from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.core.cache import cache
from .models import InductionProof

User = get_user_model()

LIST_URL = '/api/v1/induction/get-induction-proofs/'


class ProofCardFieldsTest(TransactionTestCase):
    """Verify the list endpoint exposes goal and completion fields for proof cards."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='cardtest_user',
            email='cardtest@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        try:
            cache.clear()
        except Exception:
            pass

    def tearDown(self):
        try:
            cache.clear()
        except Exception:
            pass

    def _make_proof(self, name, complete=False):
        return InductionProof.objects.create(
            user=self.user,
            name=name,
            tag='lemma1',
            induction_variable='L',
            anchor_value='null',
            leap_variable='K',
            lhs_leap_goal='(reverse (reverse L))',
            rhs_leap_goal='L',
            lhs_anchor_goal='(reverse (reverse null))',
            rhs_anchor_goal='null',
            inductive_hypothesis_lhs='(reverse (reverse K))',
            inductive_hypothesis_rhs='K',
            induction_type='lists',
            is_complete=complete,
            is_active=True,
        )

    def test_list_response_includes_lhs_leap_goal(self):
        """Each proof dict in the list response must include lhs_leap_goal."""
        self._make_proof('testRevRev')
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        proofs = response.data.get('proofs', [])
        self.assertEqual(len(proofs), 1)
        self.assertIn('lhs_leap_goal', proofs[0])
        self.assertEqual(proofs[0]['lhs_leap_goal'], '(reverse (reverse L))')

    def test_list_response_includes_rhs_leap_goal(self):
        """Each proof dict in the list response must include rhs_leap_goal."""
        self._make_proof('testRevRev')
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        proofs = response.data.get('proofs', [])
        self.assertEqual(len(proofs), 1)
        self.assertIn('rhs_leap_goal', proofs[0])
        self.assertEqual(proofs[0]['rhs_leap_goal'], 'L')

    def test_list_response_includes_is_complete_false(self):
        """is_complete must be False for an incomplete proof."""
        self._make_proof('incompleteProof', complete=False)
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        proofs = response.data.get('proofs', [])
        self.assertEqual(len(proofs), 1)
        self.assertIn('is_complete', proofs[0])
        self.assertFalse(proofs[0]['is_complete'])

    def test_list_response_includes_is_complete_true(self):
        """is_complete must be True for a completed proof."""
        self._make_proof('completeProof', complete=True)
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        proofs = response.data.get('proofs', [])
        self.assertEqual(len(proofs), 1)
        self.assertIn('is_complete', proofs[0])
        self.assertTrue(proofs[0]['is_complete'])

    def test_is_complete_flag_distinguishes_proofs(self):
        """Two proofs with different is_complete values must return distinct flags."""
        self._make_proof('done', complete=True)
        self._make_proof('notDone', complete=False)
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        proofs = response.data.get('proofs', [])
        self.assertEqual(len(proofs), 2)
        flags = {p['name']: p['is_complete'] for p in proofs}
        self.assertTrue(flags['done'])
        self.assertFalse(flags['notDone'])

    def test_inactive_proofs_excluded_from_list(self):
        """Archived (is_active=False) proofs must not appear in the list."""
        active = self._make_proof('activeProof', complete=False)
        inactive = self._make_proof('archivedProof', complete=True)
        inactive.is_active = False
        inactive.save()
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        proofs = response.data.get('proofs', [])
        self.assertEqual(len(proofs), 1)
        self.assertEqual(proofs[0]['name'], 'activeProof')
