from .ERCommon import *
from .ERRuleset import *
import expression_tree.Parser as Parser
import expression_tree.Labeler as Labeler
import expression_tree.Decorator as Decorator

reservedLabels = ["cons", "if", "first", "rest", "null?", "cons?", "zero?", "consList", "expt", "quotient",
                  "remainder", "and", "or", "not", "implies", "nand", "iff", "nor", "xor", ">", "<", "+", "-", "*"]


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
            'advMath': advMath(),
            #'doubleFront': DoubleFront(),  # this is fake for demo. remove when UDF working
        }
        self.proofLines = []
        self.errLog = []
        self.debug = debug

    def addProofLine(self, lineStr, ruleStr=None, highlightPos=0, substitution=None):
        # prooflines now contain pointers to their proof's ruleset so they can refer to UDFs
        if substitution != None:
            subLine = ERProofLine(substitution, self.debug, self.ruleSet) 

        proofLine = ERProofLine(lineStr, self.debug, self.ruleSet) 

        if proofLine.errLog == None:
            proofLine.errLog = []
        if proofLine.errLog == []:
            if ruleStr != None:
                if substitution!=None:
                    proofLine.applySubstitution(self.ruleSet, ruleStr, highlightPos, subLine)
                else:
                    proofLine.applyRule(self.ruleSet, ruleStr, highlightPos)
            if proofLine.errLog != []:
                self.errLog.extend(proofLine.errLog)
        else:
            self.errLog.extend(proofLine.errLog)

        if self.errLog == []:
            self.proofLines.append(proofLine)

    def deleteProofLine (self):
        # when user delete's proof line on front end, simply pop the last proofline from the list
        # are there any checks that should be performed prior to popping?

        # one check might be... 
        # do not allow the deletion of a "blank" line
        # if you delete the blank line, can get stuck in a situation where 
        # you are "stuck"
        self.proofLines.pop()

    def getPrevRacket(self):
        return str(self.proofLines[-1].exprTree)

    def addUDF(self, label, typeStr, body):
        errLog = Parser.preProcess(label,udf=True)[1] #added udf=True so that preprocessing will bypass empty string check
        if errLog != []:
            self.errLog.extend(errLog)
            return
        ''' removing this since can get this a better way that deals with nested parens
        # index = 0
        # for i in range(len(labelList)):
        #     if labelList[i] != '(':
        #         break
        #     index += 1
        # really need to count to first non (, also think about if there could ever be )) at end or just always single )
        #paramsList = labelList[index+1:-1] #TODO: endpoint might not be -1 if there's nested parens!
        #udfLabel = labelList[index]'''

        noparens = label.replace("(", " ").replace(")", " ").split()
        udfLabel = noparens[0]
        paramsList = noparens[1:]

        racTypeObj = str2Type(typeStr)
        if "ERROR" in str(racTypeObj): #must check type first so we can know if body is good
            self.errLog.append(f"Error in type string: {typeStr}")
            return #prevents bodynode from being created
        if self.errLog != []:
            return
        bodyNode = ERProofLine(
            f"{body if body else label}",
            ruleDict=self.ruleSet,
            udfType=racTypeObj,
            isUdf=True,
        )
        if bodyNode.errLog != []:
            self.errLog.extend(bodyNode.errLog)
        if not (udfLabel not in self.ruleSet.keys() and udfLabel not in reservedLabels):
            self.errLog.append(
                f"'{udfLabel}' is an invalid label for your Definition")
        if racTypeObj.getDomain() != None:
            if len(paramsList) != len(racTypeObj.getDomain()):
                self.errLog.append(f"Cannot map {len(paramsList)} parameters to {len(racTypeObj.getDomain())} types")
        if self.errLog == []:
            param2TypeDict = {}
            for j in range(len(paramsList)):
                param2TypeDict[paramsList[j]] = RacType(racTypeObj.getDomain()[j]) #got rid of getDomain here and switched to value[0]
            filledBodyNode = fillBody(bodyNode.exprTree, udfLabel, racTypeObj, param2TypeDict)
            self.ruleSet[udfLabel] = UDF(udfLabel, filledBodyNode, racTypeObj, paramsList)

class ERProofLine:
    def __init__(self, goal, debug=False, ruleDict=None, udfType=None,isUdf=False): #added optional pointer to parent proof's ruleset
        self.exprTree = None
        self.errLog = []
        self.debug = debug
        self.positions = dict() # a dict of 4-tuples of the next pos when hitting up,down,left,right. keyd by startpos
        if ruleDict != None:
            self.ruleSet = ruleDict
        else:
            self.ruleSet=dict()

        tokenList, self.errLog = Parser.preProcess(goal, errLog=self.errLog, debug=self.debug,udf=isUdf)
        if self.errLog == []:
            tree = Parser.buildTree(tokenList, debug=self.debug)[0]  # might not need to pass errLog
            if self.errLog == []:
                if Parser.checkQuotes(tree):
                    self.errLog.append(f"Cannot have nested quotes")
            labeledTree = Labeler.labelTree(tree, ruleDict)
            labeledTree, _ = updatePositions(labeledTree)

        if self.errLog == []:
            decTree, self.errLog = Decorator.decorateTree(labeledTree, self.errLog)
        if self.errLog == []: #added userType in case of UDF
            decTree, self.errLog = Decorator.checkFunctions(decTree, self.errLog, theRuleDict=ruleDict, userType=udfType)
        if self.errLog == []:
            self.errLog = Decorator.remTemps(labeledTree, self.errLog, theRuleDict=ruleDict)
        if self.errLog == []:
            self.exprTree = decTree
        if self.errLog == []: #makes the positions dict for arrow key navigation
            self.positions = Decorator.makePosDict(self.exprTree, self.positions)
        #checks to make sure that there are no nested quotes
        
                



    def applyRule(self, ruleSet: dict[str, Rule], rule: str, startPos: int, subNode:Node=None):
        targetNode = findNode(self.exprTree, startPos, self.errLog)[0]
        if targetNode == None:
            self.errLog.append(
                f'Could not find Token with starting index {startPos}')
        if not (rule in ruleSet.keys()):
            self.errLog.append(f'Could not find rule associated with {rule}')
        # checking to see if highlighted portion is within a quote
        if "'(" in targetNode.ancestors():
            self.errLog.append(f"Cannot apply rules within a quoted expression")
        if self.errLog == []:       
            selectedRule = ruleSet[rule]
            if rule == 'advMath':
                isApplicable, error = selectedRule.isApplicable(targetNode, subNode)
                if isApplicable:
                    newNode = selectedRule.insertSubstitution(
                        targetNode, subNode)  # copy information to targetNode
                    targetNode.replaceWith(newNode)
                    updatePositions(self.exprTree)
                else:
                    self.errLog.append(error)
            else:
                isApplicable, error = selectedRule.isApplicable(targetNode)
                if isApplicable:
                    newNode = selectedRule.insertSubstitution(
                        targetNode)  # copy information to targetNode
                    targetNode.replaceWith(newNode)
                    updatePositions(self.exprTree)
                else:
                    self.errLog.append(error)

    def applySubstitution(self, ruleSet: dict[str, Rule], rule: str, startPos: int, subLine: 'ERProofLine'):
        targetNode = findNode(self.exprTree, startPos, self.errLog)[0]
        if targetNode == None:
            self.errLog.append(
                f'Could not find Token with starting index {startPos}')
        if not (rule in ruleSet.keys()):
            self.errLog.append(f'Could not find rule associated with {rule}')
        # checking to see if highlighted portion is within a quote
        if "'(" in targetNode.ancestors():
            self.errLog.append(f"Cannot apply rules within a quoted expression")
        if self.errLog == []:
            replacementExprTree = copy.deepcopy(subLine.exprTree)
            subLine.applyRule(ruleSet, rule, 0, targetNode)
            if subLine.errLog != []:
                self.errLog.extend(subLine.errLog)
            elif subLine.exprTree != targetNode:
                self.errLog.append(
                    f"substitution evaluated to {str(subLine.exprTree)} but expected {str(targetNode)}"
                )
        if self.errLog == []:
            targetNode.replaceWith(replacementExprTree)
            updatePositions(self.exprTree)


def updatePositions(inputTree: Node, count: int = 0) -> tuple[Node, int]:
    inputTree.startPosition = count
    count += len(inputTree.data)

    if len(inputTree.children) > 0:
        for childIndex, child in enumerate(inputTree.children):
            newChild, newCount = updatePositions(child, count)
            inputTree.children[childIndex] = newChild
            count = newCount + 1
    return inputTree, count

# fills in the types for the params
def fillBody(bodyNode, udfLabel, racTypeObj, param2TypeDict):
    if bodyNode.data == udfLabel:
        bodyNode.type = racTypeObj
        bodyNode.numArgs = len(param2TypeDict)
    elif bodyNode.data in param2TypeDict.keys():
        bodyNode.type = param2TypeDict[bodyNode.data]
        bodyNode.numArgs = len(param2TypeDict)
    for i, c in enumerate(bodyNode.children):
        bodyNode.children[i] = fillBody(c, udfLabel, racTypeObj, param2TypeDict)
    return bodyNode
