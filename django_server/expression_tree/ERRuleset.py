from abc import ABC, abstractmethod
from .ERCommon import *
from .ERGenerics import ERGeneric, GenericInt, GenericList, GenericBool, GenericAny
import copy
from .Parser import makeBasicAst
from .Labeler import labelTree  # , fillPositions
from enum import Enum
from collections.abc import Callable
#pylance showing false positive for sympy import
import sympy as sp # type: ignore

# recursively check if two nodes are identical
def isMatch(xNode: Node, yNode: Node) -> bool:
    if xNode.data != yNode.data:  # or len(xNode.children) != len(yNode.children): #since BRacket has set # inputs for a function, data same is enough for #children same       #xNode.name != yNode.name or \
       # xNode.numArgs != yNode.numArgs or \
       # xNode.length != yNode.length or \
       # xNode.type != yNode.type or \
        return False
    # elif len(xNode.children) != 0:
    #     checker = False
    #     for i in range(len(xNode.children)):
    #         if isMatch(xNode.children[i], yNode.children[i]):
    #             checker = True
    #     return checker
    # else:
    #     return True
    if len(xNode.children) != len(yNode.children):
        return False
    sofar = True
    for i in range(len(xNode.children)):  # defaults to True if no children since no loop
        # if any are false, sofar will be false
        sofar &= isMatch(xNode.children[i], yNode.children[i])
    return sofar

class RuleType(Enum):
    BUILT_IN = 0
    DEFINITION = 1
    AXIOM = 2
    MATH = 3
    LEMMA = 4
    IH = 5

    def __str__(self):
        if self == RuleType.BUILT_IN:
            return 'built-in Racket procedure'
        if self == RuleType.IH:
            return 'IH'
        if self == RuleType.MATH:
            return 'algebraic math rule'
        return self.name.lower()
    
class Rule(ABC):
    def __init__(self, label, ruleType: RuleType = RuleType.BUILT_IN):
        self._label = label
        self._ruleType = ruleType

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, newLabel):
        self._label = newLabel

    @property
    def ruleType(self):
        return self._ruleType

    @abstractmethod
    def isApplicable(self, ruleNode: Node, rawParams: list[str] = None) -> tuple[bool, str]:
        pass

    @abstractmethod
    def insertSubstitution(self, ruleNode: Node) -> Node:
        pass

class BuiltIn(Rule):
    def __init__(self, label, allowGenerics=False):
        super().__init__(label, RuleType.BUILT_IN)        
        self._allowGenerics = allowGenerics

    def isApplicable(self, ruleNode: Node, rawParams: list[str] = None) -> tuple[bool, str]:
        if rawParams:
            return False, f"Unexpected assignments {rawParams[1:-1]}"
        if not ruleNode.children:
            return False, f"Cannot apply '{self.label}' on a '{ruleNode.name}'"
        # Check if the operator matches the rule label
        if ruleNode.children[0].data != self.label:
            return False, f"Cannot evaluate {self.label} on a '{ruleNode.children[0].data}' expression"
        #if (len(ruleNode.children[1].children) != 0 and ruleNode.children[1].data != "'(") or (len(ruleNode.children[2].children) != 0 and ruleNode.children[2].data != "'("):
        if True in map(lambda child: (len(child.children) != 0 and child.data != "'(") or child.name == 'TBD', ruleNode.children[1:]):
            return False, 'Insufficiently resolved arguments'
        if not self._allowGenerics:
            generics = [child.data for child in ruleNode.children[1:] if isinstance(child.name, ERGeneric)]
            if len(generics) != 0:
                return False, f"Cannot evaluate '{self.label}' expression with generic arguments"
        return True, 'BuiltIn.isApplicable() PASS'

class If(BuiltIn):
    def __init__(self):
        super().__init__('if', allowGenerics=True)
        self.racType = str2Type("(BOOL,ANY,ANY)>ANY")

    def isApplicable(self, ruleNode: Node, rawParams: list[str] = None) -> tuple[bool, str]:
        # Check if the operator matches the rule label
        if ruleNode.children[0].data != self.label:
            return False, f"Cannot evaluate if on a '{ruleNode.children[0].data}' expression"
        if len((cond := ruleNode.children[1]).children) != 0 and cond.data == '(' or cond.name == 'TBD':
            return False, "Insufficiently resolved condition argument"
        if not isMatch(ruleNode.children[2], ruleNode.children[3]) and isinstance(ruleNode.children[1].name, ERGeneric):
            return False, f"Cannot determine truth value of generic argument '{ruleNode.children[1].data}'"
        return True, 'If.isApplicable() PASS'

    def insertSubstitution(self, ruleNode: Node) -> Node:
        condition = ruleNode.children[1]
        xNode = ruleNode.children[2]
        yNode = ruleNode.children[3]
        if condition.data == '#t' or isMatch(xNode, yNode):
            return xNode
        elif condition.data == '#f':
            return yNode

class NullQ(BuiltIn):
    def __init__(self):
        super().__init__('null?', allowGenerics=True)
        self.racType = str2Type("ANY>BOOL")

    def isApplicable(self, ruleNode: Node, rawParams: list[str] = None) -> tuple[bool, str]:
        parentPassed, parentMessage = super().isApplicable(ruleNode)
        if not parentPassed:
            return parentPassed, parentMessage
        if isinstance(ruleNode.children[1].name, (GenericList, GenericAny)):
            if ruleNode.children[1].name.neverNull:
                return True, 'NullQ.isApplicable() PASS'
            return False, f"Cannot determine value of 'null?' expression with generic argument '{ruleNode.children[1]}'"
        # string should not print out if debug=False
        return True, 'NullQ.isApplicable() PASS'

    def insertSubstitution(self, ruleNode: Node) -> Node:
        if not ruleNode.children[1].type.isType("LIST") or isinstance(ruleNode.children[1].name, ERGeneric):
            return Node(data='#f', tokenType=RacType((None, Type.BOOL)), name=False)
        # must check nonlists first to avoid thinking no children is a null list
        if len(ruleNode.children[1].children) == 0:
            return Node(data='#t', tokenType=RacType((None, Type.BOOL)), name=True)
        return Node(data='#f', tokenType=RacType((None, Type.BOOL)), name=False)

# NOTE: cons? procedure not currently in rule set
class ConsQ(Rule):
    def __init__(self):
        super().__init__('cons?')
        self.racType = str2Type("ANY>BOOL")

    def isApplicable(self, ruleNode: Node, rawParams: list[str] = None) -> tuple[bool, str]:
        if ruleNode.children[0].data != 'cons?':
            return False, f'Cannot apply cons? rule to {ruleNode.children[0].data}'
        elif ruleNode.children[1].children[0].data != 'cons':
            return False, f'cons? can only be applied with a cons'
        return True, 'ConsQ.isApplicable() PASS'  # string should not print out if debug=False

    def insertSubstitution(self, ruleNode: Node) -> Node:
        trueNode = Node(data='#t', tokenType=RacType(
            (None, Type.BOOL)), name=True)
        return trueNode

class ZeroQ(BuiltIn):
    def __init__(self):
        super().__init__('zero?', allowGenerics=True)
        self.racType = str2Type("ANY>BOOL") # NOTE: consider making (INT>BOOL) instead

    def isApplicable(self, ruleNode: Node, rawParams: list[str] = None) -> tuple[bool, str]:
        parentPassed, parentMessage = super().isApplicable(ruleNode)
        if not parentPassed:
            return parentPassed, parentMessage
        if isinstance(ruleNode.children[1].name, (GenericInt, GenericAny)):
            if ruleNode.children[1].name != 0:
                return True, 'ZeroQ.isApplicable() PASS'
            return False, f"Cannot determine value of 'zero?' expression with generic argument '{ruleNode.children[1].data}'"
        return True, 'ZeroQ.isApplicable() PASS'  # string should not print out if debug=False

    def insertSubstitution(self, ruleNode: Node) -> Node:
        trueNode = Node(data='#t', tokenType=RacType(
            (None, Type.BOOL)), name=True)
        falseNode = Node(data='#f', tokenType=RacType(
            (None, Type.BOOL)), name=False)
        if isinstance(ruleNode.children[1].data, (GenericInt, GenericAny)):
            return falseNode
        return trueNode if ruleNode.children[1].data == '0' else falseNode

class ConsList(BuiltIn):
    def __init__(self):
        super().__init__('cons')
        self.racType = str2Type("(ANY,LIST)>LIST")

    def insertSubstitution(self, ruleNode: Node) -> Node:
        if ruleNode.children[2].data =="null":
            ruleNode.children[2].data = "'("  # changing null to '( to make consistent case handling
        # at this point the second argument is definitely '( although possibly with no children/entries
        if ruleNode.children[1].data == "'(": #need to get rid of the object's quote to avoid nesting quotes
            if len(ruleNode.children[1].children) == 0:
                newtype = RacType((None, Type.LIST))  # consing a '()
            else:
                newtype = ruleNode.children[1].children[0].type
                if newtype.getType() == Type.FUNCTION:
                    newtype = newtype.getRange()  # changing the type of the paren to be the output type of the operand
            parenNode = Node(
                children=ruleNode.children[1].children, data="(", tokenType=newtype, parent=ruleNode.children[1])
            for ch in ruleNode.children[1].children:
                ch.parent = parenNode  # changing the parent of the children to the new node
            ruleNode.children[1].children = [parenNode]  # replacing the old children with the new node
            lNode = ruleNode.children[1]  # this will be the node used for replacement
            lNode.children.extend(ruleNode.children[2].children)
        else:  # consObj is a nonquoted object
            lNode = Node(children=[ruleNode.children[1]], data="'(", tokenType=RacType((None, Type.LIST)))  # length=len(self.children[2].children)+1)
            lNode.children.extend(ruleNode.children[2].children)
            for child in lNode.children:
                child.parent = lNode
        return lNode

class FirstList(BuiltIn):
    def __init__(self):
        super().__init__('first')

    def isApplicable(self, ruleNode: Node, rawParams: list[str] = None) -> tuple[bool, str]:  # presumes buildtree checked types/qty already
        parentPassed, parentMessage = super().isApplicable(ruleNode)
        if not parentPassed:
            return parentPassed, parentMessage
        if ruleNode.children[1].length == 0:
            return False, 'first requires non-empty list'
        return True, 'FirstList.isApplicable() PASS'

    def insertSubstitution(self, ruleNode: Node) -> Node:
        origList = copy.deepcopy(ruleNode.children[1])
        if origList.children[0].data == "(":
            origList.children[0].data = "'("
        return origList.children[0]

class RestList(BuiltIn):
    def __init__(self):
        super().__init__('rest')

    def isApplicable(self, ruleNode: Node, rawParams: list[str] = None) -> tuple[bool, str]:  # presumes buildtree checked types/qty already
        parentPassed, parentMessage = super().isApplicable(ruleNode)
        if not parentPassed:
            return parentPassed, parentMessage
        if ruleNode.children[1].length == 0:
            return False, 'rest requires non-empty list'
        return True, 'RestList.isApplicable() PASS'

    def insertSubstitution(self, ruleNode: Node) -> Node:
        origList = ruleNode.children[1]
        if (n :=len(origList.children)) == 1:
            return Node(data="null", tokenType=RacType((None, Type.LIST)), name=[])
        newNode = Node(data="'(", tokenType=RacType((None, Type.LIST)), \
                    name=origList.name[1:] if isinstance(oname :=origList.name, list) and \
                    len(oname) >0 else None, length=n-1)
        for ind in range(1, n): #shift all elements left
            newNode.children.append(origList.children[ind])
        return newNode  # could have just returned in place by removing first element

class Equals(BuiltIn):
    def __init__(self):
        super().__init__('=', allowGenerics=True)

    def insertSubstitution(self, ruleNode: Node|None):
        argOne = str(ruleNode.children[1])
        argTwo = str(ruleNode.children[2])
        return Node(data="#t" if argOne == argTwo else "#f", tokenType=RacType((None, Type.BOOL)), name=argOne == argTwo)  # converting node


# NOTE: for [type]? expressions, when the argument is of type ANY, it currently evaluates to #f
class TypeQ(BuiltIn):
    def __init__(self, label, typeToCheck: Type):
        super().__init__(label, allowGenerics=True)
        self._typeToCheck = typeToCheck

    def insertSubstitution(self, ruleNode: Node) -> Node:
        trueNode = Node(data='#t', tokenType=RacType((None, Type.BOOL)), name=True)
        falseNode = Node(data='#f', tokenType=RacType((None, Type.BOOL)), name=False)
        return trueNode if ruleNode.children[1].type.getType() == self._typeToCheck else falseNode

class IntegerQ(TypeQ):
    def __init__(self):
        super().__init__('integer?', Type.INT)
    
class ListQ(TypeQ):
    def __init__(self):
        super().__init__('list?', Type.LIST)

# TODO: this needs to be generalized to use a python math library and normal forms, and not just the 4 basic operations
'''
class Math(Rule):
    def __init__(self):
        super().__init__('math')

    def __init__(self):
        self.mathSymbols = ARITHMETIC+["expt", "<=",">=","quotient","remainder"]
        self.mathDict = {"+":lambda x,y: x+y, "-":lambda x,y: x-y, "*":lambda x,y: x*y, "expt":lambda x,y: x**y, "=":lambda x,y: x ==y, ">":lambda x,y: x>y, \
                  ">=":lambda x,y: x >=y, "<":lambda x,y: x<y, "<=":lambda x,y: x<=y, "quotient":lambda x,y: x//y, "remainder":lambda x,y: x%y}

    def isApplicable(self, ruleNode: Node, rawParams: list[str] = None) -> tuple[bool, str]:
        # note: no need to check argument types or number of arguments, since that is done in buildTree
        if (len(ruleNode.children) != 0 and ruleNode.children[0].data not in self.mathSymbols):
            return False, f'Cannot apply math rule to {ruleNode.children[0].data}'
        elif len(ruleNode.children[1].children) != 0 or len(ruleNode.children[2].children) != 0:  # checking for (+ 1 (+ 2 3)) type errors
            return False, "insufficiently resolved arguments"

        argOne = ruleNode.children[1].name
        argTwo = ruleNode.children[2].name

        if (ruleNode.children[0].data =="remainder" or ruleNode.children[0].data=="quotient") and argTwo==0:
            return False, "denominator can't be zero"
        elif ruleNode.children[0].data == "expt" and argOne*argOne != 1  and argTwo < 0:  # note: currently PB has no negatives anyway!
            return False, "expt with negative arguments results in non-integer output"
        elif ruleNode.children[0].data == "expt" and argOne == 0 and argTwo == 0:
            return False, "0^0 is undefined"
        return True, "Math.isApplicable() PASS"  # string should not print out if debug=False

    def insertSubstitution(self, ruleNode: Node) -> Node:
        argOne = ruleNode.children[1].name
        argTwo = ruleNode.children[2].name
        newname = self.mathDict[ruleNode.children[0].data](argOne, argTwo)  # compute the result
        if isinstance(newname, bool):
            newdata = "#t" if newname else "#f"  # convert to racket bool
            newtype = RacType((None, Type.BOOL))
        else:
            newdata = str(newname)
            newtype = RacType((None, Type.INT))
        return Node(data=newdata, tokenType=newtype, name=newname)  # converting node
'''
class Symbolic(BuiltIn, ABC):
    @abstractmethod
    def getStdExpr(self, ruleNode: Node) -> str:
        pass

    def insertSubstitution(self, ruleNode: Node) -> Node:
        try:
            symbolicExpr = sp.simplify(sp.sympify(self.getStdExpr(ruleNode)))
            
            # Determine the type of the result (e.g., INT or BOOL)
            if symbolicExpr.is_Boolean:
                newtype = RacType((None, Type.BOOL))
                newname = "#t" if symbolicExpr else "#f"
            elif symbolicExpr.is_Integer:
                newtype = RacType((None, Type.INT))
                newname = int(symbolicExpr)
            else:
                newtype = RacType((None, Type.ANY))
                newname = str(symbolicExpr)
            
            newdata = str(newname)

            # Create a new node with the simplified expression
            return Node(data=newdata, tokenType=newtype, name=newname)
        except Exception as e:
            raise ValueError(f"Error in insertSubstitution: {str(e)}")

class Math(Symbolic):
    def getStdExpr(self, ruleNode: Node) -> str:
        return ruleNode.mathStr()

class Plus(Math):
    def __init__(self):
        super().__init__('+')

class Minus(Math):
    def __init__(self):
        super().__init__('-')

class Times(Math):
    def __init__(self):
        super().__init__('*')

class Quotient(Math):
    def __init__(self):
        super().__init__('quotient')
    
    def isApplicable(self, ruleNode: Node, rawParams: list[str] = None) -> tuple[bool, str]:
        parentPassed, parentMessage = super().isApplicable(ruleNode)
        if not parentPassed:
            return False, parentMessage
        if int(ruleNode.children[-1].data) == 0:
            return False, "denominator can't be zero"
        return True, 'Quotient.isApplicable() PASS'

class Remainder(Math):
    def __init__(self):
        super().__init__('remainder')
    
    def isApplicable(self, ruleNode: Node, rawParams: list[str] = None) -> tuple[bool, str]:
        parentPassed, parentMessage = super().isApplicable(ruleNode)
        if not parentPassed:
            return False, parentMessage
        if int(ruleNode.children[-1].data) == 0:
            return False, "denominator can't be zero"
        return True, 'Remainder.isApplicable() PASS'

class Expt(Math):
    def __init__(self):
        super().__init__('expt')
    
    def isApplicable(self, ruleNode: Node, rawParams: list[str] = None) -> tuple[bool, str]:
        parentPassed, parentMessage = super().isApplicable(ruleNode)
        if not parentPassed:
            return False, parentMessage
        if int(ruleNode.children[1].data) == 0 and int(ruleNode.children[2].data) == 0:
            return False, '0^0 is undefined'
        if int(ruleNode.children[2].data) < 0:
            return False, f'{ruleNode.children[2]} contains illegal character'
        return True, 'Expt.isApplicable() PASS'

# NOTE: consider allowing generic arguments in comparison operators?
# probably not a priority until negatives are implemented
class LessThan(Math):
    def __init__(self):
        super().__init__('<')

class LessOrEqual(Math):
    def __init__(self):
        super().__init__('<=')

class GreaterThan(Math):
    def __init__(self):
        super().__init__('>')

class GreaterOrEqual(Math):
    def __init__(self):
        super().__init__('>=')

""" class Logic(Rule):
    def __init__(self):
        super().__init__('logic')

    def __init__(self):
        self.logicDict ={"and":lambda x,y: x and y, "or":lambda x,y: x or y, "not":lambda x,y: not x, "xor":lambda x,y: (x or y) and not(x and y), \
                    "implies": lambda x,y: (not x) or y} # not set up for "iff":lambda x,y: x==y, "nor":lambda x,y: not(x or y), "nand":lambda x,y: not(x and y) 
    # note: no need to check argument types or number of arguments, since that is done in buildTree

    def isApplicable(self, ruleNode: Node, rawParams: list[str] = None) -> tuple[bool, str]:
        if (len(ruleNode.children) != 0 and ruleNode.children[0].data not in self.logicDict.keys()):
            return False, f'Cannot apply logic rule to {ruleNode.children[0].data}'
        elif len(ruleNode.children[1:]) < 2 and ruleNode.children[0].data !="not":
            return False, f'Not enough arguments provided to {ruleNode.children[0].data}'
        elif len(ruleNode.children[1].children) != 0 or (ruleNode.children[0].data !="not" and len(ruleNode.children[2].children) != 0): #checking for (or (not #t) #t) type errors
            return False, "insufficiently resolved arguments"
        return True, "Logic.isApplicable() PASS"  # string should not print out if debug=False

    def insertSubstitution(self, ruleNode: Node) -> Node:
        argOne = ruleNode.children[1].name
        argTwo = (True if ruleNode.children[0].data == "not" else ruleNode.children[2].name) #y=True isn't used for "not" lambda operation, 2 params for consistency
        newname = self.logicDict[ruleNode.children[0].data](argOne, argTwo)
        newdata = "#t" if newname else "#f"  # convert to racket bool
        newtype = RacType((None, Type.BOOL))
        return Node(data=newdata, tokenType=newtype, name=newname)  # converting node """

class Logic(Symbolic):
    def getStdExpr(self, ruleNode: Node) -> str:
        return ruleNode.logicStr()
    
class And(Logic):
    def __init__(self):
        super().__init__('and')

class Or(Logic):
    def __init__(self):
        super().__init__('or')

class Not(Logic):
    def __init__(self):
        super().__init__('not')

class Xor(Logic):
    def __init__(self):
        super().__init__('xor')

class Implies(Logic):
    def __init__(self):
        super().__init__('implies')
class UDF(Rule):
    def __init__(self, label, filledBodyNode, racTypeObj, paramsList):
        super().__init__(label, RuleType.DEFINITION)
        self.body = filledBodyNode
        self.racType = racTypeObj
        self.params = paramsList

    def isApplicable(self, ruleNode: Node, rawParams: list[str] = None) -> tuple[bool, str]:
        if ruleNode.children != []:
            if ruleNode.children[0].data != self.label:
                return False, f'Cannot apply {self.label} definition to {ruleNode.children[0].data}'
            if len(ruleNode.children[1:]) != len(self.racType.getDomain()):
                return False, f"{self.label} must take {len(self.racType.getDomain())} inputs"

            providedIns = [c.type for c in ruleNode.children[1:]]
            # needs to be x.value for x in func.type.value[0] when in main rackexpr, but just func.type.value[0] for UDF checking
            expectedIns = [x if isinstance(x, RacType) else RacType(x) for x in
                           self.racType.value[0]]  # tricky since value[1] could be tuple or could be RacType
            if not all(x == y for x, y in zip(providedIns, expectedIns)):
                return [False,
                        f'Cannot match argument out typeList {[str(x) for x in providedIns]} with expected typeList {[str(x) for x in expectedIns]}']
        return True, f"{self.label.capitalize()}.isApplicable() PASS"  # string should not print out if debug=False

    def insertSubstitution(self, ruleNode: Node) -> Node:
        expCopy = copy.deepcopy(self.body)
        recursiveReplaceNodes(expCopy, self.params, ruleNode.children[1:])
        return expCopy

class IH(Rule):
    def __init__(self, indHypLHS: Node, indHypRHS: Node):
        super().__init__('IH', RuleType.IH)
        self.indHypLHS = indHypLHS
        self.indHypRHS = indHypRHS

    def isApplicable(self, ruleNode: Node, rawParams: list[str] = None) -> tuple[bool, str]:
        if rawParams:
            return False, f"IH rule takes no parameters"
        
        # Check if ruleNode matches either indHypLHS or indHypRHS by comparing string representations
        nodeStr = str(ruleNode)
        lhsStr = str(self.indHypLHS)
        rhsStr = str(self.indHypRHS)
        
        if nodeStr == lhsStr or nodeStr == rhsStr:
            return True, "IH.isApplicable() PASS"
        else:
            return False, f"Node '{nodeStr}' does not match induction hypothesis LHS '{lhsStr}' or RHS '{rhsStr}'"

    def insertSubstitution(self, ruleNode: Node) -> Node:
        nodeStr = str(ruleNode)
        lhsStr = str(self.indHypLHS)
        rhsStr = str(self.indHypRHS)
        
        # If the node matches LHS, replace with RHS; if it matches RHS, replace with LHS
        if nodeStr == lhsStr:
            return self.indHypRHS.clone()
        elif nodeStr == rhsStr:
            return self.indHypLHS.clone()

class Axiom(Rule, ABC):
    ParamFinder = Callable[[Node], tuple[Node | tuple[Node, ...], ...]] 
    # ParamFinder is a custom type representing a function that takes a node and returns a tuple
    # of the nodes where the param should be found in relation to the input node.
    # When a param *may* be in different locations (e.g. when an axiom is commutative),
    # the ParamFinder function should include logic to determine which location is correct.
    # If there are more than one correct locations, members of the output tuple may also be a tuple of Nodes

    def __init__(self, label: str, paramFinders: dict[str, ParamFinder]):
        super().__init__(label, ruleType=RuleType.AXIOM)
        self._paramFinders = paramFinders

        # Maps param to a representative node in the expression tree  
        self._paramMappings: dict[str, Node | None] = {key: None for key in paramFinders.keys()}
    
    @property
    def params(self):
        return self._paramFinders
    
    def _matchSingleParam(self, ruleNode: Node, param: str, assignment: str) -> tuple[bool, str]:
        finder = self._paramFinders[param]
        
        for paramLocation in finder(ruleNode):
            if isinstance(paramLocation, tuple):
                expectedValues: list[str] = []
                for loc in paramLocation:
                    if (expected := str(loc)) == assignment:
                        self._paramMappings[param] = loc
                        return True, ""
                    expectedValues.append(expected)
                wrappedWithQuotes = [f'"{expected}"' for expected in expectedValues]
                expectedValuesStr = ', '.join(wrappedWithQuotes[:-1]) + ' or ' + wrappedWithQuotes[-1]
                return False, (f'Value mismatch: expected {expectedValuesStr} '
                                f'for {param}, but "{assignment}" was provided')
            # Use AST-level comparison so whitespace/formatting differences don't cause
            # false rejections, while still catching genuine mismatches (e.g. x=null vs x=1).
            assignmentTree = makeBasicAst(assignment)[0]
            if isMatch(paramLocation, assignmentTree):
                self._paramMappings[param] = paramLocation
                return True, ""
            return False, (f'Value mismatch: expected "{str(paramLocation)}" '
                           f'for {param}, but "{assignment}" was provided')
        self._paramMappings[param] = paramLocation
        return True, ""
    
    def _getUnassignedParamsMsg(self, unassignedParams: set[str]) -> str:
        if len(unassignedParams) == 0:
            return ''
        if len(unassignedParams) == 1:
            return (f"Too few assignments were provided: param '{unassignedParams.pop()}' "
                    "does not have an assignment")
        orderedParams = [key for key in list(self._paramFinders.keys()) if key in unassignedParams]
        return (f"Too few assignments were provided: params {str(orderedParams)[1:-1]} "
                "do not have assignments")
    
    def matchParams(self, ruleNode: Node, rawParams: list[str]) -> tuple[bool, str]:
        unassignedParams = set(self._paramFinders.keys())

        for paramAssignment in rawParams:
            if '=' not in paramAssignment:
                return False, f'"{paramAssignment}" does not have an assignment. Did you forget an equals sign?'
            param, assignment = paramAssignment.split('=', 1)
            if param not in unassignedParams:
                return False, f'Unexpected assignment "{paramAssignment}" was provided'
            if makeBasicAst(assignment)[1]:
                return False, f'Failed to build AST from assignment "{assignment}"'
            matched, message = self._matchSingleParam(ruleNode, param, assignment)
            if not matched:
                return False, message
            unassignedParams.remove(param)
        if len(unassignedParams) != 0:
            return False, self._getUnassignedParamsMsg(unassignedParams)
        return True, 'PASS'
    
    @abstractmethod
    def verifyStructure(self, ruleNode: Node) -> tuple[bool, str]:
        """
        Checks ruleNode to see if its structure is correct to rewrite with the axiom.
        Runs before matchParams() in isApplicable()
        """
        pass

    def verifyValues(self) -> tuple[bool, str]:
        """
        Checks that the mapped values are valid to rewrite with the axiom.
        Runs after matchParams() in isApplicable()
        """
        return True, "PASS"

    def isApplicable(self, ruleNode: Node, rawParams: list[str] = None) -> tuple[bool, str]:
        if not rawParams:
            rawParams = []

        if not ruleNode.children:
            return False, f"Cannot apply '{self.label}' rule on a node with no children"

        # clear _paramMappings
        self._paramMappings = {key: None for key in self._paramMappings.keys()}

        passed, message = self.verifyStructure(ruleNode)
        if not passed:
            return False, message
        
        passed, message = self.matchParams(ruleNode, rawParams)
        if not passed:
            self._paramMappings = {key: None for key in self._paramMappings.keys()}
            return False, message
        
        passed, message = self.verifyValues()
        if not passed:
            return False, message
        
        return True, 'Axiom.isApplicable() PASS'

class ConsProp(Axiom):
    def __init__(self):
        LFinder: Axiom.ParamFinder = lambda node: (node.children[1].children[1], node.children[2].children[1])
        super().__init__('cons-first-rest', {'L': LFinder})
    
    def verifyStructure(self, ruleNode: Node) -> tuple[bool, str]:
        if ruleNode.children[0].data != 'cons':
            return False, f"Cannot rewrite with cons-first-rest rule when root operation is '{ruleNode.children[0].data}'"
        elif len(ruleNode.children[1].children) == 0 or len(ruleNode.children[2].children) == 0 or \
        ruleNode.children[1].children[0].data != 'first' or ruleNode.children[2].children[0].data != 'rest':
            return False, "Can only rewrite with cons-first-rest rule when first arg is a 'first' expression and second arg is a 'rest' expression"
        elif not isMatch(ruleNode.children[1].children[1], ruleNode.children[2].children[1]):
            return False, "Cannot rewrite with cons-first-rest rule when the arguments of 'first' and 'rest' are different lists"
        return True, "PASS"
    
    def verifyValues(self) -> tuple[bool, str]:
        if str(LNode := self._paramMappings['L']) in ("null", "'()"):
            return False, "first and rest require non-empty lists"
        if LNode.data == '(': # disallow insufficiently resolved arguments in case of null result
            return False, "Insufficiently resolved arguments"
        if isinstance(LNode.name, ERGeneric) and not LNode.name.neverNull:
            return False, "L must never be null when rewriting with cons-first-rest rule"
        return True, ''

    def insertSubstitution(self, ruleNode: Node) -> Node:
        lNode = ruleNode.children[1].children[1]
        return lNode

class FirstProp(Axiom):
    def __init__(self):
        xFinder: Axiom.ParamFinder = lambda node: (node.children[1].children[1],)
        LFinder: Axiom.ParamFinder = lambda node: (node.children[1].children[2],)
        super().__init__('first-cons', {'x': xFinder, 'L': LFinder})

    def verifyStructure(self, ruleNode: Node) -> tuple[bool, str]:
        if ruleNode.children[0].data != 'first':
            return False, f"Cannot rewrite with first-cons rule when root operation is '{ruleNode.children[0].data}'"
        elif len(ruleNode.children[1].children) == 0 or ruleNode.children[1].children[0].data != 'cons':
            return False, "Can only rewrite with first-cons rule when argument is a 'cons' expression"
        # string should not print out if debug=False
        return True, 'PASS'

    def insertSubstitution(self, ruleNode: Node) -> Node:
        xNode = ruleNode.children[1].children[1]
        return xNode

class RestProp(Axiom):
    def __init__(self):
        xFinder: Axiom.ParamFinder = lambda node: (node.children[1].children[1],)
        LFinder: Axiom.ParamFinder = lambda node: (node.children[1].children[2],)
        super().__init__('rest-cons', {'x': xFinder, 'L': LFinder})

    def verifyStructure(self, ruleNode: Node) -> tuple[bool, str]:
        if ruleNode.children[0].data != 'rest':
            return False, f"Cannot rewrite with rest-cons rule when root operation is '{ruleNode.children[0].data}'"
        elif len(ruleNode.children[1].children) == 0 or ruleNode.children[1].children[0].data != 'cons':
            return False, "Can only rewrite with rest-cons rule when argument is a 'cons' expression"
        # string should not print out if debug=False
        return True, ''

    def insertSubstitution(self, ruleNode: Node) -> Node:
        lNode = ruleNode.children[1].children[2]
        return lNode

class NullQCons(Axiom):
    def __init__(self):
        xFinder: Axiom.ParamFinder = lambda node: (node.children[1].children[1],)
        LFinder: Axiom.ParamFinder = lambda node: (node.children[1].children[2],)
        super().__init__('null?-cons', {'x': xFinder, 'L': LFinder})

    def verifyStructure(self, ruleNode: Node) -> tuple[bool, str]:
        if ruleNode.children[0].data != 'null?':
            return False, f"Cannot rewrite with null?-cons rule when root operation is '{ruleNode.children[0].data}'"
        if ruleNode.children[1].data != '(' or ruleNode.children[1].children[0].data != 'cons':
            return False, f"Cannot rewrite with null?-cons rule when argument is not a 'cons' expression"
        return True, ""

    def insertSubstitution(self, ruleNode: Node) -> Node:
        return Node(data='#f', tokenType=RacType((None, Type.BOOL)), name=False)

class ZeroQPlus(Axiom):
    def __init__(self):
        # Return a tuple containing ONE element which is a tuple of alternatives
        # The outer tuple is for the for-loop iteration, the inner tuple provides position alternatives
        aFinder: Axiom.ParamFinder = lambda node: ((node.children[1].children[1], node.children[1].children[2]),)
        kFinder: Axiom.ParamFinder = lambda node: ((node.children[1].children[1], node.children[1].children[2]),)
        super().__init__("zero?+", {'a': aFinder, 'k': kFinder})

    def verifyStructure(self, ruleNode: Node) -> tuple[bool, str]:
        if ruleNode.children[0].data != 'zero?':
            return False, f"Cannot rewrite with zero?+ rule when root operation is '{ruleNode.children[0].data}'"
        if ruleNode.children[1].data != '(' or ruleNode.children[1].children[0].data != '+':
            return False, f"Can only rewrite with zero?+ rule when argument of zero? is a '+' expression"
        return True, ""
    
    def verifyValues(self):
        if (self._paramMappings['a'].data == '(' or self._paramMappings['k'].name == '('):
            return False, "Insufficiently resolved arguments"
        if not(self._paramMappings['a'].name >= 0 and self._paramMappings['k'].name >= 0):
            return False, "Neither 'a' nor 'k' can be negative when rewriting with zero?+ rule"
        if not(self._paramMappings['a'].name != 0 or self._paramMappings['k'].name != 0):
            return False, "One of either 'a' or 'k' must be positive when rewriting with zero?+ rule"
        return True, ""

    def insertSubstitution(self, ruleNode: Node) -> Node:
        return Node(data='#f', tokenType=RacType((None, Type.BOOL)), name=False)

class MinusPlus(Axiom):
    def __init__(self):
        def aFinder(node: Node):
            if node.children[1].children[1] == node.children[2]:
                return (node.children[1].children[1], node.children[2])
            return (node.children[1].children[2], node.children[2])
        
        def kFinder(node: Node):
            if node.children[1].children[1] == node.children[2]:
                return (node.children[1].children[2],)
            return (node.children[1].children[1],)
        
        super().__init__('-+', {'a': aFinder, 'k': kFinder})

    def verifyStructure(self, ruleNode: Node) -> tuple[bool, str]:
        if not ruleNode.children or len(ruleNode.children) < 3:
            return False, 'Cannot rewrite with -+ rule when node structure is invalid'
        if ruleNode.children[0].data != '-':
            return False, f'Cannot rewrite with -+ rule when the root operation is {ruleNode.children[0].data}'
        if ruleNode.children[1].data != '(' or len(ruleNode.children[1].children) < 3 or ruleNode.children[1].children[0].data != '+':
            return False, f'Cannot rewrite with -+ rule when the first argument of - is not a + expression'
        if str(ruleNode.children[2]) not in (str(ruleNode.children[1].children[1]), str(ruleNode.children[1].children[2])):
            return False, "Cannot rewrite with -+ rule when the second argument of - doesn't match an argument of +"
        return True, ""
    
    def insertSubstitution(self, ruleNode: Node) -> Node:
        return self._paramMappings['k']

class AndProp(Axiom):
    def __init__(self):
        def pFinder(node: Node):
            if node.children[1].data == '#f':
                return (node.children[2],)
            return (node.children[1],)
        super().__init__('and', {'p': pFinder})

    def verifyStructure(self, ruleNode: Node) -> tuple[bool, str]:
        if ruleNode.children[0].data != 'and':
            return False, f"Cannot rewrite '{ruleNode.children[0].data}' expression with 'and' rule"
        if ruleNode.children[1].data != '#f' and ruleNode.children[2].data != '#f':
            return False, "Can only rewrite with 'and' rule when one argument is '#f'"
        return True, ''

    def insertSubstitution(self, ruleNode: Node) -> Node:
        return Node(data='#f', tokenType=RacType((None, Type.BOOL)), name=False)

class OrProp(Axiom):
    def __init__(self):
        def pFinder(node: Node):
            if node.children[1].data == '#t':
                return (node.children[2],)
            return (node.children[1],)
        super().__init__('and', {'p': pFinder})

    def verifyStructure(self, ruleNode: Node) -> tuple[bool, str]:
        if ruleNode.children[0].data != 'or':
            return False, f"Cannot rewrite '{ruleNode.children[0].data}' expression with 'or' rule"
        if ruleNode.children[1].data != '#t' and ruleNode.children[2].data != '#t':
            return False, "Can only rewrite with 'or' rule when one argument is '#t'"
        return True, ''

    def insertSubstitution(self, ruleNode: Node) -> Node:
        return Node(data='#t', tokenType=RacType((None, Type.BOOL)), name=True)

class ImpliesProp(Axiom):
    def __init__(self):
        def PFinder(node: Node):
            if node.children[1].data == '#f' and node.children[2].data == '#t':
                return ((node.children[1], node.children[2]),)
            if node.children[1].data == '#f':
                return (node.children[2],)
            if node.children[2].data == '#t':
                return (node.children[1],)
        super().__init__("implies", {'p': PFinder})

    def verifyStructure(self, ruleNode: Node) -> tuple[bool, str]:
        if ruleNode.children[0].data != 'implies':
            return False, f"Cannot rewrite '{ruleNode.children[0].data}' expression with 'implies' rule"
        if ruleNode.children[1].data != '#f' and ruleNode.children[2].data != '#t':
            return False, "Can only rewrite with 'implies' rule when first argument is '#f' or second argument is '#t'"
        return True, ''

    def insertSubstitution(self, ruleNode: Node) -> Node:
        return Node(data='#t', tokenType=RacType((None, Type.BOOL)), name=True)

class TypeQProp(Axiom):
    def __init__(self, label, typeToCheck: Type):
        opFinder: Axiom.ParamFinder = lambda node: (node.children[1].children[0],)
        super().__init__(label, {'op': opFinder})
        self._typeToCheck = typeToCheck

    def verifyStructure(self, ruleNode: Node) -> tuple[bool, str]:
        if ruleNode.children[0].data != self.label:
            return False, f"Cannot rewrite '{ruleNode.children[0]}' expression with '{self.label}' rule"
        if ruleNode.children[1].data != '(' or len(ruleNode.children[1].children) == 0:
            return False, f"Cannot rewrite with '{self.label}' rule when argument is not a function call"
        return True, ""
    
    def verifyValues(self) -> tuple[bool, str]:
        if self._paramMappings['op'].type.getRange().isType('ANY'):
            return False, "Cannot determine output type of 'op'"
        return True, ""
    
    def insertSubstitution(self, ruleNode: Node) -> Node:
        trueNode = Node(data='#t', tokenType=RacType((None, Type.BOOL)), name=True)
        falseNode = Node(data='#f', tokenType=RacType((None, Type.BOOL)), name=False)
        return (trueNode if ruleNode.children[1].children[0].type.getRange().isType(str(self._typeToCheck))
                else falseNode)

class IntegerQProp(TypeQProp):
    def __init__(self):
        super().__init__('integer?', Type.INT)

class ListQProp(TypeQProp):
    def __init__(self):
        super().__init__('list?', Type.LIST)

# --- helpers for AdvMath non-math abstraction ---

def _collect_node_names(node: Node, names: set) -> None:
    # harvests every string data token from the entire tree
    # so that _fresh_var can avoid generating a name that already appears
    if isinstance(node.data, str):
        names.add(node.data)
    for child in node.children:
        _collect_node_names(child, names)

def _fresh_var(used: set) -> str:
    # returns the next lowercase letter (or two-letter combo) not already in 'used'
    # and adds it to 'used' so future calls won't collide
    import string
    for c in string.ascii_lowercase:
        if c not in used:
            used.add(c)
            return c
    for c1 in string.ascii_lowercase:
        for c2 in string.ascii_lowercase:
            name = c1 + c2
            if name not in used:
                used.add(name)
                return name
    return "z_var"  # unreachable in practice

_MATH_OPS = MathSet | ARITHMETIC  # {'+','-','*','expt','quotient','remainder','=','>','<','<=','>='}
_OP_TRANSLATE = {"expt": "**", "quotient": "//", "remainder": "%", "=": "=="}

def _abstractedMathStr(node: Node, abstract_pairs: list, used_names: set) -> str:
    # Converts a node tree to a SymPy-readable infix string.
    # Non-math function calls (e.g. (length L)) are replaced wholesale with a
    # fresh placeholder variable.  Two calls that are structurally identical
    # (isMatch) share the same placeholder so SymPy sees them as the same symbol.
    # Leaf node: number, variable name, or math-operator token (+ - * etc.)
    if node.children == []:
        return node.data
    # Parenthesized application: data="(", children=[op_node, arg1, arg2]
    if node.data == "(" and len(node.children) >= 2:
        op = node.children[0].data
        if op in _MATH_OPS and len(node.children) == 3:
            # Recognized binary math operator — recurse into both operands
            op_str = _OP_TRANSLATE.get(op, op)
            left = _abstractedMathStr(node.children[1], abstract_pairs, used_names)
            right = _abstractedMathStr(node.children[2], abstract_pairs, used_names)
            if left == "ERROR" or right == "ERROR":
                return "ERROR"
            return "(" + left + op_str + right + ")"
        else:
            # Non-math call (e.g. length, cons, rest, f, …) — treat entire
            # subtree as an opaque symbol.  Reuse the same variable if we have
            # already seen a structurally identical subtree (isMatch).
            for existing_node, var_name in abstract_pairs:
                if isMatch(existing_node, node):
                    return var_name
            var_name = _fresh_var(used_names)
            abstract_pairs.append((node, var_name))
            return var_name
    return "ERROR"

# --- end helpers ---

class AdvMath(Rule):
    def __init__(self):
        super().__init__('advMath', RuleType.MATH)

# presumes buildtree checked types/qty already for main node and the subnode
# "subnode" is the exptree created by the user in the Substitution pane.
    def isApplicable(self, ruleNode: Node, subNode:Node) -> tuple[bool, str]:  # presumes buildtree checked types/qty already
        try:
            # Collect every token name from both trees so _fresh_var won't
            # collide with existing variable names like k, n, L, etc.
            used_names: set = set()
            _collect_node_names(ruleNode, used_names)
            _collect_node_names(subNode, used_names)
            # Shared list of (Node, placeholder_var) pairs — same subtree in
            # both expressions will receive the same placeholder symbol.
            abstract_pairs: list = []
            main_expr_str = _abstractedMathStr(ruleNode, abstract_pairs, used_names)
            sub_expr_str  = _abstractedMathStr(subNode,  abstract_pairs, used_names)
            if main_expr_str == "ERROR" or sub_expr_str == "ERROR":
                return False, 'Math rule: expression could not be converted for symbolic comparison'
            
            # Parse expressions with SymPy
            main_sympy = sp.sympify(main_expr_str)
            sub_sympy = sp.sympify(sub_expr_str)
            
            # Get all free symbols
            symbols = list(main_sympy.free_symbols | sub_sympy.free_symbols)
            
            # First try: check if their difference simplifies to 0 (works for most algebra)
            difference = sp.simplify(main_sympy - sub_sympy)
            if difference.equals(0):
                return True, "advMath.isApplicable() PASS"
            
            # Second try: if that failed and we have symbols, use numerical verification
            # This is necessary for floor division where SymPy can't reason about bounds symbolically
            # (e.g., floor(k/(k+1)) = 0 for positive k requires understanding that 0 < k/(k+1) < 1)
            if symbols:
                test_values = [1, 2, 3, 5, 10, 100]
                all_equiv = True
                
                # Generate test combinations for up to 2 symbols
                import itertools
                if len(symbols) == 1:
                    test_combos = [(v,) for v in test_values]
                elif len(symbols) == 2:
                    test_combos = list(itertools.product(test_values[:4], repeat=2))
                else:
                    # For 3+ symbols, use limited test combos
                    test_combos = list(itertools.product(test_values[:3], repeat=len(symbols)))
                
                for combo in test_combos:
                    try:
                        sub_dict = dict(zip(symbols, combo))
                        # Numerically evaluate both expressions with concrete values
                        main_result = main_sympy.subs(sub_dict).evalf()
                        sub_result = sub_sympy.subs(sub_dict).evalf()
                        # Convert to int to handle floor division properly
                        if int(main_result) != int(sub_result):
                            all_equiv = False
                            break
                    except:
                        # If evaluation fails, skip this combo
                        continue
                
                if all_equiv and test_combos:
                    return True, "advMath.isApplicable() PASS"
            
            return False, f"main and substitute expressions are not equivalent"
                
        except Exception as e:
            return False, f"Error checking mathematical equivalence: {str(e)}"

    # note: ERproofline.applyRule will take care of proper highlight position etc
    def insertSubstitution(self, ruleNode: Node, subNode: Node) -> Node:
        return subNode

def recursiveReplaceNodes(node: Node, params: list, values: list) -> None:
    if node.data in params:
        index = params.index(node.data)
        node.replaceWith(values[index])
        return  # no need to check children if we replaced the node
    for child in node.children:
        recursiveReplaceNodes(child, params, values)

""" #Unfinished recursive advmath for stage 1 math specification
class AdvMath(Rule):
    def __init__(self):
        super().__init__('advMath')

    def isApplicable(self, ruleNode: Node, rawParams: list[str] = None) -> tuple[bool, str]:
        if ruleNode.isArith():
            return True, "AdvMath.isApplicable() PASS"
        else:
            return False, "Cannot apply advMath rule to non-arithmetic expression" #TODO temp
        
    def insertSubstitution(self, ruleNode: Node) -> Node:
        for child in ruleNode.children:
            if Math.isApplicable(child):
                child = AdvMath().insertSubstitution(child)
        ruleNode = Math().insertSubstitution(ruleNode) """

EVAL_PROCEDURES: dict[str, BuiltIn] = {
    'if': If(),
    'null?': NullQ(),
    'zero?': ZeroQ(),
    'cons': ConsList(),
    'first': FirstList(),
    'rest': RestList(),
    'and': And(),
    'or': Or(),
    'not': Not(),
    'implies': Implies(),
    'xor': Xor(),
    '+': Plus(),
    '-': Minus(),
    '*': Times(),
    'quotient': Quotient(),
    'remainder': Remainder(),
    'expt': Expt(),
    '<': LessThan(),
    '<=': LessOrEqual(),
    '>': GreaterThan(),
    '>=': GreaterOrEqual(),
    '=': Equals(),
    'integer?': IntegerQ(),
    'list?': ListQ(),
}

REWRITE_RULES: dict[str, Rule] = {
    'and': AndProp(),
    'or': OrProp(),
    'implies': ImpliesProp(),
    'integer?': IntegerQProp(),
    'list?': ListQProp(),
    'cons-first-rest': ConsProp(),
    'first-cons': FirstProp(),
    'rest-cons': RestProp(),
    'null?-cons': NullQCons(),
    '-+': MinusPlus(),
    'zero?+': ZeroQPlus(),
    'math': AdvMath()
}

DEFAULT_RULE_SET: dict[str, dict[str, Rule]] = {
    'eval': EVAL_PROCEDURES,
    'apply': {},
    'rewrite': REWRITE_RULES
}

def getDefaultRuleSet():
    return DEFAULT_RULE_SET.copy()