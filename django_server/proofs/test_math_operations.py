"""
Test cases for basic math operations (+, -, *, quotient, remainder, expt)
and comparison operators (=, <, <=, >, >=)
"""

from .test_helpers import test_racket_function, do_single_test_case, _RED, _RESET

totalFails = 0

print('[Summary] Math Operations Tests')

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
    ("(+ k 0)", ["Cannot evaluate '+' expression with generic arguments"]), # generic
    ("(+ 1 (+ 2 3))", ['Insufficiently resolved arguments']), # insufficiently resolved
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
    ("(- 5 (- 2 1))", ['Insufficiently resolved arguments']), # insufficiently resolved
    ("(- k 0)", ["Cannot evaluate '-' expression with generic arguments"]), # generic
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
    ("(* k 0)", ["Cannot evaluate '*' expression with generic arguments"]), # generic
    ("(* 2 (+ 3 4))", ['Insufficiently resolved arguments']), # insufficiently resolved
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
    ("(quotient 12 (quotient 6 2))", ['Insufficiently resolved arguments']), # insufficiently resolved
    ("(quotient k 1)", ["Cannot evaluate 'quotient' expression with generic arguments"]), # generic
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
    ("(remainder 12 (quotient 29 6))", ['Insufficiently resolved arguments']), # insufficiently resolved
    ("(remainder k 1)", ["Cannot evaluate 'remainder' expression with generic arguments"]), # generic
    ("(remainder 2 0)", ["denominator can't be zero"]), # division by zero
    ("(remainder 0 2)", 0),  # remainder with 0 numerator
    ("(remainder 14 5)", 4)  # normal test case
]
totalFails += test_racket_function('remainder', remainder_tests)

expt_tests = [
    # bad operation
    ("(cons 1 null)", ["Cannot evaluate expt on a 'cons' expression"]),
    ("(* 2 3)", ["Cannot evaluate expt on a '*' expression"]),
    ("(expt 3)", ['expt only takes 2 arguments, but 1 was provided']), # too few arguments
    ("(expt 2 2 2)", ['expt only takes 2 arguments, but 3 were provided']), # too many arguments
    ("(expt 5 #t)",
    ["Cannot match argument out typeList ['INT', 'BOOL'] with expected typeList ['INT', 'INT']"]), # bad type
    ("(expt 3 (expt 2 2))", ['Insufficiently resolved arguments']), # insufficiently resolved
    ("(expt 0 0)", ['0^0 is undefined']),  # undef
    ("(expt 3 -1)", ['-1 contains illegal character']), # fraction, not a legal input due to -1
    ("(expt k 0)", ["Cannot evaluate 'expt' expression with generic arguments"]), # generic
    ("(expt 2 0)", 1), # expt with 0 power
    ("(expt 0 2)", 0), # expt with 0 base
    ("(expt 2 3)", 8) # normal test case
]
totalFails += test_racket_function('expt', expt_tests)

print('[Summary] Comparison Operators')

eq_tests = [
    # bad operation
    ("(cons 1 null)", ["Cannot evaluate = on a 'cons' expression"]),
    ("(* 2 3)", ["Cannot evaluate = on a '*' expression"]),
    ("(= 3)", ['= only takes 2 arguments, but 1 was provided']), # too few arguments
    ("(= 2 2 2)", ['= only takes 2 arguments, but 3 were provided']), # too many arguments
    ("(= #t #t)", '#t'), # allowed to use '=' for any type in buddy racket
    ("(= 3 (+ 1 2))", ['Insufficiently resolved arguments']), # insufficiently resolved
    ("(= k k)", "#t"), # generic
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
    ("(= (2 3) '(2 3))", ['Insufficiently resolved arguments']), # compare unquoted list to quoted list
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
    ("(< 3 (+ 1 2))", ['Insufficiently resolved arguments']), # insufficiently resolved
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
    ("(<= 3 (+ 1 2))", ['Insufficiently resolved arguments']), # insufficiently resolved
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
    ("(> 3 (+ 1 2))", ['Insufficiently resolved arguments']), # insufficiently resolved
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
    ("(>= 3 (+ 1 2))", ['Insufficiently resolved arguments']), # insufficiently resolved
    ("(>= 4 3)", '#t'), # greater than
    ("(>= 3 3)", '#t'), # equal
    ("(>= 3 4)", '#f') # less than
]
totalFails += test_racket_function('>=', ge_tests)

# Check that 'math' rule can no longer be used in place of the individual operators
totalFails += do_single_test_case('eval math', '(+ 1 2)', 
                                  ["Cannot evaluate algebraic math rule"])
totalFails += do_single_test_case('math', '(+ 1 2)', ["Rule must start with 'eval', 'apply', or 'rewrite'"])

print("\nMath operations tests completed!\n" if totalFails == 0 else f"{_RED}Math operations: {totalFails} failures{_RESET}\n")
