from recParser import *
from Decorator import *
from Labeler import *
import copy

expression_dict = {} #dictionary of expressions, key is the label, value is a tuple of the list of types and the expression

def addExpression(label: str, type_str: str, expression: str) -> None:
    errs, expressionNode = testErrs(expression)
    #print(errs)
    types = type_str.split(",")
    reservedLabels = ["cons", "if", "first", "rest", "null?", "cons?", "zero?", "consList", "expt", "quotient", "remainder", "and", "or", "not", "implies", "nand", "iff", "nor", "xor", ">", "<", "+", "-", "*"]
    if errs == [] and label not in expression_dict.keys() and label not in reservedLabels: #check if expr gets built correctly and if label is not already a function
        expression_dict[label] = (types, expressionNode)
    #print(expression_dict)

#example (f x y) or (g a b c)
#label is the name, 'f'
#type is types of the inputs x and y and the output, 'INT, BOOL, LIST' or 'INT, INT, INT, BOOL'
#expr is what it turns into eg '(cons x (cons y null))', put into dict only as a fully decorated node
#check errors: no existing labels or reserved words
#label can have a ? at the end ONLY if output type is bool
#check parentheses and everything


def checkExpression(node: Node, label: str) -> bool:
    if label in expression_dict.keys():
        types, expression = expression_dict[label]
        #print(node.children, expression.children)
        if len(node.children) == len(expression.children) and (node.children[0].data == label): 
            for i in range(1, len(node.children)):
                if str(node.children[i].type.getType()) != types[i]:
                    #print(node.children[i].type.getType(), types[i])
                    #print(type(node.children[i].type.getType()), type(types[i]))
                    return False #throw error Types do not match
            expCopy = copy.deepcopy(expression)
            print(expCopy.children)
            expCopy.children[1:] = node.children[1:]
            node.replaceNode(expCopy)
            return True
    return False #throw error Label not found in given node

def testErrs(expr):
    exprList,errLog = preProcess(expr,errLog=[])
    if errLog!=[]:
        print(errLog)
        return errLog,None
    decTree, errLog = decorateTree(labelTree(buildTree(exprList,)[0]),errLog)
    if errLog!=[]:
        print(errLog)
        return errLog,None
    errLog = remTemps(decTree, errLog)
    if errLog!=[]:
        print(errLog)
        return errLog,None
    decTree, errLog = checkFunctions(decTree,errLog)
    if errLog!=[]:
        print(errLog)
        return errLog,None
    #errLog = decTree.applyRule("math", errLog)
    #if errLog!=[]:
    #    return errLog,None
    return [],decTree

#def recursiveReplaceNodes(node, )