#from django.test import TestCase

# Create your tests here.
from expression_tree.ERProofEngine import ERProof, ERProofLine
from expression_tree.ERCommon import Node
import sympy as sp
import json
from expression_tree.ERCommon import makeJson


def do_single_test_case(prefix: str, func: str, expr: str, expected, proof: ERProof = None, args: str = None) -> int:
    if proof == None:
        proof = ERProof()
    if prefix != '':
        prefix += ' '
    if args:
        rule = prefix + func + f" with {args}"
    else:
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

def run_test_cases(prefix: str, func: str, tests: list[tuple], proof: ERProof = None, defaultGenerics=True) -> int:
    '''
    Runs test cases with a single rule\n
    defaultGenerics specifies whether or not to use the default generics k (int), p (bool), L (list), and x (any)
    '''
    if proof is None:
        proof = ERProof()
    if defaultGenerics:
        if 'k' not in proof.generics.keys():
            proof.addGeneric('k', 'int')
        if 'p' not in proof.generics.keys():
            proof.addGeneric('p', 'bool')
        if 'L' not in proof.generics.keys():
            proof.addGeneric('L', 'list')
        if 'M' not in proof.generics.keys():
            proof.addGeneric('M', 'list')
        if 'x' not in proof.generics.keys():
            proof.addGeneric('x', 'any')
    fails = 0
    for trial in tests:
        if len(trial) == 2:
            expr, expected = trial
            fails += do_single_test_case(prefix, func, expr, expected, proof)
        else:
            expr, args, expected = trial
            fails += do_single_test_case(prefix, func, expr, expected, proof, args)
    return fails

def test_racket_function(func: str, tests: list[tuple], allowGenerics=False, appliable=False) -> int:
    # expects last test case to not have errors
    fails = run_test_cases('eval', func, tests)

    expr, _ = tests[-1]
    fails += do_single_test_case('', func, expr,
                                 expected=["Rule must start with 'eval', 'apply', or 'rewrite'"])
    if not appliable:
        fails += do_single_test_case('apply', func, expr,
                                expected=[f'Could not find definition/lemma associated with {func}'])
    return fails

def test_list_func_props(func: str, tests: list[tuple], proof: ERProof = None) -> int:
    fails = run_test_cases('rewrite', func, tests, proof)
    if len(tests[-1]) == 2:
        expr, _ = tests[-1]
        fails += do_single_test_case('rewrite', func + 'Prop', expr, [f'Could not find rule associated with'
                                                                      f' {func + 'Prop'}'], proof)
    else:
        expr, args, _ = tests[-1]
        fails += do_single_test_case('rewrite', func + 'Prop', expr, [f'Could not find rule associated with'
                                                                      f' {func + 'Prop'}'], proof, args)
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
totalFails = test_racket_function('remainder', remainder_tests)

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
    ("(expt 3 -1)", ['-1 contains illegal characters']), # fraction, not a legal input due to -1
    ("(expt k 0)", ["Cannot evaluate 'expt' expression with generic arguments"]), # generic
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
totalFails += do_single_test_case('eval', 'math', '(+ 1 2)', ["Cannot evaluate a property"])
totalFails += do_single_test_case('', 'math', '(+ 1 2)', ["Rule must start with 'eval', 'apply', or 'rewrite'"])

# Logic Function Tests
print('\nTesting Logic Rules:\n')
not_tests = [
    ("(cons 1 null)", ["Cannot evaluate not on a 'cons' expression"]),
    ("(and #t #t)", ["Cannot evaluate not on a 'and' expression"]),
    ("(not #t #t)", ['not only takes 1 arguments, but 2 were provided']),
    ("(not)", ['not only takes 1 arguments, but 0 were provided']),
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
totalFails += test_racket_function('and', and_tests)

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
totalFails += test_racket_function('or', or_tests)

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
totalFails += test_racket_function('implies', implies_tests)

# Check that logic is no longer a valid rule
totalFails += do_single_test_case('eval', 'logic', '(and #t #t)', ['Could not find rule associated with logic'])
totalFails += do_single_test_case('', 'logic', '(and #t #t)', ["Rule must start with 'eval', 'apply', or 'rewrite'"])

# List function tests
print('\nTesting List Function Rules...\n')
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
totalFails += test_racket_function('cons', cons_tests, appliable=True)
totalFails += do_single_test_case('eval', 'consList', "(cons 1 null)", 
                                  ['Could not find rule associated with consList']) # check consList no longer working

first_tests = [
    ("(+ 1 2)", ["Cannot evaluate first on a '+' expression"]),
    ("(cons 1 null)", ["Cannot evaluate first on a 'cons' expression"]),
    ("(first 1)", ["Cannot match argument out typeList ['INT'] with expected typeList ['LIST']"]),
    ("(first)", ['first only takes 1 arguments, but 0 were provided']),
    ("(first '(1 2) '(3 4))", ['first only takes 1 arguments, but 2 were provided']),
    ("(first (cons 1 null))", ['Insufficiently resolved arguments']), # error expected because the rule is 'eval first',
    ("(first L)", ["Cannot evaluate 'first' expression with generic arguments"]),
    ("(first null)", ['first requires non-empty list']),
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
    ("(rest (cons 1 null))", ['Insufficiently resolved arguments']), # error expected because the rule is 'eval rest'
    ("(rest null)", ['rest requires non-empty list']),
    ("(rest L)", ["Cannot evaluate 'rest' expression with generic arguments"]),
    ("(rest '(1 2 3))", "'(2 3)"), # rest for non-nested list
    ("(rest '((1 2) (3) (4)))", "'((3) (4))") # rest for nested list
]
totalFails += test_racket_function('rest', rest_tests, appliable=True)
totalFails += do_single_test_case('eval', 'restList', "(rest '(1 2 3))",
                                   ['Could not find rule associated with restList'])

print('\nTesting All Other Built-Ins\n')
zeroQ_tests = [
    ("(+ 1 2)", ["Cannot evaluate zero? on a '+' expression"]),
    ("(cons 1 null)", ["Cannot evaluate zero? on a 'cons' expression"]),
    ("(zero? 1 2)", ["zero? only takes 1 arguments, but 2 were provided"]),
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
    ("(null? null null)", ["null? only takes 1 arguments, but 2 were provided"]),
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
    ("(if 0 1 2)", ["Cannot match argument out typeList ['INT', 'INT', 'INT'] with expected typeList ['BOOL', 'ANY', 'ANY']"]),
    ("(if (= 1 1) 1 2)", ["Insufficiently resolved condition argument"]),
    ("(if #t 1 #f)", 1),
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
    ("(integer? 1 2)", ["integer? only takes 1 arguments, but 2 were provided"]),
    ("(integer? 1)", '#t'),
    ("(integer? k)", '#t'),
    ("(integer? null)", '#f'),
    ("(integer? '(1 2))", '#f'),
    ("(integer? L)", "#f"),
    ("(integer? #t)", '#f'),
    ("(integer? p)", '#f'),
    ("(integer? x)", '#f') # integer? with generic any currently evaluates to false
]
totalFails += test_racket_function('integer?', integerQ_tests)

listQ_tests = [
    ("(+ 1 2)", ["Cannot evaluate list? on a '+' expression"]),
    ("(list? null null)", ["list? only takes 1 arguments, but 2 were provided"]),
    ("(list? 1)", '#f'),
    ("(list? k)", '#f'),
    ("(list? null)", '#t'),
    ("(list? '(1 2))", '#t'),
    ("(list? L)", "#t"),
    ("(list? #t)", '#f'),
    ("(list? p)", '#f'),
    ("(list? x)", '#f') # list? with generic any currently evaluates to false
]
test_racket_function('list?', listQ_tests)

print('\nTest Undefined Labels\n')
totalFails += do_single_test_case('rewrite', 'cons-first-rest', '(cons (first L) (rest L))',
                                  ["No definition found for label '['L']'"], args="x=(first L), L=(rest L)")

axiomProof = ERProof()
axiomProof.addGeneric('a', 'int', {'assumption': 'None'})
axiomProof.addGeneric('b', 'int', {'assumption': 'Positive'})
axiomProof.addGeneric('M', 'list')
print("\nList Function Property Testing\n")
cons_prop_tests = [
    ("(cons 1 null)", "x=1, L=null",
     ["Can only apply cons-first-rest property when first arg is a 'first' expression and second arg is a 'rest' expression"]),
    ("(cons 1 (rest '(1 2)))", "x=1, L=(rest '(1 2))",
     ["Can only apply cons-first-rest property when first arg is a 'first' expression and second arg is a 'rest' expression"]),
    ("(cons (first '(1 2)) '(2))", "x=(first '(1 2)), L='(2)",
     ["Can only apply cons-first-rest property when first arg is a 'first' expression and second arg is a 'rest' expression"]),
    ("(cons (first L) (rest M))", "x=(first L), L=(rest M)", ["Cannot apply cons-first-rest property on two different "
                                                              "lists"]),
    ("(cons (first '(1 2)) (rest '(1 3)))", "x=(first '(1 2)), L=(rest '(1 3))", ["Cannot apply cons-first-rest "
                                                                                  "property on "
                                                                                  "two "
                                                                                  "different "
                                                                                  "lists"]),
    ("(cons (first null) (rest null))", "x=(first null), L=(rest null)", ["first requires non-empty list"]),
    # cannot apply
    # property when
    # list is
    # null
    ("(cons (first '(1 2)) (rest null))", "x=(first '(1 2)), L=(rest null)", ["rest requires non-empty list"]),
    # '() instead
    # of null
    ("(cons (first 1) (rest '(1)))", "x=(first 1), L=(rest '(1))", ["Cannot match argument out typeList ['INT'] with "
                                                                    "expected "
                                                                    "typeList ['LIST']"]),
    # bad type in argument expression
    ("(cons (first '(1 2) '(3)) (rest '(2 3)))", "x=(first '(1 2) '(3)), L=(rest '(2 3))", ["first only takes 1 "
                                                                                            "arguments, "
                                                                                            "but 2 were "
                                                                                            "provided"]),
    # extra argument in argument expressions
    ("(cons (first '(1 2)) (rest '(1) '(2)))", "x=(first '(1 2)), L=(rest '(1) '(2))", ["rest only takes 1 arguments, "
                                                                                        "but 2 were "
                                                                                        "provided"]),
    ("(cons (first '(1 2)) (rest '(1 2)) null)", "x=(first '(1 2)), L=(rest '(1 2)), M=null", ["cons only takes 2 "
                                                                                               "arguments, "
                                                                                               "but 3 were provided"]),
    # extra argument in cons expression
    ("(cons (first '(1 2)) (rest '(1 2)))", "x=(first '(1 2)), L=(rest '(1 2))", "'(1 2)"),
    ("(cons (first (cons 2 null)) (rest (cons 2 null)))", "x=(first (cons 2 null)), L=(rest (cons 2 null))",
     "(cons 2 null)"),  # list not completely resolved
    ("(cons (first L) (rest L))", "x=(first L), L=(rest L)", "L")  # symbols
]
totalFails += test_list_func_props('cons-first-rest', cons_prop_tests, axiomProof)

first_prop_tests = [
    ("(rest '(1 2))", "L='(1 2)", ["Cannot apply first-cons property to a 'rest' expression"]),
    ("(first '(1 2))", "L='(1 2)", ["Can only apply first-cons property when argument is a 'cons' expression"]),
    ("(first (cons 1 1))", # bad type in argument expression
     "L=(cons 1 1)", ["Cannot match argument out typeList ['INT', 'INT'] with expected typeList ['ANY', 'LIST']"]),
    ("(first (cons 1 '(2 3) '(4 5)))", "L=(cons 1 '(2 3) '(4 5))", ["cons only takes 2 arguments, but 3 were "
                                                                    "provided"]),
    # extra argument in argument expression
    ("(first (cons 1 null) null)", "L=(cons 1 null), M=null", ["first only takes 1 arguments, but 2 were provided"]),
    # extra argument in argument expression
    ("(first (cons 1 null))", "L=(cons 1 null)", "1"),
    ("(first (cons 9 '(8 7)))", "L=(cons 9 '(8 7))", "9"),
    ("(first (cons x L))", "L=(cons x L)", "x"),  # symbolic
    ("(first (cons (+ (* 4 5) (* 6 7)) null))", "L=(cons (+ (* 4 5) (* 6 7)) null)", "(+ (* 4 5) (* 6 7))"),
    # first cons argument not completely
    # simplified
    ("(first (cons 46 (cons 2 null)))", "L=(cons 46 (cons 2 null))", "46")  # second cons argument not completely
    # simplified
]
totalFails += test_list_func_props('first-cons', first_prop_tests)

rest_prop_tests = [
    ("(first '(1 2))", "L='(1 2)", ["Cannot apply rest-cons property to a 'first' expression"]),
    ("(rest '(1 2))", "L='(1 2)", ["Can only apply rest-cons property when argument is a 'cons' expression"]),
    ("(rest (cons 1 1))", # bad type in argument expression
     "L=(cons 1 1)", ["Cannot match argument out typeList ['INT', 'INT'] with expected typeList ['ANY', 'LIST']"]),
    ("(rest (cons 1 '(2 3) '(4 5)))", "L=(cons 1 '(2 3) '(4 5))", ["cons only takes 2 arguments, but 3 were provided"]),
    # extra argument in
    # argument expression
    ("(rest (cons 1 null) null)", "L=(cons 1 null), M=null", ["rest only takes 1 arguments, but 2 were provided"]),
    # extra argument in argument expression
    ("(rest (cons 1 null))", "L=(cons 1 null)", "null"),
    ("(rest (cons 9 '(8 7)))", "L=(cons 9 '(8 7))", "'(8 7)"),
    ("(rest (cons x L))", "L=(cons x L)", "L"),  # symbolic
    ("(rest (cons (+ (* 4 5) (* 6 7)) null))", "L=(cons (+ (* 4 5) (* 6 7)) null)", "null"),
    # first cons argument not completely simplified
    ("(rest (cons 46 (cons 2 null)))", "L=(cons 46 (cons 2 null))", "(cons 2 null)")  # second cons argument not
    # completely simplified
]
totalFails += test_list_func_props('rest-cons', rest_prop_tests)

minus_plus_tests = [
    ("(+ 1 2)", 'x=1, y=2', ["Cannot apply -+ when the root operation is +"]),
    ("(- 2 1)", 'x=2, y=1', ["Cannot apply -+ when the first argument of - is not a + expression"]),
    ("(- (* 2 2) 2)", 'x=(* 2 2), y=2', ["Cannot apply -+ when the first argument of - is not a + expression"]),
    # bad types
    ("(- (+ null 1) 1)", 'x=(+ null 1), y=1', ["Cannot match argument out typeList ['LIST', 'INT'] with expected "
                                               "typeList ['INT', "
                                               "'INT']"]),
    ("(- (+ 1 #f) #f)", 'x=(+ 1 #f), y=#f', ["Cannot match argument out typeList ['INT', 'BOOL'] with expected "
                                             "typeList ['INT', 'INT']",
    "Cannot match argument out typeList ['INT', 'BOOL'] with expected typeList ['INT', 'INT']"]),
    # too many arguments
    ("(- (+ 1 2 3) 2)", 'x=(+ 1 2 3), y=2', ["+ only takes 2 arguments, but 3 were provided"]),
    ("(- (+ k 1) 1 2)", 'x=(+ k 1), y=1, z=2', ["- only takes 2 arguments, but 3 were provided"]),
    # Insufficiently resolved arguments
    ("(- (+ 1 2) (+ 1 1))", 'x=(+ 1 2), y=(+ 1 1)', ["Insufficiently resolved arguments"]),
    ("(- (+ 1 (+ 1 1)) 2)", 'x=(+ 1 (+ 1 1)), y=2', ["Insufficiently resolved arguments"]),
    ("(- (+ 1 (+ 1 1)) (+ 1 1))", 'x=(+ 1 (+ 1 1)), y=(+ 1 1)', ["Insufficiently resolved arguments"]),
    # arguments don't match
    ("(- (+ k 2) 1)", 'x=(+ k 2), y=1', ["Cannot apply -+ when the second argument of - doesn't match the second "
                                         "argument of +"]),
    # valid
    ("(- (+ 2 1) 1)", 'x=(+ 2 1), y=1', "2"),
    ("(- (+ (* 8 8) 3) 3)", 'x=(+ (* 8 8) 3), y=3', "(* 8 8)"),
    ("(- (+ k 9) 9)", 'x=(+ k 9), y=9', "k")
]
totalFails += run_test_cases("rewrite", "-+", minus_plus_tests)
totalFails += do_single_test_case("eval", "-+", minus_plus_tests[-1][0], ["Cannot evaluate a property"])
totalFails += do_single_test_case("apply", "-+", minus_plus_tests[-1][0], ["Cannot apply a property"])

nullQ_cons_tests = [
    ("(rest '(1 2))", "L='(1 2)", ["Cannot apply null?-cons property when root operation is 'rest'"]),
    ("(first '(1 2))", "L='(1 2)", ["Cannot apply null?-cons property when root operation is 'first'"]),
    ("(null? null)", "L=null", ["Cannot apply null?-cons property when argument is not a 'cons' expression"]),
    ("(null? '(1 2 3))", "L='(1 2 3)", ["Cannot apply null?-cons property when argument is not a 'cons' expression"]),
    ("(null? (cons 1 null) null)", "L=(cons 1 null), M=null", ["null? only takes 1 arguments, but 2 were provided"]),
    ("(null? (cons 1 1))", "L=(cons 1 1)", ["Cannot match argument out typeList ['INT', 'INT'] with expected typeList ["
                                            "'ANY', 'LIST']"]),  # bad type in cons
    ("(null? (cons 1 1 null))", "L=(cons 1 1 null)", ["cons only takes 2 arguments, but 3 were provided"]),  # too many
    # arguments in cons
    ("(null? (cons x L))", "L=(cons x L)", "#f"),  # symbolic
    ("(null? (cons (+ 1 2) (cons null null)))", "L=(cons (+ 1 2) (cons null null))", "#f"),  # not fully resolved
    ("(null? (cons 1 null))", "L=(cons 1 null)", "#f")
]
totalFails += run_test_cases("rewrite", "null?-cons", nullQ_cons_tests)
totalFails += do_single_test_case("eval", "null?-cons", nullQ_cons_tests[-1][0], ["Cannot evaluate a property"])

zeroQ_plus_tests = [
    ("(zero? (+ 0 1))", 'x=(+ 0 1)', '#f'),
    ("(zero? (+ 1 0))", 'x=(+ 1 0)', '#f'),
    ("(zero? (+ a k))", 'x=(+ a k)', ["Can only apply zero?+ property when one argument of + is positive and the other "
                                      "is "
                                      "nonnegative"]),
    ("(zero? (+ a b))", 'x=(+ a b)', ["Can only apply zero?+ property when one argument of + is positive and the other "
                                      "is "
                                      "nonnegative"]),
    ("(zero? (+ k a))", 'x=(+ k a)', ["Can only apply zero?+ property when one argument of + is positive and the other "
                                      "is "
                                      "nonnegative"]),
    ("(zero? (+ k 0))", 'x=(+ k 0)', ["Can only apply zero?+ property when one argument of + is positive and the other "
                                      "is "
                                      "nonnegative"]),
    ("(zero? (+ b 0))", 'x=(+ b 0)', '#f'),
    ("(zero? (+ b x))", 'x=(+ b x)', "#f"),  # using GenericAny (should be treated as a nonnegative int)
    ("(zero? (+ b k))", 'x=(+ b k)', '#f')
]
totalFails += run_test_cases("rewrite", "zero?+", zeroQ_plus_tests, axiomProof)
totalFails += do_single_test_case("eval", "zero?+", zeroQ_plus_tests[-1][0], ["Cannot evaluate a property"], axiomProof)
totalFails += do_single_test_case("apply", "zero?+", zeroQ_plus_tests[-1][0], ["Cannot apply a property"], axiomProof)

and_prop_tests = [
    ("(or #t #f)", "x=#t, y=#f", ["Cannot rewrite 'and' property on a 'or' expression"]),
    ("(and #t #t)", "x=#t, y=#t", ["Can only rewrite 'and' property when one argument is '#f'"]),
    ("(and #f #f)", "x=#f, y=#f", ["Cannot rewrite 'and' property when both arguments are '#f'"]),
    ("(and #f null)", "x=#f, y=null",
     ["Cannot match argument out typeList ['BOOL', 'LIST'] with expected typeList ['BOOL', 'BOOL']"]),
    ("(and 1 #f)", "x=1, y=#f",
     ["Cannot match argument out typeList ['INT', 'BOOL'] with expected typeList ['BOOL', 'BOOL']"]),
    ("(and #f #t)", "x=#f, y=#t", "#f"),  # one argument is false
    ("(and #t #f)", "x=#t, y=#f", "#f"),  # one argument is false
    ("(and #f (if (zero? 1) #t #f))", "x=#f, y=(if (zero? 1) #t #f)", "#f"),  # will work because the first argument is
    # false
    ("(and (if (zero? 1) #t #f) #f)", "x=(if (zero? 1) #t #f), y=#f", "#f")
    # will work because the second argument is false
]
totalFails += run_test_cases("rewrite", "and", and_prop_tests, axiomProof)
totalFails += do_single_test_case("apply", "and", and_prop_tests[-1][0], ["Could not find definition/lemma "
                                                                          "associated with and"], axiomProof)

or_prop_tests = [
    ("(and #t #f)", "x=#t, y=#f", ["Cannot rewrite 'or' property on a 'and' expression"]),
    ("(or #f #f)", "x=#f, y=#f", ["Can only rewrite 'or' property when one argument is '#t'"]),
    ("(or #t #t)", "x=#t, y=#t", ["Cannot rewrite 'or' property when both arguments are '#t'"]),
    ("(or #t null)", "x=#t, y=null",
     ["Cannot match argument out typeList ['BOOL', 'LIST'] with expected typeList ['BOOL', 'BOOL']"]),
    ("(or 1 #t)", "x=1, y=#t",
     ["Cannot match argument out typeList ['INT', 'BOOL'] with expected typeList ['BOOL', 'BOOL']"]),
    ("(or #t #f)", "x=#t, y=#f", "#t"),  # one argument is true
    ("(or #f #t)", "x=#f, y=#t", "#t"),  # one argument is true
    ("(or #t (if (zero? 1) #t #f))", "x=#t, y=(if (zero? 1) #t #f)", "#t"),  # will work because the first argument is
    # true
    ("(or (if (zero? 1) #t #f) #t)", "x=(if (zero? 1) #t #f), y=#t", "#t")
    # will work because the second argument is true
]
totalFails += run_test_cases("rewrite", "or", or_prop_tests, axiomProof)
totalFails += do_single_test_case("apply", "or", or_prop_tests[-1][0], ["Could not find definition/lemma "
                                                                        "associated with or"], axiomProof)

implies_prop_tests = [
    ("(and #t #f)", "x=#t, y=#f", ["Cannot rewrite 'implies' property on a 'and' expression"]),
    ("(implies #t #t)", "x=#t, y=#t", ["Can only rewrite 'implies' property when first argument is '#f'"]),
    ("(implies #f (if (zero? 1) #t #f))", "x=#f, y=(if (zero? 1) #t #f)", "#t"),  # lets unresolved expression be
    # second argument
]
totalFails += run_test_cases("rewrite", "implies", implies_prop_tests, axiomProof)
totalFails += do_single_test_case("apply", "implies", implies_prop_tests[-1][0], ["Could not find definition/lemma "
                                                                                  "associated with implies"],
                                  axiomProof)

print("\nUDF testing:\n")
udfProof = ERProof()
udfProof.addUDF("(f x y)", "(INT,INT)>INT", "(* x y)")
udfProof.addUDF("(g x)", "INT>BOOL", "(< x 5)")
udfProof.addUDF("(h x y)", "(LIST,LIST)>LIST", "(cons (first x) (cons (first y) null))")
udfProof.addUDF("(i x)", "LIST>BOOL", "(zero? (first x))")
udfProof.addUDF("a", "INT", "5")
udfProof.addUDF("q", "BOOL", "#f")
# udfProof.addUDF("(h)", "()>INT", "5") TODO: need to implement 0 argument UDFs
# udfProof.addUDF("i", "INT", "3") TODO need to implement 0 argument UDFs
# 2 arguments
totalFails += do_single_test_case('', 'f', "(f 3 4)", ["Rule must start with 'eval', 'apply', or 'rewrite'"], udfProof)
totalFails += do_single_test_case('eval', 'f',  "(f 3 4)", ['Cannot evaluate a user-defined function'], udfProof)
totalFails += do_single_test_case('apply', 'f', "(f 3 4)", ['Not enough arguments given for f. f requires 2 '
                                                            'arguments, while you gave 0'],
                                  udfProof)
totalFails += do_single_test_case('apply', 'f x=3, y=4, z=5', "(f 3 4)", ['Too many arguments given for f. f '
                                                                          'requires 2 arguments, while you gave 3'],
                                  udfProof)
totalFails += do_single_test_case('apply', 'f x=3 y=4', "(f 3 4)", ['Too many assignments for a given argument \'x=3 '
                                                                    'y=4\'. Did you forget a comma?'], udfProof)
totalFails += do_single_test_case('apply', 'f z=3, y=4', "(f 3 4)",
                                  ["Argument 'z' is in position 1 but expected 'x' for f"], udfProof)
totalFails += do_single_test_case('apply', 'f x=3, z=4', "(f 3 4)",
                                  ["Argument 'z' is in position 2 but expected 'y' for f"],
                                  udfProof)
totalFails += do_single_test_case('apply', 'f y=4, x=3', "(f 3 4)", ["Argument 'y' is in position 1 but expected 'x' "
                                                                     "for f", "Argument 'x' is in position 2 but "
                                                                              "expected 'y' for f"], udfProof)
totalFails += do_single_test_case('apply', 'f x=#t, y=4', "(f 3 4)", ["Type mismatch in argument 'x=#t': expected "
                                                                      "INT, got BOOL"], udfProof)
totalFails += do_single_test_case('apply', "f x=3, y='(1 2 3)", "(f 3 4)", ["Type mismatch in argument 'y='(1 2 3)': "
                                                                            "expected "
                                                                            "INT, got LIST"], udfProof)
totalFails += do_single_test_case('apply', 'f x=4, y=5', "(f 3 4)", ["Value mismatch in argument 'x': expected 3, "
                                                                     "got 4", "Value mismatch in argument 'y': "
                                                                              "expected 4, got 5"], udfProof)
totalFails += do_single_test_case('apply', 'f x=3, y=4', "(f 3 4)", "(* 3 4)", udfProof)

# 1 argument
totalFails += do_single_test_case('', 'g x=3', "(g 3)", ["Rule must start with 'eval', 'apply', or 'rewrite'"],
                                  udfProof)
totalFails += do_single_test_case('eval', 'g x=3', "(g 3)", ['Cannot evaluate a user-defined function'], udfProof)
totalFails += do_single_test_case('apply', 'g', "(g 3)", ['Not enough arguments given for g. g requires 1 arguments, '
                                                          'while you gave 0'], udfProof)
totalFails += do_single_test_case('apply', 'g x=3, y=4', "(g 3)", ['Too many arguments given for g. g requires 1 '
                                                                   'arguments, while you gave 2'], udfProof)
totalFails += do_single_test_case('apply', 'g y=3', "(g 3)", ["Argument 'y' is in position 1 but expected 'x' for g"],
                                  udfProof)
totalFails += do_single_test_case('apply', 'g x=#t', "(g 3)", ["Type mismatch in argument 'x=#t': expected INT, "
                                                               "got BOOL"], udfProof)
totalFails += do_single_test_case('apply', 'g x=3', "(g 4)", ["Value mismatch in argument 'x': expected 4, got 3"],
                                  udfProof)
totalFails += do_single_test_case('apply', 'g x=3', "(g 3)", "(< 3 5)", udfProof)

# 2 list argument
totalFails += do_single_test_case('apply', 'h', "(h '(1 2 3) '(4 5 6))", ['Not enough arguments given for h. h '
                                                                          'requires 2 arguments, while you gave 0'],
                                  udfProof)
totalFails += do_single_test_case('apply', "h x='(1 2 3), y='(4 5 6), z='(7 8 9)", "(h '(1 2 3) '(4 5 6))", ['Too many '
                                                                                                             'arguments given for h. h requires 2 arguments, while you gave 3'],
                                  udfProof)
totalFails += do_single_test_case('apply', "h x='(1 2 3) y='(4 5 6)", "(h '(1 2 3) '(4 5 6))",
                                  ["Too many assignments for a given argument 'x='(1 2 3) y='(4 5 6)'. Did you forget a comma?"],
                                  udfProof)
totalFails += do_single_test_case('apply', "h z='(1 2 3), y='(4 5 6)", "(h '(1 2 3) '(4 5 6))",
                                  ["Argument 'z' is in position 1 but expected 'x' for h"],
                                  udfProof)
totalFails += do_single_test_case('apply', "h x='(1 2 3), z='(4 5 6)", "(h '(1 2 3) '(4 5 6))",
                                  ["Argument 'z' is in position 2 but expected 'y' for h"],
                                  udfProof)
totalFails += do_single_test_case('apply', "h y='(4 5 6), x='(1 2 3)", "(h '(1 2 3) '(4 5 6))",
                                  ["Argument 'y' is in position 1 but expected 'x' for h",
                                   "Argument 'x' is in position 2 but expected 'y' for h"],
                                  udfProof)
totalFails += do_single_test_case('apply', "h x='(1 2 3), y=#t", "(h '(1 2 3) '(4 5 6))",
                                  ["Type mismatch in argument 'y=#t': expected LIST, got BOOL"],
                                  udfProof)
totalFails += do_single_test_case('apply', "h x='(1 2 3), y='(4 5 6)", "(h '(3 2 1) '(6 5 4))",
                                  ["Value mismatch in argument 'x': expected '(3 2 1), got '(1 2 3)",
                                   "Value mismatch in argument 'y': expected '(6 5 4), got '(4 5 6)"],
                                  udfProof)
totalFails += do_single_test_case('apply', "h x='(1 2 3), y='(4 5 6)", "(h '(1 2 3) '(4 5 6))",
                                  "(cons (first '(1 2 3)) (cons (first '(4 5 6)) null))", udfProof)

# 1 list argument
totalFails += do_single_test_case('apply', 'i', "(i '(0 1 2))", ['Not enough arguments given for i. i requires 1 '
                                                                 'arguments, while you gave 0'], udfProof)
totalFails += do_single_test_case('apply', "i x='(0 1 2), y='(3 4 5)", "(i '(0 1 2))", ['Too many arguments given for '
                                                                                        'i. i requires 1 arguments, while you gave 2'],
                                  udfProof)
totalFails += do_single_test_case('apply', "i y='(0 1 2)", "(i '(0 1 2))",
                                  ["Argument 'y' is in position 1 but expected 'x' for i"], udfProof)
totalFails += do_single_test_case('apply', "i x=#t", "(i '(0 1 2))", ["Type mismatch in argument 'x=#t': expected "
                                                                      "LIST, got BOOL"], udfProof)
totalFails += do_single_test_case('apply', "i x='(0 1 2)", "(i '(3 4 5))",
                                  ["Value mismatch in argument 'x': expected '(3 4 5), got '(0 1 2)"], udfProof)
totalFails += do_single_test_case('apply', "i x='(0 1 2)", "(i '(0 1 2))", "(zero? (first '(0 1 2)))", udfProof)

# check that a non-function definition is caught as insufficiently resolved
totalFails += do_single_test_case("eval", "+", "(+ a 1)", ["Insufficiently resolved arguments"], udfProof)
totalFails += do_single_test_case("eval", "if", "(if q 1 2)", ["Insufficiently resolved condition argument"], udfProof)

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