#from django.test import TestCase

# Create your tests here.
from expression_tree.ERProofEngine import ERProof, ERProofLine
from expression_tree.ERCommon import Node
import sympy as sp

err_strings = [
    # expected errs
    ("(cons 1 null)", ['Cannot apply math rule to cons']),  # bad operation
    # too many args
    ("(+ 1 1 1)", ['+ only takes 2 arguments, but 3 were provided']),
    # too few args
    ("(* 3)", ['* only takes 2 arguments, but 1 was provided']),
    ("(-)", ['- only takes 2 arguments, but 0 were provided']),  # no args
    ("(expt 0 0)", ['0^0 is undefined']),  # undef
    # fraction, not a legal input due to -1
    ("(expt 3 -1)", ['-1 contains illegal characters']),
    # bad type
    ("(+ 1 #t)",
     ["Cannot match argument out typeList ['INT', 'BOOL'] with expected typeList ['INT', 'INT']"]),
    # too many args
    ("(+ 1 2 3)", ['+ only takes 2 arguments, but 3 were provided']),
    # insufficiently resolved
    ("(+ 1 (+ 2 3))", ['insufficiently resolved arguments']),
    ("(quotient 3 0)", ["denominator can't be zero"]),  # div by 0
    ("(remainder 2 0)", ["denominator can't be zero"]),  # div by 0
    # bad type
    ("(< 2 #f)", ["Cannot match argument out typeList ['INT', 'BOOL'] with expected typeList ['INT', 'INT']"])]

good_strgs = [
    # expected output
    ("(expt 1 2)", 1),  # expt with 1 base
    ("(expt 2 0)", 1),  # expt with 0 power
    ("(expt 0 2)", 0),  # expt with 0 base
    ("(quotient 0 2)", 0),  # quotient with 0 numerator
    ("(expt 2 1)", 2),  # expt with 1 power
    ("(quotient 7 3)", 2),  # quotient with remainder
    ("(+ 1 2)", 3),  # addition
    ("(< 3 4)", "#t"),  # less than
    ("(< 4 3)", "#f")  # greater than
]

fails = 0

print("\nMath testing Errs:\n")
for trial in err_strings+good_strgs:
    expr, expected = trial
    print("input:", expr)
    proof = ERProof()
    proof.addProofLine(expr, 'math')

    ans = str(proof.errLog if proof.errLog != [] else proof.getPrevRacket())
    word = "errors" if isinstance(expected, list) else "output"
    expected = str(expected)
    if ans == expected:
        print(f"PASS: expected {word}: {ans}\n")
    else:
        print(f"FAIL! expected {word}: {expected} but got: {ans}\n")
        fails = +1

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
        fails += 1


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
    fails += 1

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
        fails += 1

print("\nall tests passed!\n" if fails == 0 else f"number of fails: {fails}\n")
#proof.addProofLine(expr, "math")
#print(f"before rule = {expr}, after rule = {proof.getPrevRacket() if proof.errLog == [] else proof.errLog}")