import recParser, Labeler, typeFile, Decorator, ruleDefinition

test_strgs=[
    "(fish 10 20)", #expected + 10 20
    "(s 10 (1 2 3))", #expected (cons 10 (1 2 3))
    "(F 5 1)", #QUESTION 1 ON CS270 LAB 8 #expected (if (= 5 0) 5 (+ 1 (F 5 (- 1 1))))
]

ruleDefinition.addExpression("fish", "INT,INT,INT", "(+ x y)")
ruleDefinition.addExpression("s", "INT,LIST,LIST", "(cons z w)")
ruleDefinition.addExpression("F", "INT,INT,INT", "(if (= b 0) a (+ 1 (F a (- b 1))))")

for expr in test_strgs:
    print("input =", expr)
    exprList,errLog = recParser.preProcess(expr,errLog=[])
    exprTree = recParser.buildTree(exprList,)[0] # might not need to pass errLog
    labeledTree = Labeler.labelTree(exprTree)
    decTree, errLog = Decorator.decorateTree(labeledTree,errLog)
    errLog = Decorator.remTemps(decTree, errLog)
    decTree,errLog = Decorator.checkFunctions(decTree,errLog)
    print(errLog)
    print(ruleDefinition.expression_dict)
    ruleDefinition.checkExpression(decTree, decTree.children[0].data)
    print("after rule =", decTree)