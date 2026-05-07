"""
Common test utilities and helper functions for proof testing
"""

from expression_tree.ERProofEngine import ERProof, ERProofLine, TwoSidedProof
from expression_tree.IndProofs import IndProof
from expression_tree.ERCommon import Node, makeJson, findNode
from expression_tree.ERRuleset import recursiveReplaceNodes, IH
import sympy as sp  # type: ignore
import json
import sys

_RED   = "\x1b[1;31m" if sys.stdout.isatty() else ""
_RESET = "\x1b[0m"    if sys.stdout.isatty() else ""


def show_node_ids(exprTree: Node, indent=0):
    if exprTree is None:
        return
    print("  " * indent + f"ID {exprTree.startPosition}: '{exprTree.data}' (type: {exprTree.type})")
    for child in exprTree.children:
        show_node_ids(child, indent + 1)


def find_node_id_by_data(exprTree: Node, data: str):
    if exprTree is None:
        return None
    if str(exprTree.data) == data:
        return exprTree.startPosition
    for child in exprTree.children:
        nid = find_node_id_by_data(child, data)
        if nid is not None:
            return nid
    return None


def find_call_node_id(exprTree: Node, op: str):
    if exprTree is None:
        return None
    if str(exprTree.data) == '(':
        if len(exprTree.children) > 0 and str(exprTree.children[0].data) == op:
            return exprTree.startPosition
    for child in exprTree.children:
        nid = find_call_node_id(child, op)
        if nid is not None:
            return nid
    return None


def do_single_test_case(rule: str, expr: str, expected, proof: ERProof = None) -> int:
    if proof == None:
        proof = ERProof()
    proof.addProofLine(expr, rule)
    ans = str(proof.errLog if proof.errLog != [] else proof.getPrevRacket())
    word = "errors" if isinstance(expected, list) else "output"
    expected = str(expected)
    proof.proofLines.clear()
    proof.errLog.clear()
    if ans == expected:
        return 0
    print(f"{_RED}FAIL: expr={expr} rule='{rule}' expected {word}: {expected} but got: {ans}{_RESET}\n")
    return 1


def run_test_cases(rule: str, tests: list[tuple], proof: ERProof = None, defaultGenerics=True) -> int:
    '''
    Runs test cases with a single rule\n
    defaultGenerics specifies whether or not to use the default generics k (int), p (bool), L (list), and x (any)
    '''
    if proof is None:
        proof = ERProof()
    if defaultGenerics:
        proof.addGeneric('k', 'int')
        proof.addGeneric('p', 'bool')
        proof.addGeneric('L', 'list')
        proof.addGeneric('M', 'list')
        proof.addGeneric('x', 'any')
    fails = 0
    for trial in tests:
        if len(trial) == 2:
            expr, expected = trial
            fails += do_single_test_case(rule, expr, expected, proof)
        else:
            expr, args, expected = trial
            justification = rule + ' with ' + args
            fails += do_single_test_case(justification, expr, expected, proof)
    return fails


def test_racket_function(func: str, tests: list[tuple], hasAxiom=False) -> int:
    # expects last test case to not have errors
    testProof = ERProof()
    fails = run_test_cases(f'eval {func}', tests, testProof)

    expr, _ = tests[-1]
    fails += do_single_test_case(func, expr,
                                 expected=["Rule must start with 'eval', 'apply', or 'rewrite'"],
                                 proof=testProof)
    fails += do_single_test_case('apply ' + func, expr, 
                                 [f"Cannot apply built-in Racket procedure"],
                                 proof=testProof)
    if not hasAxiom:
        fails += do_single_test_case('rewrite ' + func, expr,
                                expected=[f"Cannot rewrite using built-in Racket procedure"],
                                proof=testProof)
    return fails


def test_axiom(
    axiom: str,
    tests: list[tuple],
    proof: ERProof,
    builtInProp: bool = False,
    addDefaultGenerics: bool = False,
    eval_expected: list | None = None,
    apply_expected: list | None = None,
) -> int:
    # Add default generics only when explicitly requested to avoid duplicate-label errors.
    fails = run_test_cases(f'rewrite {axiom}', tests, proof, defaultGenerics=addDefaultGenerics)

    # Check that eval/apply emit the expected errors for axioms or built-ins.
    expr, *_ = tests[-1]
    if eval_expected is None:
        if builtInProp and axiom in {"and", "or", "implies"}:
            eval_expected = [f"Cannot evaluate '{axiom}' expression with generic arguments"]
        elif builtInProp:
            eval_expected = ["Insufficiently resolved arguments"]
        else:
            eval_expected = ["Cannot evaluate axiom"]

    if apply_expected is None:
        apply_expected = ["Cannot apply built-in Racket procedure"] if builtInProp else ["Cannot apply axiom"]

    fails += do_single_test_case(f'eval {axiom}', expr, eval_expected, proof)
    fails += do_single_test_case(f'apply {axiom}', expr, apply_expected, proof)
    return fails
