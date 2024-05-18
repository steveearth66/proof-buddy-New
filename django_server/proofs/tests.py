#from django.test import TestCase

# Create your tests here.
from expression_tree.ERProofEngine import ERProof

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
     ['+ takes in types [INT, INT], but provided inputs were [INT, BOOL]']),
    # too many args
    ("(+ 1 2 3)", ['+ only takes 2 arguments, but 3 were provided']),
    # insufficiently resolved
    ("(+ 1 (+ 2 3))", ['insufficiently resolved arguments']),
    ("(quotient 3 0)", ["denominator can't be zero"]),  # div by 0
    ("(remainder 2 0)", ["denominator can't be zero"]),  # div by 0
    # bad type
    ("(< 2 #f)", ['< takes in types [INT, INT], but provided inputs were [INT, BOOL]'])]

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

print("\nMath testing Errs:\n")
fails = 0
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
     'and takes in types [BOOL, BOOL], but provided inputs were [INT, BOOL]']),
    # bad type
    ("(not 1)", ['not takes in types [BOOL], but provided inputs were [INT]']),
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

print("all tests passed!\n" if fails == 0 else f"number of fails: {fails}\n")