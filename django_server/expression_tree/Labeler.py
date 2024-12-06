# This file conducts an initial pass over the input AST to populate a type for each Node object

# import RacType objects and Type Enum
from .ERCommon import Type, RacType, Node
from .ERobj import pdict  # import dictionary of ERobj objects
import re  # for regex usage

# class wrapper for identifying a type based on regex


class Label:
    def __init__(self, regex, dataType):
        self.regex = regex
        self.dataType = dataType


# list of labels to map strings to types
LABEL_LIBRARY = [
    Label(r'(?:^)null(?:$)', Type.LIST),  # null values
    Label(r'(?:^)\'\((?:$)', Type.LIST),  # quoted lists
    # temporary type for "(" characters. final type will be given by the Decorator
    Label(r'^\($', Type.TEMP),
    Label(r'#t|#T', Type.BOOL),  # True boolean values
    Label(r'#f|#F', Type.BOOL),  # False boolean values
    Label(r'(\d+)', Type.INT),  # integers
]

# list of built-in Racket functions
BUILT_IN_FUNCTIONS = ['if', 'cons', 'first', 'rest', 'null?', '+', '-', '*', 'quotient', 'remainder', 'zero?',
                      "expt", "=", "<=", ">=", "<", ">", "and", "or", "not", "xor", "implies", "list?", "int?"]

# give every Node object in the AST an initial type (ifs will be done later in remTemps since their range varies)
def labelTree(inputTree: Node, ruleDict=None) -> Node:
    # if inputTree is empty, return the empty list
    if inputTree == []:
        return
    if ruleDict == None:
        ruleDict = dict()

    # get the token in the Node
    root = inputTree
    data = root.data

    # check if the token is a built-in function
    if inputTree.data in BUILT_IN_FUNCTIONS:

        # set type and numArgs attributes based on information in ERobj.py
        erObj = pdict[inputTree.data]
        if len(erObj.ins) == 1:
            # converting to new type representation
            inputTree.type = RacType((((None, erObj.ins[0]),), (None, erObj.outtype)))
        else:
            # converting to new type representation
            inputTree.type = RacType(
                (tuple([(None, inType) for inType in erObj.ins]), (None, erObj.outtype)))
        inputTree.numArgs = erObj.numArgs

    # check if the token is a user-defined function
    elif inputTree.data in ruleDict.keys():
        inputTree.type = ruleDict[inputTree.data].racType
        if inputTree.type.isType("FUNCTION"):
            inputTree.numArgs = len(inputTree.type.getDomain())
    else:

        # check if the token matches a label regex
        for label in LABEL_LIBRARY:
            matcher = re.compile(label.regex)
            if matcher.match(root.data) != None:
                root.type = RacType((None, label.dataType))
                if root.type.isType("INT"):
                    # storing the integer value in the node to be used with arithmetic operations
                    root.name = int(root.data)
                break

    # if the Node is still unlabeled, default its type to be Type.PARAM
    if root.type.getType() == None:
        root.type = RacType((None, Type.PARAM))

    # label the children of the root Node
    for child in root.children:
        labelTree(child, ruleDict)

    # return the tree
    return root
