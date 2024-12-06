from .Parser import *
from .Decorator import *
from .Labeler import *
#from ERCommon import *
import copy

expression_dict = {}  # dictionary of expressions, key is the label, value is a tuple of the parameters, list of types, and the expression


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

# list of user-defined functions (non-built-ins)
USER_DEFINED_FUNCTIONS = ['fact']

# dictionary of type specification for user-defined functions, parameters will be provided externally
UDFdict = {"fact": {"type": RacType(
    (((None, Type.INT),), (None, Type.INT))), "numArgs": 1}}

# give every Node object in the AST an initial type


def labelTree(inputTree: Node) -> Node:
    # if inputTree is empty, return the empty list
    if inputTree == []:
        return

    # get the token in the Node
    root = inputTree
    data = root.data

    # check if the token is a built-in function
    if inputTree.data in BUILT_IN_FUNCTIONS:

        # set type and numArgs attributes based on information in ERobj.py
        erObj = pdict[inputTree.data]
        if len(erObj.ins) == 1:
            # converting to new type representation
            inputTree.type = RacType(
                (((None, erObj.ins[0]),), (None, erObj.outtype)))
        else:
            # converting to new type representation
            inputTree.type = RacType(
                (tuple([(None, inType) for inType in erObj.ins]), (None, erObj.outtype)))
        inputTree.numArgs = erObj.numArgs

    # check if the token is a user-defined function
    elif inputTree.data in USER_DEFINED_FUNCTIONS:
        inputTree.type = UDFdict[inputTree.data]["type"]
        inputTree.numArgs = UDFdict[inputTree.data]["numArgs"]
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
        labelTree(child)

    # return the tree
    return root
