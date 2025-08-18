from abc import ABC, abstractmethod
from .ERCommon import *
from .ERGenerics import ERGeneric, GenericInt, GenericList, GenericBool, GenericAny
import copy
from .Parser import buildTree, preProcess
from .Labeler import labelTree  # , fillPositions
from typing import Dict
import sympy as sp

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
    sofar = True
    for i in range(len(xNode.children)):  # defaults to True if no children since no loop
        # if any are false, sofar will be false
        sofar &= isMatch(xNode.children[i], yNode.children[i])
    return sofar

# TODO: modify rules to support generics
class Rule(ABC):
    def __init__(self, label, isProperty=False):
        self.label = label
        self.isProperty = isProperty

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, newLabel):
        self._label = newLabel

    @abstractmethod
    def isApplicable(self, ruleNode: Node) -> tuple[bool, str]:
        pass

    @abstractmethod
    def insertSubstitution(self, ruleNode: Node) -> Node:
        pass

class BuiltIn(Rule, ABC):
    def __init__(self, label, allowGenerics=False):
        super().__init__(label)
        self._allowGenerics = allowGenerics

    def isApplicable(self, ruleNode: Node) -> tuple[bool, str]:
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

    def isApplicable(self, ruleNode: Node) -> tuple[bool, str]:
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

    def isApplicable(self, ruleNode: Node) -> tuple[bool, str]:
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

    def isApplicable(self, ruleNode: Node) -> tuple[bool, str]:
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

    def isApplicable(self, ruleNode: Node) -> tuple[bool, str]:
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

    def isApplicable(self, ruleNode: Node) -> tuple[bool, str]:  # presumes buildtree checked types/qty already
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

    def isApplicable(self, ruleNode: Node) -> tuple[bool, str]:  # presumes buildtree checked types/qty already
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
    
# NOTE: for both integer? and list? expressions, 
# when the argument is of type ANY, it currently evaluates to #f
class IntegerQ(BuiltIn):
    def __init__(self):
        super().__init__('integer?', allowGenerics=True)
    
    def insertSubstitution(self, ruleNode: Node) -> Node:
        trueNode = Node(data='#t', tokenType=RacType((None, Type.BOOL)), name=True)
        falseNode = Node(data='#f', tokenType=RacType((None, Type.BOOL)), name=False)
        return trueNode if ruleNode.children[1].type.getType() == Type.INT else falseNode
    
class ListQ(BuiltIn):
    def __init__(self):
        super().__init__('list?', allowGenerics=True)
    
    def insertSubstitution(self, ruleNode: Node) -> Node:
        trueNode = Node(data='#t', tokenType=RacType((None, Type.BOOL)), name=True)
        falseNode = Node(data='#f', tokenType=RacType((None, Type.BOOL)), name=False)
        return trueNode if ruleNode.children[1].type.getType() == Type.LIST else falseNode

# TODO: this needs to be generalized to use a python math library and normal forms, and not just the 4 basic operations
'''
class Math(Rule):
    def __init__(self):
        super().__init__('math')

    def __init__(self):
        self.mathSymbols = ARITHMETIC+["expt", "<=",">=","quotient","remainder"]
        self.mathDict = {"+":lambda x,y: x+y, "-":lambda x,y: x-y, "*":lambda x,y: x*y, "expt":lambda x,y: x**y, "=":lambda x,y: x ==y, ">":lambda x,y: x>y, \
                  ">=":lambda x,y: x >=y, "<":lambda x,y: x<y, "<=":lambda x,y: x<=y, "quotient":lambda x,y: x//y, "remainder":lambda x,y: x%y}

    def isApplicable(self, ruleNode: Node) -> tuple[bool, str]:
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
    
    def isApplicable(self, ruleNode: Node) -> tuple[bool, str]:
        parentPassed, parentMessage = super().isApplicable(ruleNode)
        if not parentPassed:
            return False, parentMessage
        if int(ruleNode.children[-1].data) == 0:
            return False, "denominator can't be zero"
        return True, 'Quotient.isApplicable() PASS'

class Remainder(Math):
    def __init__(self):
        super().__init__('remainder')
    
    def isApplicable(self, ruleNode: Node) -> tuple[bool, str]:
        parentPassed, parentMessage = super().isApplicable(ruleNode)
        if not parentPassed:
            return False, parentMessage
        if int(ruleNode.children[-1].data) == 0:
            return False, "denominator can't be zero"
        return True, 'Remainder.isApplicable() PASS'

class Expt(Math):
    def __init__(self):
        super().__init__('expt')
    
    def isApplicable(self, ruleNode: Node) -> tuple[bool, str]:
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

    def isApplicable(self, ruleNode: Node) -> tuple[bool, str]:
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
        super().__init__(label)
        self.body = filledBodyNode
        self.racType = racTypeObj
        self.params = paramsList

    def isApplicable(self, ruleNode: Node) -> tuple[bool, str]:
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

class ConsProp(Rule):
    def __init__(self):
        super().__init__('cons-first-rest', isProperty=True)
        self.params = ['x', 'L']
        self.racType = str2Type("(ANY, LIST)>ANY")

    def isApplicable(self, ruleNode: Node) -> tuple[bool, str]:
        if ruleNode.children[0].data != 'cons':
            return False, f"Cannot apply cons-first-rest property to a '{ruleNode.children[0].data}' expression"
        elif len(ruleNode.children[1].children) == 0 or len(ruleNode.children[2].children) == 0 or \
        ruleNode.children[1].children[0].data != 'first' or ruleNode.children[2].children[0].data != 'rest':
            return False, "Can only apply cons-first-rest property when first arg is a 'first' expression and second arg is a 'rest' expression"
        elif ruleNode.children[1].children[1].data == 'null':
            return False, "first requires non-empty list"
        elif ruleNode.children[2].children[1].data == 'null':
            return False, "rest requires non-empty list"
        elif not isMatch(ruleNode.children[1].children[1], ruleNode.children[2].children[1]):
            return False, f'Cannot apply cons-first-rest property on two different lists'
        # string should not print out if debug=False
        return True, 'Cons.isApplicable() PASS'

    def insertSubstitution(self, ruleNode: Node) -> Node:
        lNode = ruleNode.children[1].children[1]
        return lNode

class FirstProp(Rule):
    def __init__(self):
        super().__init__('first-cons', isProperty=True)
        self.params = ['L']
        self.racType = str2Type("LIST>ANY")

    def isApplicable(self, ruleNode: Node) -> tuple[bool, str]:
        if ruleNode.children[0].data != 'first':
            return False, f"Cannot apply first-cons property to a '{ruleNode.children[0].data}' expression"
        elif len(ruleNode.children[1].children) == 0 or ruleNode.children[1].children[0].data != 'cons':
            return False, "Can only apply first-cons property when argument is a 'cons' expression"
        # string should not print out if debug=False
        return True, 'First.isApplicable() PASS'

    def insertSubstitution(self, ruleNode: Node) -> Node:
        xNode = ruleNode.children[1].children[1]
        return xNode

class RestProp(Rule):
    def __init__(self):
        super().__init__('rest-cons', isProperty=True)
        self.params = ['L']
        self.racType = str2Type("LIST>ANY")

    def isApplicable(self, ruleNode: Node) -> tuple[bool, str]:
        if ruleNode.children[0].data != 'rest':
            return False, f"Cannot apply rest-cons property to a '{ruleNode.children[0].data}' expression"
        elif len(ruleNode.children[1].children) == 0 or ruleNode.children[1].children[0].data != 'cons':
            return False, "Can only apply rest-cons property when argument is a 'cons' expression"
        # string should not print out if debug=False
        return True, 'Rest.isApplicable() PASS'

    def insertSubstitution(self, ruleNode: Node) -> Node:
        lNode = ruleNode.children[1].children[2]
        return lNode

class NullQCons(Rule):
    def __init__(self):
        super().__init__('null?-cons', isProperty=True)
        self.params = ['L']
        self.racType = str2Type("LIST>BOOL")

    def isApplicable(self, ruleNode: Node) -> tuple[bool, str]:
        if ruleNode.children[0].data != 'null?':
            return False, f"Cannot apply null?-cons property when root operation is '{ruleNode.children[0].data}'"
        if ruleNode.children[1].data != '(' or ruleNode.children[1].children[0].data != 'cons':
            return False, f"Cannot apply null?-cons property when argument is not a 'cons' expression"
        return True, "NullQCons.isApplicable() PASS"

    def insertSubstitution(self, ruleNode: Node) -> Node:
        return Node(data='#f', tokenType=RacType((None, Type.BOOL)), name=False)

class ZeroQPlus(Rule):
    def __init__(self):
        super().__init__("zero?+", isProperty=True)
        self.params = ['x']
        self.racType = str2Type("INT>BOOL")

    def isApplicable(self, ruleNode: Node) -> tuple[bool, str]:
        if ruleNode.children[0].data != 'zero?':
            return False, f"Cannot apply zero?+ property when root operation is '{ruleNode.children[0].data}'"
        if ruleNode.children[1].data != '(' or ruleNode.children[1].children[0].data != '+':
            return False, f"Can only apply zero?+ property when argument of zero? is a '+' expression"
        plusArgs = [child.name for child in ruleNode.children[1].children[1:]]
        if not(plusArgs[0] >= 0) or not(plusArgs[1] >= 0)  or not(plusArgs[0] != 0 or plusArgs[1] != 0):
            return False, 'Can only apply zero?+ property when one argument of + is positive and the other is nonnegative'

        return True, "ZeroQPlus.isApplicable() PASS"

    def insertSubstitution(self, ruleNode: Node) -> Node:
        return Node(data='#f', tokenType=RacType((None, Type.BOOL)), name=False)

class MinusPlus(Rule):
    def __init__(self):
        super().__init__('-+', isProperty=True)
        self.params = ['x', 'y']
        self.racType = str2Type("(INT,INT)>INT")

    def isApplicable(self, ruleNode: Node) -> tuple[bool, str]:
        if ruleNode.children[0] != '-':
            return False, f'Cannot apply -+ when the root operation is {ruleNode.children[0]}'
        if ruleNode.children[1].data != '(' or ruleNode.children[1].children[0].data != '+':
            return False, f'Cannot apply -+ when the first argument of - is not a + expression'
        if ruleNode.children[2].data == '(' or ruleNode.children[1].children[2].data == '(':
            return False, 'Insufficiently resolved arguments'
        if ruleNode.children[2].data != ruleNode.children[1].children[2].data:
            return False, "Cannot apply -+ when the second argument of - doesn't match the second argument of +"
        return True, "MinusPlus.isApplicable() PASS"
    
    def insertSubstitution(self, ruleNode: Node) -> Node:
        return ruleNode.children[1].children[1]

class AndProp(Rule):
    def __init__(self):
        super().__init__("and", isProperty=True)
        self.params = ['x', 'y']
        self.racType = str2Type("(BOOL,BOOL)>BOOL")

    def isApplicable(self, ruleNode: Node) -> tuple[bool, str]:
        if ruleNode.children[0].data != 'and':
            return False, f"Cannot rewrite 'and' property on a '{ruleNode.children[0].data}' expression"
        if ruleNode.children[1].data != '#f' and ruleNode.children[2].data != '#f':
            return False, "Can only rewrite 'and' property when one argument is '#f'"
        if ruleNode.children[1].data == '#f' and ruleNode.children[2].data == '#f':
            return False, "Cannot rewrite 'and' property when both arguments are '#f'"
        return True, 'AndProp.isApplicable() PASS'

    def insertSubstitution(self, ruleNode: Node) -> Node:
        return Node(data='#f', tokenType=RacType((None, Type.BOOL)), name=False)


class OrProp(Rule):
    def __init__(self):
        super().__init__("or", isProperty=True)
        self.params = ['x', 'y']
        self.racType = str2Type("(BOOL,BOOL)>BOOL")

    def isApplicable(self, ruleNode: Node) -> tuple[bool, str]:
        if ruleNode.children[0].data != 'or':
            return False, f"Cannot rewrite 'or' property on a '{ruleNode.children[0].data}' expression"
        if ruleNode.children[1].data != '#t' and ruleNode.children[2].data != '#t':
            return False, "Can only rewrite 'or' property when one argument is '#t'"
        if ruleNode.children[1].data == '#t' and ruleNode.children[2].data == '#t':
            return False, "Cannot rewrite 'or' property when both arguments are '#t'"
        return True, 'OrProp.isApplicable() PASS'

    def insertSubstitution(self, ruleNode: Node) -> Node:
        return Node(data='#t', tokenType=RacType((None, Type.BOOL)), name=False)


class ImpliesProp(Rule):
    def __init__(self):
        super().__init__("implies", isProperty=True)
        self.params = ['x', 'y']
        self.racType = str2Type("(BOOL,BOOL)>BOOL")

    def isApplicable(self, ruleNode: Node) -> tuple[bool, str]:
        if ruleNode.children[0].data != 'implies':
            return False, f"Cannot rewrite 'implies' property on a '{ruleNode.children[0].data}' expression"
        if ruleNode.children[1].data != '#f':
            return False, "Can only rewrite 'implies' property when first argument is '#f'"
        return True, 'ImpliesProp.isApplicable() PASS'

    def insertSubstitution(self, ruleNode: Node) -> Node:
        return Node(data='#t', tokenType=RacType((None, Type.BOOL)), name=True)

class TypeQProp(Rule):
    def __init__(self, label, typeStr):
        super().__init__(label, isProperty=True)
        self.params = ['op']
        self.racType = str2Type("ANY>BOOL")
        self.typeStr = typeStr

    def isApplicable(self, ruleNode: Node) -> tuple[bool, str]:
        if ruleNode.children[0].data != self.label:
            return False, f"Cannot rewrite '{ruleNode.children[0]}' expression with '{self.label}' rule"
        if ruleNode.children[1].data != '(' or len(ruleNode.children[1].children) == 0:
            return False, f"Cannot apply '{self.label}' rewrite when argument is not a function call"
        if ruleNode.children[1].children[0].data in ('cons', 'if'):
            return False, "Cannot determine output type of argument operation"
        return True, "TypeQProp.isApplicable() PASS"
    
    def insertSubstitution(self, ruleNode: Node) -> Node:
        trueNode = Node(data='#t', tokenType=RacType((None, Type.BOOL)), name=True)
        falseNode = Node(data='#f', tokenType=RacType((None, Type.BOOL)), name=False)
        return trueNode if ruleNode.children[1].children[0].type.getRange().isType(self.typeStr) else falseNode

class IntegerQProp(TypeQProp):
    def __init__(self):
        super().__init__('integer?', 'INT')

class ListQProp(TypeQProp):
    def __init__(self):
        super().__init__('list?', 'LIST')

class advMath(Rule):
    
    def __init__(self):
        super().__init__('advMath', isProperty=True)

# presumes buildtree checked types/qty already for main node and the subnode
# "subnode" is the exptree created by the user in the Substitution pane.
    def isApplicable(self, ruleNode: Node, subNode:Node) -> tuple[bool, str]:  # presumes buildtree checked types/qty already
        for node in [ruleNode, subNode]:
            if not node.allMath():
                return False, f'Math rule requires only math functions, but {"main" if node==ruleNode else "substitute"} expression had {node.funcSet()-set(["+","-","*","expt", "quotient","remainder"])}'
        if not sp.sympify(ruleNode.mathStr()).equals(sp.sympify(subNode.mathStr())):
            return False, f"main and substitute expressions are not equivalent"
        return True, "advMath.isApplicable() PASS"

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

    def isApplicable(self, ruleNode: Node) -> tuple[bool, str]:
        if ruleNode.isArith():
            return True, "AdvMath.isApplicable() PASS"
        else:
            return False, "Cannot apply advMath rule to non-arithmetic expression" #TODO temp
        
    def insertSubstitution(self, ruleNode: Node) -> Node:
        for child in ruleNode.children:
            if Math.isApplicable(child):
                child = AdvMath().insertSubstitution(child)
        ruleNode = Math().insertSubstitution(ruleNode) """