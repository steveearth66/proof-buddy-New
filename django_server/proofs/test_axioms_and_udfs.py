"""
Test cases for axioms (cons-first-rest, first-cons, rest-cons, -+, null?-cons, zero?+, 
and, or, implies, integer?, list?) and UDF (user-defined functions)
"""

from expression_tree.ERProofEngine import ERProof
from .test_helpers import test_axiom, do_single_test_case, _RED, _RESET

totalFails = 0

print('[Summary] Undefined Labels')
totalFails += do_single_test_case('rewrite cons-first-rest with L=L', '(cons (first L) (rest L))',
                                  ["No definition found for label 'L'"])

print('[Summary] Axiom Parameter Mapping')
totalFails += do_single_test_case("rewrite cons-first-rest with x=(first '(1)), L=(rest'(1))",
                                  "(cons (first '(1)) (rest '(1)))", 
                                  ['Unexpected assignment "x=(first \'(1))" was provided'])
totalFails += do_single_test_case("rewrite cons-first-rest with L='(1), x='(1)",
                                  "(cons (first '(1)) (rest '(1)))", 
                                  ['Unexpected assignment "x=\'(1)" was provided'])
totalFails += do_single_test_case("rewrite cons-first-rest with L='(1), L='(1)",
                                  "(cons (first '(1)) (rest '(1)))",
                                  ['Unexpected assignment "L=\'(1)" was provided'])

totalFails += do_single_test_case("rewrite first-cons with x=(+ 1 2, L=null",
                                  "(first (cons (+ 1 2) null))", 
                                  ['Failed to build AST from assignment "(+ 1 2"'])

axiomProof = ERProof()
axiomProof.addGeneric('a', 'int', {'assumption': 'None'})
axiomProof.addGeneric('b', 'int', {'assumption': 'Positive'})
axiomProof.addGeneric('M', 'list')
axiomProof.addGeneric('k', 'int')
axiomProof.addGeneric('p', 'bool')
axiomProof.addGeneric('L', 'list')
axiomProof.addGeneric('x', 'any')

print("[Summary] Axiom Tests")

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
    ("(zero? (+ 0 1))", 'a=1, k=0', '#f'),  # used to fail before making zero?+ flexible with parameter ordering
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

print("[Summary] UDF Rule Tests")
udfProof = ERProof()
udfProof.addUDF("(fc x y)", "(INT,INT)>INT", "(* x y)")
udfProof.addUDF("(g x)", "INT>BOOL", "(< x 5)")
udfProof.addUDF("(h x y)", "(LIST,LIST)>LIST", "(cons (first x) (cons (first y) null))")
udfProof.addUDF("(i x)", "LIST>BOOL", "(zero? (first x))")
udfProof.addUDF("a", "INT", "5")
udfProof.addUDF("q", "BOOL", "#f")

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

print("\nAxiom and UDF tests completed!\n" if totalFails == 0 else f"{_RED}Axiom and UDF: {totalFails} failures{_RESET}\n")
