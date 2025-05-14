#from django.test import TestCase

# Create your tests here.
from expression_tree.ERProofEngine import ERProof, ERProofLine
from expression_tree.ERCommon import Node
import sympy as sp
import json
from expression_tree.ERCommon import makeJson

def test_loop_body(func: str, expr: str, expected, prefix: str = 'eval') -> int:
    if prefix != '':
        prefix += ' '
    print("input:", expr)
    proof = ERProof()
    proof.addProofLine(expr, prefix + func)
    ans = str(proof.errLog if proof.errLog != [] else proof.getPrevRacket())
    word = "errors" if isinstance(expected, list) else "output"
    expected = str(expected)
    if ans == expected:
        print(f"PASS: expected {word}: {ans}\n")
        return 0
    else:
        print(f"FAIL! expected {word}: {expected} but got: {ans}\n")
        return 1

def test_racket_function(func: str, tests: list[tuple]) -> int:
    # expects last test case to not have errors
    fails = 0
    for trial in tests:
        expr, expected = trial
        fails += test_loop_body(func, expr, expected)
    fails += test_loop_body(func, expr, 
                            expected=["Rule must start with 'eval' or 'apply'"], prefix='')
    fails += test_loop_body(func, expr,
                            expected=['Cannot apply built-in Racket function'], prefix='apply')
    return fails

totalFails = 0

plus_tests = [
     # bad operation
    ("(cons 1 null)", ['Cannot apply + rule to cons']),
    #("(* 2 3)", ['Cannot apply + rule to *']) # commented out due to low priority
    # too few arguments
    ("(+ 1)", ['+ only takes 2 arguments, but 1 was provided']),
    ("(+)", ['+ only takes 2 arguments, but 0 were provided']),
    ("(+ 1 1 1)", ['+ only takes 2 arguments, but 3 were provided']), # too many arguments
    ("(+ 1 #t)",
    ["Cannot match argument out typeList ['INT', 'BOOL'] with expected typeList ['INT', 'INT']"]), # bad type
    ("(+ 1 (+ 2 3))", ['insufficiently resolved arguments']), # insufficiently resolved
    ("(+ 1 2)", 3) # valid test case
]
totalFails += test_racket_function('+', plus_tests)

minus_tests = [
    # bad operation
    ("(cons 1 null)", ['Cannot apply - rule to cons']),
    #("(* 2 3)", ['Cannot apply - rule to *']) # commented out due to low priority
    # too few arguments
    ("(- 3)", ['- only takes 2 arguments, but 1 was provided']),
    ("(-)", ['- only takes 2 arguments, but 0 were provided']),
    ("(- 5 1 2)", ['- only takes 2 arguments, but 3 were provided']), # too many arguments
    ("(- #f 1)",
    ["Cannot match argument out typeList ['BOOL', 'INT'] with expected typeList ['INT', 'INT']"]), # bad type
    ("(- 5 (- 2 1))", ['insufficiently resolved arguments']), # insufficiently resolved
    ("(- 3 5)", -2), # output negative number
    ("(- 5 3)", 2) # valid test case
]
totalFails += test_racket_function('-', minus_tests)

times_tests = [
    ("(cons 1 null)", ['Cannot apply - rule to cons']),
    #("(- 2 3)", ['Cannot apply * rule to -']) # commented out due to low priority
    ("(* 3)", ['* only takes 2 arguments, but 1 was provided']), # too few arguments
    ("(* 2 3 4)", ['* only takes 2 arguments, but 3 were provided']), # too many arguments
    ("(* #t 1)",
    ["Cannot match argument out typeList ['BOOL', 'INT'] with expected typeList ['INT', 'INT']"]), # bad type
    ("(* 2 (+ 3 4))", ['insufficiently resolved arguments']), # insufficiently resolved
    ("(* 8 9)", 72) # valid test case
]
totalFails += test_racket_function('*', times_tests)

quotient_tests = [
    # bad operation
    ("(cons 1 null)", ['Cannot apply quotient rule to cons']),
    #("(* 2 3)", ['Cannot apply quotient rule to *']) # commented out due to low priority
    ("(quotient 3)", ['quotient only takes 2 arguments, but 1 was provided']), # too few arguments
    ("(quotient 12 2 3)", ['quotient only takes 2 arguments, but 3 were provided']), # too many arguments
    ("(quotient #t 1)",
    ["Cannot match argument out typeList ['BOOL', 'INT'] with expected typeList ['INT', 'INT']"]), # bad type
    ("(quotient 12 (quotient 6 2))", ['insufficiently resolved arguments']), # insufficiently resolved
    ("(quotient 3 0)", ["denominator can't be zero"]), # division by zero
    ("(quotient 0 2)", 0),  # quotient with 0 numerator
    ("(quotient 7 3)", 2)  # quotient with remainder
]
totalFails += test_racket_function('quotient', quotient_tests)

remainder_tests = [
    # bad operation
    ("(cons 1 null)", ['Cannot apply remainder rule to cons']),
    #("(* 2 3)", ['Cannot apply remainder rule to *']) # commented out due to low priority
    ("(remainder 3)", ['remainder only takes 2 arguments, but 1 was provided']), # too few arguments
    ("(remainder 14 5 3)", ['remainder only takes 2 arguments, but 3 were provided']), # too many arguments
    ("(remainder 5 #t)",
    ["Cannot match argument out typeList ['INT', 'BOOL'] with expected typeList ['INT', 'INT']"]), # bad type
    ("(remainder 12 (quotient 29 6))", ['insufficiently resolved arguments']), # insufficiently resolved
    ("(remainder 2 0)", ["denominator can't be zero"]), # division by zero
    ("(remainder 0 2)", 0),  # remainder with 0 numerator
    ("(remainder 14 5)", 4)  # normal test case
]
totalFails = test_racket_function('remainder', remainder_tests)

expt_tests = [
    # bad operation
    ("(cons 1 null)", ['Cannot apply expt rule to cons']),
    #("(* 2 3)", ['Cannot apply expt rule to *']) # commented out due to low priority
    ("(expt 3)", ['expt only takes 2 arguments, but 1 was provided']), # too few arguments
    ("(expt 2 2 2)", ['expt only takes 2 arguments, but 3 were provided']), # too many arguments
    ("(expt 5 #t)",
    ["Cannot match argument out typeList ['INT', 'BOOL'] with expected typeList ['INT', 'INT']"]), # bad type
    ("(expt 3 (expt 2 2))", ['insufficiently resolved arguments']), # insufficiently resolved
    ("(expt 0 0)", ['0^0 is undefined']),  # undef
    ("(expt 3 -1)", ['-1 contains illegal characters']), # fraction, not a legal input due to -1
    ("(expt 2 0)", 1), # expt with 0 power
    ("(expt 0 2)", 0), # expt with 0 base
    ("(expt 2 3)", 8) # normal test case
]
totalFails = test_racket_function('expt', expt_tests)

eq_tests = [
    # bad operation
    ("(cons 1 null)", ['Cannot apply = rule to cons']),
    #("(* 2 3)", ['Cannot apply = rule to *']) # commented out due to low priority
    ("(= 3)", ['= only takes 2 arguments, but 1 was provided']), # too few arguments
    ("(= 2 2 2)", ['= only takes 2 arguments, but 3 were provided']), # too many arguments
    ("(= #t #t)",
    ["Cannot match argument out typeList ['BOOL', 'BOOL'] with expected typeList ['INT', 'INT']"]), # bad type
    ("(= 3 (+ 1 2))", ['insufficiently resolved arguments']), # insufficiently resolved
    ("(< 4 3)", '#f'), # greater than
    ("(< 3 3)", '#t'), # equal
    ("(< 3 4)", '#f') # less than
]
totalFails += test_racket_function('=', eq_tests)

lt_tests = [
    # bad operation
    ("(cons 1 null)", ['Cannot apply < rule to cons']),
    #("(<= 2 3)", ['Cannot apply < rule to <=']) # commented out due to low priority
    ("(< 3)", ['< only takes 2 arguments, but 1 was provided']), # too few arguments
    ("(< 2 3 4)", ['< only takes 2 arguments, but 3 were provided']), # too many arguments
    ("(< #f #t)",
    ["Cannot match argument out typeList ['BOOL', 'BOOL'] with expected typeList ['INT', 'INT']"]), # bad type
    ("(< 3 (+ 1 2))", ['insufficiently resolved arguments']), # insufficiently resolved
    ("(< 4 3)", '#f'), # greater than
    ("(< 3 3)", '#f'), # equal
    ("(< 3 4)", '#t') # less than
]
totalFails += test_racket_function('<', lt_tests)

le_tests = [
    # bad operation
    ("(cons 1 null)", ['Cannot apply <= rule to cons']),
    #("(< 2 3)", ['Cannot apply <= rule to <']) # commented out due to low priority
    ("(<= 3)", ['<= only takes 2 arguments, but 1 was provided']), # too few arguments
    ("(<= 2 3 4)", ['<= only takes 2 arguments, but 3 were provided']), # too many arguments
    ("(<= 0 #t)",
    ["Cannot match argument out typeList ['INT', 'BOOL'] with expected typeList ['INT', 'INT']"]), # bad type
    ("(<= 3 (+ 1 2))", ['insufficiently resolved arguments']), # insufficiently resolved
    ("(<= 4 3)", '#f'), # greater than
    ("(<= 3 3)", '#t'), # equal
    ("(<= 3 4)", '#t') # less than
]
totalFails += test_racket_function('<=', le_tests)

gt_tests = [
    # bad operation
    ("(cons 1 null)", ['Cannot apply > rule to cons']),
    #("(< 2 3)", ['Cannot apply > rule to <']) # commented out due to low priority
    ("(> 3)", ['> only takes 2 arguments, but 1 was provided']), # too few arguments
    ("(> 4 3 2)", ['> only takes 2 arguments, but 3 were provided']), # too many arguments
    ("(> 1 #f)",
    ["Cannot match argument out typeList ['INT', 'BOOL'] with expected typeList ['INT', 'INT']"]), # bad type
    ("(> 3 (+ 1 2))", ['insufficiently resolved arguments']), # insufficiently resolved
    ("(> 4 3)", '#t'), # greater than
    ("(> 3 3)", '#f'), # equal
    ("(> 3 4)", '#f') # less than
]
totalFails += test_racket_function('>', gt_tests)

ge_tests = [
    # bad operation
    ("(cons 1 null)", ['Cannot apply >= rule to cons']),
    #("(< 2 3)", ['Cannot apply >= rule to <']) # commented out due to low priority
    ("(>= 3)", ['>= only takes 2 arguments, but 1 was provided']), # too few arguments
    ("(>= 4 3 2)", ['>= only takes 2 arguments, but 3 were provided']), # too many arguments
    ("(>= #f #t)",
    ["Cannot match argument out typeList ['BOOL', 'BOOL'] with expected typeList ['INT', 'INT']"]), # bad type
    ("(>= 3 (+ 1 2))", ['insufficiently resolved arguments']), # insufficiently resolved
    ("(>= 4 3)", '#t'), # greater than
    ("(>= 3 3)", '#t'), # equal
    ("(>= 3 4)", '#f') # less than
]
totalFails += test_racket_function('>=', ge_tests)

Log_err_strings = [
    # expected errs
    ("(cons 1 null)", ['Cannot apply logic rule to cons']),  # bad operation
    # too many args
    ("(or #t #t #t)", ['or only takes 2 arguments, but 3 were provided']),
    # too few args
    ("(and 3)", ['and only takes 2 arguments, but 1 was provided']),
    # no args
    ("(implies)", ['implies only takes 2 arguments, but 0 were provided']),
    ("(and 1 #t)", [
     # bad type
     "Cannot match argument out typeList ['INT', 'BOOL'] with expected typeList ['BOOL', 'BOOL']"]),
    # bad type
    ("(not 1)", ["Cannot match argument out typeList ['INT'] with expected typeList ['BOOL']"]),
    # too many args
    ("(not #t #f)", ['not only takes 1 arguments, but 2 were provided']),
    # insufficiently resolved
    ("(or #t (and #f #f))", ['insufficiently resolved arguments'])
]

Log_good_strgs = [
    # expected output
    ("(not #t)", "#f"),
    ("(not #f)", "#t"),
    ("(and #t #t)", "#t"),
    ("(or #f #f)", "#f"),
    ("(implies #f #f)", "#t"),
    ("(implies #t #f)", "#f"),
    # ("(nand #t #f)", "#t"),
    # ("(iff #f #f)", "#t"),
    # ("(iff #f #t)", "#f"),
    # ("(nor #f #f)", "#t"),
    ("(xor #t #t)", "#f")
]

print("\nLogic testing Errs:\n")
for trial in Log_err_strings+Log_good_strgs:
    expr, expected = trial
    print("input:", expr)
    proof = ERProof()
    proof.addProofLine(expr, 'logic')

    ans = str(proof.errLog if proof.errLog != [] else proof.getPrevRacket())
    word = "errors" if isinstance(expected, list) else "output"
    expected = str(expected)
    if ans == expected:
        print(f"PASS: expected {word}: {ans}\n")
    else:
        print(f"FAIL! expected {word}: {expected} but got: {ans}\n")
        totalFails += 1


print("\nUDF testing:\n")
proof=ERProof()
proof.addUDF("(f x y)", "(INT,INT)>INT", "(* x y)")
proof.addProofLine("(f 3 4)", "f")
print("(f x y) defined as (* x y)")
print("input: (f 3 4), using rule f")
ans = str(proof.errLog if proof.errLog != [] else proof.getPrevRacket())
expected = "(* 3 4)"
word = "errors" if isinstance(expected, list) else "output"
if ans == expected:
    print(f"PASS: expected {word}: {ans}\n")
else:
    print(f"FAIL! expected {word}: {expected} but got: {ans}\n")
    totalFails += 1

#node method tests for funcset, ancestor, allMath, mathstr: method, expr, expected
methTests = [
("funcset", "(+ (- 9 (* 2 3)) (quotient (+ 2 8) (remainder 7 3)))",\
 {'-', 'remainder', 'quotient', '*', '+'}),
("ancestors", "(+ (- 9 (* 2 3)) (quotient (+ 2 8) (remainder 7 3)))", ['(', '(']),
("allMath", "(+ (- 9 (* 2 3)) (quotient (+ 2 8) (remainder 7 3)))","True"),
("allMath", "(+ 3 (if #t 1 1))","False"),
("mathstr", "(expt 3 (if #t 2 2))","ERROR"),
("mathstr", "(+ 2 3)","(2+3)"),
("mathstr", "(expt x (+ 1 y))","(x**(1+y))"),
("mathstr", "(+ (- 9 (* 2 3))(quotient (+ 2 8)(remainder 7 3)))","((9-(2*3))+((2+8)/(7%3)))"),
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
    elif meth == "simp":
        ans = str(sp.sympify(expTree.mathStr()))
    elif meth == "sub":
        exp1 = ERProofLine(expr[0]).exprTree
        exp2 = ERProofLine(expr[1]).exprTree
        ans = str(sp.sympify(exp1.mathStr()).equals(sp.sympify(exp2.mathStr())))
    print(f"{'PASS' if ans==expected else 'FAIL'}: for input={expTree if meth!='sub' else [str(exp1),str(exp2)]} with method {meth}, expected {expected} and got={ans}")
    if ans!=expected:
        totalFails += 1

print("\nall tests passed!\n" if totalFails == 0 else f"number of fails: {totalFails}\n")

proof=ERProof()
proof.addUDF("(f x)", "int>int", "(if (zero? x) 0 (+ x (f (- x 1))))")
if proof.errLog != []:
    print(proof.errLog)
else:
    print("no errors with UDF")
proof.addProofLine("(f 3)", "f")
#proof.addProofLine(expr, "math")
#print(f"before rule = {expr}, after rule = {proof.getPrevRacket() if proof.errLog == [] else proof.errLog}")
print("ready to check posDict")
check1 = ERProofLine("(if (zero? 5) (+ (* 2 10) 30) (* (+ 20 11) (+ 12 13)))")
expectDict = {0: [0, 1, 0, 0], 1: [0, 1, 1, 4], 4: [0, 5, 1, 14], 5: [4, 5, 5, 11], 11: [4, 11, 5, 11], 
14: [0, 15, 4, 30], 15: [14, 15, 15, 17], 17: [14, 18, 15, 26], 18: [17, 18, 18, 20], 20: [17, 20, 18, 22], 
22: [17, 22, 20, 22], 26: [14, 26, 17, 26], 30: [0, 31, 14, 30], 31: [30, 31, 31, 33], 33: [30, 34, 31, 43], 
34: [33, 34, 34, 36], 36: [33, 36, 34, 39], 39: [33, 39, 36, 39], 43: [30, 44, 33, 43], 44: [43, 44, 44, 46], 
46: [43, 46, 44, 49], 49: [43, 49, 46, 49]}
print(f"{'PASS' if check1.positions == expectDict else 'FAIL'}: for position dict of {check1.exprTree}")

nestcheck1 = ERProofLine("(if (zero? 5) (+ (* 2 10) 30) (* (+ 20 11) (+ 12 13)))")
print(nestcheck1.errLog)
nestcheck2 = ERProofLine("(first '(3 '(4 5) 6))")
print(nestcheck2.errLog)
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
    else:
        print(f"PASS: makeJson on {js}")
print(f"number of json errors: {jerrs}")