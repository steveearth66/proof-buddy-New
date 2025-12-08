#from django.test import TestCase

# Create your tests here.
from platform import node
from expression_tree.ERProofEngine import ERProof, ERProofLine
from expression_tree.IndProofs import IndProof
from expression_tree.ERCommon import Node, makeJson, findNode
import sympy as sp
import json
from expression_tree.ERCommon import makeJson

def show_node_ids(exprTree:Node, indent=0):
    if exprTree is None:
        return
    print("  " * indent + f"ID {exprTree.startPosition}: '{exprTree.data}' (type: {exprTree.type})")
    for child in exprTree.children:
        show_node_ids(child, indent + 1)

def do_single_test_case(rule: str, expr: str, expected, proof: ERProof = None) -> int:
    if proof == None:
        proof = ERProof()
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

def run_test_cases(rule: str, tests: list[tuple], proof: ERProof = None, defaultGenerics=True) -> int:
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

def test_axiom(axiom: str, tests: list[tuple], proof: ERProof, builtInProp=False) -> int:
    fails = run_test_cases(f'rewrite {axiom}', tests, proof)
    expr, args, _ = tests[-1]
    if not builtInProp:
        fails += do_single_test_case(f'eval {axiom}', expr, ["Cannot evaluate axiom"], proof)
        fails += do_single_test_case(f'apply {axiom} with {args}', expr, ["Cannot apply axiom"], proof)
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
totalFails += do_single_test_case('eval math', '(+ 1 2)', 
                                  ["Cannot evaluate algebraic math rule"])
totalFails += do_single_test_case('math', '(+ 1 2)', ["Rule must start with 'eval', 'apply', or 'rewrite'"])

# Logic Function Tests
print('\nTesting Logic Rules:\n')
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
totalFails += do_single_test_case('eval logic', '(and #t #t)', ["Could not find rule associated with 'logic'"])
totalFails += do_single_test_case("logic", '(and #t #t)', ["Rule must start with 'eval', 'apply', or 'rewrite'"])

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

print('\nTesting All Other Built-Ins\n')
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

print('\nTest Undefined Labels\n')
totalFails += do_single_test_case('rewrite cons-first-rest with L=L', '(cons (first L) (rest L))',
                                  ["No definition found for label 'L'"])

print('\nTest Axiom Param Mapping\n')
totalFails += do_single_test_case("rewrite cons-first-rest with x=(first '(1)), L=(rest'(1))",
                                  "(cons (first '(1)) (rest '(1)))", 
                                  ['Unexpected assignment "x=(first \'(1))" was provided'])
totalFails += do_single_test_case("rewrite cons-first-rest with L='(1), x='(1)",
                                  "(cons (first '(1)) (rest '(1)))", 
                                  ['Unexpected assignment "x=\'(1)" was provided'])
totalFails += do_single_test_case("rewrite cons-first-rest with L='(1), L='(1)",
                                  "(cons (first '(1)) (rest '(1)))",
                                  ['Unexpected assignment "L=\'(1)" was provided'])

# below test case commented out because L'(1) appears to not be caught as an assignment by regex 
# in ERProofLine.applyRule()
'''totalFails += do_single_test_case("rewrite cons-first-rest with L'(1)",
                                  "(cons (first '(1)) (rest '(1)))",
                                  ['"L\'(1)" does not have an assignment. ' 
                                   'Did you forget an equals sign?'])'''

totalFails += do_single_test_case("rewrite first-cons with x=(+ 1 2, L=null",
                                  "(first (cons (+ 1 2) null))", 
                                  ['Failed to build AST from assignment "(+ 1 2"'])

axiomProof = ERProof()
axiomProof.addGeneric('a', 'int', {'assumption': 'None'})
axiomProof.addGeneric('b', 'int', {'assumption': 'Positive'})
axiomProof.addGeneric('M', 'list')
print("\nAxiom Testing\n")
cons_prop_tests = [
    ("(cons 1 null)",
     ["Can only rewrite with cons-first-rest rule when first arg is a 'first' expression and second arg is a 'rest' expression"]),
    ("(cons 1 (rest '(1 2)))",
     ["Can only rewrite with cons-first-rest rule when first arg is a 'first' expression and second arg is a 'rest' expression"]),
    ("(cons (first '(1 2)) '(2))",
     ["Can only rewrite with cons-first-rest rule when first arg is a 'first' expression and second arg is a 'rest' expression"]),
    ("(cons (first L) (rest M))",
     ["Cannot rewrite with cons-first-rest rule when the arguments of 'first' and 'rest' are different lists"]),
    ("(cons (first '(1 2)) (rest '(1 3)))", 
     ["Cannot rewrite with cons-first-rest rule when the arguments of 'first' and 'rest' are different lists"]),
    ("(cons (first null) (rest null))", "L=null", ["first and rest require non-empty lists"]),
    # cannot rewrite when list is null
    ("(cons (first 1) (rest '(1)))", 
     ["Cannot match argument out typeList ['INT'] with expected typeList ['LIST']"]),
    # bad type in argument expression
    ("(cons (first '(1 2) '(3)) (rest '(2 3)))", ["first only takes 1 argument, but 2 were provided"]),
    # extra argument in argument expressions
    ("(cons (first '(1 2)) (rest '(1) '(2)))", "L='(1 2)", ["rest only takes 1 argument, but 2 were provided"]),
    ("(cons (first '(1 2)) (rest '(1 2)) null)", "L='(1 2)", ["cons only takes 2 arguments, but 3 were provided"]),
    # extra argument in cons expression
    ("(cons (first '(1 2)) (rest '(1 2)))", 
     ["Too few assignments were provided: param 'L' does not have an assignment"]), # no assignments
    ("(cons (first '(1 2)) (rest '(1 2)))", "L='(1)",
     ['Value mismatch: expected "\'(1 2)" for L, but "\'(1)" was provided']),
    ("(cons (first '(1 2)) (rest '(1 2)))", "L='(1 2)", "'(1 2)"),
    ("(cons (first (cons 2 null)) (rest (cons 2 null)))", "L=(cons 2 null)", 
     ['Insufficiently resolved arguments']),  # list not completely resolved
    ("(cons (first L) (rest L))", "L=L", "L")  # symbols
]
totalFails += test_axiom('cons-first-rest', cons_prop_tests, axiomProof)

first_prop_tests = [
    ("(rest '(1 2))", ["Cannot rewrite with first-cons rule when root operation is 'rest'"]),
    ("(first '(1 2))", ["Can only rewrite with first-cons rule when argument is a 'cons' expression"]),
    ("(first (cons 1 1))", # bad type in argument expression
     "x=1, L=1", ["Cannot match argument out typeList ['INT', 'INT'] with expected typeList ['ANY', 'LIST']"]),
    ("(first (cons 1 '(2 3) '(4 5)))", ["cons only takes 2 arguments, but 3 were provided"]),
    # extra argument in argument expression
    ("(first (cons 1 null) null)", ["first only takes 1 argument, but 2 were provided"]),
    # extra argument in argument expression
    ("(first (cons 1 null))", ["Too few assignments were provided: "
                                "params 'x', 'L' do not have assignments"]),
    ("(first (cons 1 null))", "x=null, L=1", 
     ['Value mismatch: expected "1" for x, but "null" was provided']),
    ("(first (cons 1 null))", "x=1, L=null", "1"),
    ("(first (cons 9 '(8 7)))", "x=9, L='(8 7)", "9"),
    ("(first (cons x L))", "x=x, L=L", "x"),  # symbolic
    ("(first (cons (+ (* 4 5) (* 6 7)) null))", "x=(+ (* 4 5) (* 6 7)), L=null", "(+ (* 4 5) (* 6 7))"),
    # first cons argument not completely simplified
    ("(first (cons 46 (cons 2 null)))", "x=46, L=(cons 2 null)", "46")  # second cons argument not completely simplified
]
totalFails += test_axiom('first-cons', first_prop_tests, axiomProof)
rest_prop_tests = [
    ("(first '(1 2))", ["Cannot rewrite with rest-cons rule when root operation is 'first'"]),
    ("(rest '(1 2))", ["Can only rewrite with rest-cons rule when argument is a 'cons' expression"]),
    ("(rest (cons 1 1))", # bad type in argument expression
      ["Cannot match argument out typeList ['INT', 'INT'] with expected typeList ['ANY', 'LIST']"]),
    ("(rest (cons 1 '(2 3) '(4 5)))", ["cons only takes 2 arguments, but 3 were provided"]),
    # extra argument in argument expression
    ("(rest (cons 1 null) null)", ["rest only takes 1 argument, but 2 were provided"]),
    # extra argument in argument expression
    ("(rest (cons 1 null))", ["Too few assignments were provided: "
                                "params 'x', 'L' do not have assignments"]),
    ("(rest (cons 1 null))", "x=null, L=1", 
     ['Value mismatch: expected "1" for x, but "null" was provided']),
    ("(rest (cons 1 null))", "x=1, L=null", "null"),
    ("(rest (cons 9 '(8 7)))", "x=9, L='(8 7)", "'(8 7)"),
    ("(rest (cons x L))", "x=x, L=L", "L"),  # symbolic
    ("(rest (cons (+ (* 4 5) (* 6 7)) null))", "x=(+ (* 4 5) (* 6 7)), L=null", "null"),
    # first cons argument not completely simplified
    ("(rest (cons 46 (cons 2 null)))", "x=46, L=(cons 2 null)", "(cons 2 null)")  
    # second cons argument not completely simplified
]
totalFails += test_axiom('rest-cons', rest_prop_tests, axiomProof)

minus_plus_tests = [
    ("(+ 1 2)", ["Cannot rewrite with -+ rule when the root operation is +"]),
    ("(- 2 1)", ["Cannot rewrite with -+ rule when the first argument of - is not a + expression"]),
    ("(- (* 2 2) 2)", ["Cannot rewrite with -+ rule when the first argument of - is not a + expression"]),
    # bad types
    ("(- (+ null 1) 1)", ["Cannot match argument out typeList ['LIST', 'INT']"
                          " with expected typeList ['INT', 'INT']"]),
    ("(- (+ 1 #f) #f)", ["Cannot match argument out typeList ['INT', 'BOOL'] with expected typeList ['INT', 'INT']",
      "Cannot match argument out typeList ['INT', 'BOOL'] with expected typeList ['INT', 'INT']"]),
    # too many arguments
    ("(- (+ 1 2 3) 2)", ["+ only takes 2 arguments, but 3 were provided"]),
    ("(- (+ k 1) 1 2)", ["- only takes 2 arguments, but 3 were provided"]),
    # arguments don't match
    ("(- (+ k 2) 1)", ["Cannot rewrite with -+ rule when the second argument of - "
                        "doesn't match an argument of +"]),
    ("(- (+ k 1) 1)", ["Too few assignments were provided: params 'a', 'k' do not have assignments"]),
    ("(- (+ k 1) 1)", "a=k, k=1", ['Value mismatch: expected "1" for a, but "k" was provided']),
    # valid
    ("(- (+ 2 1) 1)", 'a=1, k=2', "2"),
    ("(- (+ (* 8 8) 3) 3)", 'a=3, k=(* 8 8)', "(* 8 8)"),
    ("(- (+ k 9) 9)", 'a=9, k=k', "k"),
    ("(- (+ 1 k) 1)", 'a=1, k=k', "k")
]
totalFails += test_axiom("-+", minus_plus_tests, axiomProof)

nullQ_cons_tests = [
    ("(rest '(1 2))", "x=1, L=2", ["Cannot rewrite with null?-cons rule when root operation is 'rest'"]),
    ("(first '(1 2))", "x=1, L=2", ["Cannot rewrite with null?-cons rule when root operation is 'first'"]),
    ("(null? null)", "L=null", ["Cannot rewrite with null?-cons rule when argument is not a 'cons' expression"]),
    ("(null? '(1 2 3))", "x=1, L=2", ["Cannot rewrite with null?-cons rule when argument is not a 'cons' expression"]),
    ("(null? (cons 1 null) null)", "x=1, L=null", ["null? only takes 1 argument, but 2 were provided"]),
    ("(null? (cons 1 1))", "x=1, L=1", ["Cannot match argument out typeList ['INT', 'INT'] with expected typeList ["
                                            "'ANY', 'LIST']"]),  # bad type in cons
    ("(null? (cons 1 1 null))", "x=1, L=null", ["cons only takes 2 arguments, but 3 were provided"]),  # too many arguments in cons
    ("(null? (cons 1 null))", 
     ["Too few assignments were provided: params 'x', 'L' do not have assignments"]),
    ("(null? (cons 1 null))", "x=null, L=1", 
     ['Value mismatch: expected "1" for x, but "null" was provided']),
    ("(null? (cons x L))", "x=x, L=L", "#f"),  # symbolic
    ("(null? (cons (+ 1 2) (cons null null)))", "x=(+ 1 2), L=(cons null null)", "#f"),  # not fully resolved
    ("(null? (cons 1 null))", "x=1, L=null", "#f")
]
totalFails += test_axiom("null?-cons", nullQ_cons_tests, axiomProof)

zeroQ_plus_tests = [
    ("(null? 5)", ["Cannot rewrite with zero?+ rule when root operation is 'null?'"]),
    ("(zero? 5)", ["Can only rewrite with zero?+ rule when argument of zero? is a '+' expression"]),
    ("(zero? (- 2 1))", 
     ["Can only rewrite with zero?+ rule when argument of zero? is a '+' expression"]),
    ("(zero? (+ 0 1))", 
     ["Too few assignments were provided: params 'a', 'k' do not have assignments"]),
    ("(zero? (+ 0 1))", 'a=1, k=0', ['Value mismatch: expected "0" for a, but "1" was provided']),
    ("(zero? (+ 0 1))", 'a=0, k=1', '#f'),
    ("(zero? (+ 1 0))", 'a=1, k=0', '#f'),
    # a: all, b: positive, k: non-negative
    ("(zero? (+ a k))", 'a=a, k=k', 
     ["Neither 'a' nor 'k' can be negative when rewriting with zero?+ rule"]),
    ("(zero? (+ a b))", 'a=a, k=b', 
     ["Neither 'a' nor 'k' can be negative when rewriting with zero?+ rule"]),
    ("(zero? (+ k a))", 'a=k, k=a', 
     ["Neither 'a' nor 'k' can be negative when rewriting with zero?+ rule"]),
    ("(zero? (+ k 0))", 'a=k, k=0', 
     ["One of either 'a' or 'k' must be positive when rewriting with zero?+ rule"]),
    ("(zero? (+ b 0))", 'a=b, k=0', '#f'),
    ("(zero? (+ b x))", 'a=b, k=x', "#f"),  # using GenericAny (should be treated as a nonnegative int)
    ("(zero? (+ b k))", 'a=b, k=k', '#f')
]
totalFails += test_axiom("zero?+", zeroQ_plus_tests, axiomProof)

and_prop_tests = [
    ("(or #t #f)", ["Cannot rewrite 'or' expression with 'and' rule"]),
    ("(and #t #t)", ["Can only rewrite with 'and' rule when one argument is '#f'"]),
    ("(and #f null)", "p=null",
     ["Cannot match argument out typeList ['BOOL', 'LIST'] with expected typeList ['BOOL', 'BOOL']"]),
    ("(and 1 #f)", "p=1",
     ["Cannot match argument out typeList ['INT', 'BOOL'] with expected typeList ['BOOL', 'BOOL']"]),
    ("(and #f #t)", ["Too few assignments were provided: param 'p' does not have an assignment"]),
    ("(and #f #t)", "p=#f", ['Value mismatch: expected "#t" for p, but "#f" was provided']),
    ("(and #f #t)", "p=#t", "#f"),  # one argument is false
    ("(and #t #f)", "p=#t", "#f"),  # one argument is false
    ("(and #f (if (zero? 1) #t #f))", "p=(if (zero? 1) #t #f)", "#f"),  # will work because the first argument is
    # false
    ("(and (if (zero? 1) #t #f) #f)", "p=(if (zero? 1) #t #f)", "#f"),
    # will work because the second argument is false
    ("(and p #f)", "p=p", "#f") # symbolic
]
totalFails += test_axiom("and", and_prop_tests, axiomProof, builtInProp=True)

or_prop_tests = [
    ("(and #t #f)", "p=#f", ["Cannot rewrite 'and' expression with 'or' rule"]),
    ("(or #f #f)", "p=#f", ["Can only rewrite with 'or' rule when one argument is '#t'"]),
    ("(or #t null)", "p=null",
     ["Cannot match argument out typeList ['BOOL', 'LIST'] with expected typeList ['BOOL', 'BOOL']"]),
    ("(or 1 #t)", "p=1",
     ["Cannot match argument out typeList ['INT', 'BOOL'] with expected typeList ['BOOL', 'BOOL']"]),
    ("(or #t #f)", ["Too few assignments were provided: param 'p' does not have an assignment"]),
    ("(or #t #f)", "p=#t", ['Value mismatch: expected "#f" for p, but "#t" was provided']),
    ("(or #t #f)", "p=#f", "#t"),  # one argument is true
    ("(or #f #t)", "p=#f", "#t"),  # one argument is true
    ("(or #t (if (zero? 1) #t #f))", "p=(if (zero? 1) #t #f)", "#t"),  # will work because the first argument is
    # true
    ("(or (if (zero? 1) #t #f) #t)", "p=(if (zero? 1) #t #f)", "#t"),
    # will work because the second argument is true
    ("(or p #t)", "p=p", "#t") # symbolic
]
totalFails += test_axiom("or", or_prop_tests, axiomProof, builtInProp=True)

implies_prop_tests = [
    ("(and #t #f)", ["Cannot rewrite 'and' expression with 'implies' rule"]),
    ("(implies #t #f)", ["Can only rewrite with 'implies' rule when first argument is '#f' "
                         "or second argument is '#t'"]),
    ("(implies #f p)", ["Too few assignments were provided: param 'p' does not have an assignment"]),
    ("(implies #f p)", "p=#f", ['Value mismatch: expected "p" for p, but "#f" was provided']),
    ("(implies p #t)", "p=#t", ['Value mismatch: expected "p" for p, but "#t" was provided']),
    ("(implies #f #t)", ["Too few assignments were provided: param 'p' does not have an assignment"]),
    ("(implies #f #t)", "p=p", ['Value mismatch: expected "#f" or "#t" for p, but "p" was provided']), 
    ("(implies #f #t)", "p=#f", "#t"),
    ("(implies #f #t)", "p=#t", "#t"),
    ("(implies #f (if (zero? 1) #t #f))", "p=(if (zero? 1) #t #f)", "#t"),  # lets unresolved expression be
    # second argument
    ("(implies #f #f)", "p=#f", "#t"),
    ("(implies #t #t)", "p=#t", "#t"),
    ("(implies #f p)", "p=p", "#t"),
    ("(implies p #t)", "p=p", "#t")
]
totalFails += test_axiom("implies", implies_prop_tests, axiomProof, builtInProp=True)

axiomProof.addUDF("(F n)", "INT>INT", "(if (<= n 1) n (+ (F (- n 1)) (F (- n 2))))")
axiomProof.addUDF("(G L)", "LIST>LIST", "(cons 1 L)")
integerQ_prop_tests = [
    ("(integer? 1)", ["Cannot rewrite with 'integer?' rule when argument is not a function call"]),
    ("(integer? (cons 1 null))", ["Too few assignments were provided: param 'op' does not have an assignment"]),
    ("(integer? (cons 1 null))", "op=(cons 1 null)", 
     ['Value mismatch: expected "cons" for op, but "(cons 1 null)" was provided']),
    ("(integer? (first L))", "op=first", ["Cannot determine output type of 'op'"]),
    ("(integer? (cons 1 null))", "op=cons", "#f"),
    ("(integer? (and #f #t))", "op=and", "#f"),
    ("(integer? (+ 1 2))", "op=+", "#t"),
    ("(integer? (+ k 1))", "op=+", "#t"),
    ("(integer? (+ k (- 2 1)))", "op=+", "#t"), 
    ("(integer? (F k))", "op=F", "#t"),
    ("(integer? (F p))", "op=F", ["Cannot match argument out typeList ['BOOL'] with expected typeList ['INT']"]),
    ("(integer? (H k))", "op=H", ["No definition found for label 'H'"]),
    ("(integer? (G L))", "op=G", "#f")
]
totalFails += test_axiom('integer?', integerQ_prop_tests, axiomProof, builtInProp=True)

listQ_prop_tests = [
    ("(list? null)", ["Cannot rewrite with 'list?' rule when argument is not a function call"]),
    ("(list? (if #t 1 2))", "op=if", ["Cannot determine output type of 'op'"]), 
    ("(list? (cons 1 null))", "op=cons", "#t"),
    ("(list? (and #f #t))", "op=and", "#f"),
    ("(list? (+ 1 2))", "op=+", "#f"),
    ("(list? (+ k 1))", "op=+", "#f"),
    ("(list? (+ k (- 2 1)))", "op=+", "#f"), 
    ("(list? (F k))", "op=F", "#f"),
    ("(list? (G k))", "op=G", ["Cannot match argument out typeList ['INT'] with expected typeList ['LIST']"]),
    ("(list? (G L))", "op=G", "#t")
]
totalFails += test_axiom('list?', listQ_prop_tests, axiomProof, builtInProp=True)

print("\nUDF testing:\n")
udfProof = ERProof()
udfProof.addUDF("(fc x y)", "(INT,INT)>INT", "(* x y)")
udfProof.addUDF("(g x)", "INT>BOOL", "(< x 5)")
udfProof.addUDF("(h x y)", "(LIST,LIST)>LIST", "(cons (first x) (cons (first y) null))")
udfProof.addUDF("(i x)", "LIST>BOOL", "(zero? (first x))")
udfProof.addUDF("a", "INT", "5")
udfProof.addUDF("q", "BOOL", "#f")
# udfProof.addUDF("(h)", "()>INT", "5") TODO: need to implement 0 argument UDFs
# udfProof.addUDF("i", "INT", "3") TODO need to implement 0 argument UDFs
# 2 arguments
totalFails += do_single_test_case("fc", "(fc 3 4)", ["Rule must start with 'eval', 'apply', or 'rewrite'"], udfProof)
totalFails += do_single_test_case('eval fc',  "(fc 3 4)", ['Cannot evaluate definition'], udfProof)
totalFails += do_single_test_case("apply fc", "(fc 3 4)", ['Not enough arguments given for fc. fc requires 2 '
                                                            'arguments, while you gave 0'],
                                  udfProof)
totalFails += do_single_test_case("apply fc x=3, y=4, z=5", "(fc 3 4)", ['Too many arguments given for fc. fc '
                                                                          'requires 2 arguments, while you gave 3'],
                                  udfProof)
totalFails += do_single_test_case("apply fc x=3 y=4", "(fc 3 4)", ['Too many assignments for a given argument \'x=3 '
                                                                   'y=4\'. Did you forget a comma?'], udfProof)
totalFails += do_single_test_case("apply fc z=3, y=4", "(fc 3 4)",
                                  ["Argument 'z' is in position 1 but expected 'x' for fc"], udfProof)
totalFails += do_single_test_case("apply fc x=3, z=4", "(fc 3 4)",
                                  ["Argument 'z' is in position 2 but expected 'y' for fc"],
                                  udfProof)
totalFails += do_single_test_case("apply fc y=4, x=3", "(fc 3 4)", ["Argument 'y' is in position 1 but expected 'x' "
                                                                     "for fc", "Argument 'x' is in position 2 but "
                                                                              "expected 'y' for fc"], udfProof)
totalFails += do_single_test_case("apply fc x=#t, y=4", "(fc 3 4)", ["Type mismatch in argument 'x=#t': expected "
                                                                      "INT, got BOOL"], udfProof)
totalFails += do_single_test_case("apply fc x=3, y='(1 2 3)", "(fc 3 4)", ["Type mismatch in argument 'y='(1 2 3)': "
                                                                            "expected "
                                                                            "INT, got LIST"], udfProof)
totalFails += do_single_test_case("apply fc x=4, y=5", "(fc 3 4)", ["Value mismatch in argument 'x': expected 3, "
                                                                     "got 4", "Value mismatch in argument 'y': "
                                                                              "expected 4, got 5"], udfProof)
totalFails += do_single_test_case("apply fc x=3, y=4", "(fc 3 4)", "(* 3 4)", udfProof)

# 1 argument
totalFails += do_single_test_case("g x=3", "(g 3)", ["Rule must start with 'eval', 'apply', or 'rewrite'"],
                                  udfProof)
totalFails += do_single_test_case('eval g x=3', "(g 3)", ['Cannot evaluate definition'], udfProof)
totalFails += do_single_test_case("apply g", "(g 3)", ['Not enough arguments given for g. g requires 1 argument, '
                                                          'while you gave 0'], udfProof)
totalFails += do_single_test_case("apply g x=3, y=4", "(g 3)", ['Too many arguments given for g. g requires 1 '
                                                                   'argument, while you gave 2'], udfProof)
totalFails += do_single_test_case("apply g y=3", "(g 3)", ["Argument 'y' is in position 1 but expected 'x' for g"],
                                  udfProof)
totalFails += do_single_test_case("apply g x=#t", "(g 3)", ["Type mismatch in argument 'x=#t': expected INT, "
                                                               "got BOOL"], udfProof)
totalFails += do_single_test_case("apply g x=3", "(g 4)", ["Value mismatch in argument 'x': expected 4, got 3"],
                                  udfProof)
totalFails += do_single_test_case("apply g x=3", "(g 3)", "(< 3 5)", udfProof)

# 2 list argument
totalFails += do_single_test_case("apply h", "(h '(1 2 3) '(4 5 6))", ['Not enough arguments given for h. h '
                                                                          'requires 2 arguments, while you gave 0'],
                                  udfProof)
totalFails += do_single_test_case("apply h x='(1 2 3), y='(4 5 6), z='(7 8 9)", "(h '(1 2 3) '(4 5 6))", ['Too many '
                                                                                                             'arguments given for h. h requires 2 arguments, while you gave 3'],
                                  udfProof)
totalFails += do_single_test_case("apply h x='(1 2 3) y='(4 5 6)", "(h '(1 2 3) '(4 5 6))",
                                  ["Too many assignments for a given argument 'x='(1 2 3) y='(4 5 6)'. Did you forget a comma?"],
                                  udfProof)
totalFails += do_single_test_case("apply h z='(1 2 3), y='(4 5 6)", "(h '(1 2 3) '(4 5 6))",
                                  ["Argument 'z' is in position 1 but expected 'x' for h"],
                                  udfProof)
totalFails += do_single_test_case("apply h x='(1 2 3), z='(4 5 6)", "(h '(1 2 3) '(4 5 6))",
                                  ["Argument 'z' is in position 2 but expected 'y' for h"],
                                  udfProof)
totalFails += do_single_test_case("apply h y='(4 5 6), x='(1 2 3)", "(h '(1 2 3) '(4 5 6))",
                                  ["Argument 'y' is in position 1 but expected 'x' for h",
                                   "Argument 'x' is in position 2 but expected 'y' for h"],
                                  udfProof)
totalFails += do_single_test_case("apply h x='(1 2 3), y=#t", "(h '(1 2 3) '(4 5 6))",
                                  ["Type mismatch in argument 'y=#t': expected LIST, got BOOL"],
                                  udfProof)
totalFails += do_single_test_case("apply h x='(1 2 3), y='(4 5 6)", "(h '(3 2 1) '(6 5 4))",
                                  ["Value mismatch in argument 'x': expected '(3 2 1), got '(1 2 3)",
                                   "Value mismatch in argument 'y': expected '(6 5 4), got '(4 5 6)"],
                                  udfProof)
totalFails += do_single_test_case("apply h x='(1 2 3), y='(4 5 6)", "(h '(1 2 3) '(4 5 6))",
                                  "(cons (first '(1 2 3)) (cons (first '(4 5 6)) null))", udfProof)

# 1 list argument
totalFails += do_single_test_case("apply i", "(i '(0 1 2))", ['Not enough arguments given for i. i requires 1 '
                                                                 'argument, while you gave 0'], udfProof)
totalFails += do_single_test_case("apply i x='(0 1 2), y='(3 4 5)", "(i '(0 1 2))", ['Too many arguments given for '
                                                                                        'i. i requires 1 argument, while you gave 2'],
                                  udfProof)
totalFails += do_single_test_case("apply i y='(0 1 2)", "(i '(0 1 2))",
                                  ["Argument 'y' is in position 1 but expected 'x' for i"], udfProof)
totalFails += do_single_test_case("apply i x=#t", "(i '(0 1 2))", ["Type mismatch in argument 'x=#t': expected "
                                                                      "LIST, got BOOL"], udfProof)
totalFails += do_single_test_case("apply i x='(0 1 2)", "(i '(3 4 5))",
                                  ["Value mismatch in argument 'x': expected '(3 4 5), got '(0 1 2)"], udfProof)
totalFails += do_single_test_case("apply i x='(0 1 2)", "(i '(0 1 2))", "(zero? (first '(0 1 2)))", udfProof)

# check that a non-function definition is caught as insufficiently resolved
totalFails += do_single_test_case("eval +", "(+ a 1)", ["Insufficiently resolved arguments"], udfProof)
totalFails += do_single_test_case("eval if", "(if q 1 2)", ["Insufficiently resolved condition argument"], udfProof)

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
proof.addUDF("(fd x)", "int>int", "(if (zero? x) 0 (+ x (fd (- x 1))))")
if proof.errLog != []:
    print(proof.errLog)
else:
    print("no errors with UDF")
proof.addProofLine("(fd 3)", "fd")
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

print("\nTesting IndProofs:\n")
# Read induction test inputs from file
import os
test_file = os.path.join(os.path.dirname(__file__), "indTest.txt")
with open(test_file, 'r') as f:
    lines = [line.strip() for line in f.readlines() if line.strip()]

# Print the raw file content with headers
print("Induction test parameters from indTest.txt:")
for line in lines:
    print(f"  {line}")
print()

# Strip everything up to and including the colon
def extract_value(line):
    if ':' in line:
        return line.split(':', 1)[1].strip()
    return line.strip()

# Parse setup section (first 7 lines)
struct = extract_value(lines[0])
ivar = extract_value(lines[1])
aval = extract_value(lines[2])
lvar = extract_value(lines[3])
fname = extract_value(lines[4])
ftype = extract_value(lines[5])
fdef = extract_value(lines[6])

# Initialize induction proof
indProof = IndProof()
indProof.struct = struct
indProof.indVar = Node(ivar)
indProof.anchorVal = Node(aval)
indProof.leapVar = Node(lvar)

s2 = fname.lstrip("(")  # remove leading (
flet = s2.split()[0]    # split on whitespace, take first

indProof.baseCase.addUDF(fname, ftype, fdef)
indProof.leapStep.addUDF(fname, ftype, fdef)

# Parse test cases (starting from line 8 onwards, in groups of 3: expected, highlight node, rule)
inderrs = 0
current_expr = f"({flet} {aval})"  # Start with initial base case expression
pl = ERProofLine(current_expr)
indProof.baseCase.LHS.addProofLine(current_expr, "")

i = 8  # Start after setup section (0-6 is setup, 7 is blank)
while i < len(lines):
    expected_line = lines[i] if i < len(lines) else ""
    node_line = lines[i + 1] if i + 1 < len(lines) else ""
    rule_line = lines[i + 2] if i + 2 < len(lines) else ""
    
    expected = extract_value(expected_line)
    node_id = int(extract_value(node_line)) if extract_value(node_line).lstrip('-').isdigit() else -1
    rule = extract_value(rule_line)
    
    if node_id == -1:  # End of tests
        print(f"\nProof complete! Final expression: {pl.exprTree}")
        break
    
    print(f"\nApplying rule: {rule} to node {node_id}")
    print(f"  Expected: {expected}")
    
    # Apply the rule
    try:
        pl.applyRule(rule, node_id)
        result = str(pl.exprTree)
        
        if result == expected:
            print(f"  PASS: Got expected result")
        else:
            print(f"  FAIL: Expected {expected} but got {result}")
            inderrs += 1
    except Exception as e:
        print(f"  ERROR applying rule: {e}")
        inderrs += 1
    
    i += 3

print(f"\nNumber of IndProof errors: {inderrs}")
      