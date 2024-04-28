from typing import Union, Tuple, List
from enum import Enum

ARITHMETIC = ["+","*","-","=",">","<"] # any other math uses ascii, such as expt, quotient, remainder. Note: "/" not permitted

class Type(Enum):
    TEMP = 'TEMP'
    BOOL = 'BOOL'
    INT = 'INT'
    LIST = 'LIST'
    PARAM = 'PARAM'
    ANY = 'ANY'
    ERROR = 'ERROR'
    NONE = 'NONE'
    FUNCTION = 'FUNCTION' # this is only here for getType and should never be used directly

    def __str__(self):
        return self.value

RacType = Union[Tuple[None, Type], Tuple[Tuple['RacType', ...], Type]]

class TypeList:
    def __init__(self, value:list[RacType]):
        self.value = value
    def __str__(self):
        if self.value == None:
            return '[None]'
        else:
            return '[' + ', '.join(str(x) for x in self.value) + ']'

# pretty print recursive function (commas between domain elements, with > separating out range)
def helpPrint(items):
    if isinstance(items, RacType):
        return helpPrint(items.value)
    elif isinstance(items, tuple) and items[0] is None:
        return str(items[1])
    elif isinstance(items, tuple):
        domain = ', '.join(helpPrint(item) for item in items[0] if item is not None)
        range = helpPrint(items[1])
        return f"({domain}) > {range}"
    return str(items)

class RacType:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return helpPrint(self.value)
    
    def __eq__(self,other):
        if other == None:
            return False
        else:
            return str(self) == str(other)
    
    def getType(self) -> RacType:
        if self.value[0]==None:
            return self.value[1]
        return Type.FUNCTION

    def getDomain(self):
        if self.getType() != Type.FUNCTION:
            return None
        return [RacType(x) for x in self.value[0]]

    def getRange(self) -> RacType:
        return RacType(self.value[1])

    def isType(self, typeStr)->bool:
        return str(self.getType()) == typeStr

# a helper function for setType that returns the position in the list of the root delimiter (either > or ,)
def findDelim(delim:str, tlist:list)->int:
    counter=0 #checking for when parens first become balanced
    for i in range(len(tlist)): #must use range since index matters
        counter += 1 if tlist[i]=="(" else -1 if tlist[i]==")" else 0
        if counter == 0 and tlist[i]==delim:
            return i+1
    return -1 # the string had unbalanced parens or did not contain delim

def list2Tup(slist:list[str])->tuple:
    return () #TODO complete this  

#given a tokenized list of a single type (i.e. NOT a list of types like potentially in a domain), returns the ractype for it. note: could be a function
def list2Type(slist:list[str])->RacType:
    if ">" not in slist:
        strg = "".join(slist)
        if strg=="":
            return RacType(Type.ERROR)
        if strg[0]=="(":
            strg = str[1:-1] #cutting out any surrounding parens (note that strg is not a function, so an open parens isn't needed)
        return RacType((None,Type.__members__.get(strg)))
    return RacType() # TODO: this is what needs to be done if it is a function

# Node object used to compose the AST
class Node:
    def __init__(self, children=None, parent=None, data:str='', tokenType:RacType=RacType((None,None)), name=None, debug:bool=False, numArgs:int=None, length:int=None, startPosition=None):
        self.children = children # by specification, children[0] is the "operator" for functions
        if children == None:
            self.children = []
        self.parent = parent # reference to the Node's parent (will be None for the root Node)
        self.data = data # this is the string name to be displayed (what used to be called "name" in the old PB)
        self.name = name # this is what used to be called "value" in the old PB
        self.type = tokenType # type of the node, (ex. boolean, int, function, etc.), specification described in typeFile
        self.debug = debug # False = standard execution, True = print info useful when debugging the pipeline
        self.numArgs = numArgs # for functions, it's the number of inputs
        self.length = length # for lists, it's the length
        self.startPosition = startPosition # starting position index of Node.data in the preprocessed string

    # Node.type attribute getter
    @property
    def type(self):
        return self._type
    
    # Node.type attribute setter
    @type.setter
    def type(self, newType):
        self._type = newType

    # convert the Node into a representation that is printed to the console
    def __str__(self):

        # print any unassigned type info during debugging
        if self.type == None and self.debug:
            outStr = f'{self.children}, {self.data}'
            print(outStr)

        # print value and type of each Node object, and a whitespace character for readability
        if self.debug:
            ans = f'{self.name},{self.type},{self.startPosition} '
        else:
            ans = self.data # print standardized syntax
        
        # print the Node's children if there are any
        if len(self.children) > 0:
            for i in range(len(self.children)):
                if i == len(self.children)-1 or self.debug:
                    ans += str(self.children[i])
                else:
                    ans += str(self.children[i]) + ' '
            ans += ')'
        return ans
    
    # this sets every node in the tree to the same debug setting
    def fullDebug(self, setting:bool):  
        if self!=None:
            self.debug=setting
            for c in self.children:
                c.fullDebug(setting)
        return

    # a node's setter method which takes in a string and sets the type of the node based on the string
    def setType(self, strg:str)->None:
        if ">" not in strg:
            self.type=RacType((None,Type.__members__.get(strg)))
        else:
            # make a "token list"
            slist = strg.upper().replace("(", " ( ").replace(">", " > ").replace(",", " , ").replace(")", " ) ").strip().split()
            if (ind:=findDelim(">",slist)) == -1:
                self.type=RacType(Type.ERROR) # e.g. mismatched parens
            else:
                outlist = slist[ind+1:] #everything after the >
                outtype = list2Type(outlist)
                domsList = slist[:ind] #everything before the >
                domsTup = list2Tup(domsList) # 
        return

    def replaceWith(self, newNode): #is there a better way to do this?
        self.data = newNode.data
        self.name = newNode.name
        self.type = newNode.type
        self.numArgs = newNode.numArgs
        self.length = newNode.length
        self.children = newNode.children
        self.debug = newNode.debug
        #do NOT change self.parent, to maintain place in tree

    # this takes in a list of parenthesized string tokens and splits it into ans[0]= token list of first element, ans[1]=token list of parenthesized rest
    # example: "(INT,LIST,BOOL)" would be [INT, (LIST,BOOL)], all tokenized.  also [((INT,BOOL)>LIST, BOOL)] would be [(INT,BOOL)>LIST, (BOOL)]
    def sepFirst(slist:list[str])->list:
        ind = findDelim(",",slist[1:-1]) #need to ignore out parens
        #if ind == -1:
        #   return [slist[1:-1],["(",")"]] #note this does not convert slist to a type with list2Type yet, it just removes the parens
        return [slist[1:ind],["("]+([")"] if ind==-1 else slist[ind+1:])]

def findNode(tree:Node, target:int,errLog:list[str],found=None)->Node:
    if found ==  None:
        found = []

    print(f"tree={tree.data} start={tree.startPosition}")
    print(target)
    if tree.startPosition == target:
        found.extend([tree])

    for child in tree.children:
        if not found:
            found.extend(findNode(child, target, errLog,found))
    return found

    '''
    do settype tests with:
    INT>BOOL
    (INT)>BOOL
    (INT,LIST)>BOOL
    (INT,LIST)>(INT>BOOL)
    (INT,LIST)>INT>BOOL #note: this is same as above since > associates left to right
    LIST>(INT)>BOOL
    (INT)>(LIST>BOOL)
    '''


'''
# unit tests
tests = [RacType((None, Type.INT)), RacType((((((None, Type.LIST), (None, Type.BOOL)), \
        Type.INT), (((None, Type.INT), (None, Type.LIST)), (None, Type.BOOL))), (None, Type.LIST)))]

for t in tests:
    print(f"expr is type {t.getType()}, domainList = {TypeList(t.getDomain())}, range = {t.getRange()}")
'''