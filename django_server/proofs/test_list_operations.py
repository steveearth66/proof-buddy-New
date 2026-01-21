"""
Test cases for list operations (cons, first, rest) and predicates (zero?, null?, if, integer?, list?)
"""

from .test_helpers import test_racket_function, do_single_test_case

totalFails = 0

print('[Summary] List Operations Tests')

cons_tests = [
    ("(+ 1 2)", ["Cannot evaluate cons on a '+' expression"]),
    ("(first '(9 8 7))", ["Cannot evaluate cons on a 'first' expression"]),
    ("(cons 1 1)", ["Cannot match argument out typeList ['INT', 'INT'] with expected typeList ['ANY', 'LIST']"]),
    ("(cons (+ 1 2) '(4 5))", ['Insufficiently resolved arguments']),
    ("(cons 1 (cons 2 null))", ['Insufficiently resolved arguments']),
    ("(cons null)", ['cons only takes 2 arguments, but 1 was provided']),
    ("(cons 1 '(2 3) null)", ['cons only takes 2 arguments, but 3 were provided']),
    ("(cons x null)", ["Cannot evaluate 'cons' expression with generic arguments"]),
    ("(cons 1 L)", ["Cannot evaluate 'cons' expression with generic arguments"]),
    ("(cons 1 null)", "'(1)"), # cons int to null
    ("(cons 9 '(8 7))", "'(9 8 7)"), # cons int to non-null
    ("(cons #t null)", "'(#t)"), # cons bool to null
    ("(cons #t '(#f #t))", "'(#t #f #t)"), # cons bool to list of bools
    ("(cons #t '(1 2))", "'(#t 1 2)"), # cons bool to list of ints
    ("(cons '(1 2) '(3 4))", "'((1 2) 3 4)") # cons list to list
]
totalFails += test_racket_function('cons', cons_tests)
totalFails += do_single_test_case('eval consList', "(cons 1 null)", 
                                  ["Could not find rule associated with 'consList'"]) # check consList no longer working

first_tests = [
    ("(+ 1 2)", ["Cannot evaluate first on a '+' expression"]),
    ("(cons 1 null)", ["Cannot evaluate first on a 'cons' expression"]),
    ("(first 1)", ["Cannot match argument out typeList ['INT'] with expected typeList ['LIST']"]),
    ("(first)", ['first only takes 1 argument, but 0 were provided']),
    ("(first '(1 2) '(3 4))", ['first only takes 1 argument, but 2 were provided']),
    ("(first (cons 1 null))", ['Insufficiently resolved arguments']), # error expected because the rule is 'eval first',
    ("(first L)", ["Cannot evaluate 'first' expression with generic arguments"]),
    ("(first null)", ['first requires non-empty list']),
    ("(first '(1 2 3))", "1"), # first for non-nested list
    ("(first '((1 2) (3) (4)))", "'(1 2)") # first for nested list
]
totalFails += test_racket_function('first', first_tests)
totalFails += do_single_test_case('eval firstList', "(first '(1 2 3))",
                                   ["Could not find rule associated with 'firstList'"])

rest_tests = [
    ("(+ 1 2)", ["Cannot evaluate rest on a '+' expression"]),
    ("(cons 1 null)", ["Cannot evaluate rest on a 'cons' expression"]),
    ("(rest 1)", ["Cannot match argument out typeList ['INT'] with expected typeList ['LIST']"]),
    ("(rest)", ['rest only takes 1 argument, but 0 were provided']),
    ("(rest '(1 2) '(3 4))", ['rest only takes 1 argument, but 2 were provided']),
    ("(rest (cons 1 null))", ['Insufficiently resolved arguments']), # error expected because the rule is 'eval rest'
    ("(rest null)", ['rest requires non-empty list']),
    ("(rest L)", ["Cannot evaluate 'rest' expression with generic arguments"]),
    ("(rest '(1 2 3))", "'(2 3)"), # rest for non-nested list
    ("(rest '((1 2) (3) (4)))", "'((3) (4))") # rest for nested list
]
totalFails += test_racket_function('rest', rest_tests)
totalFails += do_single_test_case('eval restList', "(rest '(1 2 3))",
                                   ["Could not find rule associated with 'restList'"])

print('[Summary] Predicate Tests')

zeroQ_tests = [
    ("(+ 1 2)", ["Cannot evaluate zero? on a '+' expression"]),
    ("(cons 1 null)", ["Cannot evaluate zero? on a 'cons' expression"]),
    ("(zero? 1 2)", ["zero? only takes 1 argument, but 2 were provided"]),
    ("(zero? (+ 1 2))", ["Insufficiently resolved arguments"]),
    ("(zero? (- 1 2))", ["Insufficiently resolved arguments"]),
    ("(zero? k)", ["Cannot determine value of 'zero?' expression with generic argument 'k'"]),
    ("(zero? L)", "#f"),
    ("(zero? #f)", '#f'),
    ("(zero? '(1 2))", '#f'),
    ("(zero? 0)", '#t'),
    ("(zero? 1)", '#f')
]
totalFails += test_racket_function('zero?', zeroQ_tests)

nullQ_tests = [
    ("(+ 1 2)", ["Cannot evaluate null? on a '+' expression"]),
    ("(cons 1 null)", ["Cannot evaluate null? on a 'cons' expression"]),
    ("(null? null null)", ["null? only takes 1 argument, but 2 were provided"]),
    ("(null? (cons 1 null))", ["Insufficiently resolved arguments"]),
    ("(null? 1)", "#f"),
    ("(null? #f)", "#f"),
    ("(null? L)", "#f"),
    ("(null? null)", "#t"),
    ("(null? '())", "#t"),
    ("(null? '(1 2 3))", "#f")
]
totalFails += test_racket_function('null?', nullQ_tests)

if_tests = [
    ("(+ 1 2)", ["Cannot evaluate if on a '+' expression"]),
    ("(cons 1 null)", ["Cannot evaluate if on a 'cons' expression"]),
    ("(if #t 1 2 3)", ["if only takes 3 arguments, but 4 were provided"]),
    ("(if 0 1 2)", ["The first argument of an if function must be Boolean but INT was provided"]),
    ("(if (= 1 1) 1 2)", ["Insufficiently resolved condition argument"]),
    ("(if #t 1 #f)", ["Final arguments of an if function must have matching types, but INT and BOOL were provided"]),
    ("(if p 1 2)", ["Cannot determine truth value of generic argument 'p'"]),
    ("(if #t 1 2)", 1),
    ("(if #f 1 2)", 2),
    ("(if #t null '(1 2))", "null"),
    ("(if #f null '(1 2))", "'(1 2)"),
    ("(if #t #f #t)", "#f"),
    ("(if #f #f #t)", "#t"),
    ("(if #t (+ 1 2) (+ 3 4))", "(+ 1 2)"), # latter arguments not fully resolved
    ("(if p (cons 1 null) (cons 1 null))", "(cons 1 null)"), # generic condition, same outputs regardless of condition value
]
test_racket_function('if', if_tests)

integerQ_tests = [
    ("(+ 1 2)", ["Cannot evaluate integer? on a '+' expression"]),
    ("(integer? (+ 1 2))", ["Insufficiently resolved arguments"]),
    ("(integer? 1 2)", ["integer? only takes 1 argument, but 2 were provided"]),
    ("(integer? 1)", '#t'),
    ("(integer? k)", '#t'),
    ("(integer? null)", '#f'),
    ("(integer? '(1 2))", '#f'),
    ("(integer? L)", "#f"),
    ("(integer? #t)", '#f'),
    ("(integer? p)", '#f'),
    ("(integer? x)", '#f') # integer? with generic any currently evaluates to false
]
totalFails += test_racket_function('integer?', integerQ_tests, hasAxiom=True)

listQ_tests = [
    ("(+ 1 2)", ["Cannot evaluate list? on a '+' expression"]),
    ("(list? (cons 1 null))", ["Insufficiently resolved arguments"]),
    ("(list? null null)", ["list? only takes 1 argument, but 2 were provided"]),
    ("(list? 1)", '#f'),
    ("(list? k)", '#f'),
    ("(list? null)", '#t'),
    ("(list? '(1 2))", '#t'),
    ("(list? L)", "#t"),
    ("(list? #t)", '#f'),
    ("(list? p)", '#f'),
    ("(list? x)", '#f') # list? with generic any currently evaluates to false
]
test_racket_function('list?', listQ_tests, hasAxiom=True)

print("\nList operations tests completed!\n" if totalFails == 0 else f"List operations: {totalFails} failures\n")
