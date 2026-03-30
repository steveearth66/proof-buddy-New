"""
Regression test: applying a UDF rule when the user has highlighted the wrong
(outer) node previously caused an IndexError inside the mismatch-check loop,
which bubbled up as an unhandled exception and returned HTTP 400.

Bug: ERProofEngine.applyRule() iterated over assigned params and did
     `targetNode.children[i + 1]` without checking whether the target node
     actually had that many children.  When the entire outer expression was
     highlighted instead of the UDF's application node, the children list was
     too short and the index lookup crashed.

Fix: added a bounds-check that breaks out of the mismatch loop early when
     `i + 1 >= len(targetNode.children)`, allowing isApplicable() to produce
     the proper user-facing error.

Run with: python manage.py test induction_api.test_wrong_highlight
"""

from django.test import SimpleTestCase
from expression_tree.IndProofs import IndProof
from expression_tree.default_udfs import DEFAULT_UDFS


def _build_lhs():
    """
    Build a leap-step LHS proof engine loaded with default UDFs and the three
    generics needed for the revAppSingle proof (a:any, K:list, b:any).
    """
    ind = IndProof(struct='list')
    lhs = ind.leapStep.LHS
    for d in DEFAULT_UDFS:
        label = d.get('label')
        type_str = d.get('type')
        body = d.get('expression')
        if label and type_str and body:
            lhs.addUDF(label, type_str, body)
    lhs.addGeneric('a', 'any')
    lhs.addGeneric('K', 'list')
    lhs.addGeneric('b', 'any')
    return lhs


PREMISE = '(reverse (append (cons a K) (cons b null)))'
RULE    = 'apply append L=(cons a K),M=(cons b null)'

# In PREMISE the token positions are:
#  pos=0  '('  <- root of (reverse ...)
#  pos=9  '('  <- root of (append (cons a K) (cons b null))
WRONG_POS   = 0   # the outer (reverse ...) node — wrong target for 'apply append'
CORRECT_POS = 9   # the inner (append ...) node — correct target


class WrongHighlightRegressionTest(SimpleTestCase):
    """
    Applying a UDF rule with the wrong node highlighted must not raise an
    exception.  It must produce a validation error and return gracefully.
    """

    def _fresh_lhs_with_premise(self):
        lhs = _build_lhs()
        lhs.addProofLine(PREMISE)
        self.assertEqual(lhs.errLog, [], f"Premise parse failed: {lhs.errLog}")
        lhs.errLog = []
        return lhs

    # ------------------------------------------------------------------

    def test_correct_position_succeeds(self):
        """
        Baseline: applying 'apply append' at the correct (append ...) node
        produces the expected result with no errors.
        """
        lhs = self._fresh_lhs_with_premise()

        lhs.addProofLine(PREMISE, RULE, CORRECT_POS)

        self.assertEqual(lhs.errLog, [], f"Unexpected errors at correct pos: {lhs.errLog}")
        result = lhs.getPrevRacket()
        # The append definition unfolds into an if expression
        self.assertIn('if', result)
        self.assertIn('null?', result)

    def test_wrong_position_gives_error_not_exception(self):
        """
        Regression: applying 'apply append' at the outer (reverse ...) node
        must NOT raise an IndexError / unhandled exception.  It must populate
        errLog with a validation message and leave the proof unchanged.
        """
        lhs = self._fresh_lhs_with_premise()
        lines_before = len(lhs.proofLines)

        # This call previously raised IndexError and would have produced HTTP 400.
        try:
            lhs.addProofLine(PREMISE, RULE, WRONG_POS)
        except Exception as exc:
            self.fail(
                f"apply rule at wrong position raised an exception instead of "
                f"returning a validation error: {type(exc).__name__}: {exc}"
            )

        # The engine must have recorded at least one error.
        self.assertNotEqual(
            lhs.errLog,
            [],
            "Expected a validation error when applying 'append' to the outer "
            "'reverse' node, but errLog is empty.",
        )

        # No new proof line should have been appended (the step was rejected).
        self.assertEqual(
            len(lhs.proofLines),
            lines_before,
            "A new proof line must not be added when the rule application fails.",
        )

    def test_wrong_position_error_message_is_informative(self):
        """
        The error message produced for the wrong-node case should be meaningful
        (not just a raw Python exception string).
        """
        lhs = self._fresh_lhs_with_premise()
        lhs.addProofLine(PREMISE, RULE, WRONG_POS)

        combined = ' '.join(lhs.errLog).lower()
        # The error should mention something about mismatch, argument, or the
        # label — not a bare "list index out of range".
        self.assertNotIn(
            'list index out of range',
            combined,
            f"Raw IndexError leaked into errLog: {lhs.errLog}",
        )
        self.assertTrue(
            len(combined) > 0,
            "errLog should contain at least one non-empty error message.",
        )
