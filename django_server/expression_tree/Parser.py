# This file parses an input Racket string and converts it to an equivalent expression tree representation (called an AST)

import string  # for string helper functions
from .ERCommon import *  # import RacType for type hints
from .ERobj import *  # for accessing pdict and ERObj declarations in applyRule

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

# errLog is a list of strings of error messages that will be passed at each step of the tree-building process


# None will generate a warning since it's not a list of strings
# takes in a string and returns a list of tokens, and a list of error messages
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
