from abc import ABC, abstractmethod
from .ERCommon import *
import copy
from .Parser import buildTree, preProcess
from .Labeler import labelTree  # , fillPositions
from .Decorator import decorateTree, remTemps, checkFunctions


# recursively check if two nodes are identical #TODO: replace elif chain with something prettier
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


class Rule(ABC):
    def __init__(self, label):
        self.label = label

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


class If(Rule):
    def __init__(self):
        super().__init__('if')

    def isApplicable(self, ruleNode: Node) -> tuple[bool, str]:
        if (len(ruleNode.children) != 0 and ruleNode.children[0].data != 'if'):
            return False, f'Cannot apply if rule to {ruleNode.children[0].data}'
        elif (len(ruleNode.children) != 4):
            return False, f'If rule expects 3 arguments, but received {len(ruleNode.children)}'
        elif ruleNode.children[1].data not in ['#t', '#f']:
            return False, f'Cannot determine truth value of {ruleNode.children[1]}'
        # string should not print out if debug=False
        return True, 'If.isApplicable() PASS'

    def insertSubstitution(self, ruleNode: Node) -> Node:
        condition = ruleNode.children[1]
        xNode = ruleNode.children[2]
        yNode = ruleNode.children[3]
        if condition.data == '#t' or isMatch(xNode, yNode):
            return xNode
        elif condition.data == '#f':
            return yNode


class Cons(Rule):
    def __init__(self):
        super().__init__('cons')

    def isApplicable(self, ruleNode: Node) -> tuple[bool, str]:
        if ruleNode.children[0].data != 'cons':
            return False, f'Cannot apply cons rule to {ruleNode.children[0].data}'
        elif len(ruleNode.children[1].children) == 0 or len(ruleNode.children[2].children) or \
                ruleNode.children[1].children[0].data != 'first' or ruleNode.children[2].children[0].data != 'rest':
            return False, f'Can only apply the cons rule to first and rest'
        elif not isMatch(ruleNode.children[1].children[1], ruleNode.children[2].children[1]):
            return False, f'Cannot apply cons rule on two different lists'
        # string should not print out if debug=False
        return True, 'Cons.isApplicable() PASS'

    def insertSubstitution(self, ruleNode: Node) -> Node:
        lNode = ruleNode.children[1].children[1]
        return lNode


class First(Rule):
    def __init__(self):
        super().__init__('first')

    def isApplicable(self, ruleNode: Node) -> tuple[bool, str]:
        if ruleNode.children[0].data != 'first':
            return False, f'Cannot apply first rule to {ruleNode.children[0].data}'
        elif len(ruleNode.children[1].children) == 0 or ruleNode.children[1].children[0].data != 'cons':
            return False, f'first rule can only be applied with a cons'
        # string should not print out if debug=False
        return True, 'First.isApplicable() PASS'

    def insertSubstitution(self, ruleNode: Node) -> Node:
        xNode = ruleNode.children[1].children[1]
        return xNode


class Rest(Rule):
    def __init__(self):
        super().__init__('rest')

    def isApplicable(self, ruleNode: Node) -> tuple[bool, str]:
        if ruleNode.children[0].data != 'rest':
            return False, f'Cannot apply rest rule to {ruleNode.children[0].data}'
        elif len(ruleNode.children[1].children) == 0 or ruleNode.children[1].children[0].data != 'cons':
            return False, f'rest rule can only be applied with a cons'
        # string should not print out if debug=False
        return True, 'Rest.isApplicable() PASS'

    def insertSubstitution(self, ruleNode: Node) -> Node:
        lNode = ruleNode.children[1].children[2]
        return lNode


class NullQ(Rule):
    def __init__(self):
        super().__init__('null?')

    def isApplicable(self, ruleNode: Node) -> tuple[bool, str]:
        if ruleNode.children[0].data != 'null?':
            return False, f'Cannot apply null rule to {ruleNode.children[0].data}'
        if str(ruleNode.children[1].type) not in ["LIST", "ANY", "TEMP"]:
            # check for nonlists before checking next err condition
            return True, 'NullQ.isApplicable() PASS'
        if (target := ruleNode.children[1].data) != 'null' and target != "'(":
            # (null? L) or (null? (if #t null null))
            return False, f'insufficiently resolved arguments'
        # string should not print out if debug=False
        return True, 'NullQ.isApplicable() PASS'

    def insertSubstitution(self, ruleNode: Node) -> Node:
        if not ruleNode.children[1].type.isType("LIST"):
            return Node(data='#f', tokenType=RacType((None, Type.BOOL)), name=False)
        # must check nonlists first to avoid thinking no children is a null list
        if len(ruleNode.children[1].children) == 0:
            return Node(data='#t', tokenType=RacType((None, Type.BOOL)), name=True)
        return Node(data='#f', tokenType=RacType((None, Type.BOOL)), name=False)


class ConsQ(Rule):
    def __init__(self):
        super().__init__('cons?')

    def isApplicable(self, ruleNode: Node) -> tuple[bool, str]:
        if ruleNode.children[0].data != 'cons?':
            return False, f'Cannot apply cons? rule to {ruleNode.children[0].data}'
        elif ruleNode.children[1].children[0].data != 'cons':
            return False, f'cons? can only be applied with a cons'
        # string should not print out if debug=False
        return True, 'ConsQ.isApplicable() PASS'

    def insertSubstitution(self, ruleNode: Node) -> Node:
        trueNode = Node(data='#t', tokenType=RacType(
            (None, Type.BOOL)), name=True)
        return trueNode


class ZeroQ(Rule):
    def __init__(self):
        super().__init__('zero?')

    def isApplicable(self, ruleNode: Node) -> tuple[bool, str]:
        if ruleNode.children[0].data != 'zero?':
            return False, f'Cannot apply zero rule to {ruleNode.children[0].data}'
        elif len(ruleNode.children[1].children) > 0:
            if ruleNode.children[1].children[0].data != '+':
                return False, f'zero? can only be applied with a +'
            else:
                try:
                    argOne = int(ruleNode.children[1].children[1].data)
                    argTwo = int(ruleNode.children[1].children[2].data)
                except:
                    return False, "ValueError in ZeroQ - argument(s) for + not a valid int"
        elif ruleNode.children[1].type.getType() != Type.INT:
            return False, f'zero? can only be applied to int type'
        # string should not print out if debug=False
        return True, 'ZeroQ.isApplicable() PASS'

    def insertSubstitution(self, ruleNode: Node) -> Node:
        trueNode = Node(data='#t', tokenType=RacType(
            (None, Type.BOOL)), name=True)
        falseNode = Node(data='#f', tokenType=RacType(
            (None, Type.BOOL)), name=False)
        if ruleNode.children[1].children == [] and ruleNode.children[1].type.getType() == Type.INT:
            return trueNode if ruleNode.children[1].data == '0' else falseNode

        argOne = int(ruleNode.children[1].children[1].data)
        argTwo = int(ruleNode.children[1].children[2].data)
        return trueNode if (argOne >= 0 and argTwo >= 0) or (argOne + argTwo > 0) else falseNode


class ConsList(Rule):
    def __init__(self):
        super().__init__('consList')

    def isApplicable(self, ruleNode: Node) -> tuple[bool, str]:
        if ruleNode.data != "(":
            return False, "must select entire expression to apply consList rule"
        elif len(ruleNode.children) == 0 or ruleNode.children[0].data != 'cons':
            return False, 'operator must be cons to apply consList rule'
        # NOTE: this case should have been caught earlier in buildtree, but just to be safe
        elif num := (len(ruleNode.children)) != 3:
            return False, f'cons expects 2 arguments, but you provided {num-1}'
        elif (ruleNode.children[1].data) == "(":
            return False, 'insufficiently resolved first argument'
        elif (ruleNode.children[2].data) not in ("null", "'("):
            return False, 'insufficiently resolved second argument, which must be a list'
        # string should not print out if debug=False
        return True, "ConsList.isApplicable() PASS"

    def insertSubstitution(self, ruleNode: Node) -> Node:
        if ruleNode.children[2].data == "null":
            # changing null to '( to make consistent case handling
            ruleNode.children[2].data = "'("
        # at this point the second argument is definitely '( although possibly with no children/entries
        # need to get rid of the object's quote to avoid nesting quotes
        if ruleNode.children[1].data == "'(":
            if len(ruleNode.children[1].children) == 0:
                newtype = RacType((None, Type.LIST))  # consing a '()
            else:
                newtype = ruleNode.children[1].children[0].type
                if newtype.getType() == Type.FUNCTION:
                    # changing the type of the paren to be the output type of the operand
                    newtype = newtype.getRange()
            parenNode = Node(
                children=ruleNode.children[1].children, data="(", tokenType=newtype, parent=ruleNode.children[1])
            for ch in ruleNode.children[1].children:
                ch.parent = parenNode  # changing the parent of the children to the new node
            # replacing the old children with the new node
            ruleNode.children[1].children = [parenNode]
            # this will be the node used for replacement
            lNode = ruleNode.children[1]
            lNode.children.extend(ruleNode.children[2].children)
        else:  # consObj is a nonquoted object
            lNode = Node(children=[ruleNode.children[1]], data="'(", tokenType=RacType(
                (None, Type.LIST)))  # length=len(self.children[2].children)+1)
            lNode.children.extend(ruleNode.children[2].children)
            for child in lNode.children:
                child.parent = lNode
        return lNode

# TODO: this needs to be generalized to use a python math library and normal forms, and not just the 4 basic operations


class Math(Rule):
    def __init__(self):
        super().__init__('math')

    def __init__(self):
        self.mathSymbols = ARITHMETIC + \
            ["expt", "<=", ">=", "quotient", "remainder"]
        self.mathDict = {"+": lambda x, y: x+y, "-": lambda x, y: x-y, "*": lambda x, y: x*y, "expt": lambda x, y: x**y, "=": lambda x, y: x == y, ">": lambda x, y: x > y,
                         ">=": lambda x, y: x >= y, "<": lambda x, y: x < y, "<=": lambda x, y: x <= y, "quotient": lambda x, y: x//y, "remainder": lambda x, y: x % y}

    def isApplicable(self, ruleNode: Node) -> tuple[bool, str]:
        # note: no need to check argument types or number of arguments, since that is done in buildTree
        if (len(ruleNode.children) != 0 and ruleNode.children[0].data not in self.mathSymbols):
            return False, f'Cannot apply math rule to {ruleNode.children[0].data}'
        # checking for (+ 1 (+ 2 3)) type errors
        elif len(ruleNode.children[1].children) != 0 or len(ruleNode.children[2].children) != 0:
            return False, "insufficiently resolved arguments"

        argOne = ruleNode.children[1].name
        argTwo = ruleNode.children[2].name

        if (ruleNode.children[0].data == "remainder" or ruleNode.children[0].data == "quotient") and argTwo == 0:
            return False, "denominator can't be zero"
        # note: currently PB has no negatives anyway!
        elif ruleNode.children[0].data == "expt" and argOne*argOne != 1 and argTwo < 0:
            return False, "expt with negative arguments results in non-integer output"
        elif ruleNode.children[0].data == "expt" and argOne == 0 and argTwo == 0:
            return False, "0^0 is undefined"
        # string should not print out if debug=False
        return True, "Math.isApplicable() PASS"

    def insertSubstitution(self, ruleNode: Node) -> Node:
        argOne = ruleNode.children[1].name
        argTwo = ruleNode.children[2].name
        newname = self.mathDict[ruleNode.children[0].data](
            argOne, argTwo)  # compute the result
        if isinstance(newname, bool):
            newdata = "#t" if newname else "#f"  # convert to racket bool
            newtype = RacType((None, Type.BOOL))
        else:
            newdata = str(newname)
            newtype = RacType((None, Type.INT))
        # converting node
        return Node(data=newdata, tokenType=newtype, name=newname)


class Logic(Rule):
    def __init__(self):
        super().__init__('logic')

    def __init__(self):
        self.logicDict = {"and": lambda x, y: x and y, "or": lambda x, y: x or y, "not": lambda x, y: not x, "xor": lambda x, y: (x or y) and not (x and y),
                          # not set up for "iff":lambda x,y: x==y, "nor":lambda x,y: not(x or y), "nand":lambda x,y: not(x and y)
                          "implies": lambda x, y: (not x) or y}
    # note: no need to check argument types or number of arguments, since that is done in buildTree

    def isApplicable(self, ruleNode: Node) -> tuple[bool, str]:
        if (len(ruleNode.children) != 0 and ruleNode.children[0].data not in self.logicDict.keys()):
            return False, f'Cannot apply logic rule to {ruleNode.children[0].data}'
        elif len(ruleNode.children[1:]) < 2 and ruleNode.children[0].data != "not":
            return False, f'Not enough arguments provided to {ruleNode.children[0].data}'
        # checking for (or (not #t) #t) type errors
        elif len(ruleNode.children[1].children) != 0 or (ruleNode.children[0].data != "not" and len(ruleNode.children[2].children) != 0):
            return False, "insufficiently resolved arguments"
        # string should not print out if debug=False
        return True, "Logic.isApplicable() PASS"

    def insertSubstitution(self, ruleNode: Node) -> Node:
        argOne = ruleNode.children[1].name
        # y=True isn't used for "not" lambda operation, 2 params for consistency
        argTwo = (True if ruleNode.children[0].data ==
                  "not" else ruleNode.children[2].name)
        newname = self.logicDict[ruleNode.children[0].data](argOne, argTwo)
        newdata = "#t" if newname else "#f"  # convert to racket bool
        newtype = RacType((None, Type.BOOL))
        # converting node
        return Node(data=newdata, tokenType=newtype, name=newname)


class UDF(Rule):
    def __init__(self, label, filledBodyNode, racTypeObj, paramsList):
        super().__init__(label)
        self.body = filledBodyNode
        self.racType = racTypeObj
        self.params = paramsList

    def isApplicable(self, ruleNode: Node) -> tuple[bool, str]:
        if ruleNode.children[0].data != self.label:
            return False, f'Cannot apply {self.label} definition to {ruleNode.children[0].data}'
        if len(ruleNode.children[1:]) != len(self.racType.getDomain()):
            return False, f"{self.label} must take {len(self.racType.getDomain())} inputs"
        ruleNodeRange = [c.type.getRange() for c in ruleNode.children[1:]]
        if not all(x == y for x, y in zip(ruleNodeRange, self.racType.getDomain())):
            return False, f'Cannot match argument out typeList {[str(x) for x in ruleNodeRange]} with expected typeList {[str(x) for x in self.racType.getDomain()]}'
        # string should not print out if debug=False
        return True, f"{self.label.capitalize()}.isApplicable() PASS"

    def insertSubstitution(self, ruleNode: Node) -> Node:
        expCopy = copy.deepcopy(self.body)
        recursiveReplaceNodes(expCopy, self.params, ruleNode.children[1:])
        return expCopy


class RestList(Rule):
    def __init__(self):
        super().__init__('restList')

    # presumes buildtree checked types/qty already
    def isApplicable(self, ruleNode: Node) -> tuple[bool, str]:
        if ruleNode.data != "(" or len(ruleNode.children) != 2 or ruleNode.children[0].data != "rest":
            return False, f'restList rule requires calling rest function'
        # this handles (rest null), (rest '()) :
        if len(ruleNode.children[1].children) == 0:
            return False, f'restList rule requires nonempty list'
        if ruleNode.children[1].data != "'(":
            # null case already handled. e.g. (rest L)
            return False, f'restList rule requires explicit list'
        return True, "RestList.isApplicable() PASS"

    def insertSubstitution(self, ruleNode: Node) -> Node:
        origList = ruleNode.children[1]
        if (n := len(origList.children)) == 1:
            return Node(data="null", tokenType=RacType((None, Type.LIST)), name=[])
        newNode = Node(data="'(", tokenType=RacType((None, Type.LIST)),
                       name=origList.name[1:] if isinstance(oname := origList.name, list) and
                       len(oname) > 0 else None, length=n-1)
        for ind in range(1, n):  # shift all elements left
            newNode.children.append(origList.children[ind])
        return newNode  # could have just returned in place by removing first element


class FirstList(Rule):
    def __init__(self):
        super().__init__('firstList')

    # presumes buildtree checked types/qty already
    def isApplicable(self, ruleNode: Node) -> tuple[bool, str]:
        if ruleNode.data != "(" or len(ruleNode.children) != 2 or ruleNode.children[0].data != "first":
            return False, f'firstList rule requires calling rest function'
        # this handles (rest null), (rest '()) :
        if len(ruleNode.children[1].children) == 0:
            return False, f'firstList rule requires nonempty list'
        if ruleNode.children[1].data != "'(":
            # null case already handled. e.g. (rest L)
            return False, f'firstList rule requires explicit list'
        return True, "RestList.isApplicable() PASS"

    def insertSubstitution(self, ruleNode: Node) -> Node:
        origList = copy.deepcopy(ruleNode.children[1])
        if origList.children[0].data == "(":
            origList.children[0].data = "'("
        return origList.children[0]


def recursiveReplaceNodes(node: Node, params: list, values: list) -> None:
    if node.data in params:
        index = params.index(node.data)
        node.replaceWith(values[index])
    for child in node.children:
        recursiveReplaceNodes(child, params, values)

# Placeholder function to fake UDF for demo


class DoubleFront(Rule):
    def __init__(self):
        super().__init__('doubleFront')

    # since this isn't built-in, buildtree might not do the type checking, so doing it here
    def isApplicable(self, ruleNode: Node) -> tuple[bool, str]:
        if ruleNode.data != "(" or len(ruleNode.children) != 3 or ruleNode.children[0].data != "doubleFront":
            return False, f'must apply the doubleFront definition to a doubleFront function call of 2 arguments'
        if not (ruleNode.children[1].type.isType("INT") and ruleNode.children[2].type.isType("LIST")):
            return False, f'doubleFront takes [INT,LIST] but received {[str(ruleNode.children[1].type), str(ruleNode.children[2].type)]}'
        return True, "DoubleFront.isApplicable() PASS"

    def insertSubstitution(self, ruleNode: Node) -> Node:
        defStr = "(if (or (zero? n) (null? L)) L (cons (* 2 (first L)) (doubleFront (- n 1) (rest L))))"
        decTree = decorateTree(
            labelTree(buildTree(preProcess(defStr, [])[0],)[0]), [])[0]
        # this might crash if it hasn't been updated
        errLog = remTemps(decTree, [])
        newNode = checkFunctions(decTree, errLog)[0]
        recursiveReplaceNodes(newNode, ["n", "L"], [
                              ruleNode.children[1], ruleNode.children[2]])
        return newNode  # could have just returned in place by removing first element