"""
Tests that user errors from failed rule applications are written only to the
correct (case, side) combination in the database — not cross-contaminating the
paired case (base ↔ leap) with the same side and line number.

Bug being guarded: Both the apply_rule and substitution endpoints had a
.filter() that omitted case=case.lower() when writing error text back to the
DB.  Since InductionProofLine rows are unique on (proof, case, side, line_number),
a failure on base LHS would previously also overwrite the leap LHS row's errors
field.  The fix adds case= to both filter calls.

Run with: python manage.py test induction_api.test_error_persistence
"""

from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.core.cache import cache
from .models import InductionProof, InductionProofLine

User = get_user_model()


class ErrorPersistenceCaseIsolationTests(TransactionTestCase):
    """
    Verify that a failed rule or substitution writes its error only to the
    matching case row, leaving the opposite case's row untouched.
    """

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='errtest_user',
            email='errtest@example.com',
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

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    def _start_proof(self, name, tag):
        """
        Create an InductionProof DB record, seed its id into the cache so that
        set-current-proof can find it and save the four premise lines, then call
        set-current-proof to initialise the engine.

        The key ordering requirement: proof_id must already be in the cache when
        set-current-proof runs, because that endpoint only writes premises to the
        DB when existing_proof_id is not None.

        Returns the InductionProof instance.
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
            rhs_anchor_goal='1',
            lhs_leap_goal='(+ (+ k 1) 1)',
            rhs_leap_goal='(+ 1 (+ k 1))',
        )

        # Seed a fresh IndProof + the proof_id into the cache BEFORE calling
        # set-current-proof, so the endpoint's get_or_set_induction_obj() call
        # returns this proof_id and triggers DB saves.
        ind = IndProof()
        save_induction_obj_to_cache(self.user, ind, proof.id)

        # lhsPremise / rhsPremise are the general (un-substituted) goals.
        # set-current-proof substitutes n->0 for base and n->(+ k 1) for leap,
        # then saves all four premise lines to the database.
        init_data = {
            'struct': 'int',
            'ivar': 'n',
            'aval': '0',
            'lvar': 'k',
            'lhsPremise': '(+ n 1)',
            'rhsPremise': '(+ 1 n)',
            'definitions': [],
        }

        response = self.client.post(
            '/api/v1/induction/set-current-proof', init_data, format='json'
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            f"set-current-proof failed: {response.data}",
        )

        return proof

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------

    def test_failed_apply_rule_writes_error_only_to_correct_case(self):
        """
        A bad rule applied to BASE LHS must write an error only to the
        base LHS premise row.  The leap LHS premise row must stay error-free.
        """
        print("\n-> Testing apply-rule error isolation between base and leap cases...")

        proof = self._start_proof('Error Isolation - apply_rule', 'err-apply-rule')

        base_premise = InductionProofLine.objects.filter(
            proof=proof, case='base', side='LHS', line_number=0
        ).first()
        leap_premise = InductionProofLine.objects.filter(
            proof=proof, case='leap', side='LHS', line_number=0
        ).first()

        self.assertIsNotNone(
            base_premise, "Base LHS premise not saved to DB by set-current-proof"
        )
        self.assertIsNotNone(
            leap_premise, "Leap LHS premise not saved to DB by set-current-proof"
        )

        # Both lines should start clean.
        self.assertEqual(base_premise.errors, '', "Base LHS premise should start with no errors")
        self.assertEqual(leap_premise.errors, '', "Leap LHS premise should start with no errors")

        # Apply a deliberately bad rule on the BASE case LHS.
        # lineNumber=1 means line_index = lineNumber-1 = 0, so the error is
        # written back onto premise line 0 — which exists in both base and leap.
        rule_data = {
            'case': 'base',
            'side': 'LHS',
            'currentRacket': base_premise.racket,
            'rule': 'nonexistent-rule-xyz',
            'startPosition': 0,
            'lineNumber': 1,
        }

        response = self.client.post(
            '/api/v1/induction/apply-rule', rule_data, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(
            response.data.get('isValid'),
            "Expected the bad rule to be rejected (isValid should be False)",
        )

        # Refresh from DB.
        base_premise.refresh_from_db()
        leap_premise.refresh_from_db()

        # Base case row must now carry an error.
        self.assertNotEqual(
            base_premise.errors,
            '',
            "Base LHS premise should have an error written after failed rule application",
        )

        # Leap case row must still be clean (this was the bug).
        self.assertEqual(
            leap_premise.errors,
            '',
            "Leap LHS premise must NOT receive errors from a base-case rule failure",
        )

        print(f"  ✓ Base LHS premise errors (non-empty): {base_premise.errors!r}")
        print(f"  ✓ Leap LHS premise errors (should be ''): {leap_premise.errors!r}")

    def test_failed_substitution_writes_error_only_to_correct_case(self):
        """
        A bad substitution applied to LEAP RHS must write an error only to the
        leap RHS premise row.  The base RHS premise row must stay error-free.
        """
        print("\n-> Testing substitution error isolation between base and leap cases...")

        proof = self._start_proof('Error Isolation - substitution', 'err-substitution')

        base_premise = InductionProofLine.objects.filter(
            proof=proof, case='base', side='RHS', line_number=0
        ).first()
        leap_premise = InductionProofLine.objects.filter(
            proof=proof, case='leap', side='RHS', line_number=0
        ).first()

        self.assertIsNotNone(
            base_premise, "Base RHS premise not saved to DB by set-current-proof"
        )
        self.assertIsNotNone(
            leap_premise, "Leap RHS premise not saved to DB by set-current-proof"
        )

        self.assertEqual(base_premise.errors, '', "Base RHS premise should start with no errors")
        self.assertEqual(leap_premise.errors, '', "Leap RHS premise should start with no errors")

        # Apply a bad rule on the LEAP case RHS (no substitution value so the engine
        # reaches errLog path rather than throwing a parser exception that causes 400).
        sub_data = {
            'case': 'leap',
            'side': 'RHS',
            'currentRacket': leap_premise.racket,
            'rule': 'nonexistent-rule-xyz',
            'startPosition': 0,
            'lineNumber': 1,
        }

        response = self.client.post(
            '/api/v1/induction/substitution', sub_data, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(
            response.data.get('isValid'),
            "Expected the bad substitution to be rejected (isValid should be False)",
        )

        base_premise.refresh_from_db()
        leap_premise.refresh_from_db()

        # Leap case row must carry an error.
        self.assertNotEqual(
            leap_premise.errors,
            '',
            "Leap RHS premise should have an error written after failed substitution",
        )

        # Base case row must be clean (this was the bug).
        self.assertEqual(
            base_premise.errors,
            '',
            "Base RHS premise must NOT receive errors from a leap-case substitution failure",
        )

        print(f"  ✓ Leap RHS premise errors (non-empty): {leap_premise.errors!r}")
        print(f"  ✓ Base RHS premise errors (should be ''): {base_premise.errors!r}")

    def test_failed_apply_rule_on_non_premise_line_isolates_by_case(self):
        """
        A bad rule targeting a non-premise line (line 1) must write its error
        only to the correct case's line 1, not to the other case's line 1.

        The DB write bug would affect any line_number, not just the premise.
        This test creates line 1 in both base and leap LHS directly (bypassing
        the engine API) so the filter has something to hit in both cases, then
        confirms case isolation holds for that non-zero line_number.
        """
        print("\n-> Testing apply-rule error isolation on a non-premise line (line 1)...")

        proof = self._start_proof('Error Isolation - non-premise', 'err-non-premise')

        # Directly create line 1 in both cases so both exist in the DB at the
        # same (side='LHS', line_number=1) position — necessary for the old bug
        # to have been able to corrupt the wrong row.
        base_line1 = InductionProofLine.objects.create(
            proof=proof,
            case='base',
            side='LHS',
            racket='1',
            rule='eval +',
            start_position=0,
            line_number=1,
            errors='',
        )
        leap_line1 = InductionProofLine.objects.create(
            proof=proof,
            case='leap',
            side='LHS',
            racket='(+ k 1)',
            rule='eval +',
            start_position=0,
            line_number=1,
            errors='',
        )

        # Attempt a bad rule on BASE LHS with lineNumber=2 so the view writes
        # the error back to line_index = lineNumber-1 = 1.
        base_premise = InductionProofLine.objects.filter(
            proof=proof, case='base', side='LHS', line_number=0
        ).first()
        rule_data = {
            'case': 'base',
            'side': 'LHS',
            'currentRacket': base_line1.racket,
            'rule': 'nonexistent-rule-xyz',
            'startPosition': 0,
            'lineNumber': 2,
        }

        response = self.client.post(
            '/api/v1/induction/apply-rule', rule_data, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data.get('isValid'))

        base_line1.refresh_from_db()
        leap_line1.refresh_from_db()

        self.assertNotEqual(
            base_line1.errors,
            '',
            "Base LHS line 1 should have an error after the failed rule",
        )
        self.assertEqual(
            leap_line1.errors,
            '',
            "Leap LHS line 1 must NOT receive errors from a base-case rule failure",
        )

        print(f"  ✓ Base LHS line 1 errors (non-empty): {base_line1.errors!r}")
        print(f"  ✓ Leap LHS line 1 errors (should be ''): {leap_line1.errors!r}")

    def test_failed_rewrite_math_substitution_isolates_by_case(self):
        """
        A 'rewrite math' substitution sent via the /substitution endpoint with
        an actual substitution value that the engine rejects must write its error
        only to the correct case's row, not the paired case's row.

        This specifically exercises the 'rewrite math' path (substitution value
        is passed through to _apply_line) rather than a plain rule failure.
        """
        print("\n-> Testing rewrite-math substitution error isolation between cases...")

        proof = self._start_proof('Error Isolation - rewrite math', 'err-rewrite-math')

        base_premise = InductionProofLine.objects.filter(
            proof=proof, case='base', side='LHS', line_number=0
        ).first()
        leap_premise = InductionProofLine.objects.filter(
            proof=proof, case='leap', side='LHS', line_number=0
        ).first()

        self.assertIsNotNone(base_premise)
        self.assertIsNotNone(leap_premise)
        self.assertEqual(base_premise.errors, '')
        self.assertEqual(leap_premise.errors, '')

        # 'rewrite math' with a substitution value that doesn't appear in the
        # expression causes the engine to set errLog (200 + isValid:False) rather
        # than raising an exception (which would give a 400).
        sub_data = {
            'case': 'base',
            'side': 'LHS',
            'currentRacket': base_premise.racket,
            'rule': 'rewrite math',
            'substitution': '(+ 999 999)',   # subexpression that doesn't exist in the line
            'startPosition': 0,
            'lineNumber': 1,
        }

        response = self.client.post(
            '/api/v1/induction/substitution', sub_data, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(
            response.data.get('isValid'),
            "Expected rewrite math with non-matching substitution to fail (isValid=False)",
        )

        base_premise.refresh_from_db()
        leap_premise.refresh_from_db()

        self.assertNotEqual(
            base_premise.errors,
            '',
            "Base LHS premise should carry the rewrite-math error",
        )
        self.assertEqual(
            leap_premise.errors,
            '',
            "Leap LHS premise must NOT receive errors from a base-case rewrite-math failure",
        )

        print(f"  ✓ Base LHS premise errors (non-empty): {base_premise.errors!r}")
        print(f"  ✓ Leap LHS premise errors (should be ''): {leap_premise.errors!r}")

    def test_failed_apply_rule_on_leap_does_not_contaminate_base(self):
        """
        Reverse direction: a bad rule on LEAP LHS must not write errors to
        the BASE LHS premise row.
        """
        print("\n-> Testing apply-rule error isolation: leap failure does not touch base...")

        proof = self._start_proof('Error Isolation - apply_rule leap->base', 'err-apply-rule-rev')

        base_premise = InductionProofLine.objects.filter(
            proof=proof, case='base', side='LHS', line_number=0
        ).first()
        leap_premise = InductionProofLine.objects.filter(
            proof=proof, case='leap', side='LHS', line_number=0
        ).first()

        self.assertIsNotNone(base_premise)
        self.assertIsNotNone(leap_premise)
        self.assertEqual(base_premise.errors, '')
        self.assertEqual(leap_premise.errors, '')

        rule_data = {
            'case': 'leap',
            'side': 'LHS',
            'currentRacket': leap_premise.racket,
            'rule': 'nonexistent-rule-xyz',
            'startPosition': 0,
            'lineNumber': 1,
        }

        response = self.client.post('/api/v1/induction/apply-rule', rule_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data.get('isValid'))

        base_premise.refresh_from_db()
        leap_premise.refresh_from_db()

        self.assertNotEqual(leap_premise.errors, '',
            "Leap LHS premise should have an error after the failed rule")
        self.assertEqual(base_premise.errors, '',
            "Base LHS premise must NOT receive errors from a leap-case rule failure")

        print(f"  ✓ Leap LHS premise errors (non-empty): {leap_premise.errors!r}")
        print(f"  ✓ Base LHS premise errors (should be ''): {base_premise.errors!r}")

    def test_failed_apply_rule_on_non_premise_leap_does_not_contaminate_base(self):
        """
        Reverse direction for non-premise lines: a bad rule targeting line 1 on
        LEAP LHS must not write errors to BASE LHS line 1.
        """
        print("\n-> Testing apply-rule error isolation on non-premise line: leap->base direction...")

        proof = self._start_proof('Error Isolation - non-premise leap->base', 'err-non-premise-rev')

        base_line1 = InductionProofLine.objects.create(
            proof=proof, case='base', side='LHS', racket='1',
            rule='eval +', start_position=0, line_number=1, errors=''
        )
        leap_line1 = InductionProofLine.objects.create(
            proof=proof, case='leap', side='LHS', racket='(+ k 1)',
            rule='eval +', start_position=0, line_number=1, errors=''
        )

        rule_data = {
            'case': 'leap',
            'side': 'LHS',
            'currentRacket': leap_line1.racket,
            'rule': 'nonexistent-rule-xyz',
            'startPosition': 0,
            'lineNumber': 2,
        }

        response = self.client.post('/api/v1/induction/apply-rule', rule_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data.get('isValid'))

        base_line1.refresh_from_db()
        leap_line1.refresh_from_db()

        self.assertNotEqual(leap_line1.errors, '',
            "Leap LHS line 1 should have an error after the failed rule")
        self.assertEqual(base_line1.errors, '',
            "Base LHS line 1 must NOT receive errors from a leap-case rule failure")

        print(f"  ✓ Leap LHS line 1 errors (non-empty): {leap_line1.errors!r}")
        print(f"  ✓ Base LHS line 1 errors (should be ''): {base_line1.errors!r}")

    def test_failed_rewrite_math_on_leap_does_not_contaminate_base(self):
        """
        Reverse direction for rewrite-math: a bad substitution on LEAP LHS must
        not write errors to BASE LHS premise.
        """
        print("\n-> Testing rewrite-math substitution error isolation: leap->base direction...")

        proof = self._start_proof('Error Isolation - rewrite math leap->base', 'err-rewrite-rev')

        base_premise = InductionProofLine.objects.filter(
            proof=proof, case='base', side='LHS', line_number=0
        ).first()
        leap_premise = InductionProofLine.objects.filter(
            proof=proof, case='leap', side='LHS', line_number=0
        ).first()

        self.assertIsNotNone(base_premise)
        self.assertIsNotNone(leap_premise)
        self.assertEqual(base_premise.errors, '')
        self.assertEqual(leap_premise.errors, '')

        sub_data = {
            'case': 'leap',
            'side': 'LHS',
            'currentRacket': leap_premise.racket,
            'rule': 'rewrite math',
            'substitution': '(+ 999 999)',
            'startPosition': 0,
            'lineNumber': 1,
        }

        response = self.client.post('/api/v1/induction/substitution', sub_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data.get('isValid'))

        base_premise.refresh_from_db()
        leap_premise.refresh_from_db()

        self.assertNotEqual(leap_premise.errors, '',
            "Leap LHS premise should carry the rewrite-math error")
        self.assertEqual(base_premise.errors, '',
            "Base LHS premise must NOT receive errors from a leap-case rewrite-math failure")

        print(f"  ✓ Leap LHS premise errors (non-empty): {leap_premise.errors!r}")
        print(f"  ✓ Base LHS premise errors (should be ''): {base_premise.errors!r}")
