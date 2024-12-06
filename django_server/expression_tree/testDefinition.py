import expression_tree.recParser as recParser
import expression_tree.Labeler as Labeler
import expression_tree.Decorator as Decorator
import expression_tree.expressionDefinition as expressionDefinition
import expression_tree.typeFile as typeFile

test_strgs = [
    "(fish 10 20)",  # expected + 10 20
    "(s 10 '(1 2 3))",  # expected (cons 10 (1 2 3))
    "(F 5 1)",  # Q1 lab 8 expected (if (= 1 0) 5 (+ 1 (F 5 (- 1 1))))
    "(H 3 2)",  # Q2 lab 8 expected (if (< 3 2) 0 (+ 1 (H (- 3 2) 2)"
    "(Q 3 2)",  # Q3 lab 8 expected (if (= 2 1) 3 (+ 3 (Q 3 (- 2 1)))"
    "(biggerThanThree 4)",  # expected (if (> 4 3) #t #f)
    "(doubleFront 2 '(1 2 3 4))",  # monday demo
]

expressionDefinition.addExpression(
    "fish", "INT,INT,INT", ['x', 'y'], "(+ x y)")
expressionDefinition.addExpression(
    "s",  "INT,LIST,LIST", ['z', 'w'], "(cons z w)")
expressionDefinition.addExpression(
    "F", "INT,INT,INT", ['a', 'b'], "(if (= b 0) a (+ 1 (F a (- b 1))))")
expressionDefinition.addExpression(
    "H", "INT,INT,INT", ['a', 'b'], "(if (< a b) 0 (+ 1 (H (- a b) b)))")
expressionDefinition.addExpression(
    "Q", "INT,INT,INT", ['a', 'b'], "(if (= b 1) a (+ a (Q a (- b 1))))")
expressionDefinition.addExpression("biggerThanThree", "INT,BOOL", [
                                   'a'], "(if (> a 3) #t #f)")
expressionDefinition.addExpression("doubleFront", "INT,LIST,LIST", [
                                   'n', 'L'], "(if (or (zero? n) (null? L)) L (cons (* 2 (first L)) (doubleFront (- n 1) (rest L)))))")

for expr in test_strgs:
    print("input =", expr)
    exprList, errLog = recParser.preProcess(expr, errLog=[])
    # might not need to pass errLog
    exprTree = recParser.buildTree(exprList,)[0]
    labeledTree = Labeler.labelTree(exprTree)
    decTree, errLog = Decorator.decorateTree(labeledTree, errLog)
    errLog = Decorator.remTemps(decTree, errLog)
    decTree, errLog = Decorator.checkFunctions(decTree, errLog)
    # print(errLog)
    # print(expressionDefinition.expression_dict)
    expressionDefinition.checkExpression(
        decTree, decTree.children[0].data, errLog)
    print("after rule =", decTree)
