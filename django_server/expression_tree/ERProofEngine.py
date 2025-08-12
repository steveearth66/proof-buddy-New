from .ERCommon import *
from .ERRuleset import *
from .ERGenerics import GenericInt, GenericBool, GenericList, GenericAny
import expression_tree.Parser as Parser
import expression_tree.Labeler as Labeler
import expression_tree.Decorator as Decorator
import re

reservedLabels = ["cons", "if", "first", "rest", "null?", "cons?", "zero?", "consList", "expt", "quotient",
                  "remainder", "and", "or", "not", "implies", "nand", "iff", "nor", "xor", ">", "<", "+", "-", "*",
                  "null", "=", "-+", "math", "cons-first-rest", "first-cons", "rest-cons", "null?-cons"]

class ERProof:
    def __init__(self, debug=False):
        self.ruleSet = {
            'if': If(),
            'cons': ConsList(),
            'rest': RestList(),
            'first': FirstList(),
            'cons-first-rest': ConsProp(),
            'first-cons': FirstProp(),
            'rest-cons': RestProp(),
            'null?-cons': NullQCons(),
            'null?': NullQ(),
            'cons?': ConsQ(),
            'zero?': ZeroQ(),
            'integer?': IntegerQ(),
            'list?': ListQ(),
            'zero?+': ZeroQPlus(),
            '+': Plus(),
            '-': Minus(),
            '*': Times(),
            'quotient': Quotient(),
            'remainder': Remainder(),
            'expt': Expt(),
            '=': Equals(),
            '<': LessThan(),
            '<=': LessOrEqual(),
            '>': GreaterThan(),
            '>=': GreaterOrEqual(),
            'and': (And(), AndProp()),
            'or': (Or(), OrProp()),
            'not': Not(),
            'xor': Xor(),
            'implies': (Implies(), ImpliesProp()),
            '-+': MinusPlus(),
            'math': advMath(),
            #'doubleFront': DoubleFront(),  # this is fake for demo. remove when UDF working
        }
        self.generics = {}
        self.proofLines = []
        self.errLog = []
        self.debug = debug

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
                    proofLine.applySubstitution(self.ruleSet, ruleStr, highlightPos, subLine)
                else:
                    proofLine.applyRule(self.ruleSet, ruleStr, highlightPos, self.generics)
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
        # if not (udfLabel not in self.ruleSet.keys() and udfLabel not in reservedLabels):
        if udfLabel in self.ruleSet.keys() or udfLabel in reservedLabels or udfLabel in self.generics.keys() or not udfLabel.isalpha():
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

    def removeUDF(self, label):
        if len(label) != 1:
            label = label.split()[0][1:]
        if label in self.ruleSet.keys():
            del self.ruleSet[label]
        else:
            self.errLog.append(f"Could not find UDF with label '{label}'")

    def addGeneric(self, label: str, type: str, restrictions: dict | None = None):
        if label in reservedLabels or label in self.ruleSet.keys() or label in self.generics.keys() or not label.isalpha():
            self.errLog.append(f"Could not use generic with label '{label}': label is already being used")
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

class ERProofLine:
    def __init__(self, goal, debug=False, ruleDict=None, udfType=None,isUdf=False, generics=None): #added optional pointer to parent proof's ruleset
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
            labeledTree = Labeler.labelTree(tree, ruleDict, generics)
            labeledTree, _ = updatePositions(labeledTree)

        if self.errLog == []:
            decTree, self.errLog = Decorator.decorateTree(labeledTree, self.errLog, ruleDict=ruleDict, generics=generics)
        #if self.errLog == []: #added userType in case of UDF
        #    decTree, self.errLog = Decorator.checkFunctions(decTree, self.errLog, theRuleDict=ruleDict, userType=udfType)
        if self.errLog == []:
            self.errLog = Decorator.remTemps(decTree, self.errLog, theRuleDict=ruleDict)
        if self.errLog == []: #added userType in case of UDF
            decTree, self.errLog = Decorator.checkFunctions(decTree, self.errLog, theRuleDict=ruleDict, userType=udfType)
        if self.errLog == []:
            self.exprTree = decTree
        if self.errLog == []: #makes the positions dict for arrow key navigation
            self.positions = Decorator.makePosDict(self.exprTree, self.positions)
        #checks to make sure that there are no nested quotes

    def parse_and_typecheck_args(self, ruleName: str, rawParams: list[str], expectedNames: list[str], expectedTypes:
    list[RacType], targetNode: Node) -> tuple[list, bool]:
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
                               f"arguments, while you gave {len(rawParams)}")
            return [], True
        elif got > need:
            self.errLog.append(f"Too many arguments given for {ruleName}. {ruleName} requires {len(expectedNames)} "
                               f"arguments, while you gave {len(rawParams)}")
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
            labeled = Labeler.labelTree(tree, ruleDict=self.ruleSet)
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

    def find_undefined_labels(self, node: Node, ruleSet: dict[str, Rule] = None, generics: dict[str, ERGeneric] =
    None) -> \
            list[str]:
        """
        Recursively find undefined labels in the expression tree.
        Args:
            node: The current node in the expression tree.
            ruleSet: A dictionary of defined rules.
            generics: A dictionary of defined generics.
        Returns:
            A list of undefined labels found in the node's children.
        """
        if ruleSet is None:
            ruleSetet = {}
        if generics is None:
            generics = {}
        undefined_labels = []
        for child in node.children:
            if child.data[0] == "'" or child.data[0] == "(":
                nested_children = self.find_undefined_labels(child, ruleSet, generics)
                if nested_children and nested_children not in undefined_labels:
                    # Avoid adding duplicates
                    undefined_labels.append(nested_children)
            elif (child.data not in ruleSet.keys() and child.data not in reservedLabels and child.data not in
                  generics.keys() and child.data.isalpha()):  # TODO: change to checking if type PARAM when
                # we fix that
                undefined_labels.append(child.data)
        return undefined_labels

    def applyRule(self, ruleSet: dict[str, Rule], rule: str, startPos: int, generics=None, subNode: Node = None):
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

        if ruleCategory not in ["eval", "apply", "rewrite"]:
            self.errLog.append("Rule must start with 'eval', 'apply', or 'rewrite'")
            return

        if rule == "":
            msg = "Rule must include the "
            if ruleCategory == "eval":
                msg += "function to be evaluated"
            elif ruleCategory == "apply":
                msg += "definition/lemma to be applied"
            else:
                msg += "property to be rewritten"
            self.errLog.append(msg)
            return

        if rule not in ruleSet.keys() - {'consProp', 'firstProp', 'restProp'}:  # 'apply consProp' is not valid
            self.errLog.append(f'Could not find rule associated with {rule}')
            return

        entry = ruleSet[rule]

        selected: Rule | None = None
        match ruleCategory:
            case 'eval':
                if isinstance(entry, tuple):
                    selected = entry[0]  # select eval rule from tuple
                elif getattr(entry, 'isProperty', False):
                    self.errLog.append("Cannot evaluate a property")
                elif isinstance(entry, UDF):
                    self.errLog.append("Cannot evaluate a user-defined function")
                elif rule == 'math':
                    self.errLog.append("Could not find built-in Racket procedure associated with 'math'")
                else:
                    selected = entry
            case 'rewrite':
                if isinstance(entry, tuple):
                    selected = entry[1]  # select rewrite rule from tuple
                elif getattr(entry, 'isProperty', False):
                    selected = entry
                else:
                    self.errLog.append(f"Cannot rewrite {rule} as it is not a property")
            case 'apply':
                if isinstance(entry, UDF):  # TODO: might need to add support for other types in future
                    selected = entry
                elif getattr(entry, 'isProperty', False):
                    self.errLog.append("Cannot apply a property")
                else:
                    self.errLog.append(f"Could not find definition/lemma associated with {rule}")
            case _:
                self.errLog.append("Rule must start with 'eval', 'apply', or 'rewrite'")

        if self.errLog:
            return

        if (ruleCategory == "rewrite") or isinstance(selected, UDF):
            values, hadErr = self.parse_and_typecheck_args(
                rule,
                ruleParams,
                selected.params,
                selected.racType.getDomain(),
                targetNode
            )
            for label in self.find_undefined_labels(targetNode, ruleSet, generics):
                self.errLog.append(f"No definition found for label '{label}'")
            if hadErr or self.errLog:
                return

        if ruleCategory == "eval" and rule == 'math':
            ok, err = selected.isApplicable(targetNode, subNode)
        else:
            ok, err = selected.isApplicable(targetNode)

        if not ok:
            self.errLog.append(err)
            return

        if ruleCategory == "eval" and isinstance(selected, UDF):
            # shouldn't get here but just in case
            self.errLog.append("Cannot evaluate a user-defined function")
            return

        newNode = (
            selected.insertSubstitution(targetNode, subNode)
            if ruleCategory == "eval" and rule == 'math'
            else selected.insertSubstitution(targetNode)
        )
        targetNode.replaceWith(newNode)
        updatePositions(self.exprTree)

    def applySubstitution(self, ruleSet: dict[str, Rule], rule: str, startPos: int, subLine: 'ERProofLine'):
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
