from .ERCommon import *
from .ERGenerics import *
from .ERRuleset import Rule, RuleType, UDF, getDefaultRuleSet, isMatch
import expression_tree.Parser as Parser
import expression_tree.Labeler as Labeler
import expression_tree.Decorator as Decorator
import re
import copy

reservedLabels = ["cons", "if", "first", "rest", "null?", "cons?", "zero?", "integer?", "list?", "consList", "expt", 
                  "quotient", "remainder", "and", "or", "not", "implies", "nand", "iff", "nor", "xor", ">", "<", "+", 
                  "-", "*", "null", "=", "-+", "math", "cons-first-rest", "first-cons", "rest-cons", "null?-cons",
                  "IH"]

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
        stripped = label[:-1] if label.endswith('?') else label
        valid_chars = len(stripped) > 0 and stripped.isalpha()
        return False not in map(lambda iterable: label not in iterable, (
            reservedLabels, *self.ruleSet.values(), self.generics
        )) and valid_chars
    
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
            generics=self.generics,
            udfLabel=udfLabel
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
            # Post-fillBody: validate if-branch types now that PARAMs are resolved
            post_errors = []
            _validate_filled_if_branches(filledBodyNode, post_errors)
            if post_errors:
                self.errLog.extend(post_errors)
                return
            self.ruleSet['apply'][udfLabel] = UDF(udfLabel, filledBodyNode, racTypeObj, paramsList)
           # print(f"Added UDF '{udfLabel}' with type '{str(racTypeObj)}' and body '{str(filledBodyNode)}'")

    def removeUDF(self, label):
        if len(label) != 1:
            label = label.split()[0].lstrip("(")
        if label in self.ruleSet['apply']:
            del self.ruleSet['apply'][label]

    def removeGeneric(self, label: str):
        if label in self.generics:
            del self.generics[label]

    def addGeneric(self, label: str, type: str, restrictions: dict | None = None):
        # If the generic already exists, remove it to allow redefinition
        if label in self.generics:
            del self.generics[label]
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
        self.isComplete = False
        # TODO: is there a way to not have a separate definitions list, 
        # since they are also stored in the ruleSet?
        self.definitions = []

    def toggleSide(self):
        self.currentSide = self.RHS if self.currentSide == self.LHS else self.LHS
    
    def setCurrentSide(self, side: str):
        if side.upper() not in ('LHS', 'RHS'):
            raise ValueError("Invalid side literal: side must be either 'LHS' or 'RHS'")
        self.currentSide = self.LHS if side == 'LHS' else self.RHS
    
    def checkComplete(self, is_student):
        """
        Check if proof is complete:
        - Last non-empty lines of LHS and RHS must be the same
        - No blank lines except possibly the last line (for user input)
        - Special case: If both sides have only premises (no derivations), compare first lines
        - NO lines can have hidden expressions or justifications
        """
        lhs_lines = self.LHS.proofLines
        rhs_lines = self.RHS.proofLines
        # Helper to check if a line is blank
        def is_blank(line):
            expr_blank = not line.exprTree or not str(line.exprTree).strip()
            rule_blank = not line.appliedRule or not line.appliedRule.strip()
            return expr_blank or rule_blank

        # Helper to check if line has hidden fields
        def is_hidden(line):
            return getattr(line, 'hide_expression', False) or getattr(line, 'hide_justification', False)

        # Special case: If both sides have exactly 1 line (just premise), compare them
        if len(lhs_lines) == 1 and len(rhs_lines) == 1:
            lhs_expr = str(lhs_lines[0].exprTree).strip() if lhs_lines[0].exprTree else ""
            rhs_expr = str(rhs_lines[0].exprTree).strip() if rhs_lines[0].exprTree else ""
            
            # Check visibility for the single lines
            if lhs_expr and rhs_expr and lhs_expr == rhs_expr and not is_hidden(lhs_lines[0]) and not is_hidden(rhs_lines[0]):
                self.isComplete = True
                return True
            else:
                self.isComplete = False
                return False
        
        if not lhs_lines or not rhs_lines:
            self.isComplete = False
            return False
        
        # Get last non-blank line index from each side
        lhs_last = None
        lhs_last_idx = -1
        for i, line in enumerate(reversed(lhs_lines)):
            if not is_blank(line):
                lhs_last = str(line.exprTree).strip()
                lhs_last_idx = len(lhs_lines) - 1 - i
                break

        rhs_last = None
        rhs_last_idx = -1
        for i, line in enumerate(reversed(rhs_lines)):
            if not is_blank(line):
                rhs_last = str(line.exprTree).strip()
                rhs_last_idx = len(rhs_lines) - 1 - i
                break

        # Check if last non-blank lines match
        if not lhs_last or not rhs_last or lhs_last != rhs_last:
            self.isComplete = False
            return False

        # Check for internal blank lines only up to (not including) the last non-blank line.
        # Blank lines AFTER the last non-blank line are ignored — they are cleared wrong
        # attempts or the trailing blank kept for user input, not gaps in the proof chain.
        for line in lhs_lines[:lhs_last_idx]:
            if is_blank(line):
                self.isComplete = False
                return False

        for line in rhs_lines[:rhs_last_idx]:
            if is_blank(line):
                self.isComplete = False
                return False

        for line in lhs_lines:
            if not is_blank(line) and (is_student and is_hidden(line)):
                self.isComplete = False
                return False

        for line in rhs_lines:
            if not is_blank(line) and (is_student and is_hidden(line)):
                self.isComplete = False
                return False

        self.isComplete = True
        return True
    
    def markIncomplete(self):
        """Mark proof as incomplete (called when user edits)"""
        self.isComplete = False
    
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
        self.premise: Node = None

    def addProofLine(self, lineStr, ruleStr=None, highlightPos=0, substitution=None, auto_infer=False):
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
                    proofLine.applyRule(ruleStr, highlightPos, auto_infer=auto_infer)
            elif len(self.proofLines) == 0:
                # This is the first line of the proof, so it's a premise
                proofLine.appliedRule = "Premise"
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

    def __str__(self):
        """Display proof lines with line numbers, expressions, rules, and node descriptions"""
        lines = []
        for line_num, proofLine in enumerate(self.proofLines):
            expr_str = str(proofLine.exprTree) if proofLine.exprTree else ""
            rule_str = proofLine.appliedRule if proofLine.appliedRule else ""
            
            # For nodes, get the expression from the previous line
            node_description = ""
            if proofLine.appliedRuleNodeId is not None and line_num > 0:
                prev_line = self.proofLines[line_num - 1]
                node = findNode(prev_line.exprTree, proofLine.appliedRuleNodeId, [])[0]
                if node:
                    node_str = str(node)
                    node_description = f"on node {proofLine.appliedRuleNodeId}: {node_str}"
            
            lines.append(f"{line_num}\t{expr_str}\t{rule_str}\t{node_description}")
        return "\n".join(lines)

class ERProofLine(ProofComponent):
    def __init__(self, goal, debug=False, ruleDict=None, udfType=None, isUdf=False, generics=None, udfLabel=None): #added optional pointer to parent proof's ruleset
        super().__init__(ruleSet=ruleDict, generics=generics, debug=debug)
        self.exprTree = None
        self.positions = dict() # a dict of 4-tuples of the next pos when hitting up,down,left,right. keyd by startpos
        self.appliedRule = None # stores the rule that was applied to generate this line
        self.appliedRuleNodeId = None # stores the node ID where the rule was applied on the previous line
        self.resultNodeId = None # stores the node ID of the changed portion in this line's result
        self.hide_expression = False
        self.hide_justification = False
        self.errors = ""

        # Special case: allow blank lines (used for cleared lines)
        if goal == "" or goal is None or (isinstance(goal, str) and goal.strip() == ""):
            # Create a minimal empty tree node
            self.exprTree = Node("")
            self.positions = {}
            return

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
            decTree, self.errLog = Decorator.checkFunctions(decTree, self.errLog, userType=udfType, udfLabel=udfLabel)
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

    def applyRule(self, rule: str, startPos: int, subNode: Node = None, auto_infer: bool = False):
        fullRuleString = rule  # Store the original full rule string before parsing
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
        # Normalize arrows to equals for assignments from UI
        ruleParams = " ".join(parts[2:]).replace("\u21A6", "=").replace("\u2192", "=")
        ruleParams = ruleParams.replace("'()", "null")  # replace empty list with 'null'
        # normalize spaces around '=' so assignments like 'x = 1' parse correctly
        ruleParams = re.sub(r"\s*=\s*", "=", ruleParams)
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

        # ── HIGH support: auto-infer parameter mappings from highlighted node ──
        # Must run before UDF/Axiom validation so inferred params satisfy the checks below.
        if auto_infer and not ruleParams:
            ruleParams, fullRuleString = _infer_params_for_rule(
                selected, targetNode, ruleCategory, rule, fullRuleString
            )
        # ── END HIGH support inference ──

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
            # Value mismatch check: each assigned value must match the actual argument
            # in the expression (e.g. 'apply fc x=4' on '(fc 3)' should be rejected).
            mismatch_errors = []
            for i, (param, value) in enumerate(zip(ruleParams, values)):
                name, _ = param.split('=', 1)
                if i + 1 >= len(targetNode.children):
                    # Wrong target node selected (e.g. applying 'append' on 'reverse' node);
                    # isApplicable below will produce the proper error message.
                    break
                expected_node = targetNode.children[i + 1]
                if str(value) != str(expected_node):
                    mismatch_errors.append(
                        f"Value mismatch in argument '{name.strip()}': "
                        f"expected {str(expected_node)}, got {str(value)}"
                    )
            if mismatch_errors:
                self.errLog.extend(mismatch_errors)
                return
        if selected._ruleType == RuleType.MATH:
            ok, err = selected.isApplicable(targetNode, subNode)
        elif selected._ruleType == RuleType.LOGIC:
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
            if selected.ruleType in (RuleType.MATH, RuleType.LOGIC)
            else selected.insertSubstitution(targetNode)
        )
        targetNode.replaceWith(newNode)
        updatePositions(self.exprTree)
        
        # Successfully applied the rule, so store the full rule string and the node IDs
        self.appliedRule = fullRuleString
        self.appliedRuleNodeId = startPos  # Where rule was applied (on previous line)
        self.resultNodeId = targetNode.startPosition  # The changed node in result (on this line)

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
            elif not isMatch(subLine.exprTree, targetNode):
                self.errLog.append(
                    f"substitution evaluated to {str(subLine.exprTree)} but expected {str(targetNode)}"
                )
        if self.errLog == []:
            targetNode.replaceWith(replacementExprTree)
            updatePositions(self.exprTree)
            # Record the applied rule and node ids for display purposes
            self.appliedRuleNodeId = startPos  # Where substitution was applied (on previous line)
            self.resultNodeId = targetNode.startPosition  # The changed node in result (on this line)
            # Record the applied rule
            try:
                # Build a full rule string including substitution expression
                sub_str = str(subLine.exprTree) if subLine and subLine.exprTree is not None else ""
                self.appliedRule = f"{rule} with {sub_str}" if sub_str else rule
                self.appliedRuleNodeId = startPos
            except Exception:
                # Fallback: at least record basic rule and node id
                self.appliedRule = rule
                self.appliedRuleNodeId = startPos


def updatePositions(inputTree: Node, count: int = 0) -> tuple[Node, int]:
    inputTree.startPosition = count
    count += len(inputTree.data)

    if len(inputTree.children) > 0:
        for childIndex, child in enumerate(inputTree.children):
            newChild, newCount = updatePositions(child, count)
            inputTree.children[childIndex] = newChild
            count = newCount + 1
    return inputTree, count

def _unify_lemma_params(premise_node: Node, target_node: Node,
                        param_names: list, bindings: dict) -> bool:
    """
    Walk premise_node and target_node in parallel.
    When premise_node.data is a free-variable name (in param_names),
    bind it to the string representation of the corresponding target subtree.
    Returns True if unification succeeds, False on structural mismatch or conflict.
    """
    if premise_node.data in param_names:
        name = premise_node.data
        val_str = str(target_node)
        if name in bindings and bindings[name] != val_str:
            return False  # conflicting binding
        bindings[name] = val_str
        return True
    if premise_node.data != target_node.data:
        return False
    if len(premise_node.children) != len(target_node.children):
        return False
    for pc, tc in zip(premise_node.children, target_node.children):
        if not _unify_lemma_params(pc, tc, param_names, bindings):
            return False
    return True


def _infer_params_for_rule(selected_rule, target_node: Node, rule_category: str,
                           rule_name: str, full_rule_string: str) -> tuple:
    """
    HIGH support: infer parameter mappings from the highlighted target node.
    Returns (ruleParams, fullRuleString) where ruleParams is a list of "name=value"
    strings and fullRuleString is updated with ↦ arrows.
    If inference is not applicable, returns ([], full_rule_string) unchanged.
    """
    # Only infer for UDFs and Axioms
    if selected_rule.ruleType == RuleType.DEFINITION:
        param_names = selected_rule.params
        # Children: [0]=func_label, [1..]=arguments
        value_nodes = target_node.children[1:]
        if len(param_names) != len(value_nodes):
            return [], full_rule_string
        ruleParams = [f"{name}={str(val)}" for name, val in zip(param_names, value_nodes)]
        mappings = ", ".join(f"{name}\u21a6{str(val)}" for name, val in zip(param_names, value_nodes))
        new_full = f"{rule_category} {rule_name} with {mappings}"
        return ruleParams, new_full
    if selected_rule.ruleType == RuleType.AXIOM:
        # Verify structure first — if it fails, let normal error handling fire
        ok, _ = selected_rule.verifyStructure(target_node)
        if not ok:
            return [], full_rule_string
        ruleParams = []
        arrows = []
        for param_name, finder in selected_rule.params.items():
            locations = finder(target_node)
            if not locations:
                return [], full_rule_string
            first_loc = locations[0]
            # finder may return a tuple of alternatives for commutative params
            val_node = first_loc[0] if isinstance(first_loc, tuple) else first_loc
            val_str = str(val_node)
            ruleParams.append(f"{param_name}={val_str}")
            arrows.append(f"{param_name}\u21a6{val_str}")
        mappings = ", ".join(arrows)
        new_full = f"{rule_category} {rule_name} {mappings}"
        return ruleParams, new_full
    if selected_rule.ruleType == RuleType.LEMMA:
        param_names = selected_rule.param_names
        if not param_names:
            return [], full_rule_string
        bindings = {}
        premise_copy = copy.deepcopy(selected_rule.premise_tree)
        if not _unify_lemma_params(premise_copy, target_node, param_names, bindings):
            return [], full_rule_string
        if any(n not in bindings for n in param_names):
            return [], full_rule_string
        ruleParams = [f"{n}={bindings[n]}" for n in param_names]
        arrows = ", ".join(f"{n}\u21a6{bindings[n]}" for n in param_names)
        new_full = f"{rule_category} {rule_name} {arrows}"
        return ruleParams, new_full
    return [], full_rule_string


def _resolve_type(t):
    """Unwrap nested RacType wrappers down to a plain Type enum.
    getDomain() double-wraps each domain type in RacType, so we need to
    loop until we reach a non-RacType value."""
    while isinstance(t, RacType):
        t = t.getType()
    return t


def _validate_filled_if_branches(node, errors):
    """Post-fillBody: check if-expressions have matching branch types after parameter
    types have been resolved from PARAM to their declared concrete types.
    An if-node in the AST has data='(' with children[0].data=='if'."""
    if (node.data == '(' and len(node.children) == 4
            and node.children[0].data == 'if'):
        t1 = _resolve_type(node.children[2].type)
        t2 = _resolve_type(node.children[3].type)
        if t1 is not None and t2 is not None and t1 != t2:
            if t1 not in FLEX_TYPES and t2 not in FLEX_TYPES:
                errors.append(
                    f"Definition body type error: the two result branches of an if-expression "
                    f"must have the same type, but found {t1} and {t2}. "
                    f"Check your parameter types or use type 'any' if the types should be flexible."
                )
    for child in node.children:
        _validate_filled_if_branches(child, errors)


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