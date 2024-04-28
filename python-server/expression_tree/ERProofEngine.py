from ERCommon import *
from ERRuleset import *
import Parser, Labeler, Decorator
class ERProof:
    def __init__(self, goal, debug=False):
        self.exprTree = None
        self.errLog = []
        self.debug = debug
        self.ruleset = {
            'if': If(),
            'cons': Cons(),
            'first': First(),
            'rest': Rest(),
            'null?': NullQ(),
            'cons?': ConsQ(),
            'zero?': ZeroQ(),
            'consList': ConsList(),
            'math': Math(),
            'logic': Logic()
        }
        tokenList, self.errLog = Parser.preProcess(goal,errLog=self.errLog,debug=self.debug)
        if self.errLog==[]:
            tree = Parser.buildTree(tokenList,debug=self.debug)[0] # might not need to pass errLog
            labeledTree = Labeler.labelTree(tree)
            labeledTree, _ = updatePositions(labeledTree)
        #if self.errLog == []:
        #    self.errLog = Decorator.remTemps(labeledTree, self.errLog)
        if self.errLog==[]:
            decTree, self.errLog = Decorator.decorateTree(labeledTree,self.errLog)
        if self.errLog==[]:
            decTree, self.errLog = Decorator.checkFunctions(decTree,self.errLog)
        if self.errLog==[]:
            self.exprTree = decTree

    def applyRule(self, rule: str, startPos: int):
        targetNode = findNode(self.exprTree, startPos, self.errLog)[0]
        if targetNode == None:
            self.errLog.append(f'Could not find Token with starting index {startPos}')
        if not (rule in self.ruleset.keys()):
            self.errLog.append(f'Could not find rule associated with {rule}')
        elif self.errLog == []:
            selectedRule = self.ruleset[rule]
            isApplicable, error = selectedRule.isApplicable(targetNode)
            if isApplicable:
                newNode = selectedRule.insertSubstitution(targetNode) # copy information to targetNode
                targetNode.replaceWith(newNode)
                # print(str(self.exprTree)) # should print updated tree
                updatePositions(self.exprTree)
            else:
                self.errLog.append(error)
            

def updatePositions(inputTree:Node, count:int=0) -> tuple[Node, int]:
    inputTree.startPosition = count
    count += len(inputTree.data)

    if len(inputTree.children) > 0:
        for childIndex, child in enumerate(inputTree.children):
            newChild, newCount = updatePositions(child, count)
            inputTree.children[childIndex] = newChild
            count = newCount + 1
    return inputTree, count