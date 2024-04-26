from ERCommon import *
import Parser, Labeler, Decorator
class ERProof:
    def __init__(self, goal, debug=False):
        self.exprTree = None
        self.errLog = []
        self.debug = debug
        
        tokenList, self.errLog = Parser.preProcess(goal,errLog=self.errLog,debug=self.debug)
        if self.errLog==[]:
            tree = Parser.buildTree(tokenList,debug=self.debug)[0] # might not need to pass errLog
            labeledTree = Labeler.labelTree(tree)
            labeledTree, _ = Labeler.fillPositions(labeledTree)
        if self.errLog==[]:
            decTree, self.errLog = Decorator.decorateTree(labeledTree,self.errLog)
        if self.errLog==[]:
            decTree, self.errLog = Decorator.checkFunctions(decTree,self.errLog)
        if self.errLog==[]:
            self.exprTree = decTree

    def applyRule(self, rule: str, startPos: int):
        targetNode = self.exprTree.findNode(startPos)
        if targetNode is not None:
            isApplicable, error = rule.isApplicable(targetNode)
            if isApplicable:
                newNode = rule.insertSubstitution(targetNode) # copy information to targetNode
                targetNode.replaceWith(newNode)
                # print(str(self.exprTree)) # should print updated tree
                updatePositions(self.exprTree)
            else:
                self.errLog.append(error)
        else:
            self.errLog.append(f'Could not find Token with starting index {startPos}')

def updatePositions(inputTree:Node, count:int=0) -> tuple[Node, int]:
    inputTree.startPosition = count
    count += len(inputTree.data)

    if len(inputTree.children) > 0:
        for childIndex, child in enumerate(inputTree.children):
            newChild, newCount = updatePositions(child, count)
            inputTree.children[childIndex] = newChild
            count = newCount + 1
    return inputTree, count