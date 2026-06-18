"""
Tests for normalize_rule_string and compare_rule helpers in validate_hidden_field.

These functions fix two bugs in hidden-field validation:
  1. Student omits 'with' or uses '->' instead of the stored Unicode arrow ↦
  2. In HIGH support mode, student types bare 'apply F' (no params) but the
     stored rule is 'apply F with a↦5, b↦0'.

No ORM calls outside of TestCase methods — safe for test discovery.

Run individually:
  $env:PYTHONIOENCODING="utf-8"; py manage.py test equational_reasoning_api.test_rule_comparison
"""

from django.test import TestCase
from equational_reasoning_api.views import normalize_rule_string, compare_rule


class NormalizeRuleStringTests(TestCase):
    """Unit tests for normalize_rule_string()."""

    def test_no_change_for_simple_rule(self):
        """A simple rule with no arrows or 'with' is returned as-is (whitespace collapsed)."""
        self.assertEqual(normalize_rule_string("eval -"), "eval -")

    def test_removes_with_keyword(self):
        """'with' between rule name and params is stripped."""
        result = normalize_rule_string("apply F with a=5, b=0")
        self.assertEqual(result, "apply F a=5, b=0")

    def test_unicode_mapsto_replaced(self):
        """Unicode ↦ (U+21A6) is replaced with '='."""
        result = normalize_rule_string("apply F with a\u21a65, b\u21a60")
        self.assertEqual(result, "apply F a=5, b=0")

    def test_unicode_arrow_replaced(self):
        """Unicode → (U+2192) is replaced with '='."""
        result = normalize_rule_string("apply F a\u21925, b\u21920")
        self.assertEqual(result, "apply F a=5, b=0")

    def test_spaces_around_equals_normalized(self):
        """Spaces around '=' are removed."""
        result = normalize_rule_string("apply F with a = 5, b = 0")
        self.assertEqual(result, "apply F a=5, b=0")

    def test_spaces_around_comma_normalized(self):
        """Comma spacing is normalized to exactly one space after."""
        result = normalize_rule_string("apply F a=5,b=0")
        self.assertEqual(result, "apply F a=5, b=0")

    def test_combined_normalization(self):
        """All normalizations applied together."""
        result = normalize_rule_string("apply F  with  a \u21a6 5 ,  b \u2192 0")
        self.assertEqual(result, "apply F a=5, b=0")

    def test_empty_string(self):
        """Empty string returns empty string."""
        self.assertEqual(normalize_rule_string(""), "")

    def test_none_returns_empty(self):
        """None input returns empty string."""
        self.assertEqual(normalize_rule_string(None), "")

    def test_with_only_removed_when_in_position(self):
        """'with' is only removed when it is the third token; 'rewrite with-cons' is untouched."""
        result = normalize_rule_string("rewrite with-cons")
        self.assertEqual(result, "rewrite with-cons")


class CompareRuleLowSupportTests(TestCase):
    """compare_rule() with high_support=False (LOW mode)."""

    def test_exact_match(self):
        """Stored and student are identical."""
        self.assertTrue(compare_rule("eval -", "eval -"))

    def test_without_keyword_matches_stored_without(self):
        """Student omits 'with'; stored also has no 'with' (both normalize same)."""
        self.assertTrue(compare_rule("apply F a=5, b=0", "apply F a=5, b=0"))

    def test_student_omits_with_keyword(self):
        """Student writes 'apply F a↦5, b↦0'; stored is 'apply F with a↦5, b↦0'."""
        self.assertTrue(compare_rule(
            "apply F a\u21a65, b\u21a60",
            "apply F with a\u21a65, b\u21a60"
        ))

    def test_student_uses_arrow_stored_uses_mapsto(self):
        """Student uses → arrow; stored uses ↦ arrow — both normalize to '='."""
        self.assertTrue(compare_rule(
            "apply F with a\u21925, b\u21920",
            "apply F with a\u21a65, b\u21a60"
        ))

    def test_student_uses_equals_stored_uses_mapsto(self):
        """Student types plain '='; stored has ↦."""
        self.assertTrue(compare_rule(
            "apply F with a=5, b=0",
            "apply F with a\u21a65, b\u21a60"
        ))

    def test_wrong_rule_name_fails(self):
        """Wrong rule name always fails."""
        self.assertFalse(compare_rule(
            "apply G a=5, b=0",
            "apply F with a\u21a65, b\u21a60"
        ))

    def test_wrong_param_value_fails(self):
        """Correct rule name but wrong value fails."""
        self.assertFalse(compare_rule(
            "apply F with a=99, b=0",
            "apply F with a\u21a65, b\u21a60"
        ))

    def test_bare_name_fails_in_low_mode(self):
        """Bare 'apply F' must NOT match in LOW mode even if name is correct."""
        self.assertFalse(compare_rule(
            "apply F",
            "apply F with a\u21a65, b\u21a60",
            high_support=False
        ))


class CompareRuleHighSupportTests(TestCase):
    """compare_rule() with high_support=True (HIGH mode)."""

    def test_bare_name_matches_stored_with_params(self):
        """In HIGH mode, 'apply F' matches 'apply F with a↦5, b↦0'."""
        self.assertTrue(compare_rule(
            "apply F",
            "apply F with a\u21a65, b\u21a60",
            high_support=True
        ))

    def test_bare_name_wrong_rule_still_fails(self):
        """In HIGH mode, 'apply G' does NOT match 'apply F with ...'."""
        self.assertFalse(compare_rule(
            "apply G",
            "apply F with a\u21a65, b\u21a60",
            high_support=True
        ))

    def test_explicit_correct_params_still_accepted_high_mode(self):
        """In HIGH mode, full explicit params still work."""
        self.assertTrue(compare_rule(
            "apply F with a=5, b=0",
            "apply F with a\u21a65, b\u21a60",
            high_support=True
        ))

    def test_explicit_wrong_params_still_rejected_high_mode(self):
        """In HIGH mode, wrong explicit params still fail."""
        self.assertFalse(compare_rule(
            "apply F with a=99, b=0",
            "apply F with a\u21a65, b\u21a60",
            high_support=True
        ))

    def test_bare_eval_matches_no_params_stored(self):
        """In HIGH mode, 'eval -' matches stored 'eval -' (no params case)."""
        self.assertTrue(compare_rule("eval -", "eval -", high_support=True))

    def test_partial_params_not_treated_as_bare_name(self):
        """'apply F a=5' (3 tokens after normalization) is NOT a bare name — must match exactly."""
        self.assertFalse(compare_rule(
            "apply F a=5",
            "apply F with a\u21a65, b\u21a60",
            high_support=True
        ))

    def test_bare_name_wrong_case_fails_high_mode(self):
        """In HIGH mode, 'apply f' (lowercase) does NOT match 'apply F with ...' — rule names are case-sensitive."""
        self.assertFalse(compare_rule(
            "apply f",
            "apply F with a\u21a65, b\u21a60",
            high_support=True
        ))

    def test_equals_no_with_no_comma_space_matches_low_mode(self):
        """'apply F a=5,b=0' (plain =, no 'with', no space after comma) matches in LOW mode via normalization."""
        self.assertTrue(compare_rule(
            "apply F a=5,b=0",
            "apply F with a\u21a65, b\u21a60",
            high_support=False
        ))

    def test_equals_no_with_no_comma_space_matches_high_mode(self):
        """Same as above but with high_support=True — normalization match, not bare-name path."""
        self.assertTrue(compare_rule(
            "apply F a=5,b=0",
            "apply F with a\u21a65, b\u21a60",
            high_support=True
        ))


class NormalizeWhitespaceTests(TestCase):
    """Extra whitespace in rule strings is collapsed by normalize_rule_string."""

    def test_leading_trailing_whitespace_ignored(self):
        """Leading and trailing spaces are stripped."""
        self.assertEqual(normalize_rule_string("  apply F  "), "apply F")

    def test_internal_extra_spaces_collapsed(self):
        """Multiple internal spaces between tokens are collapsed to one."""
        result = normalize_rule_string("apply      F")
        self.assertEqual(result, "apply F")

    def test_all_whitespace_variations_bare_name_high_mode(self):
        """'     apply      F    ' is treated as bare 'apply F' in HIGH mode."""
        self.assertTrue(compare_rule(
            "     apply      F    ",
            "apply F with a\u21a65, b\u21a60",
            high_support=True
        ))

    def test_all_whitespace_variations_bare_name_low_mode_fails(self):
        """Same input with extra whitespace still fails in LOW mode (bare name not accepted)."""
        self.assertFalse(compare_rule(
            "     apply      F    ",
            "apply F with a\u21a65, b\u21a60",
            high_support=False
        ))

    def test_wrong_case_with_extra_whitespace_fails(self):
        """'  apply   f  ' (extra whitespace + wrong case) still fails in HIGH mode."""
        self.assertFalse(compare_rule(
            "  apply   f  ",
            "apply F with a\u21a65, b\u21a60",
            high_support=True
        ))
