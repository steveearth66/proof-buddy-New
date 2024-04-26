from abc import ABC, abstractmethod
from .ERCommon import Node
from ERCommon import *
def isMatch(xNode:Node, yNode:Node)->bool: #recursively check if two nodes are identical #TODO: replace elif chain with something prettier
    if xNode.data != yNode.data or \
       xNode.name != yNode.name or \
       xNode.numArgs != yNode.numArgs or \
       xNode.length != yNode.length or \
       xNode.type != yNode.type or \
       len(xNode.children) != len(yNode.children):
        return False
    elif len(xNode.children) != 0:
        checker = False
        for i in range(len(xNode.children)):
            if isMatch(xNode.children[i], yNode.children[i]):
                checker = True
        return checker
    else:
        return True

class Rule(ABC):
    @abstractmethod
    def isApplicable(ruleNode: Node) -> tuple[bool,str]:
        pass

    @abstractmethod
    def insertSubstitution(ruleNode: Node)-> Node:
        pass

class If(Rule):
    def isApplicable(ruleNode) -> tuple[bool,str]:
        if (len(ruleNode.children) != 0 and ruleNode.children[0].data != 'if'):
            return False, f'Cannot apply if rule to {ruleNode.children[0].data}'
        elif (len(ruleNode.children) != 4):
            return False, f'If rule expects 4 arguments, but received {len(ruleNode.children)}'
        return True, 'If.isApplicable() PASS' # string should not print out if debug=False
    
    def insertSubstitution(ruleNode: Node) -> Node:
        condition = ruleNode.children[1]
        xNode = ruleNode.children[2]
        yNode = ruleNode.children[3]
        if condition.data == '#t' or isMatch(xNode, yNode):
            return xNode
        elif condition.data == '#f':
            return yNode

class Cons(Rule):
    def isApplicable(ruleNode) -> tuple[bool,str]:
        if ruleNode.children[0].data != 'cons':
            return False, f'Cannot apply cons rule to {ruleNode.children[0].data}'
        elif len(ruleNode.children[1].children) == 0 or len(ruleNode.children[2].children) or \
             ruleNode.children[1].children[0].data != 'first' or ruleNode.children[2].children[0].data != 'rest':
            return False, f'Can only apply the cons rule to first and rest'
        elif not isMatch(ruleNode.children[1].children[1], ruleNode.children[2].children[1]):
            return False, f'Cannot apply cons rule on two different lists'
        return True, 'Cons.isApplicable() PASS' # string should not print out if debug=False
    
    def insertSubstitution(ruleNode: Node)-> Node:
        lNode = ruleNode.children[1].children[1]
        return lNode

class First(Rule):
    def isApplicable(ruleNode) -> tuple[bool,str]:
        if ruleNode.children[0].data != 'first':
            return False, f'Cannot apply first rule to {ruleNode.children[0].data}'
        elif len(ruleNode.children[1].children[0]) == 0 or ruleNode.children[1].children[0].data != 'cons':
            return False, f'first can only be applied to the cons rule'
        return True, 'First.isApplicable() PASS' # string should not print out if debug=False
    
    def insertSubstitution(ruleNode: Node)-> Node:
        xNode = ruleNode.children[1].children[1]
        return xNode

class Rest(Rule):
    def isApplicable(ruleNode) -> tuple[bool,str]:
        if ruleNode.children[0].data != 'rest':
            return False, f'Cannot apply rest rule to {ruleNode.children[0].data}'
        elif len(ruleNode.children[1].children[0]) == 0 or ruleNode.children[1].children[0].data != 'cons':
            return False, f'rest can only be applied to the cons rule'
        return True, 'Rest.isApplicable() PASS' # string should not print out if debug=False
    
    def insertSubstitution(ruleNode: Node)-> Node:
        lNode = ruleNode.children[1].children[2]
        return lNode
    
class NullQ(Rule):
    def isApplicable(ruleNode) -> tuple[bool,str]:
        if ruleNode.children[0].data != 'null?':
            return False, f'Cannot apply null rule to {ruleNode.children[0].data}'
        elif ruleNode.children[1].children[0].data != 'cons':
            return False, f'null can only be applied to the cons rule'
        return True, 'NullQ.isApplicable() PASS' # string should not print out if debug=False
    
    def insertSubstitution(ruleNode: Node)-> Node:
        falseNode = Node(data='#f', tokenType=RacType((None, Type.BOOL)), name=False)
        return falseNode
    
class ConsQ(Rule):
    def isApplicable(ruleNode) -> tuple[bool,str]:
        if ruleNode.children[0].data != 'cons?':
            return False, f'Cannot apply cons? rule to {ruleNode.children[0].data}'
        elif ruleNode.children[1].children[0].data != 'cons':
            return False, f'cons? can only be applied to the cons rule'
        return True, 'ConsQ.isApplicable() PASS' # string should not print out if debug=False
    
    def insertSubstitution(ruleNode: Node)-> Node:
        trueNode = Node(data='#t', tokenType=RacType((None, Type.BOOL)), name=True)
        return trueNode
    
class ZeroQ(Rule):
    def isApplicable(ruleNode) -> tuple[bool,str]:
        if ruleNode.children[0].data != 'zero?':
            return False, f'Cannot apply zero rule to {ruleNode.children[0].data}'
        elif ruleNode.children[1].children==[] and ruleNode.children[1].type.getType() != Type.INT:
            return False, f'zero? can only be applied to int type'
        elif ruleNode.children[1].children[0].data != '+':
            return False, f'zero? can only be applied to addition rule'
        else:
            try:
                argOne = int(ruleNode.children[1].children[1].data)
                argTwo = int(ruleNode.children[1].children[2].data)
            except:
                return False, "ValueError in ZeroQ - argument(s) for + not a valid int"
        return True, 'ZeroQ.isApplicable() PASS' # string should not print out if debug=False
    
    def insertSubstitution(ruleNode: Node)-> Node:
        if ruleNode.children[1].children==[] and ruleNode.children[1].type.getType() == Type.INT:
            if ruleNode.children[1].data == '0':
                trueNode = Node(data='#t', tokenType=RacType((None, Type.BOOL)), name=True)
                return trueNode
            else:
                falseNode = Node(data='#f', tokenType=RacType((None, Type.BOOL)), name=False)
                return falseNode
        argOne = int(ruleNode.children[1].children[1].data)
        argTwo = int(ruleNode.children[1].children[2].data)
        if (argOne >=0 and argTwo >= 0) and (argOne > 0 or argTwo > 0):
            falseNode = Node(data='#f', tokenType=RacType((None, Type.BOOL)), name=False)
            return falseNode


class ConsList(Rule):
    def isApplicable(ruleNode: Node) -> tuple[bool, str]:
        if ruleNode.data != "(":
            return False, "must select entire expression to apply consList rule"
        elif len(ruleNode.children) == 0 or ruleNode.children[0].data != 'cons':
            return False, 'operator must be cons to apply consList rule'
        elif num:=(len(ruleNode.children)) != 3: #NOTE: this case should have been caught earlier in buildtree, but just to be safe
            return False, f'cons expects 2 arguments, but you provided {num-1}'
        elif (ruleNode.children[1].data)=="(":
            return False, 'insufficiently resolved first argument'
        elif (ruleNode.children[2].data) not in ("null","'("):
            return False, 'insufficiently resolved second argument, which must be a list'
        
    def insertSubstitution(ruleNode: Node) -> Node:
        if ruleNode.children[2].data=="null":
            ruleNode.children[2].data = "'(" #changing null to '( to make consistent case handling
        # at this point the second argument is definitely '( although possibly with no children/entries
        if ruleNode.children[1].data =="'(": #need to get rid of the object's quote to avoid nesting quotes
            if len(ruleNode.children[1].children) == 0:
                newtype = RacType((None, Type.LIST)) # consing a '()
            else:
                newtype=ruleNode.children[1].children[0].type
                if newtype.getType() == Type.FUNCTION:
                    newtype = newtype.getRange() #changing the type of the paren to be the output type of the operand
            parenNode = Node(children=ruleNode.children[1].children, data="(", tokenType=newtype, parent=ruleNode.children[1])
            for ch in ruleNode.children[1].children:
                ch.parent = parenNode #changing the parent of the children to the new node
            ruleNode.children[1].children = [parenNode] #replacing the old children with the new node
            lNode = ruleNode.children[1] #this will be the node used for replacement
            lNode.children.extend(ruleNode.children[2].children)
        else: #consObj is a nonquoted object
            lNode = Node(children=[ruleNode.children[1]], data="'(", tokenType=RacType((None, Type.LIST))) #length=len(self.children[2].children)+1)
            lNode.children.extend(ruleNode.children[2].children)
            for child in lNode.children:
                child.parent = lNode 
        return lNode

