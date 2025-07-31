from .ERCommon import *
from .ERRuleset import *
from .Generics import Generic, GenericInt, GenericBool, GenericList
import expression_tree.Parser as Parser
import expression_tree.Labeler as Labeler
import expression_tree.Decorator as Decorator
import re

reservedLabels = ["cons", "if", "first", "rest", "null?", "cons?", "zero?", "consList", "expt", "quotient",
                  "remainder", "and", "or", "not", "implies", "nand", "iff", "nor", "xor", ">", "<", "+", "-", "*"]

class ERProof:
    def __init__(self, debug=False):
        self.ruleSet = {
            'if': If(),
            'cons': ConsList(),
            'rest': RestList(),
            'first': FirstList(),
            'consProp': ConsProp(),
            'firstProp': FirstProp(),
            'restProp': RestProp(),
            'null?-cons': NullQCons(),
            'null?': NullQ(),
            'cons?': ConsQ(),
            'zero?': ZeroQ(),
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
            'and': And(),
            'or': Or(),
            'not': Not(),
            'xor': Xor(),
            'implies': Implies(),
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
            self.errLog.append(f"Could not create generic with label '{label}': label is already being used")
        type = type.lower()
        if type == 'int' and restrictions is None:
            self.generics[label] = GenericInt()
        elif type == 'int':
            self.generics[label] = GenericInt(restrictions['assumption'])
        elif type == 'list' and restrictions is None:
            self.generics[label] = GenericList()
        elif type == 'list':
            self.generics[label] = GenericList(restrictions['neverNull'])
        elif type == 'bool':
            self.generics[label] = GenericBool()
        elif type == 'any':
            self.generics[label] = Generic()
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
            decTree, self.errLog = Decorator.decorateTree(labeledTree, self.errLog)
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
        
                



    def applyRule(self, ruleSet: dict[str, Rule], rule: str, startPos: int, subNode:Node=None):
        targetNode = findNode(self.exprTree, startPos, self.errLog)[0]
        if targetNode == None:
            self.errLog.append(
                f'Could not find Token with starting index {startPos}')
        # rule = rule.split(' ')[1:][-1] if rule.split(' ')[1:] != [] else ''
        parts = rule.split()
        ruleCategory = parts[0]
        rule = parts[1] if len(parts) > 1 else ''  # takes rule being eval'd or applied
        ruleParams = ' '.join(parts[2:]) if len(parts) > 2 else ''  # everything after 'f'
        ruleParams = ruleParams.replace("\u21A6", "=")  # replace the arrow with an equals sign
        ruleParams = [m.group(0).strip() for m in re.finditer(r"\w+=.*?(?=,\s*\w+=|$)", ruleParams)]
        '''
        regex explanation:
        \w+         # key (e.g., x, y, z)
        =           # equals sign
        .*?         # non-greedy match for the value
        (?=,\s*\w+=|$)  # lookahead for next ", key=" OR end of string
        '''

        if ruleCategory not in ('eval', 'apply'):
            self.errLog.append("Rule must start with 'eval' or 'apply'")
        elif rule == '':
            self.errLog.append('Rule must include the ' + 
                               ('function to be evaluated' if ruleCategory == 'eval'
                               else 'definition/property/lemma to be applied'))
        elif rule not in ruleSet.keys() - {'consProp', 'firstProp', 'restProp'}: # 'apply consProp' is not valid
            self.errLog.append(f'Could not find rule associated with {rule}')
        elif ruleCategory == 'apply' and rule in ('cons', 'first', 'rest'):  # for cons, first, rest axioms
            rule += 'Prop'
        elif ruleCategory == 'apply' and not (isinstance(ruleSet[rule], UDF) or ruleSet[rule].isProperty):
            self.errLog.append(f"Could not find definition/lemma associated with {rule}")
        elif ruleCategory == 'apply' and isinstance(ruleSet[rule], UDF):
            stop_error = False
            given_args = []
            if len(ruleSet[rule].params) != 0:
                for arg in ruleParams:
                    if '=' not in arg:
                        self.errLog.append(
                            f"Argument '{arg}' does not have an assignment. Did you forget an equals sign?")
                        stop_error = True
                        continue
                    elif arg.count('=') > 1:
                        self.errLog.append(
                            f"Too many assignments for a given argument '{arg}'. Did you forget a comma?")
                        stop_error = True
                        continue
                    var = arg.split('=', 1)[0].strip()
                    given_args.append(var)
                if not stop_error and len(given_args) != len(ruleSet[rule].params):
                    if len(ruleSet[rule].params) > len(given_args):
                        self.errLog.append(
                            f"Not enough arguments given for {rule}. {rule} requires {len(ruleSet[rule].params)} "
                            f"arguments, while you gave {len(given_args)}")
                        stop_error = True
                    else:
                        self.errLog.append(
                            f"Too many arguments given for {rule}. {rule} requires {len(ruleSet[rule].params)} arguments, while you gave {len(given_args)}")
                        stop_error = True
                for i, (arg, expected) in enumerate(zip(given_args, ruleSet[rule].params)):
                    if arg != expected:
                        self.errLog.append(
                            f"Argument '{arg}' is in position {i + 1} but expected '{expected}' for {rule}")
                        stop_error = True
                if not stop_error:
                    expected_types = ruleSet[rule].racType.getDomain()
                    for i, (arg_str, expected_type) in enumerate(zip(ruleParams, expected_types)):
                        arg_name, arg_value_str = arg_str.split('=', 1)
                        arg_tokens, tempErrLog = Parser.preProcess(arg_value_str, errLog=[], debug=self.debug)
                        if tempErrLog:
                            self.errLog.extend([f"In argument '{arg_str}': {err}" for err in tempErrLog])
                            stop_error = True
                            continue
                        ast = Parser.buildTree(arg_tokens, debug=self.debug)[0]
                        if ast is None:
                            self.errLog.append(
                                f"Failed to build AST from value '{arg_value_str}' in argument '{arg_str}'")
                            stop_error = True
                            continue
                        labeled_ast = Labeler.labelTree(ast, ruleDict=ruleSet)
                        typed_ast, _ = Decorator.decorateTree(labeled_ast, [])
                        provided_type = typed_ast.type
                        try:
                            expected_type_unwrapped = expected_type.getType()
                        except Exception as e:
                            self.errLog.append(
                                f"Type mismatch in argument '{arg_str}': expected err: {e}, got {provided_type}")
                            stop_error = True
                            continue

                        if provided_type != expected_type_unwrapped:
                            self.errLog.append(
                                f"Type mismatch in argument '{arg_str}': expected {expected_type_unwrapped}, got {provided_type}"
                            )
                            stop_error = True
                    if not stop_error:
                        arg_values = [arg.split('=', 1)[1].strip() for arg in ruleParams]
                        target_values = [str(child) for child in targetNode.children[1:]]  # skip the first child which
                        # is the UDF label
                        for i, (user_val, target_val) in enumerate(zip(arg_values, target_values)):
                            if user_val != target_val:
                                self.errLog.append(
                                    f"Value mismatch in argument '{ruleSet[rule].params[i]}': expected {target_val}, got {user_val}")

        elif ruleCategory == 'eval' and isinstance(ruleSet[rule], UDF):
            self.errLog.append("Cannot evaluate a user-defined function")
        elif ruleCategory == 'eval' and rule == 'math':
            self.errLog.append("Could not find built-in Racket procedure associated with 'math'")
        elif ruleCategory == 'eval' and ruleSet[rule].isProperty:
            self.errLog.append("Cannot evaluate a property")
        if self.errLog == []:
            def find_undefined_labels(node: Node):
                undefined_labels = []
                for child in node.children:
                    if child.data[0] == "'" or child.data[0] == "(":
                        nested_children = find_undefined_labels(child)
                        if nested_children:
                            undefined_labels.append(nested_children)
                    elif child.type.getType() == Type.PARAM:
                        undefined_labels.append(child.data)
                return undefined_labels

            undefined_labels = find_undefined_labels(targetNode)
            for label in undefined_labels:
                self.errLog.append(f"No definition found for label '{label}'")
        # checking to see if highlighted portion is within a quote
        if "'(" in targetNode.ancestors():
            self.errLog.append(f"Cannot apply rules within a quoted expression")
            
        if self.errLog == []:       
            selectedRule = ruleSet[rule]
            if rule == 'math':
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
