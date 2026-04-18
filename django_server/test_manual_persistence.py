"""
Test for proof line database persistence.
Run with: python manage.py test test_manual_persistence
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from induction_api.models import InductionProof, InductionProofLine
from django.core.cache import cache

User = get_user_model()


class ManualPersistenceTests(TestCase):
    """Verify that proof lines are correctly persisted to the database."""

    def setUp(self):
        try:
            cache.clear()
        except Exception:
            pass
        self.user = User.objects.create_user(
            username='test_persistence_user',
            email='test@test.com',
            password='test123'
        )

    def tearDown(self):
        try:
            cache.clear()
        except Exception:
            pass

    def _make_proof(self):
        return InductionProof.objects.create(
            user=self.user,
            name='Test Proof Persistence',
            tag='test-persist',
            induction_variable='n',
            anchor_value=0,
            leap_variable='k',
            lhs_anchor_goal='(sum 0)',
            rhs_anchor_goal='0',
            lhs_leap_goal='(sum (+ k 1))',
            rhs_leap_goal='(+ (sum k) (+ k 1))'
        )

    def test_proof_line_creation(self):
        """Create a proof with 4 lines and verify all are persisted."""
        proof = self._make_proof()

        InductionProofLine.objects.create(
            proof=proof, case='base', side='LHS',
            racket='(sum 0)', rule='Premise',
            start_position=0, line_number=0
        )
        InductionProofLine.objects.create(
            proof=proof, case='base', side='LHS',
            racket='0', rule='eval sum',
            start_position=0, line_number=1
        )
        InductionProofLine.objects.create(
            proof=proof, case='base', side='RHS',
            racket='(quotient (* 0 (+ 0 1)) 2)', rule='Premise',
            start_position=0, line_number=0
        )
        InductionProofLine.objects.create(
            proof=proof, case='base', side='RHS',
            racket='0', rule='rewrite math with 0',
            start_position=0, line_number=1
        )

        base_lhs = InductionProofLine.objects.filter(proof=proof, case='base', side='LHS')
        base_rhs = InductionProofLine.objects.filter(proof=proof, case='base', side='RHS')

        self.assertEqual(base_lhs.count(), 2)
        self.assertEqual(base_rhs.count(), 2)

        eval_sum_line = base_lhs.filter(rule__icontains='eval sum').first()
        self.assertIsNotNone(eval_sum_line, "'eval sum' rule not found")

        rewrite_math_line = base_rhs.filter(rule__icontains='rewrite math').first()
        self.assertIsNotNone(rewrite_math_line, "'rewrite math' rule not found")
        self.assertIn('with', rewrite_math_line.rule, "Rule should include substitution")

    def test_proof_line_query_by_case_and_side(self):
        """Verify filtering proof lines by case and side returns correct counts."""
        proof = self._make_proof()

        for side in ('LHS', 'RHS'):
            InductionProofLine.objects.create(
                proof=proof, case='base', side=side,
                racket='x', rule='Premise',
                start_position=0, line_number=0
            )
            InductionProofLine.objects.create(
                proof=proof, case='leap', side=side,
                racket='x', rule='Premise',
                start_position=0, line_number=0
            )

        all_lines = InductionProofLine.objects.filter(proof=proof)
        self.assertEqual(all_lines.count(), 4)
        self.assertEqual(all_lines.filter(case='base').count(), 2)
        self.assertEqual(all_lines.filter(case='leap').count(), 2)