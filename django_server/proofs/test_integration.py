"""
Integration tests for proof engine - includes node method tests, JSON generation,
rewrite demonstrations, proof building, and full induction proofs
"""

import os
from expression_tree.ERProofEngine import ERProof, ERProofLine
from expression_tree.IndProofs import IndProof
from expression_tree.ERCommon import Node, makeJson, findNode
from expression_tree.ERRuleset import recursiveReplaceNodes, IH
import sympy as sp  # type: ignore

from .test_helpers import show_node_ids, find_node_id_by_data, find_call_node_id

SHOW_DETAILS = False  # set True locally if you want full step-by-step logs
totalFails = 0

print("[Summary] Node Method Tests")

# node method tests for funcset, ancestor, allMath, mathstr, logicStr: method, expr, expected
methTests = [
("funcset", "(+ (- 9 (* 2 3)) (quotient (+ 2 8) (remainder 7 3)))",\
 {'-', 'remainder', 'quotient', '*', '+'}),
("ancestors", "(+ (- 9 (* 2 3)) (quotient (+ 2 8) (remainder 7 3)))", ['(', '(']),
("allMath", "(+ (- 9 (* 2 3)) (quotient (+ 2 8) (remainder 7 3)))","True"),
("allMath", "(+ 3 (if #t 1 1))","False"),
("mathstr", "(expt 3 (if #t 2 2))","ERROR"),
("mathstr", "(+ 2 3)","(2+3)"),
("mathstr", "(expt x (+ 1 y))","(x**(1+y))"),
("mathstr", "(+ (- 9 (* 2 3))(quotient (+ 2 8)(remainder 7 3)))","((9-(2*3))+((2+8)//(7%3)))"),
("mathstr", "(= 2 3)", "(2==3)"),
("mathstr", "(< 2 3)", "(2<3)"),
("logicStr", "(if (and #t #t) (implies #t #f) (implies #f #t))", "ERROR"),
("logicStr", "(and #t (= 2 3))", "ERROR"),
("logicStr", "(not #t)", "(not True)"),
("logicStr", "(and #t #f)", "(True and False)"),
("logicStr", "(implies #t #f)", "(Implies(True, False))"),
("logicStr", "(or (not (xor #t #f)) (and #t #t))", "((not (Xor(True, False))) or (True and True))"),
("simp", "(expt (+ x 1) 2)" , "(x + 1)**2"),
("simp", "(+ (+ (* x x) (* 2 x)) 1)", "x**2 + 2*x + 1"),
("sub", ["(expt (+ x 1) 2)","(+ (+ (* x x) (* 2 x)) 2)"], "False"),
("sub", ["(expt (+ x 1) 2)","(+ (+ (* x x) (* 2 x)) 1)"], "True"),
]

for meth,expr, expected in methTests:
    if meth!="sub": #substitution test takes in 2 expressions
        expTree = ERProofLine(expr).exprTree
    if meth == "funcset":
        ans = expTree.funcSet()
    elif meth == "ancestors":
        qnode = expTree.children[2].children[1]
        ans = qnode.ancestors()
    elif meth == "allMath":
        ans = str(expTree.allMath())
    elif meth == "mathstr":
        ans = expTree.mathStr()
    elif meth == "logicStr":
        ans = expTree.logicStr()
    elif meth == "simp":
        ans = str(sp.sympify(expTree.mathStr()))
    elif meth == "sub":
        exp1 = ERProofLine(expr[0]).exprTree
        exp2 = ERProofLine(expr[1]).exprTree
        ans = str(sp.sympify(exp1.mathStr()).equals(sp.sympify(exp2.mathStr())))
    if ans != expected:
        print(f"FAIL: input={expTree if meth!='sub' else [str(exp1),str(exp2)]} method={meth} expected {expected} got={ans}")
        totalFails += 1
    elif SHOW_DETAILS:
        print(f"PASS: input={expTree if meth!='sub' else [str(exp1),str(exp2)]} method={meth} expected {expected} got={ans}")

print("\n[Summary] Position Dictionary Test")
check1 = ERProofLine("(if (zero? 5) (+ (* 2 10) 30) (* (+ 20 11) (+ 12 13)))")
expectDict = {0: [0, 1, 0, 0], 1: [0, 1, 1, 4], 4: [0, 5, 1, 14], 5: [4, 5, 5, 11], 11: [4, 11, 5, 11], 
14: [0, 15, 4, 30], 15: [14, 15, 15, 17], 17: [14, 18, 15, 26], 18: [17, 18, 18, 20], 20: [17, 20, 18, 22], 
22: [17, 22, 20, 22], 26: [14, 26, 17, 26], 30: [0, 31, 14, 30], 31: [30, 31, 31, 33], 33: [30, 34, 31, 43], 
34: [33, 34, 34, 36], 36: [33, 36, 34, 39], 39: [33, 39, 36, 39], 43: [30, 44, 33, 43], 44: [43, 44, 44, 46], 
46: [43, 46, 44, 49], 49: [43, 49, 46, 49]}
if check1.positions != expectDict:
    print(f"FAIL: position dict mismatch for {check1.exprTree}")
    totalFails += 1
elif SHOW_DETAILS:
    print(f"PASS: position dict for {check1.exprTree}")

if SHOW_DETAILS:
    print("\n[Summary] Nested Expression Parsing")
    nestcheck1 = ERProofLine("(if (zero? 5) (+ (* 2 10) 30) (* (+ 20 11) (+ 12 13)))")
    print(nestcheck1.errLog)
    nestcheck2 = ERProofLine("(first '(3 '(4 5) 6))")
    print(nestcheck2.errLog)

print("\n[Summary] JSON Generation Tests")
jsonstrgs = [
    "(-(+ 5 7)(*(+ 6 10) 2))",
    "(cons (if (= 2 3) 1 (+ (* 4 5) (* 6 7)) ) null)",
]
jsonans = [
    {0: {'data': '(', 'children': [1, 3, 11], 'startPosition': 0, 'parent': None, 'leftSib': None, 'rightSib': None}, 1: {'data': '-', 'children': [], 'startPosition': 1, 'parent': 0, 'leftSib': None, 'rightSib': 3}, 3: {'data': '(', 'children': [4, 6, 8], 'startPosition': 3, 'parent': 0, 'leftSib': 1, 'rightSib': 11}, 4: {'data': '+', 'children': [], 'startPosition': 4, 'parent': 3, 'leftSib': None, 'rightSib': 6}, 6: {'data': '5', 'children': [], 'startPosition': 6, 'parent': 3, 'leftSib': 4, 'rightSib': 8}, 8: {'data': '7', 'children': [], 'startPosition': 8, 'parent': 3, 'leftSib': 6, 'rightSib': None}, 11: {'data': '(', 'children': [12, 14, 23], 'startPosition': 11, 'parent': 0, 'leftSib': 3, 'rightSib': None}, 12: {'data': '*', 'children': [], 'startPosition': 12, 'parent': 11, 'leftSib': None, 'rightSib': 14}, 14: {'data': '(', 'children': [15, 17, 19], 'startPosition': 14, 'parent': 11, 'leftSib': 12, 'rightSib': 23}, 15: {'data': '+', 'children': [], 'startPosition': 15, 'parent': 14, 'leftSib': None, 'rightSib': 17}, 17: {'data': '6', 'children': [], 'startPosition': 17, 'parent': 14, 'leftSib': 15, 'rightSib': 19}, 19: {'data': '10', 'children': [], 'startPosition': 19, 'parent': 14, 'leftSib': 17, 'rightSib': None}, 23: {'data': '2', 'children': [], 'startPosition': 23, 'parent': 11, 'leftSib': 14, 'rightSib': None}},
    {0: {'data': '(', 'children': [1, 6, 41], 'startPosition': 0, 'parent': None, 'leftSib': None, 'rightSib': None}, 1: {'data': 'cons', 'children': [], 'startPosition': 1, 'parent': 0, 'leftSib': None, 'rightSib': 6}, 6: {'data': '(', 'children': [7, 10, 18, 20], 'startPosition': 6, 'parent': 0, 'leftSib': 1, 'rightSib': 41}, 7: {'data': 'if', 'children': [], 'startPosition': 7, 'parent': 6, 'leftSib': None, 'rightSib': 10}, 10: {'data': '(', 'children': [11, 13, 15], 'startPosition': 10, 'parent': 6, 'leftSib': 7, 'rightSib': 18}, 11: {'data': '=', 'children': [], 'startPosition': 11, 'parent': 10, 'leftSib': None, 'rightSib': 13}, 13: {'data': '2', 'children': [], 'startPosition': 13, 'parent': 10, 'leftSib': 11, 'rightSib': 15}, 15: {'data': '3', 'children': [], 'startPosition': 15, 'parent': 10, 'leftSib': 13, 'rightSib': None}, 18: {'data': '1', 'children': [], 'startPosition': 18, 'parent': 6, 'leftSib': 10, 'rightSib': 20}, 20: {'data': '(', 'children': [21, 23, 31], 'startPosition': 20, 'parent': 6, 'leftSib': 18, 'rightSib': None}, 21: {'data': '+', 'children': [], 'startPosition': 21, 'parent': 20, 'leftSib': None, 'rightSib': 23}, 23: {'data': '(', 'children': [24, 26, 28], 'startPosition': 23, 'parent': 20, 'leftSib': 21, 'rightSib': 31}, 24: {'data': '*', 'children': [], 'startPosition': 24, 'parent': 23, 'leftSib': None, 'rightSib': 26}, 26: {'data': '4', 'children': [], 'startPosition': 26, 'parent': 23, 'leftSib': 24, 'rightSib': 28}, 28: {'data': '5', 'children': [], 'startPosition': 28, 'parent': 23, 'leftSib': 26, 'rightSib': None}, 31: {'data': '(', 'children': [32, 34, 36], 'startPosition': 31, 'parent': 20, 'leftSib': 23, 'rightSib': None}, 32: {'data': '*', 'children': [], 'startPosition': 32, 'parent': 31, 'leftSib': None, 'rightSib': 34}, 34: {'data': '6', 'children': [], 'startPosition': 34, 'parent': 31, 'leftSib': 32, 'rightSib': 36}, 36: {'data': '7', 'children': [], 'startPosition': 36, 'parent': 31, 'leftSib': 34, 'rightSib': None}, 41: {'data': 'null', 'children': [], 'startPosition': 41, 'parent': 0, 'leftSib': 6, 'rightSib': None}},
]
jerrs = 0
for js,ans in zip(jsonstrgs,jsonans):
    if (myans:=makeJson(ERProofLine(js).exprTree)) != ans:
        print(f"FAIL: makeJson on {js} expected {ans} but got {myans}")
        jerrs += 1
    elif SHOW_DETAILS:
        print(f"PASS: makeJson on {js}")
print(f"number of json errors: {jerrs}")
totalFails += jerrs

if SHOW_DETAILS:
    print("\n[Summary] Rewrite -+ on (- (+ k 1) 1)")
    test_proof1 = ERProof()
    test_proof1.addGeneric('k', 'int')
    test_expr1 = "(- (+ k 1) 1)"
    print(f"Input expression: {test_expr1}")
    test_proof1.addProofLine(test_expr1)
    print(f"Line 0 added as premise: {test_proof1.getPrevRacket()}")
    prev = test_proof1.getPrevRacket()
    test_proof1.addProofLine(prev, "rewrite -+ with k=k, a=1", 0)
    print(f"After applying 'rewrite -+' to node 0: {test_proof1.getPrevRacket()}")       
    print(f"\nComplete proof:\n{test_proof1}")

if SHOW_DETAILS:
    print("\n[Summary] ERProof __str__ Demo")
    proof = ERProof()
    proof.addProofLine("(+ 1 2)")
    print(f"Line 0 added as premise: (+ 1 2)")
    prev = proof.getPrevRacket()
    proof.addProofLine(prev, "eval +", 0)
    print("Applied 'eval +' to node 0 of previous line")
    print(f"\nComplete proof using __str__:")
    print(proof)
    print(f"\nProof has {len(proof.proofLines)} lines")
    print(f"Line 0 appliedRule: '{proof.proofLines[0].appliedRule}'")
    print(f"Line 1 appliedRule: '{proof.proofLines[1].appliedRule}'")
    print(f"Line 1 appliedRuleNodeId: {proof.proofLines[1].appliedRuleNodeId}")

if SHOW_DETAILS:
    print("\n[Summary] List Operations Proof")
    proof2 = ERProof()
    proof2.addProofLine("(first (rest (cons 1 (cons 2 null))))")
    print(f"Line 0 added as premise: (first (rest (cons 1 (cons 2 null))))")
    print(f"Node IDs in line 0:")
    show_node_ids(proof2.proofLines[0].exprTree)
    prev = proof2.getPrevRacket()
    proof2.addProofLine(prev, "rewrite rest-cons with x=1, L=(cons 2 null)", 7)
    print("Applied 'rewrite rest-cons' to node 7 of previous line")
    prev = proof2.getPrevRacket()
    proof2.addProofLine(prev, "rewrite first-cons with x=2, L=null", 0)
    print("Applied 'rewrite first-cons' to node 0 of previous line")
    print(f"\nComplete list operations proof:")
    print(proof2)
    print(f"\nProof has {len(proof2.proofLines)} lines")

if SHOW_DETAILS:
    print("\n[Summary] UDF (f n) Proof")
    proof3 = ERProof()
    proof3.removeUDF('f')
    proof3.addUDF("(f n)", "int>int", "(if (zero? n) 0 (+ n (f (- n 1))))")
    if proof3.errLog:
        print(f"Error adding UDF f: {proof3.errLog}")
        proof3.errLog.clear()

    if 'f' in proof3.ruleSet['apply']:
        proof3.addProofLine("(f 0)")
        if len(proof3.proofLines) == 0:
            print(f"Error adding premise (f 0): {proof3.errLog}")
            proof3.errLog.clear()
        else:
            print("Line 0 added as premise: (f 0)")
            prev = proof3.getPrevRacket()
            proof3.addProofLine(prev, "apply f n=0", 0)
            if proof3.errLog:
                print(f"Error applying 'apply f n=0': {proof3.errLog}")
                proof3.errLog.clear()
            else:
                print("Applied 'apply f n=0' to node 0 of previous line")
                zero_id = find_call_node_id(proof3.proofLines[-1].exprTree, 'zero?')
                if zero_id is not None:
                    prev = proof3.getPrevRacket()
                    proof3.addProofLine(prev, "eval zero?", zero_id)
                    if proof3.errLog:
                        print(f"Error applying 'eval zero?': {proof3.errLog}")
                        proof3.errLog.clear()
                    else:
                        print(f"Applied 'eval zero?' to node {zero_id} of previous line")
                else:
                    print("Could not find '(zero? ...)' call node to evaluate")
            prev = proof3.getPrevRacket()
            proof3.addProofLine(prev, "eval if", 0)
            if proof3.errLog:
                print(f"Error applying 'eval if': {proof3.errLog}")
                proof3.errLog.clear()
            else:
                print("Applied 'eval if' to node 0 of previous line")

        # Print the complete proof
        print(f"\nComplete UDF (f n) proof:\n")
        print(proof3)
        print(f"\nProof has {len(proof3.proofLines)} lines")


if SHOW_DETAILS:
    # Demonstrate math rewrite success and failure on the single k node
    print("\n\n[Summary] Testing Math Rewrite on k within (+ k 2) -> replace k with (* 1 k):\n")
    math_proof_ok = ERProof()
    math_proof_ok.addGeneric('k', 'int')
    expr_math = "(+ k 2)"
    math_proof_ok.addProofLine(expr_math)
    k_id = find_node_id_by_data(math_proof_ok.proofLines[-1].exprTree, 'k')
    math_proof_ok.addProofLine(math_proof_ok.getPrevRacket(), "rewrite math", k_id, "(* 1 k)")
    if math_proof_ok.errLog:
        print(f"Math rewrite (expected success) errors: {math_proof_ok.errLog}")
    else:
        print(f"After math rewrite success: {math_proof_ok.getPrevRacket()}")
        print(f"Complete proof:\n{math_proof_ok}")

    print("\n[Summary] Testing math rewrite on k within (+ k 2) with non-equivalent substitute (* 3 k):\n")
    math_proof_fail = ERProof()
    math_proof_fail.addGeneric('k', 'int')
    math_proof_fail.addProofLine(expr_math)
    k_id_fail = find_node_id_by_data(math_proof_fail.proofLines[-1].exprTree, 'k')
    math_proof_fail.addProofLine(math_proof_fail.getPrevRacket(), "rewrite math", k_id_fail, "(* 3 k)")
    if math_proof_fail.errLog:
        print(f"Math rewrite (expected failure) errors: {math_proof_fail.errLog}")
    else:
        print(f"Unexpected success: {math_proof_fail.getPrevRacket()}")
        print(f"Complete proof:\n{math_proof_fail}")

    # TEST: Quotient floor division rewrite - verifies that rewrite math with quotient works correctly
    print("\n[Summary] Quotient Floor Division Rewrite")
    print("Goal: (zero? (quotient k (+ k 1))) -> (zero? 0)")

    proof_quotient_test = ERProof()
    proof_quotient_test.addGeneric('k', 'int')
    expr_quotient = "(zero? (quotient k (+ k 1)))"
    proof_quotient_test.addProofLine(expr_quotient)
    print(f"Premise: {expr_quotient}")

    if not proof_quotient_test.errLog:
        prev = proof_quotient_test.getPrevRacket()
        proof_quotient_test.addProofLine(prev, "rewrite math", 7, "0")
        if proof_quotient_test.errLog:
            print(f"Result: FAIL — {proof_quotient_test.errLog}")
        else:
            result = str(proof_quotient_test.proofLines[-1].exprTree)
            expected = "(zero? 0)"
            print(f"After rewrite: {result}")
            if result == expected:
                print("Result: PASS — floor division semantics preserved")
            else:
                print(f"Result: FAIL — expected {expected}, got {result}")
    else:
        print(f"Result: FAIL — error parsing initial expression: {proof_quotient_test.errLog}")

# Continue with induction proof tests (from lines 1000-1648 of original file)
