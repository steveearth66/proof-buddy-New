"""
Tests for InductionProof.is_complete database persistence.

Verifies that the is_complete field is:
  - False by default on proof creation
  - Set to True in the DB when check-completion is called and BOTH base AND leap
    cases are complete  
  - Remains False when only one case is complete
  - Reverted to False when proof is edited after being marked complete

Pattern follows test_error_persistence.py:
  create proof via ORM + seed cache + call set-current-proof, then directly
  insert InductionProofLine records to simulate completed/incomplete states.

Run with:
  cd django_server
  python manage.py test induction_api.tests_is_complete_persistence
"""

from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.core.cache import cache

from induction_api.models import InductionProof, InductionProofLine

User = get_user_model()

# ---------------------------------------------------------------------------
# URL constants
# ---------------------------------------------------------------------------
BASE = '/api/v1/induction/'
SET_PROOF_URL   = f'{BASE}set-current-proof'
CHECK_URL       = f'{BASE}check-completion'

# ---------------------------------------------------------------------------
# Payloads
# ---------------------------------------------------------------------------
# Theorem: (+ n 1) = (+ 1 n)   (commutative addition with anchor n=0)
# Base premises (n->0): LHS=(+ 0 1), RHS=(+ 1 0)   -- do NOT trivially match
# Leap premises (n->(+ k 1)): LHS=(+ (+ k 1) 1), RHS=(+ 1 (+ k 1))
SET_PROOF_DATA = {
    'struct': 'int',
    'ivar': 'n',
    'aval': '0',
    'lvar': 'k',
    'lhsPremise': '(+ n 1)',
    'rhsPremise': '(+ 1 n)',
    'definitions': [],
}

# A racket string that both base LHS and RHS can converge to (concrete integer).
BASE_MEETING_POINT = '1'
# A racket string that both leap LHS and RHS can converge to (generic expression).
LEAP_MEETING_POINT = '(+ k 1)'


class IsCompletePersistenceTests(TransactionTestCase):
    """Tests for InductionProof.is_complete field persistence via the check-completion endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser_ic',
            email='ic@example.com',
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

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _setup_proof(self, name='testproof', tag='t1'):
        """
        Create an InductionProof in the DB, seed the cache, then call
        set-current-proof to initialise the engine and persist the four
        premise lines.  Returns the saved InductionProof instance.

        Mirrors the helper in test_error_persistence.py.
        """
        from expression_tree.IndProofs import IndProof
        from .views import save_induction_obj_to_cache

        proof = InductionProof.objects.create(
            user=self.user,
            name=name,
            tag=tag,
            induction_variable='n',
            anchor_value='0',
            leap_variable='k',
            lhs_anchor_goal='(+ 0 1)',
            rhs_anchor_goal='(+ 1 0)',
            lhs_leap_goal='(+ (+ k 1) 1)',
            rhs_leap_goal='(+ 1 (+ k 1))',
        )

        # Seed the cache so set-current-proof can find the proof_id and
        # write premises to the DB.
        ind = IndProof()
        save_induction_obj_to_cache(self.user, ind, proof.id)

        response = self.client.post(SET_PROOF_URL, SET_PROOF_DATA, format='json')
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            f"set-current-proof failed: {response.data}",
        )
        return proof

    def _add_matching_lines(self, proof, case, meeting_point):
        """
        Directly insert line_number=1 InductionProofLines for both sides of
        the given case, with the same racket expression.  This simulates the
        user having applied rules so both sides reach the same expression.
        """
        for side in ('LHS', 'RHS'):
            InductionProofLine.objects.update_or_create(
                proof=proof,
                case=case,
                side=side,
                line_number=1,
                defaults={
                    'racket': meeting_point,
                    'rule': 'eval +',
                    'start_position': 0,
                    'selected_node': 0,
                    'result_node': 0,
                    'json_tree': {},
                    'errors': '',
                },
            )

    def _check_completion(self, case):
        """POST to check-completion and return the response data dict."""
        resp = self.client.post(CHECK_URL, {'case': case}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK,
                         f"check-completion failed: {resp.data}")
        return resp.data

    def _fresh_is_complete(self, proof):
        """Re-fetch is_complete from DB (bypasses any in-memory state)."""
        return InductionProof.objects.get(id=proof.id).is_complete

    # -----------------------------------------------------------------------
    # Tests
    # -----------------------------------------------------------------------

    def test_is_complete_false_by_default(self):
        """
        [NEGATIVE] Newly created proof must have is_complete=False before
        check-completion is ever called.
        """
        print("\n[NEGATIVE] is_complete defaults to False on creation")
        proof = self._setup_proof('default-test', 'd1')
        self.assertFalse(
            self._fresh_is_complete(proof),
            "is_complete should be False immediately after proof creation",
        )
        print("  PASS: is_complete=False confirmed on creation")

    def test_is_complete_false_when_only_base_complete(self):
        """
        [NEGATIVE] is_complete stays False in the DB when only the base case
        is complete and the leap case has no matching lines.
        """
        print("\n[NEGATIVE] is_complete stays False when only base case is complete")
        proof = self._setup_proof('base-only', 'b1')

        # Make base case complete: add matching result lines for base LHS and RHS.
        self._add_matching_lines(proof, 'base', BASE_MEETING_POINT)

        result = self._check_completion('base')

        self.assertTrue(result['isComplete'],
                        "Base case itself should be reported complete")
        self.assertFalse(result['overallComplete'],
                         "overallComplete should be False (leap not done)")
        self.assertFalse(
            self._fresh_is_complete(proof),
            "is_complete should still be False in DB when leap is not complete",
        )
        print("  PASS: is_complete=False confirmed when only base is done")

    def test_is_complete_false_when_only_leap_complete(self):
        """
        [NEGATIVE] is_complete stays False in the DB when only the leap case
        is complete and the base case has no matching lines.
        """
        print("\n[NEGATIVE] is_complete stays False when only leap case is complete")
        proof = self._setup_proof('leap-only', 'l1')

        # Make leap case complete: add matching result lines for leap LHS and RHS.
        self._add_matching_lines(proof, 'leap', LEAP_MEETING_POINT)

        result = self._check_completion('leap')

        self.assertTrue(result['isComplete'],
                        "Leap case itself should be reported complete")
        self.assertFalse(result['overallComplete'],
                         "overallComplete should be False (base not done)")
        self.assertFalse(
            self._fresh_is_complete(proof),
            "is_complete should still be False in DB when base is not complete",
        )
        print("  PASS: is_complete=False confirmed when only leap is done")

    def test_is_complete_true_when_both_cases_complete(self):
        """
        [POSITIVE] is_complete becomes True in the DB when BOTH base AND leap
        cases are complete and check-completion is called.
        """
        print("\n[POSITIVE] is_complete=True when both base and leap are complete")
        proof = self._setup_proof('both-done', 'bd1')

        # Complete both cases.
        self._add_matching_lines(proof, 'base', BASE_MEETING_POINT)
        self._add_matching_lines(proof, 'leap', LEAP_MEETING_POINT)

        # Checking base updates is_complete based on overall (both done -> True).
        result = self._check_completion('base')
        self.assertTrue(result['overallComplete'],
                        "overallComplete should be True after both cases are done")

        self.assertTrue(
            self._fresh_is_complete(proof),
            "is_complete should be True in DB after both cases are complete",
        )
        print("  PASS: is_complete=True persisted to DB")

    def test_is_complete_reverts_to_false_after_edit(self):
        """
        [NEGATIVE] A proof that was complete (is_complete=True) reverts to
        is_complete=False when one side is edited so the cases no longer match.
        """
        print("\n[NEGATIVE] is_complete reverts to False after editing a completed proof")
        proof = self._setup_proof('revert-test', 'rv1')

        # --- Bring proof to completion ---
        self._add_matching_lines(proof, 'base', BASE_MEETING_POINT)
        self._add_matching_lines(proof, 'leap', LEAP_MEETING_POINT)
        self._check_completion('leap')  # triggers is_complete=True in DB

        self.assertTrue(
            self._fresh_is_complete(proof),
            "Precondition failed: proof should be complete before edit",
        )

        # --- Simulate an edit: remove the matching leap RHS result line ---
        # Now leap LHS last line = LEAP_MEETING_POINT but leap RHS last line
        # is back to the premise, which is different -> leap no longer complete.
        InductionProofLine.objects.filter(
            proof=proof, case='leap', side='RHS', line_number=1
        ).delete()

        result = self._check_completion('leap')

        self.assertFalse(result['isComplete'],
                         "Leap case should be incomplete after removing the result line")
        self.assertFalse(result['overallComplete'],
                         "overallComplete should be False after edit")
        self.assertFalse(
            self._fresh_is_complete(proof),
            "is_complete should revert to False in DB after proof is edited",
        )
        print("  PASS: is_complete reverted to False after proof was edited")

    def test_overall_complete_false_in_response_when_incomplete(self):
        """
        [NEGATIVE] check-completion response includes overallComplete=False
        when neither case is complete.
        """
        print("\n[NEGATIVE] response has overallComplete=False when proof is incomplete")
        self._setup_proof('response-neg', 'rn1')
        result = self._check_completion('base')
        self.assertIn('overallComplete', result)
        self.assertFalse(result['overallComplete'])
        print("  PASS: overallComplete=False confirmed in response")

    def test_overall_complete_true_in_response_when_complete(self):
        """
        [POSITIVE] check-completion response includes overallComplete=True
        when both cases are complete.
        """
        print("\n[POSITIVE] response has overallComplete=True when both cases are done")
        proof = self._setup_proof('response-pos', 'rp1')
        self._add_matching_lines(proof, 'base', BASE_MEETING_POINT)
        self._add_matching_lines(proof, 'leap', LEAP_MEETING_POINT)

        result = self._check_completion('leap')
        self.assertIn('overallComplete', result)
        self.assertTrue(result['overallComplete'])
        print("  PASS: overallComplete=True confirmed in response")
