"""
Tests for the AVal(s) feature — Step 1: infrastructure refactor.

Covers:
  - _parse_avals() helper (pure function, no DB)
  - start_induction_proof accepting comma-separated anchor values
  - set_current_proof using only the first anchor (single-value backward compat)

Run individually:
  $env:PYTHONIOENCODING="utf-8"; py manage.py test induction_api.test_multiple_anchors
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.core.cache import cache

User = get_user_model()

BASE_URL = '/api/v1/induction/'
START_URL = f'{BASE_URL}start-induction-proof'
SET_URL = f'{BASE_URL}set-current-proof'


class ParseAvalsTests(TestCase):
    """Unit tests for _parse_avals() — no DB access."""

    def _parse(self, val, struct='int'):
        from induction_api.views import _parse_avals
        return _parse_avals(val, struct)

    def test_single_value(self):
        self.assertEqual(self._parse('0'), ['0'])

    def test_multiple_values(self):
        self.assertEqual(self._parse('0,1'), ['0', '1'])

    def test_three_values(self):
        self.assertEqual(self._parse('0,1,2'), ['0', '1', '2'])

    def test_whitespace_trimmed(self):
        self.assertEqual(self._parse(' 0 , 1 '), ['0', '1'])

    def test_consecutive_commas_skipped(self):
        self.assertEqual(self._parse('0,,1'), ['0', '1'])

    def test_trailing_comma_ignored(self):
        self.assertEqual(self._parse('0,1,'), ['0', '1'])

    def test_list_induction_untouched(self):
        # For list induction, _parse_avals must return the value unchanged
        self.assertEqual(self._parse('null', 'list'), ['null'])

    def test_list_quoted_list_untouched(self):
        self.assertEqual(self._parse("'()", 'list'), ["'()"])


class StartProofAnchorTests(TestCase):
    """start_induction_proof should accept comma-separated integer anchor values."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser_anchors',
            email='testanchors@example.com',
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

    def _base_data(self, anchor_value):
        return {
            'proof_name': 'TestAnchorProof',
            'proof_tag': 'ta',
            'induction_variable': 'n',
            'anchor_value': anchor_value,
            'leap_variable': 'k',
            'lhs_leap_goal': '(f n)',
            'rhs_leap_goal': '(g n)',
            'lhs_anchor_goal': '(f 0)',
            'rhs_anchor_goal': '(g 0)',
            'induction_type': 'integers',
            'side': 'LHS',
            'is_anchor': True,
            'inductive_hypothesis_lhs': '(f k)',
            'inductive_hypothesis_rhs': '(g k)',
        }

    def test_single_anchor_accepted(self):
        response = self.client.post(START_URL, self._base_data('0'), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_multiple_anchors_accepted(self):
        response = self.client.post(START_URL, self._base_data('0,1'), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_multiple_anchors_with_spaces_accepted(self):
        response = self.client.post(START_URL, self._base_data(' 0 , 1 '), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_nonneg_single_stored(self):
        response = self.client.post(START_URL, self._base_data('3'), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        from induction_api.models import InductionProof
        proof = InductionProof.objects.filter(user=self.user).latest('created_at')
        self.assertEqual(proof.anchor_value, '3')

    def test_multiple_anchors_stored_as_csv(self):
        response = self.client.post(START_URL, self._base_data('0,1'), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        from induction_api.models import InductionProof
        proof = InductionProof.objects.filter(user=self.user).latest('created_at')
        self.assertIn('0', proof.anchor_value)
        self.assertIn('1', proof.anchor_value)

    def test_non_integer_rejected(self):
        response = self.client.post(START_URL, self._base_data('abc'), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_negative_anchor_rejected(self):
        response = self.client.post(START_URL, self._base_data('-1'), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_second_anchor_rejected(self):
        # "0,abc" — first is valid but second is not
        response = self.client.post(START_URL, self._base_data('0,abc'), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class SetCurrentProofAnchorTests(TestCase):
    """set_current_proof should use the first anchor value; behavior identical to single anchor."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser_setanchor',
            email='testsetanchor@example.com',
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

    def _set_data(self, aval):
        return {
            'struct': 'int',
            'ivar': 'n',
            'aval': aval,
            'lvar': 'k',
            'lhsPremise': '(+ n 1)',
            'rhsPremise': '(+ 1 n)',
            'definitions': []
        }

    def test_single_anchor_succeeds(self):
        response = self.client.post(SET_URL, self._set_data('0'), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['isValid'])

    def test_multiple_anchors_succeeds(self):
        # "0,1" should succeed and use anchor 0 for the base case
        response = self.client.post(SET_URL, self._set_data('0,1'), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['isValid'])

    def test_multiple_anchors_base_premise_matches_single(self):
        # The base case premise built from "0,1" must match the one from "0" alone
        r_single = self.client.post(SET_URL, self._set_data('0'), format='json')
        cache.clear()
        r_multi = self.client.post(SET_URL, self._set_data('0,1'), format='json')

        single_lhs = r_single.data['base']['LHS']['racket']
        multi_lhs = r_multi.data['base']['LHS']['racket']
        self.assertEqual(single_lhs, multi_lhs)
