from ERCommon import *
from ERRuleset import *
import Parser, Labeler, Decorator

reservedLabels = ["cons", "if", "first", "rest", "null?", "cons?", "zero?", "consList", "expt", "quotient", "remainder", "and", "or", "not", "implies", "nand", "iff", "nor", "xor", ">", "<", "+", "-", "*"]

class ERProof:
    def __init__(self, debug=False):
        self.ruleSet = {
            'if': If(),
            'cons': Cons(),
            'first': First(),
            'rest': Rest(),
            'null?': NullQ(),
            'cons?': ConsQ(),
            'zero?': ZeroQ(),
            'consList': ConsList(),
            'math': Math(),
            'logic': Logic(),
            'restList': RestList(),
            'firstList': FirstList(),
        }
        self.proofLines = []
        self.errLog = []
        self.debug = debug

    def addProofLine(self, lineStr, ruleStr=None, highlightPos=0):
        proofLine = ERProofLine(lineStr, self.debug)
        if proofLine.errLog == []:
            if ruleStr != None:
                proofLine.applyRule(self.ruleSet, ruleStr, highlightPos)
            if proofLine.errLog != []:
                self.errLog.extend(proofLine.errLog)
        else:
            self.errLog.extend(proofLine.errLog)
        
        if self.errLog == []:
            self.proofLines.append(proofLine)
    
    def getPrevRacket(self):
        return str(self.proofLines[-1].exprTree)
    
    def addUDF(self, label, typeStr, body):
        labelList = Parser.preProcess(label)[0]
        paramsList = labelList[2:-1]
        udfLabel = labelList[1]
        racTypeObj = str2Type(typeStr)
        bodyNode = ERProofLine(body)
        if bodyNode.errLog != []:
            self.errLog.extend(bodyNode.errLog)
        if not (udfLabel not in self.ruleSet.keys() and udfLabel not in reservedLabels):
            self.errLog.append(f"'{udfLabel}' is an invalid label for your Definition")
        if len(paramsList) != len(racTypeObj.getDomain()):
            self.errLog.append(f"Cannot map {len(paramsList)} parameters to {len(racTypeObj.getDomain())} types")
        if self.errLog == []:
            param2TypeDict = {}
            for j in range(len(paramsList)):
                param2TypeDict[paramsList[j]] = racTypeObj.getDomain()[j]
            filledBodyNode = fillBody(bodyNode.exprTree, udfLabel, racTypeObj, param2TypeDict)
            self.ruleSet[udfLabel] = UDF(udfLabel, filledBodyNode, racTypeObj, paramsList)

class ERProofLine:
    def __init__(self, goal, debug=False):
        self.exprTree = None
        self.errLog = []
        self.debug = debug
        
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

    def applyRule(self, ruleSet: dict[str, Rule], rule: str, startPos: int):
        targetNode = findNode(self.exprTree, startPos, self.errLog)[0]
        if targetNode == None:
            self.errLog.append(f'Could not find Token with starting index {startPos}')
        if not (rule in ruleSet.keys()):
            self.errLog.append(f'Could not find rule associated with {rule}')
        elif self.errLog == []:
            selectedRule = ruleSet[rule]
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

def fillBody(bodyNode, udfLabel, racTypeObj, param2TypeDict):
    if bodyNode.data == udfLabel:
        bodyNode.type = racTypeObj
    elif bodyNode.data in param2TypeDict.keys():
        bodyNode.type = param2TypeDict[bodyNode.data]
    for i,c in enumerate(bodyNode.children):
        bodyNode.children[i] = fillBody(c, udfLabel, racTypeObj, param2TypeDict)
    return bodyNode
