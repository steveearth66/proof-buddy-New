#from django.test import TestCase

# Create your tests here.
from expression_tree.ERProofEngine import ERProof, ERProofLine
from expression_tree.ERCommon import Node
import sympy as sp
import json
from expression_tree.ERCommon import makeJson

def do_single_test_case(prefix: str, func: str, expr: str, expected, proof: ERProof = None) -> int:
    if proof == None:
        proof = ERProof()
    if prefix != '':
        prefix += ' '
    rule = prefix + func
    print(f"input: {expr}, using rule '{rule}'")
    proof.addProofLine(expr, rule)
    ans = str(proof.errLog if proof.errLog != [] else proof.getPrevRacket())
    word = "errors" if isinstance(expected, list) else "output"
    expected = str(expected)
    proof.proofLines.clear()
    proof.errLog.clear()
    if ans == expected:
        print(f"PASS: expected {word}: {ans}\n")
        return 0
    else:
        print(f"FAIL! expected {word}: {expected} but got: {ans}\n")
        return 1

def run_test_cases(prefix: str, func: str, tests: list[tuple]) -> int:
    fails = 0
    for trial in tests:
        expr, expected = trial
        fails += do_single_test_case(prefix, func, expr, expected)
    return fails

def test_racket_function(func: str, tests: list[tuple], appliable=False) -> int:
    # expects last test case to not have errors
    fails = run_test_cases('eval', func, tests)

    expr, _ = tests[-1]
    fails += do_single_test_case('', func, expr, 
                            expected=["Rule must start with 'eval' or 'apply'"])
    if not appliable:
        fails += do_single_test_case('apply', func, expr,
                                expected=[f'Could not find UDF/lemma/property associated with {func}'])
    return fails

def test_list_func_props(func: str, tests: list[tuple]) -> int:
    fails = run_test_cases('apply', func, tests)
    expr, _ = tests[-1]
    fails += do_single_test_case('apply', func + 'Prop', expr, [f'Could not find rule associated with {func + 'Prop'}'])
    return fails

totalFails = 0

# Math function tests
print('Testing Math Rules:\n')
plus_tests = [
     # bad operation
    ("(cons 1 null)", ["Cannot evaluate + on a 'cons' expression"]),
    ("(* 2 3)", ["Cannot evaluate + on a '*' expression"]),
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
    ("(cons 1 null)", ["Cannot evaluate - on a 'cons' expression"]),
    ("(* 2 3)", ["Cannot evaluate - on a '*' expression"]),
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
    ("(cons 1 null)", ["Cannot evaluate * on a 'cons' expression"]),
    ("(- 2 3)", ["Cannot evaluate * on a '-' expression"]),
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
    ("(cons 1 null)", ["Cannot evaluate quotient on a 'cons' expression"]),
    ("(* 2 3)", ["Cannot evaluate quotient on a '*' expression"]),
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
    ("(cons 1 null)", ["Cannot evaluate remainder on a 'cons' expression"]),
    ("(* 2 3)", ["Cannot evaluate remainder on a '*' expression"]),
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
    ("(cons 1 null)", ["Cannot evaluate expt on a 'cons' expression"]),
    ("(* 2 3)", ["Cannot evaluate expt on a '*' expression"]),
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
    ("(cons 1 null)", ["Cannot evaluate = on a 'cons' expression"]),
    ("(* 2 3)", ["Cannot evaluate = on a '*' expression"]),
    ("(= 3)", ['= only takes 2 arguments, but 1 was provided']), # too few arguments
    ("(= 2 2 2)", ['= only takes 2 arguments, but 3 were provided']), # too many arguments
    ("(= #t #t)", '#t'), # allowed to use '=' for any type in buddy racket
    ("(= 3 (+ 1 2))", ['insufficiently resolved arguments']), # insufficiently resolved
    ("(= 4 3)", '#f'), # greater than
    ("(= 3 3)", '#t'), # equal
    ("(= 3 4)", '#f'), # less than
    ("(= #t 3)", '#f'), # comparing different types
    ("(= 3 #t)", '#f'), # comparing different types different order
    ("(= '(1 2) '(1 2))", '#t'), # comparing equal lists
    ("(= '(1         2) '(1 2))", '#t'), # comparing equal lists with different spacing
    ("(= '(1 2) '(1 3))", '#f'), # comparing lists different values
    ("(= '(1 2) '(1 2 3))", '#f'), # comparing lists different lengths
    ("(= '() null)", '#t'), # comparing empty list to null
    ("(= (2 3) '(2 3))", ['insufficiently resolved arguments']), # compare unquoted list to quoted list
    ("(= 3 '(3))", '#f')
]
totalFails += test_racket_function('=', eq_tests)

lt_tests = [
    # bad operation
    ("(cons 1 null)", ["Cannot evaluate < on a 'cons' expression"]),
    ("(<= 2 3)", ["Cannot evaluate < on a '<=' expression"]),
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
    ("(cons 1 null)", ["Cannot evaluate <= on a 'cons' expression"]),
    ("(< 2 3)", ["Cannot evaluate <= on a '<' expression"]),
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
    ("(cons 1 null)", ["Cannot evaluate > on a 'cons' expression"]),
    ("(< 2 3)", ["Cannot evaluate > on a '<' expression"]),
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
    ("(cons 1 null)", ["Cannot evaluate >= on a 'cons' expression"]),
    ("(< 2 3)", ["Cannot evaluate >= on a '<' expression"]),
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

# Check that 'math' rule can no longer be used in place of the individual operators
totalFails += do_single_test_case('eval', 'math', '(+ 1 2)', ['Cannot evaluate advanced math'])
totalFails += do_single_test_case('', 'math', '(+ 1 2)', ["Rule must start with 'eval' or 'apply'"])

# Logic Function Tests
print('\nTesting Logic Rules:\n')
not_tests = [
    ("(cons 1 null)", ["Cannot evaluate not on a 'cons' expression"]),
    ("(and #t #t)", ["Cannot evaluate not on a 'and' expression"]),
    ("(not #t #t)", ['not only takes 1 arguments, but 2 were provided']),
    ("(not)", ['not only takes 1 arguments, but 0 were provided']),
    ("(not 1)", ["Cannot match argument out typeList ['INT'] with expected typeList ['BOOL']"]),
    ("(not (and #t #f))", ['insufficiently resolved arguments']),
    ("(not #t)", "#f"),
    ("(not #f)", "#t")
]
totalFails += test_racket_function('not', not_tests)

and_tests = [
    ("(cons 1 null)", ["Cannot evaluate and on a 'cons' expression"]),
    ("(or #t #f)", ["Cannot evaluate and on a 'or' expression"]),
    ("(and #t #t #f)", ['and only takes 2 arguments, but 3 were provided']),
    ("(and #t)", ['and only takes 2 arguments, but 1 was provided']),
    ("(and 3)", ['and only takes 2 arguments, but 1 was provided']),
    ("(and 1 #t)", [
     "Cannot match argument out typeList ['INT', 'BOOL'] with expected typeList ['BOOL', 'BOOL']"]),
    ("(and #t (and #f #f))", ['insufficiently resolved arguments']),
    ("(and #t #t)", "#t"),
    ("(and #f #f)", "#f"),
    ("(and #t #f)", "#f"),
    ("(and #f #t)", "#f")
]
totalFails += test_racket_function('and', and_tests)

or_tests = [
    ("(cons 1 null)", ["Cannot evaluate or on a 'cons' expression"]),
    ("(and #t #t)", ["Cannot evaluate or on a 'and' expression"]),
    ("(or #t #t #t)", ['or only takes 2 arguments, but 3 were provided']),
    ("(or #t)", ['or only takes 2 arguments, but 1 was provided']),
    ("(or 3)", ['or only takes 2 arguments, but 1 was provided']),
    ("(or 1 #t)", [
     "Cannot match argument out typeList ['INT', 'BOOL'] with expected typeList ['BOOL', 'BOOL']"]),
    ("(or #t (or #f #f))", ['insufficiently resolved arguments']),
    ("(or #t #t)", "#t"),
    ("(or #f #f)", "#f"),
    ("(or #t #f)", "#t"),
    ("(or #f #t)", "#t")
]
totalFails += test_racket_function('or', or_tests)

xor_tests = [
    ("(cons 1 null)", ["Cannot evaluate xor on a 'cons' expression"]),
    ("(and #t #t)", ["Cannot evaluate xor on a 'and' expression"]),
    ("(xor #t #t #f)", ['xor only takes 2 arguments, but 3 were provided']),
    ("(xor #t)", ['xor only takes 2 arguments, but 1 was provided']),
    ("(xor 3)", ['xor only takes 2 arguments, but 1 was provided']),
    ("(xor 1 #t)", [
     "Cannot match argument out typeList ['INT', 'BOOL'] with expected typeList ['BOOL', 'BOOL']"]),
    ("(xor #t (not #t))", ['insufficiently resolved arguments']),
    ("(xor #t #t)", "#f"),
    ("(xor #t #f)", "#t"),
    ("(xor #f #f)", "#f")
]
totalFails += test_racket_function('xor', xor_tests)

implies_tests = [
    ("(cons 1 null)", ["Cannot evaluate implies on a 'cons' expression"]),
    ("(and #t #t)", ["Cannot evaluate implies on a 'and' expression"]),
    ("(implies #t #t #f)", ['implies only takes 2 arguments, but 3 were provided']),
    ("(implies #t)", ['implies only takes 2 arguments, but 1 was provided']),
    ("(implies #t 1)", [
     "Cannot match argument out typeList ['BOOL', 'INT'] with expected typeList ['BOOL', 'BOOL']"]),
    ("(implies #t (or #f #f))", ['insufficiently resolved arguments']),
    ("(implies #t #t)", "#t"),
    ("(implies #t #f)", "#f"),
    ("(implies #f #f)", "#t")
]
totalFails += test_racket_function('implies', implies_tests)

# Check that logic is no longer a valid rule
totalFails += do_single_test_case('eval', 'logic', '(and #t #t)', ['Could not find rule associated with logic'])
totalFails += do_single_test_case('', 'logic', '(and #t #t)', ["Rule must start with 'eval' or 'apply'"])

# List function tests
print('\nTesting List Function Rules...\n')
cons_tests = [
    ("(+ 1 2)", ["Cannot evaluate cons on a '+' expression"]),
    ("(first '(9 8 7))", ["Cannot evaluate cons on a 'first' expression"]),
    ("(cons 1 1)", ["Cannot match argument out typeList ['INT', 'INT'] with expected typeList ['ANY', 'LIST']"]),
    ("(cons (+ 1 2) '(4 5))", ['insufficiently resolved arguments']),
    ("(cons 1 (cons 2 null))", ['insufficiently resolved arguments']),
    ("(cons null)", ['cons only takes 2 arguments, but 1 was provided']),
    ("(cons 1 '(2 3) null)", ['cons only takes 2 arguments, but 3 were provided']),
    ("(cons 1 null)", "'(1)"), # cons int to null
    ("(cons 9 '(8 7))", "'(9 8 7)"), # cons int to non-null
    ("(cons #t null)", "'(#t)"), # cons bool to null
    ("(cons #t '(#f #t))", "'(#t #f #t)"), # cons bool to list of bools
    ("(cons #t '(1 2))", "'(#t 1 2)"), # cons bool to list of ints
    ("(cons '(1 2) '(3 4))", "'((1 2) 3 4)") # cons list to list
]
totalFails += test_racket_function('cons', cons_tests, appliable=True)
totalFails += do_single_test_case('eval', 'consList', "(cons 1 null)", 
                                  ['Could not find rule associated with consList']) # check consList no longer working

first_tests = [
    ("(+ 1 2)", ["Cannot evaluate first on a '+' expression"]),
    ("(cons 1 null)", ["Cannot evaluate first on a 'cons' expression"]),
    ("(first 1)", ["Cannot match argument out typeList ['INT'] with expected typeList ['LIST']"]),
    ("(first)", ['first only takes 1 arguments, but 0 were provided']),
    ("(first '(1 2) '(3 4))", ['first only takes 1 arguments, but 2 were provided']),
    ("(first (cons 1 null))", ['insufficiently resolved list argument']), # error expected because the rule is 'eval first'
    ("(first null)", ['first requires nonempty list']),
    ("(first '(1 2 3))", "1"), # first for non-nested list
    ("(first '((1 2) (3) (4)))", "'(1 2)") # first for nested list
]
totalFails += test_racket_function('first', first_tests, appliable=True)
totalFails += do_single_test_case('eval', 'firstList', "(first '(1 2 3))",
                                   ['Could not find rule associated with firstList'])

rest_tests = [
    ("(+ 1 2)", ["Cannot evaluate rest on a '+' expression"]),
    ("(cons 1 null)", ["Cannot evaluate rest on a 'cons' expression"]),
    ("(rest 1)", ["Cannot match argument out typeList ['INT'] with expected typeList ['LIST']"]),
    ("(rest)", ['rest only takes 1 arguments, but 0 were provided']),
    ("(rest '(1 2) '(3 4))", ['rest only takes 1 arguments, but 2 were provided']),
    ("(rest (cons 1 null))", ['insufficiently resolved list argument']), # error expected because the rule is 'eval rest'
    ("(rest null)", ['rest requires nonempty list']),
    ("(rest '(1 2 3))", "'(2 3)"), # rest for non-nested list
    ("(rest '((1 2) (3) (4)))", "'((3) (4))") # rest for nested list
]
totalFails += test_racket_function('rest', rest_tests, appliable=True)
totalFails += do_single_test_case('eval', 'restList', "(rest '(1 2 3))",
                                   ['Could not find rule associated with restList'])

print("\nList Function Property Testing\n")
cons_prop_tests = [
    ("(+ 1 2)", ["Cannot apply cons-first-rest property to a '+' expression"]),
    ("(cons 1 null)", 
     ["Can only apply cons-first-rest property when first arg is a 'first' expression and second arg is a 'rest' expression"]),
    ("(cons 1 (rest '(1 2)))", 
     ["Can only apply cons-first-rest property when first arg is a 'first' expression and second arg is a 'rest' expression"]),
    ("(cons (first '(1 2)) '(2))", 
     ["Can only apply cons-first-rest property when first arg is a 'first' expression and second arg is a 'rest' expression"]),
    ("(cons (first L) (rest M))", ["Cannot apply cons-first-rest property on two different lists"]),
    ("(cons (first '(1 2)) (rest '(1 3)))", ["Cannot apply cons-first-rest property on two different lists"]),
    ("(cons (first null) (rest null))", ["first requires nonempty list"]), # cannot apply property when list is null
    ("(cons (first '(1 2)) (rest '()))", ["rest requires nonempty list"]), # '() instead of null
    ("(cons (first 1) (rest '(1)))", ["Cannot match argument out typeList ['INT'] with expected typeList ['LIST']"]), # bad type in argument expression
    ("(cons (first '(1 2) '(3)) (rest '(2 3)))", ["first only takes 1 arguments, but 2 were provided"]), # extra argument in argument expressions
    ("(cons (first '(1 2)) (rest '(1) '(2)))", ["rest only takes 1 arguments, but 2 were provided"]),
    ("(cons (first '(1 2)) (rest '(1 2)) null)", ["cons only takes 2 arguments, but 3 were provided"]), # extra argument in cons expression
    ("(cons (first '(1 2)) (rest '(1 2)))", "'(1 2)"),
    ("(cons (first (cons 2 null)) (rest (cons 2 null)))", "(cons 2 null)"), # list not completely resolved
    ("(cons (first L) (rest L))", "L") # symbols
]
totalFails += test_list_func_props('cons', cons_prop_tests)

first_prop_tests = [
    ("(+ 1 2)", ["Cannot apply first-cons property to a '+' expression"]),
    ("(first '(1 2))", ["Can only apply first-cons property when argument is a 'cons' expression"]),
    ("(first (cons 1 1))", # bad type in argument expression
     ["Cannot match argument out typeList ['INT', 'INT'] with expected typeList ['ANY', 'LIST']"]),
    ("(first (cons 1 '(2 3) '(4 5)))", ["cons only takes 2 arguments, but 3 were provided"]), # extra argument in argument expression
    ("(first (cons 1 null) null)", ["first only takes 1 arguments, but 2 were provided"]), # extra argument in argument expression
    ("(first (cons 1 null))", "1"),
    ("(first (cons 9 '(8 7)))", "9"),
    ("(first (cons a L))", "a"), # symbolic
    ("(first (cons (+ (* 4 5) (* 6 7)) null))", "(+ (* 4 5) (* 6 7))"), # first cons argument not completely simplified
    ("(first (cons 46 (cons 2 null)))", "46") # second cons argument not completely simplified
]
totalFails += test_list_func_props('first', first_prop_tests)

rest_prop_tests = [
    ("(+ 1 2)", ["Cannot apply rest-cons property to a '+' expression"]),
    ("(rest '(1 2))", ["Can only apply rest-cons property when argument is a 'cons' expression"]),
    ("(rest (cons 1 1))", # bad type in argument expression
     ["Cannot match argument out typeList ['INT', 'INT'] with expected typeList ['ANY', 'LIST']"]),
    ("(rest (cons 1 '(2 3) '(4 5)))", ["cons only takes 2 arguments, but 3 were provided"]), # extra argument in argument expression
    ("(rest (cons 1 null) null)", ["rest only takes 1 arguments, but 2 were provided"]), # extra argument in argument expression
    ("(rest (cons 1 null))", "null"),
    ("(rest (cons 9 '(8 7)))", "'(8 7)"),
    ("(rest (cons a L))", "L"), # symbolic
    ("(rest (cons (+ (* 4 5) (* 6 7)) null))", "null"), # first cons argument not completely simplified
    ("(rest (cons 46 (cons 2 null)))", "(cons 2 null)") # second cons argument not completely simplified
]
totalFails += test_list_func_props('rest', rest_prop_tests)

minus_plus_tests = [
    ("(cons 1 null)", ["Cannot apply -+ when the root operation is cons"]),
    ("(- 2 1)", ["Cannot apply -+ when the first argument of - is not a + expression"]),
    ("(- (* 2 2) 2)", ["Cannot apply -+ when the first argument of - is not a + expression"]),
    # bad types
    ("(- (+ null 1) 1)", ["Cannot match argument out typeList ['LIST', 'INT'] with expected typeList ['INT', 'INT']"]),
    ("(- (+ 1 #f) #f)", 
     ["Cannot match argument out typeList ['INT', 'BOOL'] with expected typeList ['INT', 'INT']",
    "Cannot match argument out typeList ['INT', 'BOOL'] with expected typeList ['INT', 'INT']"]),
    # too many arguments
    ("(- (+ 1 2 3) 2)", ["+ only takes 2 arguments, but 3 were provided"]),
    ("(- (+ k 1) 1 2)", ["- only takes 2 arguments, but 3 were provided"]),
    # insufficiently resolved arguments
    ("(- (+ 1 2) (+ 1 1))", ["Insufficiently resolved arguments"]),
    ("(- (+ 1 (+ 1 1)) 2)", ["Insufficiently resolved arguments"]),
    ("(- (+ 1 (+ 1 1)) (+ 1 1))", ["Insufficiently resolved arguments"]),
    # arguments don't match
    ("(- (+ k 2) 1)", ["Cannot apply -+ when the second argument of - doesn't match the second argument of +"]),
    # valid
    ("(- (+ 2 1) 1)", "2"),
    ("(- (+ (* 8 8) 3) 3)", "(* 8 8)"),
    ("(- (+ k 9) 9)", "k")
]
totalFails += run_test_cases("apply", "-+", minus_plus_tests)
totalFails += do_single_test_case("eval", "-+", minus_plus_tests[-1][0], ["Cannot evaluate a property"])

print("\nUDF testing:\n")
udfProof = ERProof()
udfProof.addUDF("(f x y)", "(INT,INT)>INT", "(* x y)")
udfProof.addUDF("(g x)", "INT>BOOL", "(< x 5)")
# 2 arguments
totalFails += do_single_test_case('', 'f', "(f 3 4)", ["Rule must start with 'eval' or 'apply'"], udfProof)
totalFails += do_single_test_case('eval', 'f',  "(f 3 4)", ['Cannot evaluate a user-defined function'], udfProof)
totalFails += do_single_test_case('apply', 'f', "(f 3 4)", ['Not enough arguments given for f. f requires 2 '
                                                            'arguments, while you gave 0'],
                                  udfProof)
totalFails += do_single_test_case('apply', 'f x=3, y=4, z=5', "(f 3 4)", ['Too many arguments given for f. f '
                                                                          'requires 2 arguments, while you gave 3'],
                                  udfProof)
totalFails += do_single_test_case('apply', 'f x=3 y=4', "(f 3 4)", ['Too many assignments for a given argument \'x=3 '
                                                                    'y=4\'. Did you forget a comma?'], udfProof)
totalFails += do_single_test_case('apply', 'f x=3, y=4', "(f 3 4)", "(* 3 4)", udfProof)

# 1 argument
totalFails += do_single_test_case('', 'g x=3', "(g 3)", ["Rule must start with 'eval' or 'apply'"], udfProof)
totalFails += do_single_test_case('eval', 'g x=3', "(g 3)", ['Cannot evaluate a user-defined function'], udfProof)
totalFails += do_single_test_case('apply', 'g', "(g 3)", ['Not enough arguments given for g. g requires 1 arguments, '
                                                          'while you gave 0'], udfProof)
totalFails += do_single_test_case('apply', 'g x=3, y=4', "(g 3)", ['Too many arguments given for g. g requires 1 '
                                                                   'arguments, while you gave 2'], udfProof)
totalFails += do_single_test_case('apply', 'g x=3', "(g 3)", "(< 3 5)", udfProof)

#node method tests for funcset, ancestor, allMath, mathstr, logicStr: method, expr, expected
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