"""
Regression test: build_lemma_rule() was incorrectly including the calling
proof's generic variable names in its 'reserved' set, causing any generic
(e.g. 'b') that also appeared as a free variable in the lemma premise to be
silently excluded from the lemma's parameter list.

Concrete failure:
  Proof 'revAppSingle' has generics {a, K, b}.
  Lemma 'nullAppSingle' has premise '(null? (append X (cons b null)))'.
  Before the fix, 'b' was in reserved (because it was a generic of the caller),
  so param_names came back as ['X'] instead of ['X', 'b'].
  The UI then rejected the rule with "requires 1 parameter (X), but 2 were given".

Fix: removed generics.keys() from the reserved set inside build_lemma_rule()
     and extract_free_vars() in LemmaApplicator.py.

Run with: python manage.py test induction_api.test_lemma_param_generics
"""

from django.test import SimpleTestCase
from expression_tree.IndProofs import IndProof
from expression_tree.default_udfs import DEFAULT_UDFS
from expression_tree.LemmaApplicator import build_lemma_rule, extract_free_vars


def _make_engine(generics: dict):
    """
    Build a list-induction leap LHS engine with DEFAULT_UDFS loaded and the
    given generics added (name -> type_str).
    """
    ind = IndProof(struct='list')
    lhs = ind.leapStep.LHS
    for d in DEFAULT_UDFS:
        label = d.get('label')
        type_str = d.get('type')
        body = d.get('expression')
        if label and type_str and body:
            lhs.addUDF(label, type_str, body)
    for name, type_str in generics.items():
        lhs.addGeneric(name, type_str)
    return lhs


class LemmaParamGenericRegressionTest(SimpleTestCase):
    """
    Generic variable names in the calling proof must not be excluded from a
    lemma's free-variable (parameter) list.
    """

    # ------------------------------------------------------------------
    # extract_free_vars
    # ------------------------------------------------------------------

    def test_extract_free_vars_ignores_caller_generics(self):
        """
        When the calling proof has 'b' as a generic, extract_free_vars must
        still return 'b' as a free variable of the lemma premise.
        """
        lhs = _make_engine({'a': 'any', 'K': 'list', 'b': 'any'})
        premise = '(null? (append X (cons b null)))'

        vars_, errs = extract_free_vars(premise, lhs.ruleSet, lhs.generics)

        self.assertEqual(errs, [], f"Unexpected parse errors: {errs}")
        self.assertIn('b', vars_,
            "extract_free_vars must include 'b' even though it is a generic of the caller")
        self.assertIn('X', vars_,
            "extract_free_vars must include 'X' as a free variable")

    def test_extract_free_vars_excludes_builtins(self):
        """Reserved labels (null, cons, null?, append, ...) must never appear as params."""
        lhs = _make_engine({})
        premise = '(null? (append X (cons b null)))'

        vars_, errs = extract_free_vars(premise, lhs.ruleSet, lhs.generics)

        for reserved in ('null', 'cons', 'null?', 'append', 'if', 'first', 'rest'):
            self.assertNotIn(reserved, vars_,
                f"Reserved label '{reserved}' must not appear in free vars")

    # ------------------------------------------------------------------
    # build_lemma_rule — param_names
    # ------------------------------------------------------------------

    def test_build_lemma_rule_two_params_with_caller_generic(self):
        """
        Regression: nullAppSingle's param_names must be ['X', 'b'] (sorted),
        not ['X'], when the calling proof has 'b' as a generic.
        """
        lhs = _make_engine({'a': 'any', 'K': 'list', 'b': 'any'})
        premise    = '(null? (append X (cons b null)))'
        conclusion = '#f'

        lemma, err = build_lemma_rule('nullAppSingle', premise, conclusion,
                                      lhs.ruleSet, lhs.generics)

        self.assertIsNone(err, f"build_lemma_rule returned an error: {err}")
        self.assertEqual(
            lemma.param_names, ['X', 'b'],
            f"Expected param_names=['X', 'b'], got {lemma.param_names}"
        )

    def test_build_lemma_rule_single_param_no_generics(self):
        """
        When called from a proof with no generics, a single free variable is
        found correctly.
        """
        lhs = _make_engine({})  # no generics
        premise    = '(null? (append X null))'
        conclusion = '#f'

        lemma, err = build_lemma_rule('simpleAppNull', premise, conclusion,
                                      lhs.ruleSet, lhs.generics)

        self.assertIsNone(err, f"build_lemma_rule returned an error: {err}")
        self.assertIn('X', lemma.param_names)
        self.assertNotIn('null', lemma.param_names)
        self.assertNotIn('append', lemma.param_names)

    def test_build_lemma_rule_multiple_generics_all_become_params(self):
        """
        All generic names that appear in the lemma premise must be included as
        parameters, regardless of how many generics the caller has.
        """
        lhs = _make_engine({'a': 'any', 'K': 'list', 'b': 'any', 'c': 'any'})
        # premise uses X, b, and c — none of which are the induction variable
        premise    = '(null? (append X (cons b (cons c null))))'
        conclusion = '#f'

        lemma, err = build_lemma_rule('multiGenLemma', premise, conclusion,
                                      lhs.ruleSet, lhs.generics)

        self.assertIsNone(err, f"build_lemma_rule returned an error: {err}")
        for expected in ('X', 'b', 'c'):
            self.assertIn(expected, lemma.param_names,
                f"'{expected}' should be a lemma parameter but is missing "
                f"from {lemma.param_names}")

    # ------------------------------------------------------------------
    # End-to-end: isApplicable accepts the correct number of params
    # ------------------------------------------------------------------

    def test_lemma_applicable_with_two_params(self):
        """
        After the fix, isApplicable must accept two assignments (X=..., b=...)
        without complaining about parameter count.
        """
        from expression_tree.IndProofs import IndProof as _IndProof
        from expression_tree.ERProofEngine import ERProofLine

        lhs = _make_engine({'a': 'any', 'K': 'list', 'b': 'any'})
        premise    = '(null? (append X (cons b null)))'
        conclusion = '#f'

        lemma, err = build_lemma_rule('nullAppSingle', premise, conclusion,
                                      lhs.ruleSet, lhs.generics)
        self.assertIsNone(err)
        self.assertEqual(lemma.param_names, ['X', 'b'])

        # Build a target node: (null? (append (cons a K) (cons b null)))
        lhs.addProofLine('(null? (append (cons a K) (cons b null)))')
        self.assertEqual(lhs.errLog, [], f"Premise parse failed: {lhs.errLog}")
        target_node = lhs.proofLines[-1].exprTree

        ok, msg = lemma.isApplicable(target_node, ['X=(cons a K)', 'b=b'])
        self.assertTrue(ok, f"isApplicable rejected valid 2-param call: {msg}")
