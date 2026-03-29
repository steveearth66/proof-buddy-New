"""
LemmaApplicator.py

Pure-engine utilities for applying a user-proved lemma as a rewrite rule.
No Django ORM access here — DB lookups live in the view layer.
"""

from .Parser import makeBasicAst
from .ERRuleset import LemmaRule
from .ERProofEngine import reservedLabels


def _collect_free_vars(node, reserved: set, result: set) -> None:
    """Recursively collect alphabetic leaf labels not in *reserved*."""
    if not node.children:
        d = node.data
        if d and d.isalpha() and d not in reserved:
            result.add(d)
    else:
        for child in node.children:
            _collect_free_vars(child, reserved, result)


def extract_free_vars(premise_str: str, ruleSet: dict, generics: dict) -> tuple:
    """
    Parse *premise_str* and return ``(param_names, error_messages)``.
    *param_names* is a sorted list of alphabetic labels that are not already
    defined in *ruleSet* or *generics*.
    """
    tree, errs = makeBasicAst(premise_str)
    if errs:
        return [], errs

    reserved = set(reservedLabels)
    for cat_dict in ruleSet.values():
        reserved |= set(cat_dict.keys())
    reserved |= set(generics.keys())

    vars_found: set = set()
    _collect_free_vars(tree, reserved, vars_found)
    return sorted(vars_found), []


def build_lemma_rule(label: str, premise_str: str, conclusion_str: str,
                     ruleSet: dict, generics: dict) -> tuple:
    """
    Parse *premise_str* and *conclusion_str*, extract free variables, and
    return ``(LemmaRule, error_msg)``.  *error_msg* is ``None`` on success.
    """
    premise_tree, errs = makeBasicAst(premise_str)
    if errs:
        return None, f"Could not parse lemma premise '{premise_str}': {errs[0]}"

    conclusion_tree, errs = makeBasicAst(conclusion_str)
    if errs:
        return None, f"Could not parse lemma conclusion '{conclusion_str}': {errs[0]}"

    reserved = set(reservedLabels)
    for cat_dict in ruleSet.values():
        reserved |= set(cat_dict.keys())
    reserved |= set(generics.keys())

    vars_found: set = set()
    _collect_free_vars(premise_tree, reserved, vars_found)
    param_names = sorted(vars_found)

    lemma = LemmaRule(label, premise_tree, conclusion_tree, param_names)
    return lemma, None


def validate_lemma_application(premise_str: str, conclusion_str: str,
                                raw_params: list, target_node,
                                ruleSet: dict, generics: dict,
                                lemma_label: str = "lemma") -> tuple:
    """
    Build the lemma rule from *premise_str*/*conclusion_str*, then validate
    and apply it to *target_node* using *raw_params* (e.g. ``["n=(+ k 1)"]``).

    Returns ``(ok: bool, error_msg: str | None, result_node: Node | None)``.
    """
    lemma, err = build_lemma_rule(lemma_label, premise_str, conclusion_str,
                                  ruleSet, generics)
    if err:
        return False, err, None

    ok, msg = lemma.isApplicable(target_node, raw_params)
    if not ok:
        return False, msg, None

    result_node = lemma.insertSubstitution(target_node)
    return True, None, result_node
