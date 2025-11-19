from .ERCommon import *
from .ERGenerics import *
from .ERRuleset import Rule, RuleType, UDF, getDefaultRuleSet
import expression_tree.Parser as Parser
import expression_tree.Labeler as Labeler
import expression_tree.Decorator as Decorator
import re
import copy

reservedLabels = ["cons", "if", "first", "rest", "null?", "cons?", "zero?", "integer?", "list?", "consList", "expt", 
                  "quotient", "remainder", "and", "or", "not", "implies", "nand", "iff", "nor", "xor", ">", "<", "+", 
                  "-", "*", "null", "=", "-+", "math", "cons-first-rest", "first-cons", "rest-cons", "null?-cons"]

class ProofComponent:
    '''Defines shared functionality between classes in ERProofEngine, namely concerning ruleSet, generics, and errLog'''
    def __init__(self, ruleSet=None, generics=None, debug=False):
        self.ruleSet = getDefaultRuleSet() if ruleSet is None else ruleSet
        self.generics = dict() if generics is None else generics
        self.errLog = []
        self.debug = debug

    @property
    def racketLabels(self):
        return self.ruleSet['eval'].keys() | self.defDict.keys()

    @property
    def defDict(self):
        return {label: rule for (label, rule) in self.ruleSet['apply'].items() 
                if rule.ruleType == RuleType.DEFINITION}
    
    def _validateNewLabel(self, label: str) -> bool:
        """Checks if label is not already in use"""
        return False not in map(lambda iterable: label not in iterable, (
            reservedLabels, *self.ruleSet.values(), self.generics
        )) and label.isalpha()
    
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
            generics=self.generics
        )
        if bodyNode.errLog != []:
            self.errLog.extend(bodyNode.errLog)
        if not self._validateNewLabel(udfLabel):
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
            self.ruleSet['apply'][udfLabel] = UDF(udfLabel, filledBodyNode, racTypeObj, paramsList)
           # print(f"Added UDF '{udfLabel}' with type '{str(racTypeObj)}' and body '{str(filledBodyNode)}'")

    def removeUDF(self, label):
        if len(label) != 1:
            label = label.split()[0][1:]
        if label in self.ruleSet['apply']:
            del self.ruleSet['apply'][label]
        else:
            self.errLog.append(f"Could not find UDF with label '{label}'")

    def addGeneric(self, label: str, type: str, restrictions: dict | None = None):
        if not self._validateNewLabel(label):
            self.errLog.append(f"Can not use generic with label '{label}': label is already being used")
        type = type.lower()
        if type == 'int' and (restrictions is None or restrictions.get("assumption") is None):
            self.generics[label] = GenericInt()
        elif type == 'int':
            self.generics[label] = GenericInt(restrictions['assumption'])
        elif type == 'list' and (restrictions is None or restrictions.get("neverNull") is None):
            self.generics[label] = GenericList()
        elif type == 'list':
            self.generics[label] = GenericList(restrictions['neverNull'])
        elif type == 'bool':
            self.generics[label] = GenericBool()
        elif type == 'any':
            self.generics[label] = GenericAny()
        else:
            raise ValueError('Invalid type string')

class TwoSidedProof(ProofComponent):
    def __init__(self, debug=False):
        super().__init__()
        self.LHS = ERProof(self.ruleSet, self.generics, debug)
        self.RHS = ERProof(self.ruleSet, self.generics, debug)
        self.currentSide: ERProof = self.LHS
        self.isValid = True
        # TODO: is there a way to not have a separate definitions list, 
        # since they are also stored in the ruleSet?
        self.definitions = []

    def toggleSide(self):
        self.currentSide = self.RHS if self.currentSide == self.LHS else self.LHS
    
    def setCurrentSide(self, side: str):
        if side.upper() not in ('LHS', 'RHS'):
            raise ValueError("Invalid side literal: side must be either 'LHS' or 'RHS'")
        self.currentSide = self.LHS if side == 'LHS' else self.RHS
    
    def updateErrorsAndValidate(self):
        self.errLog.extend(self.currentSide.errLog)
        self.isValid = len(self.errLog) == 0
    
    def getErrorsAndClear(self):
        errors = copy.deepcopy(self.errLog)
        self.errLog.clear()
        self.currentSide.errLog.clear()
        return errors
    
class ERProof(ProofComponent):
    def __init__(self, ruleSet=None, generics=None, debug=False):
        super().__init__(ruleSet, generics, debug)
        self.proofLines: list[ERProofLine] = []

    def addProofLine(self, lineStr, ruleStr=None, highlightPos=0, substitution=None):
        # prooflines now contain pointers to their proof's ruleset so they can refer to UDFs
        if substitution != None:
            subLine = ERProofLine(substitution, self.debug, self.ruleSet, generics=self.generics)

        proofLine = ERProofLine(lineStr, self.debug, self.ruleSet, generics=self.generics)

        if proofLine.errLog == None:
            proofLine.errLog = []
        if proofLine.errLog == []:
            if ruleStr != None:
                if substitution!=None:
                    proofLine.applySubstitution(ruleStr, highlightPos, subLine)
                else:
                    proofLine.applyRule(ruleStr, highlightPos)
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
        if len(self.proofLines) == 0: #sometimes the proof is empty for some reason??
            return ""
        return str(self.proofLines[-1].exprTree)

class ERProofLine(ProofComponent):
    def __init__(self, goal, debug=False, ruleDict=None, udfType=None, isUdf=False, generics=None): #added optional pointer to parent proof's ruleset
        super().__init__(ruleSet=ruleDict, generics=generics, debug=debug)
        self.exprTree = None
        self.positions = dict() # a dict of 4-tuples of the next pos when hitting up,down,left,right. keyd by startpos

        tokenList, self.errLog = Parser.preProcess(goal, errLog=self.errLog, debug=self.debug,udf=isUdf)
        if self.errLog == []:
            tree = Parser.buildTree(tokenList, debug=self.debug)[0]  # might not need to pass errLog
            if self.errLog == []:
                if Parser.checkQuotes(tree):
                    self.errLog.append(f"Cannot have nested quotes")
            labeledTree = Labeler.labelTree(tree, self.defDict, self.generics)
            labeledTree, _ = updatePositions(labeledTree)

        if self.errLog == []:
            decTree, self.errLog = Decorator.decorateTree(labeledTree, self.errLog, defDict=self.defDict, generics=self.generics)
        #if self.errLog == []: #added userType in case of UDF
        #    decTree, self.errLog = Decorator.checkFunctions(decTree, self.errLog, theRuleDict=ruleDict, userType=udfType)
        if self.errLog == []:
            self.errLog = Decorator.remTemps(decTree, self.errLog, racketLabels=self.racketLabels)
        if self.errLog == []: #added userType in case of UDF
            decTree, self.errLog = Decorator.checkFunctions(decTree, self.errLog, userType=udfType)
        if self.errLog == []:
            self.exprTree = decTree
        if self.errLog == []: #makes the positions dict for arrow key navigation
            self.positions = Decorator.makePosDict(self.exprTree, self.positions)
        #checks to make sure that there are no nested quotes

    def parse_and_typecheck_args(self, ruleName: str, rawParams: list[str], expectedNames: list[str], expectedTypes:
    list[RacType], targetNode: Node) -> tuple[list, bool]:
        # NOTE: currently, this method handles param assignment checking for definitions,
        # while assignment matching for axioms/rules are handled by methods of the Axiom class
        # in ERRuleset.
        # TODO: Replace with param matching in ERRuleset? 
        """
        Parse ["x=...", "y=..."] into a list of values and check if they match the expected names and types.
        Args:
            ruleName: The name of the rule being applied.
            rawParams: The raw parameters as a list of strings, e.g., ["x=1", "y=2"].
            expectedNames: The expected parameter names for the rule.
            expectedTypes: The expected types for the parameters.
            targetNode: The node in the expression tree where the rule is being applied.
        Returns:
            A tuple containing a list of parsed values and a boolean indicating if the parsing was successful.
        """
        for param in rawParams:
            if '=' not in param:
                self.errLog.append(f"Argument '{param}' does not have an assignment. Did you forget an equals sign?")
                return [], True
            elif param.count('=') > 1:
                self.errLog.append(f"Too many assignments for a given argument '{param}'. Did you forget a comma?")
                return [], True
        got, need = len(rawParams), len(expectedNames)
        if got < need:
            self.errLog.append(f"Not enough arguments given for {ruleName}. {ruleName} requires {len(expectedNames)} "
                               f"argument{'' if len(expectedNames) == 1 else 's'}, while you gave {len(rawParams)}")
            return [], True
        elif got > need:
            self.errLog.append(f"Too many arguments given for {ruleName}. {ruleName} requires {len(expectedNames)} "
                               f"argument{'' if len(expectedNames) == 1 else 's'}, while you gave {len(rawParams)}")
            return [], True
        found_mismatch = False
        for param, expected in zip(rawParams, expectedNames):
            name, _ = param.split('=', 1)
            if name.strip() != expected:
                self.errLog.append(
                    f"Argument '{name.strip()}' is in position {expectedNames.index(expected) + 1} but expected '{expected}' for {ruleName}")
                found_mismatch = True
        if found_mismatch:
            return [], True
        parsed = []
        for param, expected_type in zip(rawParams, expectedTypes):
            _, raw = param.split('=', 1)
            tokens, errors = Parser.preProcess(raw, errLog=self.errLog, debug=self.debug)
            if errors:
                self.errLog.extend(errors)
                return [], True
            tree = Parser.buildTree(tokens, debug=self.debug)[0]
            if tree is None:
                self.errLog.append(f"Failed to build AST from value '{raw}' in argument '{param}'")
                return [], True
            labeled = Labeler.labelTree(tree, defDict=self.defDict)
            typed, _ = Decorator.decorateTree(labeled, self.errLog)
            if typed.type != expected_type.getType():
                self.errLog.append(
                    f"Type mismatch in argument '{param}': expected {expected_type.getType()}, got {typed.type}")
                return [], True
            parsed.append(typed)
        user_vals = [param.split('=', 1)[1].strip() for param in rawParams]
        target_vals = [str(child) for child in targetNode.children[1:]]
        for i, (user_val, target_val) in enumerate(zip(user_vals, target_vals)):
            if user_val != target_val:
                self.errLog.append(
                    f"Value mismatch in argument '{expectedNames[i]}': expected {target_val}, got {user_val}")
        if self.errLog:
            return [], True
        return parsed, False

    def find_undefined_labels(self, node: Node, foundLabels: set[str] = None) -> list[str]:
        """
        Recursively find undefined labels in the expression tree.
        Args:
            node: The current node in the expression tree.
        Returns:
            A list of undefined labels found in the node's children.
        """

        undefined_labels = set()
        for child in node.children:
            if child.data in ("'(", "("):
                undefined_labels |= set(self.find_undefined_labels(child))
            elif self._validateNewLabel(child.data):
                # TODO: change to checking if type PARAM when we fix that
                undefined_labels.add(child.data)
        return list(sorted(undefined_labels))
    
    def _getRuleType(self, ruleLabel: str) -> RuleType:
        for prefix in self.ruleSet:
            if (ruleObj := self.ruleSet[prefix].get(ruleLabel)) is not None:
                return ruleObj.ruleType
        raise ValueError

    def applyRule(self, rule: str, startPos: int, subNode: Node = None):
        targetNode = findNode(self.exprTree, startPos, self.errLog)[0]
        if targetNode == None:
            self.errLog.append(
                f'Could not find Token with starting index {startPos}')
        # checking to see if highlighted portion is within a quote
        if "'(" in targetNode.ancestors():
            self.errLog.append(f"Cannot apply rules within a quoted expression")

        parts = rule.split()
        ruleCategory = parts[0] if parts else ""
        rule = parts[1] if len(parts) > 1 else ""
        if len(parts) > 2 and parts[2] == "with":
            parts.pop(2)  # remove 'with'
        ruleParams = " ".join(parts[2:]).replace("\u21A6", "=")
        ruleParams = ruleParams.replace("'()", "null")  # replace empty list with 'null'
        ruleParams = [m.group(0).strip() for m in re.finditer(r"\w+=.*?(?=,\s*\w+=|$)", ruleParams)]

        if ruleCategory not in ("eval", "apply", "rewrite"):
            self.errLog.append("Rule must start with 'eval', 'apply', or 'rewrite'")
            return
        
        selected = self.ruleSet[ruleCategory].get(rule)
        if selected is None:
            try:
                entryType = str(self._getRuleType(rule))
                match ruleCategory:
                    case 'eval':
                        self.errLog.append(f"Cannot evaluate {entryType}")
                    case 'apply':
                        self.errLog.append(f"Cannot apply {entryType}")
                    case 'rewrite':
                        self.errLog.append(f"Cannot rewrite using {entryType}")
            except ValueError:
                self.errLog.append(f"Could not find rule associated with '{rule}'")

        if self.errLog:
            return
        
        for label in self.find_undefined_labels(targetNode):
            self.errLog.append(f"No definition found for label '{label}'")

        if selected.ruleType == RuleType.DEFINITION:
            values, hadErr = self.parse_and_typecheck_args(
                rule,
                ruleParams,
                selected.params,
                selected.racType.getDomain(),
                targetNode
            )
            if hadErr or self.errLog:
                return

        if selected._ruleType == RuleType.MATH:
            ok, err = selected.isApplicable(targetNode, subNode)
        elif ruleCategory == 'eval':
            ok, err = selected.isApplicable(targetNode)
        else:
            ok, err = selected.isApplicable(targetNode, ruleParams)

        if not ok:
            self.errLog.append(err)
            return

        newNode = (
            selected.insertSubstitution(targetNode, subNode)
            if selected.ruleType == RuleType.MATH
            else selected.insertSubstitution(targetNode)
        )
        targetNode.replaceWith(newNode)
        updatePositions(self.exprTree)

    def applySubstitution(self, rule: str, startPos: int, subLine: 'ERProofLine'):
        targetNode = findNode(self.exprTree, startPos, self.errLog)[0]
        if targetNode == None:
            self.errLog.append(
                f'Could not find Token with starting index {startPos}')
        #if not (rule in ruleSet.keys()):
            #self.errLog.append(f'Could not find rule associated with {rule}')
        # checking to see if highlighted portion is within a quote
        if "'(" in targetNode.ancestors():
            self.errLog.append(f"Cannot apply rules within a quoted expression")
        if self.errLog == []:
            replacementExprTree = copy.deepcopy(subLine.exprTree)
            subLine.applyRule(rule, 0, targetNode)
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