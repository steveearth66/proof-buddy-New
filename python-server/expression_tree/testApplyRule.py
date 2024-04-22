import recParser, Labeler, typeFile, Decorator

test_strings_ruleIf= [
    ("cons", "(cons (if #t (if #f 3 4) 5) null)"),
    ("cons", "(cons (first '(1 2 3)) (rest '(1 2 3)))"),
    ("first", "(first (cons 3 '(1 2)))"),
    ("rest", "(rest (cons 3 '(1 2)))"),
    ("if", "(if #t 4 5)"), #expected 4
    ("if", "(if #f x y)"), #expected y
    ("if", "(if asd a a)"), #expected a
    ("if", "(if #f b (c d e f g))"), #expected (c d e f g)
    ("if", "(if x (abc) (abc) )"), #expected (abc) 
    ("if", "(if #t (a b)(a))"), #expected (a b)
    ("if", "(if #t (if #f x y) (z))"), #expected (if #f x y)
    ("if", "(if a b c)"), #expected (if a b c) no valid change to make based on rules
    ("if", "(if a (+ x (y (z z))) (+ x (y (z z))))"), #expected (+ x (y (z z)))
    ("if", "(if a (+ x (y (z z))) (+ x (b (z z))))"), #expected no valid change
    ("if", "(fi #t x y)"), #expected invalid
    ("if", "if #t x y"), #expected invalid
    ("if", "()"), #expected invalid
    ("if", "(if )"), #expected invalid
    ("if", "(if #t b c d e)"), #expected invalid
    ("null?", "(null? (cons x (a b c)))"), #expected #f
    ("cons?", "(cons? (cons x a))"), #expected #t
    ('zero?', '(zero? (+ 0 1))'), #expected #f
    ('zero?', '(zero? (+ 0 0))'), #expected no change
    ('zero?', '(zero? (+ a 1))'), #expected no change
    ('consList', "(cons x '(y z a))"), #expected '(x y z a)
    ('consList', "(cons x '(y) (z))"), #expected error
    ('consList', "(cons x '())"), #expected '(x)
    ('consList', "(cons x '(y z a b c d e))"), #expected '(x y z a b c d e)
    ('consList', "(cons '(2) '(3))"), #expected '((2) 3)
    ('consList', "(cons 2 3)"), #expected error 'argument #2 of cons must be a list'
    ('consList', "(cons 2 '(cons (2 '(3))))"), #expected '(2 cons (2 '(3)))
    ('consList', "(cons '() '(y z a))"), #expected '(null y z a)
    ('consList', "(cons 2)"), #expected error 'cons expects 2 arguments, 1 provided'
    ('consList', "(cons null)"), #expected error 'cons expects 2 arguments, 1 provided'
    ('consList', "(cons 2 3 null)"), #expected error 'cons expects 2 arguments, 3 provided'
    ('consList', "(cons null 2)"), #expected error 'cons takes in types [ANY, LIST]'
    ('consList', "(cons null null)"), #expected '(null)
    ('consList', "(cons '() '())"), #expected '(null)
    ('consList', "(cons '() null)"), #expected '(null)
    ('consList', "(cons null '())"), #expected '(null)
    ('consList', "(cons 2 null)"), #expected '(2)
    ('consList', "(cons null '(2))"), #expected '(null)
    ('consList', "(cons '(2 3) '(4 5))"), #expected '(null)
    ('consList', "(cons x '(2))"), #expected '(x 2)
    
    
    
]

print("\napplyRule testing:\n")
for rule, expr in test_strings_ruleIf:
    print("input =", expr, "rule =", rule)
    exprList,errLog = recParser.preProcess(expr,errLog=[])
    exprTree = recParser.buildTree(exprList,)[0] # might not need to pass errLog
    labeledTree = Labeler.labelTree(exprTree)
    decTree, errLog = Decorator.decorateTree(labeledTree,errLog)
    errLog = Decorator.remTemps(decTree, errLog)
    decTree, errLog = Decorator.checkFunctions(decTree,errLog)
    errLog = decTree.applyRule(rule, errLog)
    print("after rule =", decTree)