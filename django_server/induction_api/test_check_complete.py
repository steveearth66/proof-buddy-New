"""
Unit tests for TwoSidedProof.checkComplete() in ERProofEngine.py.

These tests cover the bug fix where blank lines AFTER the last valid endpoint
(e.g. lines cleared by the user after a wrong attempt) were incorrectly
preventing the proof from being marked complete.

All tests use TestCase and contain zero module-level DB code.
"""
import sys
import os

# Allow expression_tree imports to resolve when run via manage.py test
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from django.test import TestCase

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_server.settings')

from expression_tree.ERProofEngine import TwoSidedProof, ERProofLine


def _make_line(expr_str, rule_str):
    """Create a non-blank ERProofLine with appliedRule set."""
    line = ERProofLine(expr_str)
    line.appliedRule = rule_str
    return line


def _make_blank():
    """Create a blank (cleared) ERProofLine — simulates a user clearing a line."""
    return ERProofLine("")


class CheckCompleteTests(TestCase):
    """Tests for TwoSidedProof.checkComplete()."""

    def test_clean_proof_complete(self):
        """Normal complete proof: both sides end with same expression, no blanks → COMPLETE."""
        proof = TwoSidedProof()
        proof.LHS.proofLines = [
            _make_line("3", "Premise"),
            _make_line("3", "identity"),
            _make_blank(),           # trailing blank always maintained
        ]
        proof.RHS.proofLines = [
            _make_line("3", "Premise"),
            _make_blank(),           # trailing blank
        ]
        self.assertTrue(proof.checkComplete(is_student=False))

    def test_non_matching_endpoints_incomplete(self):
        """Non-matching endpoints → INCOMPLETE."""
        proof = TwoSidedProof()
        proof.LHS.proofLines = [
            _make_line("3", "Premise"),
            _make_blank(),
        ]
        proof.RHS.proofLines = [
            _make_line("5", "Premise"),
            _make_blank(),
        ]
        self.assertFalse(proof.checkComplete(is_student=False))

    def test_cleared_lines_after_endpoint_complete(self):
        """
        BUG FIX REGRESSION TEST.

        User clears some wrong lines that were added AFTER the real endpoint.
        The valid chain on both sides ends with the same expression, but blank
        records from those cleared lines sit between the endpoint and the
        trailing blank.

        Before the fix:  checkComplete returned False (bug).
        After the fix:   checkComplete must return True.
        """
        proof = TwoSidedProof()
        # LHS: valid chain ends at "3", then two cleared blanks
        proof.LHS.proofLines = [
            _make_line("3", "Premise"),
            _make_line("3", "identity"),
            _make_blank(),   # cleared wrong attempt
            _make_blank(),   # trailing blank
        ]
        # RHS: valid chain ends at "3", then two cleared blanks
        proof.RHS.proofLines = [
            _make_line("3", "Premise"),
            _make_line("3", "commutativity"),
            _make_blank(),   # cleared wrong attempt
            _make_blank(),   # trailing blank
        ]
        self.assertTrue(proof.checkComplete(is_student=False))

    def test_one_side_has_cleared_lines_other_does_not(self):
        """
        Only one side has post-endpoint cleared blanks; the other is clean.
        Should still be COMPLETE.
        """
        proof = TwoSidedProof()
        proof.LHS.proofLines = [
            _make_line("3", "Premise"),
            _make_line("3", "identity"),
            _make_blank(),   # cleared wrong attempt
            _make_blank(),   # cleared wrong attempt
            _make_blank(),   # trailing blank
        ]
        proof.RHS.proofLines = [
            _make_line("3", "Premise"),
            _make_blank(),   # trailing blank only
        ]
        self.assertTrue(proof.checkComplete(is_student=False))

    def test_mid_chain_gap_is_incomplete(self):
        """
        A blank line BETWEEN two valid steps (a genuine gap in the chain)
        must still be detected as INCOMPLETE.
        """
        proof = TwoSidedProof()
        # LHS has a blank between premise and final step — a true gap
        proof.LHS.proofLines = [
            _make_line("3", "Premise"),
            _make_blank(),           # gap — not a post-endpoint clear
            _make_line("3", "identity"),
            _make_blank(),           # trailing blank
        ]
        proof.RHS.proofLines = [
            _make_line("3", "Premise"),
            _make_line("3", "commutativity"),
            _make_blank(),
        ]
        self.assertFalse(proof.checkComplete(is_student=False))

    def test_single_line_each_side_match(self):
        """Special case: both sides have exactly one line (just premise) and match → COMPLETE."""
        proof = TwoSidedProof()
        proof.LHS.proofLines = [_make_line("3", "Premise")]
        proof.RHS.proofLines = [_make_line("3", "Premise")]
        self.assertTrue(proof.checkComplete(is_student=False))

    def test_single_line_each_side_no_match(self):
        """Special case: single-line sides that do NOT match → INCOMPLETE."""
        proof = TwoSidedProof()
        proof.LHS.proofLines = [_make_line("3", "Premise")]
        proof.RHS.proofLines = [_make_line("5", "Premise")]
        self.assertFalse(proof.checkComplete(is_student=False))

    def test_empty_sides_incomplete(self):
        """Both sides empty → INCOMPLETE."""
        proof = TwoSidedProof()
        self.assertFalse(proof.checkComplete(is_student=False))
