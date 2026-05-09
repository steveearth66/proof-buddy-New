"""
Test cases for logic operations (not, and, or, xor, implies)
"""

from .test_helpers import test_racket_function, do_single_test_case, _RED, _RESET

totalFails = 0

print('[Summary] Logic Operations Tests')

not_tests = [
    ("(cons 1 null)", ["Cannot evaluate not on a 'cons' expression"]),
    ("(and #t #t)", ["Cannot evaluate not on a 'and' expression"]),
    ("(not #t #t)", ['not only takes 1 argument, but 2 were provided']),
    ("(not)", ['not only takes 1 argument, but 0 were provided']),
    ("(not 1)", ["Cannot match argument out typeList ['INT'] with expected typeList ['BOOL']"]),
    ("(not (and #t #f))", ['Insufficiently resolved arguments']),
    ("(not p)", ["Cannot evaluate 'not' expression with generic arguments"]),
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
    ("(and #t (and #f #f))", ['Insufficiently resolved arguments']),
    ("(and #f p)", ["Cannot evaluate 'and' expression with generic arguments"]),
    ("(and #t #t)", "#t"),
    ("(and #f #f)", "#f"),
    ("(and #t #f)", "#f"),
    ("(and #f #t)", "#f")
]
totalFails += test_racket_function('and', and_tests, hasAxiom=True)

or_tests = [
    ("(cons 1 null)", ["Cannot evaluate or on a 'cons' expression"]),
    ("(and #t #t)", ["Cannot evaluate or on a 'and' expression"]),
    ("(or #t #t #t)", ['or only takes 2 arguments, but 3 were provided']),
    ("(or #t)", ['or only takes 2 arguments, but 1 was provided']),
    ("(or 3)", ['or only takes 2 arguments, but 1 was provided']),
    ("(or 1 #t)", [
     "Cannot match argument out typeList ['INT', 'BOOL'] with expected typeList ['BOOL', 'BOOL']"]),
    ("(or #t (or #f #f))", ['Insufficiently resolved arguments']),
    ("(or #t p)", ["Cannot evaluate 'or' expression with generic arguments"]),
    ("(or #t #t)", "#t"),
    ("(or #f #f)", "#f"),
    ("(or #t #f)", "#t"),
    ("(or #f #t)", "#t")
]
totalFails += test_racket_function('or', or_tests, hasAxiom=True)

xor_tests = [
    ("(cons 1 null)", ["Cannot evaluate xor on a 'cons' expression"]),
    ("(and #t #t)", ["Cannot evaluate xor on a 'and' expression"]),
    ("(xor #t #t #f)", ['xor only takes 2 arguments, but 3 were provided']),
    ("(xor #t)", ['xor only takes 2 arguments, but 1 was provided']),
    ("(xor 3)", ['xor only takes 2 arguments, but 1 was provided']),
    ("(xor 1 #t)", [
     "Cannot match argument out typeList ['INT', 'BOOL'] with expected typeList ['BOOL', 'BOOL']"]),
    ("(xor #t (not #t))", ['Insufficiently resolved arguments']),
    ("(xor #t p)", ["Cannot evaluate 'xor' expression with generic arguments"]),
    ("(xor #f p)", ["Cannot evaluate 'xor' expression with generic arguments"]),
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
    ("(implies #t (or #f #f))", ['Insufficiently resolved arguments']),
    ("(implies #f p)", ["Cannot evaluate 'implies' expression with generic arguments"]),
    ("(implies #t #t)", "#t"),
    ("(implies #t #f)", "#f"),
    ("(implies #f #f)", "#t")
]
totalFails += test_racket_function('implies', implies_tests, hasAxiom=True)

# Check that logic is no longer a valid rule
totalFails += do_single_test_case('eval logic', '(and #t #t)', ["Cannot evaluate propositional logic rule"])
totalFails += do_single_test_case("logic", '(and #t #t)', ["Rule must start with 'eval', 'apply', or 'rewrite'"])

print("\nLogic operations tests completed!\n" if totalFails == 0 else f"{_RED}Logic operations: {totalFails} failures{_RESET}\n")
