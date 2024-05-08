# This file parses an input Racket string and converts it to an equivalent expression tree representation (called an AST)
# DEPRECATED
import string # for string helper functions
from typeFile import * # import RacType for type hints
from ERobj import *  # for accessing pdict and ERObj declarations in applyRule


# SYMBOLS: perhaps in future allow square brackets and braces.
# permits linebreak and indents for conditionals. all become \s in pre-processing step
WHITESPACE = ["\n", "\t", "\r", " "]
# any other math uses ascii, such as expt, quotient, remainder. Note: "/" not permitted
ARITHMETIC = ["+", "*", "-", "=", ">", "<"]
# needed to separate open from closed for more precision with error messaging. note ' should be '( but preproc uses char
OPEN_GROUP = ["(", "[", "{", "'"]
# possibly cond might be implemented one day with square brackets. presently, all these replaced by parens in pre-processing
CLOSE_GROUP = [")", "]", "}"]
# hashtag for bools,? for pred suffix, unicode is for λ (currently not in language), single quote for quoted lists
SPECIAL_CHARS = ["#", "?", "\u03BB", "'"]
AllowedChars = list(string.ascii_letters) + list(string.digits) + \
    WHITESPACE + ARITHMETIC + OPEN_GROUP + CLOSE_GROUP + SPECIAL_CHARS
KnownRules = {'if', 'cons', 'first', 'rest', 'null?',
              'cons?', 'zero?', 'consList', 'math', 'logic'}

# Node object used to compose the AST


class Node:

    def __init__(self, children=None, parent=None, data: str = '', tokenType: RacType = RacType((None, None)), name=None, debug: bool = False, numArgs: int = None, length: int = None, startPosition=None):
        # by specification, children[0] is the "operator" for functions
        self.children = children
        if children == None:
            self.children = []
        # reference to the Node's parent (will be None for the root Node)
        self.parent = parent
        # this is the string name to be displayed (what used to be called "name" in the old PB)
        self.data = data
        self.name = name  # this is what used to be called "value" in the old PB
        # type of the node, (ex. boolean, int, function, etc.), specification described in typeFile
        self.type = tokenType
        # False = standard execution, True = print info useful when debugging the pipeline
        self.debug = debug
        self.numArgs = numArgs  # for functions, it's the number of inputs
        self.length = length  # for lists, it's the length
        # starting position index of Node.data in the preprocessed string
        self.startPosition = startPosition

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
            ans = self.data  # print standardized syntax

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
    def fullDebug(self, setting: bool):
        if self != None:
            self.debug = setting
            for c in self.children:
                c.fullDebug(setting)
        return

    # a node's setter method which takes in a string and sets the type of the node based on the string
    def setType(self, strg: str) -> None:
        self.type = str2Type(strg)
        return

    # TODO: replace with dictionary. strange to have ruleIF methods (et al) for every node regardless of node entry
    def applyRule(self, ruleID: str, errLog=None):
        if errLog == None:
            errLog = []
        rules = {'if': self.ruleIf, 'cons': self.ruleCons, 'first': self.ruleFirst, 'rest': self.ruleRest, 'null?': self.ruleNull, 'cons?': self.ruleConsQ,
                 'zero?': self.ruleZero, 'consList': self.ruleConsList, 'math': self.ruleMath, 'logic': self.ruleLogic}
        return rules[ruleID](errLog)

    # TODO: this needs to be generalized to use a python math library and normal forms, and not just the 4 basic operations
    def ruleMath(self, errLog, debug=False):
        mathSymbols = ARITHMETIC+["expt", "<=", ">=", "quotient", "remainder"]
        mathDict = {"+": lambda x, y: x+y, "-": lambda x, y: x-y, "*": lambda x, y: x*y, "expt": lambda x, y: x**y, "=": lambda x, y: x == y, ">": lambda x, y: x > y,
                    ">=": lambda x, y: x >= y, "<": lambda x, y: x < y, "<=": lambda x, y: x <= y, "quotient": lambda x, y: x//y, "remainder": lambda x, y: x % y}
        # note: no need to check argument types or number of arguments, since that is done in buildTree
        if (len(self.children) != 0 and self.children[0].data not in mathSymbols):
            errLog.append(f'Cannot apply math rule to {self.children[0].data}')
        # checking for (+ 1 (+ 2 3)) type errors
        elif len(self.children[1].children) != 0 or len(self.children[2].children) != 0:
            errLog.append("insufficiently resolved arguments")
        else:
            argOne = self.children[1].name
            argTwo = self.children[2].name
            if (self.children[0].data == "remainder" or self.children[0].data == "quotient") and argTwo == 0:
                errLog.append("denominator can't be zero")
            # note: currently PB has no negatives anyway!
            if self.children[0].data == "expt" and argOne*argOne != 1 and argTwo < 0:
                errLog.append(
                    "expt with negative arguments results in non-integer output")
            if self.children[0].data == "expt" and argOne == 0 and argTwo == 0:
                errLog.append("0^0 is undefined")
            if errLog == []:
                newname = mathDict[self.children[0].data](
                    argOne, argTwo)  # compute the result
                if isinstance(newname, bool):
                    newdata = "#t" if newname else "#f"  # convert to racket bool
                    newtype = RacType((None, Type.BOOL))
                else:
                    newdata = str(newname)
                    newtype = RacType((None, Type.INT))
                # converting node
                self.replaceNode(
                    Node(data=newdata, tokenType=newtype, name=newname))
        return errLog

    def ruleLogic(self, errLog, debug=False):
        logicDict = {"and": lambda x, y: x and y, "or": lambda x, y: x or y, "not": lambda x, y: not x, "xor": lambda x, y: (x or y) and not (x and y),
                     # not set up for "iff":lambda x,y: x==y, "nor":lambda x,y: not(x or y), "nand":lambda x,y: not(x and y)
                     "implies": lambda x, y: (not x) or y}
        # note: no need to check argument types or number of arguments, since that is done in buildTree
        if (len(self.children) != 0 and self.children[0].data not in logicDict.keys()):
            errLog.append(f'Cannot apply logic rule to {
                          self.children[0].data}')
        # checking for (or (not #t) #t) type errors
        elif len(self.children[1].children) != 0 or (self.children[0].data != "not" and len(self.children[2].children) != 0):
            errLog.append("insufficiently resolved arguments")
        if errLog == []:
            argOne = self.children[1].name
            # y=True isn't used for "not" lambda operation, 2 params for consistency
            argTwo = (True if self.children[0].data ==
                      "not" else self.children[2].name)
            newname = logicDict[self.children[0].data](argOne, argTwo)
            newdata = "#t" if newname else "#f"  # convert to racket bool
            newtype = RacType((None, Type.BOOL))
            # converting node
            self.replaceNode(
                Node(data=newdata, tokenType=newtype, name=newname))
        return errLog

    def ruleIf(self, errLog, debug=False):
        if (len(self.children) != 0 and self.children[0].data != 'if'):
            errLog.append(f'Cannot apply if rule to {self.children[0].data}')
        elif (len(self.children) != 4):
            errLog.append(f'If function expects 3 arguments, but received {
                          len(self.children)}')
            if debug:
                if len(self.children) != 0:
                    print("child[0] data:", self.children[0].data)
                print("length of children: ", len(self.children))
        else:
            condition = self.children[1]
            xNode = self.children[2]
            yNode = self.children[3]
            if condition.data == '#t':
                self.replaceNode(xNode)
            elif condition.data == '#f':
                self.replaceNode(yNode)
            elif isMatch(xNode, yNode):
                self.replaceNode(xNode)
        return errLog

    def replaceNode(self, newNode):  # is there a better way to do this?
        self.data = newNode.data
        self.name = newNode.name
        self.type = newNode.type
        self.numArgs = newNode.numArgs
        self.length = newNode.length
        self.children = newNode.children
        self.debug = newNode.debug
        # do NOT change self.parent, to maintain place in tree

    def ruleCons(self, errLog, debug=False):
        if self.children[0].data != 'cons':
            errLog.append(f'Cannot apply cons rule to {self.children[0].data}')
        elif len(self.children[1].children) == 0 or len(self.children[2].children) or\
                self.children[1].children[0].data != 'first' or self.children[2].children[0].data != 'rest':
            errLog.append(f'Can only apply the cons rule to first and rest')
        elif not isMatch(self.children[1].children[1], self.children[2].children[1]):
            errLog.append(f'Cannot apply cons rule on two different lists')
        else:
            lNode = self.children[1].children[1]
            self.replaceNode(lNode)
        return errLog

    def ruleConsList(self, errLog, debug=False):
        # print(f"data is {self.data}")
        # for x in range(len(self.children)):
        #    print(f"child {x} is {self.children[x].data}")
        if self.data != "(":
            errLog.append(
                "must select entire expression to apply consList rule")
        elif len(self.children) == 0 or self.children[0].data != 'cons':
            errLog.append('operator must be cons to apply consList rule')
        # NOTE: this case should have been caught earlier in buildtree, but just to be safe
        elif num := (len(self.children)) != 3:
            errLog.append(
                f'cons expects 2 arguments, but you provided {num-1}')
        elif (consObj := self.children[1].data) == "(":
            errLog.append('insufficiently resolved first argument')
        elif (listname := (self.children[2].data)) not in ("null", "'("):
            errLog.append(
                'insufficiently resolved second argument, which must be a list')
        else:
            if listname == "null":
                # changing null to '( to make consistent case handling
                self.children[2].data = "'("
        # at this point the second argument is definitely '( although possibly with no children/entries
            if consObj == "'(":  # need to get rid of the object's quote to avoid nesting quotes
                if len(self.children[1].children) == 0:
                    newtype = RacType((None, Type.LIST))  # consing a '()
                else:
                    newtype = self.children[1].children[0].type
                    if newtype.getType() == Type.FUNCTION:
                        # changing the type of the paren to be the output type of the operand
                        newtype = newtype.getRange()
                parenNode = Node(
                    children=self.children[1].children, data="(", tokenType=newtype, parent=self.children[1])
                for ch in self.children[1].children:
                    ch.parent = parenNode  # changing the parent of the children to the new node
                # replacing the old children with the new node
                self.children[1].children = [parenNode]
                # this will be the node used for replacement
                lNode = self.children[1]
                lNode.children.extend(self.children[2].children)
            else:  # consObj is a nonquoted object
                lNode = Node(children=[self.children[1]], data="'(", tokenType=RacType(
                    # length=len(self.children[2].children)+1)
                    (None, Type.LIST)))
                lNode.children.extend(self.children[2].children)
                for child in lNode.children:
                    child.parent = lNode
        try:
            self.replaceNode(lNode)
        except:
            print(errLog)
        return errLog

    def ruleFirst(self, errLog, debug=False):
        if self.children[0].data != 'first':
            errLog.append(f'Cannot apply first rule to {
                          self.children[0].data}')
        elif len(self.children[1].children) == 0 or self.children[1].children[0].data != 'cons':
            errLog.append(f'first can only be applied to the cons rule')
        else:
            xNode = self.children[1].children[1]
            self.replaceNode(xNode)
        return errLog

    def ruleRest(self, errLog, debug=False):
        if self.children[0].data != 'rest':
            errLog.append(f'Cannot apply rest rule to {self.children[0].data}')
        elif len(self.children[1].children) == 0 or self.children[1].children[0].data != 'cons':
            errLog.append(f'rest can only be applied to the cons rule')
        else:
            lNode = self.children[1].children[2]
            self.replaceNode(lNode)
        return errLog

    def ruleNull(self, errLog, debug=False):
        if self.children[0].data != 'null?':
            errLog.append(f'Cannot apply null rule to {self.children[0].data}')
        elif self.children[1].children[0].data != 'cons':
            errLog.append(f'null can only be applied to the cons rule')
        else:
            falseNode = Node(data='#f', tokenType=RacType(
                (None, Type.BOOL)), name=False)
            self.replaceNode(falseNode)
        return errLog

    def ruleConsQ(self, errLog, debug=False):
        if self.children[0].data != 'cons?':
            errLog.append(f'Cannot apply cons? rule to {
                          self.children[0].data}')
        elif self.children[1].children[0].data != 'cons':
            errLog.append(f'cons? can only be applied to the cons rule')
        else:
            trueNode = Node(data='#t', tokenType=RacType(
                (None, Type.BOOL)), name=True)
            self.replaceNode(trueNode)
        return errLog

    def ruleZero(self, errLog, debug=False):
        if self.children[0].data != 'zero?':
            errLog.append(f'Cannot apply zero rule to {self.children[0].data}')
        elif self.children[1].children == []:
            if self.children[1].type.getType() != Type.INT:
                errLog.append(f'zero? can only be applied to int type')
            else:
                if self.children[1].data == '0':
                    trueNode = Node(data='#t', tokenType=RacType(
                        (None, Type.BOOL)), name=True)
                    self.replaceNode(trueNode)
                else:
                    falseNode = Node(data='#f', tokenType=RacType(
                        (None, Type.BOOL)), name=False)
                    self.replaceNode(falseNode)
        elif self.children[1].children[0].data != '+':
            errLog.append(f'zero? can only be applied to addition rule')
        else:
            try:
                argOne = int(self.children[1].children[1].data)
                argTwo = int(self.children[1].children[2].data)
                if (argOne >= 0 and argTwo >= 0) and (argOne > 0 or argTwo > 0):
                    falseNode = Node(data='#f', tokenType=RacType(
                        (None, Type.BOOL)), name=False)
                    self.replaceNode(falseNode)
            except:
                errLog.append(
                    "ValueError in ruleZero - argument for + not a valid int")
        return errLog

    def generateRacketFromRule(self, startPos, rule, errLog):
        # also need to check if rule is in the userdefined dictionary (once that's implemented)
        if rule not in KnownRules:
            errLog.append(f'Rule {rule} not recognized')
            return errLog
        targetNode = findNode(self, startPos, errLog)
        if targetNode is not None and targetNode != []:
            return targetNode[0].applyRule(rule, errLog)
        else:
            errLog.append(
                f'Could not find Token with starting index {startPos}')
            return errLog

# a helper function for setType that returns the position in the list of the root delimiter (either > or ,)


def findDelim(delim: str, tlist: list) -> int:
    counter = 0  # checking for when parens first become balanced
    for i in range(len(tlist)):  # must use range since index matters
        counter += 1 if tlist[i] == "(" else -1 if tlist[i] == ")" else 0
        if counter == 0 and tlist[i] == delim:
            # this is one more than the position for some reason (maybe i used it earlier) so i need to -1 to it in str2Type
            return i+1
    return -1  # the string had unbalanced parens or did not contain delim

# given a tokenized list of a single type (i.e. NOT a list of types like potentially in a domain), returns the ractype for it. note: could be a function


def list2Type(slist: list[str]) -> RacType:
    if ">" not in slist:
        strg = "".join(slist)
        if strg == "":
            return RacType(Type.ERROR)
        if strg[0] == "(":
            # cutting out any surrounding parens (note that strg is not a function, so an open parens isn't needed)
            strg = str[1:-1]
        return RacType((None, Type.__members__.get(strg)))
    return RacType()  # TODO: this is what needs to be done if it is a function

# this takes in a list of parenthesized string tokens and splits it into ans[0]= token list of first element, ans[1]=token list of parenthesized rest
# example: "(INT,LIST,BOOL)" would be [[INT], [(LIST,BOOL)]], all tokenized.  also [((INT,BOOL)>LIST, BOOL)] would be [[(INT,BOOL)>LIST], [(BOOL)]]


def sepFirst(slist: list[str]) -> list:
    ind = findDelim(",", slist[1:-1])  # need to ignore out parens
    return [slist[1:ind], ["("]+([")"] if ind == -1 else slist[ind+1:])]

# takes a parenthesized list of tokens (possibly one or even empty) and turns it into a tuple of RacTypes


def list2Tup(slist: list[str]) -> tuple:
    if slist == ["(", ")"]:
        return tuple([])
    firstTokL, restToksL = sepFirst(slist)
    return tuple([str2Type(firstTokL[0])])+list2Tup(restToksL)


core = ["INT", "LIST", "BOOL", "ANY"]
# takes a string and turns it into a RacType


def str2Type(tstr: str) -> RacType:
    if tstr == None or tstr == "":
        return RacType((None, Type.ERROR))
    # creates token list
    slist = tstr.upper().replace("(", " ( ").replace(">", " > ").replace(
        ",", " , ").replace(")", " ) ").strip().split()
    for item in slist:
        # note: core is defined outside definition. apparently global not needed for lists, only for ints that are being modified
        # checks to make sure all tokens are valid.
        if item not in core+[",", "(", ")", ">"]:
            return RacType((None, Type.ERROR))
    # this is a single type wrapped in parens
    if findDelim(")", slist) == len(slist) and slist[0] == "(":
        slist = slist[1:-1]  # stripping out unnecessary surrounding parens
    if len(slist) == 1 or (len(slist) == 3 and slist[0] == "(" and slist[2] == ")"):
        # grabbing a single item which could be int or (int)
        mid = slist[0] if len(slist) == 1 else slist[1]
        return RacType((None, Type.__members__.get(mid))) if mid in core else RacType(Type.ERROR)
    # must exist since single types already handled, or mismatched parens
    if (ind := findDelim(">", slist)-1) == -1:
        return RacType((None, Type.ERROR))
    outlist = slist[ind+1:]  # everything after the >
    # convert range token list back to string to do recursion
    outtype = str2Type("".join(outlist))
    # everything before the root >, so paren balanced already
    domsList = slist[:ind]
    # the function just takes a single argument (which might be a function)
    if "," not in domsList:
        return RacType(((str2Type("".join(domsList)),), outtype))
    domsTup = list2Tup(domsList)  # makes a tuple of RacTypes
    return RacType((domsTup, outtype))

# errLog is a list of strings of error messages that will be passed at each step of the tree-building process


# None will generate a warning since it's not a list of strings
def preProcess(inputString: str, errLog: list[str] = None, debug=False) -> tuple[list[str], list[str]]:
    if errLog == None:  # values assigned at func def, not each call, so need None vs []
        errLog = []

    # orig=inputString #saving original to refer to later, but might not be needed
    # inputString = inputString.lower()  #decided to permit uppercase letters and make it case sensitive to allow M vs m. caution: now  "If" is not "if"

    # standardize open/close grouping characters and whitespace
    inputString = inputString.replace("]", ")").replace("[", "(").replace("{", "(").replace("}", ")").replace(
        "\t", " ").replace("\r", " ").replace("\n", " ").replace("(", " ( ").replace(")", " ) ")
    # remove consecutive spaces, strip whitespace from front & back of inputString
    inputString = " ".join(inputString.split())

    if inputString == "":  # needed to avoid an issue in checking first character as (
        # can't return the append directly since append changes in place and doesn't return a value!!
        errLog.append("no input detected")
        return [], errLog
    # note that final replacement at end of next line attaches a \s to parens for list-splitting purposes

    # parentheses pairing check
    parenPairing = 0
    # needed to loop over index values rather than char to know if not at end
    for ind in range(len(inputString)):
        char = inputString[ind]

        # check if char is an allowed character
        if char not in AllowedChars:
            errLog.append(f"{char} not an allowed character")

        # parenPairing should only return to 0 at the very end of the input string
        if char == '(':
            parenPairing += 1
        elif char == ')':
            parenPairing -= 1

        # the following conditionals refer to the general lists of chars in case later developers decide not to the the replacements:
        # parentheses balanced in the interior of the string
        if char in OPEN_GROUP[:-1] and parenPairing == 1 and 0 < ind < len(inputString)-1 \
                and ind-2 >= 0 and inputString[ind-2] != "'":  # ommitting ' from open group and making sure the ( isn't a '(
            # "(stuff)(stuff)".  need )( check to insure "34" doesn't trigger an error
            errLog.append("contains multiple independent subexpressions")

        # separate values not wrapped in a list
        if char in WHITESPACE and inputString[0] not in OPEN_GROUP:
            # "n n" will trigger an error
            errLog.append(
                "multiple elements should be contained within a list")

    # parentheses are not balanced in the input string
    if parenPairing < 0:
        errLog.append("too many )")
    elif parenPairing > 0:
        errLog.append("too many (")

    # attaches single quote to left paren for quoted lists
    inputString = inputString.replace("' (", "'(")

    # return the list of standardized tokens, and the error log
    return inputString.split(), errLog

# helper function to find the index of the matching close parenthesis given the index of the open parenthesis


def findMatchingParenthesis(tokenList, index) -> int:
    count = 1
    for i in range(index+1, len(tokenList)):
        if tokenList[i] == '(' or tokenList[i] == "'(":
            count += 1
        elif tokenList[i] == ')':
            count -= 1
        if count == 0:
            return i

# algorithm to build the AST, composed of Node objects


def buildTree(inputList: list[str], debug=False) -> list:
    # if inputList == [], return the empty list
    if len(inputList) == 0:
        return []

    # we have something in inputList, create a Node
    # need [] inside Node init to ensure no children on instantiation
    node = Node([], debug=debug)
    node.data = inputList[0]  # fill out the data with the symbol

    # if the first token is not '(', it is a single literal (ex. boolean, int, parameter)
    # changed to accomodate quoted lists
    if inputList[0] != '(' and inputList[0] != "'(":

        # create Node where Node.data is the literal and continue processing the rest of input
        return [node] + buildTree(inputList[1:len(inputList)], debug)

    # special case for the empty list '()', just modify Node.data == '()'
    if inputList[0] == "'(" and inputList[1] == ')':  # changed to accomodate quotes
        node.data = 'null'

        # continue processing the rest of input
        return [node] + buildTree(inputList[2:len(inputList)], debug)

    # we have '(' as the first token, find the index of its matching ')'
    matchIndex = findMatchingParenthesis(inputList, 0)

    # if everything else is contained within our parenthesis pair, they will be contained in Node.children
    if matchIndex + 1 == len(inputList):
        node.children = buildTree(inputList[1:-1], debug)

        # set the parent of each child node to be the (root) node
        for child in node.children:
            child.parent = node

        # return the (root) node
        return [node]

    # there are multiple elements in our list, create a Node/subtree for things in that list, append all to Node.children
    node.children += buildTree(inputList[1:matchIndex], debug)

    # set the parent of each child node to be the (root) node
    for child in node.children:
        child.parent = node

    # continue processing the rest of input
    return [node] + buildTree(inputList[matchIndex+1:len(inputList)], debug)


# recursively check if two nodes are identical #TODO: replace elif chain with something prettier
def isMatch(xNode: Node, yNode: Node) -> bool:
    if xNode.data != yNode.data:
        return False
    elif xNode.name != yNode.name:
        return False
    elif xNode.numArgs != yNode.numArgs:
        return False
    elif xNode.length != yNode.length:
        return False
    elif xNode.type != yNode.type:
        return False
    elif len(xNode.children) != len(yNode.children):
        return False
    elif len(xNode.children) != 0:
        checker = True
        for i in range(len(xNode.children)):
            if not isMatch(xNode.children[i], yNode.children[i]):
                checker = False
        if checker:
            return True
    else:
        return True  # if everything else passed


def findNode(tree: Node, target: int, errLog: list[str], found=None) -> Node:
    if found == None:
        found = []
    print(f"tree={tree.data} start={tree.startPosition}")
    if tree.startPosition == target:
        found.append(tree)
    for child in tree.children:
        if not found:
            findNode(child, target, errLog, found)
    return found
