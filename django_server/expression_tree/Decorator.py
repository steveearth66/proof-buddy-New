# This file is intended to complete the AST creation process and find some more errors through restrictions like type checking, and adding other details

from .ERCommon import Node, Type, RacType, TypeList
# brings in ERobject whose attributes will be used to decorate the tree
from .ERobj import pdict

# decorate non-function type Nodes in the AST
def decorateTree(inputTree: Node, errLog, debug=False) -> tuple[Node, list[str]]:
    # just return if there is not AST to decorate
    if inputTree == None:
        return inputTree, errLog

    # check if parameter name is legal
    if inputTree.type.getType() == Type.PARAM and not inputTree.data.isalpha():
        errLog.append(f"{inputTree.data} contains illegal characters")
        inputTree.type = RacType((None, Type.ERROR))
    
    #checking for nested quotes
    if inputTree.data == "'(" and "'(" in inputTree.ancestors:
        errLog.append(f"nested quotes are not allowed")
        inputTree.type = RacType((None, Type.ERROR))

    # populate new Node attributes from the ERobjects, default Node.name is set to the Node.data attribute
    inputTree.name = inputTree.data

    # decorate the Node objects
    if not inputTree.type.isType("FUNCTION"):
        if inputTree.type.isType("LIST"):
            erObj = pdict[inputTree.data]
            inputTree.length = erObj.length
        elif inputTree.type.isType("INT"):
            try:
                inputTree.name = int(inputTree.data)
            except:
                inputTree.name = None # is this sufficient for error handling?
        elif inputTree.type.isType("BOOL"):
            erObj = pdict[inputTree.data.lower()]
            inputTree.name = erObj.value

    # decorate the children if there are any
    for c in inputTree.children:
        decorateTree(c, errLog, debug)

    # return a decorated AST and the status of the error log
    return inputTree, errLog

# TODO: write a function to scan for nested quotes and return err

# helper function which moves important details from one node to another when getting rid of TEMP types


# note that the .data is NOT copied, e.g. it can stay "("
def copyDetails(fromNode: Node, toNode: Node):
    toNode.type = fromNode.type
    if fromNode.type.getType() == Type.FUNCTION:
        # note we cannot pass name/value e.g. (if x + *)
        toNode.numArgs = fromNode.numArgs
    return

# this function gets rid of all Type.TEMPs and does type checking for 'if' functions. can internally change the AST and update the errLog
# need to also do UDFs in same recursive function. also have sep function that checks for nested quotes and stops rules if has a ' ancestor
# this function does type checking for "if" functions as they are the only function left with an ambiguous type signature

def remTemps(inputTree: Node, errLog=None, debug=False, theRuleDict=None) -> list[str]:
    if errLog == None:
        errLog = []
    if theRuleDict == None:
        theRuleDict = dict()
    if not isinstance(inputTree,Node):
        return errLog
    if inputTree.data in (UDFs := theRuleDict.keys()): # UDF types should have already been done in labelTree, but just in case
        inputTree.type = theRuleDict[inputTree.data].racType
        return errLog
    if inputTree.data != "(" or inputTree.children == []: # or inputTree.children[0].data != "if" also case of (udf...):
        return errLog
    for c in inputTree.children[1:]:
        errLog = errLog + remTemps(c, errLog, debug, theRuleDict)
    if errLog != []:
        return errLog
    if inputTree.data == "(":
        chType = inputTree.children[0].type.getRange() #type filled by recursion above
        if isinstance(chType, tuple):
            chType = RacType(chType)
        inputTree.type = chType
    if (func := inputTree.children[0]).data in UDFs:
        if not func.type.isType("FUNCTION"):
            errLog.append(f"function {func.data} is not a function to be called")
        else:
            inputTree.type = func.type.getRange()
        return errLog
    if func.data != "if":
        return errLog
    if (argNum := len(inputTree.children)) != 4: #these should have already been caught by checkfunctions. just double checking
        errLog.append(f"if function must have 3 arguments but {argNum-1} were provided")
        return errLog
    if not inputTree.children[1].type.isType("BOOL"):
        errLog.append(f"argument #1 of an if function must be Boolean but {str(inputTree.children[1].type.getType())} was provided")
        return errLog
    n1, n2 = inputTree.children[2], inputTree.children[3] #note, even if these are ifs, they'll have been designated types in the recursive call
    if (t1 := n1.type.getType()) != (t2 := n2.type.getType()):
        errLog.append(f"final arguments of an if function must match but {str(t1)} and {str(t2)} were provided")
        return errLog
    inputTree.type = n1.type #setting the if expression list type to the type of the output branches
    return errLog

# function to check correct number of provided arguments for functions
def argQty(treeNode: Node, ruleDict=None) -> list[bool,str]:
    if ruleDict == None:
        ruleDict = dict()
    func = treeNode.children[0]
    # this used to crash, but now with numArgs added into fillbody, it should work
   # if func.data in ruleDict.keys():
    #    if len(treeNode.children[1:]) != len(ruleDict[func.data].racType.getDomain()):
     #        return False, f"{treeNode.data} must take {len(ruleDict[treeNode.data].racType.getDomain())} inputs"
    expectedCount = func.numArgs
    providedCount = len(treeNode.children) - 1

    #if (expectedCount != providedCount) and (func.type.getType() not in FLEX_TYPES):
    if (expectedCount != providedCount):
        return [False, f"{func.name} only takes {expectedCount} arguments, but {providedCount} {'was' if providedCount == 1 else 'were'} provided"]

    # only typeCheck if everything passes
    daRules = ruleDict # to avoid possible bug with "ruleDict = ruleDict" to skip debug parameter default
    return typeCheck(treeNode, ruleDict=daRules)

# check functions meet number of arguments and type checking restrictions


def checkFunctions(inputTree: Node, errLog, debug=False, theRuleDict=None) -> tuple[Node, list[str]]:
    if inputTree == None:
        return inputTree, errLog
    if theRuleDict == None:   # added optional pointer to parent proof's ruleset
        theRuleDict = dict()


    # only check if the function has children
    if len(inputTree.children) > 0: # and inputTree.type.getType() in FLEX_TYPES:
        typPass = argQty(inputTree, theRuleDict)
        if not typPass[0]:
            errLog.append(typPass[1])

        # continue check for the children of the Node
        for child in inputTree.children:
            checkFunctions(child, errLog, debug, theRuleDict)

    # return any errors
    return inputTree, errLog

#env is depracated now that udfs implemented
#env = {}  # env dictionary to keep track of params, having it out here so it stays across iterations temporarily

# checks that an expression calling a function has the correct arg types. already checked for correct number of args
# returns True if no errors, False if there are errors. either way, also sends string msg
def typeCheck(inputTree: Node, debug=False, ruleDict=None) -> list[bool,str]:
    if ruleDict == None:
        ruleDict = dict()
    if not type(inputTree) == Node:
        return [True, "inputTree is not a Node object, so no type violation"]
    if inputTree.children == []:
        return [True, "node has no children, so no type violation"]
    if inputTree.data != "(":
        return [True, "function is not being called, so no type violation"]
    func = inputTree.children[0]
    if not func.type.isType("FUNCTION"): #TODO: this will have to be adjusted in the future for UDFs of the form ((f x) y), where child[0] could be (
        return [True, "function is nested deeper than one level, so no type violation"]
    providedIns = [c.type for c in inputTree.children[1:]]
    #needs to be x.value for x in func.type.value[0] when in main rackexpr, but just func.type.value[0] for UDF checking
    expectedIns = [(RacType(x) if isinstance(x,tuple) else x) for x in func.type.value[0]] #for some reason, getDomain is overwrapping
    if not all(x==y for x, y in zip(providedIns, expectedIns)):
        return [False, f'Cannot match argument out typeList {[str(x) for x in providedIns]} with expected typeList {[str(x) for x in expectedIns]}']    
    return [True, "no type violation discovered"]

''' #this old version of typeCheck is being replaced by the new version above
    inputTree.type=func.type.getRange() 
    # get the expected and provided domains
    expectedIns = func.type.value[0] #for some reason, getDomain is overwrapping
    providedIns = [RacType((child.type.value[0], child.type.getRange()))
                   for child in inputTree.children[1:]]
    if debug:
        print(f"expectedIns {TypeList(expectedIns)} providedIns {TypeList(providedIns)}")

    # sanity check that number of arguments are the same
    if len(expectedIns) != len(providedIns):
        return f"{func.name} takes in types {TypeList(expectedIns)}, but provided inputs were {TypeList(providedIns)}"
    else:

        # iterate through each child RacType
        for childIndex, childType in enumerate(providedIns):
            if childType.getType() not in FLEX_TYPES:
                childIndex = childIndex + 1  # offset childIndex by one to get actual index of child
                if childType.getType() == Type.PARAM:

                    # get the child's actual data
                    childData = inputTree.children[childIndex].data

                    # check if the parameter is in the (global) environment
                    if childData not in env.keys():

                        # add reference to the environment
                        # need to subtract 1 to get correct index
                        env[childData] = expectedIns[childIndex-1]

                    # lookup parameter in the environment and see if it matches the expected
                    elif (env[childData] != expectedIns[childIndex-1]) and expectedIns[childIndex-1].getType() not in FLEX_TYPES:
                        return f"{func.name} at argument #{childIndex} takes a parameter '{childData}' expected to be type {expectedIns[childIndex-1].getType()} but {env[childData].getType()} was provided"

                elif (childType != expectedIns[childIndex-1]) and not (expectedIns[childIndex-1].isType("ANY")):
                    # handle type checking for lists
                    if childType.getType() == Type.LIST:
                        return f"{func.name}'s list at argument #{childIndex} expected to output type {expectedIns[childIndex-1].getType()} but {childType.getType()} was provided"

                    # general catch-all for non-matching domains
                    else:
                        return f"{func.name} takes in types {TypeList(expectedIns)}, but provided inputs were {TypeList(providedIns)}"

    # don't return anything if the function has no errors
    return None'''

'''this function, originally remTemps, is no longer being called since it got unwieldly and has been replaced by the new remTemps
def remTemps0(inputTree: Node, errLog, debug=False) -> list[str]:
    if inputTree == None or not inputTree.type.isType("TEMP"):
        return errLog  # it's either a quoted list or not a list, so nothing to check

    # from this point on, we know the subexpression starts with an unquoted list, a "(" token
    if inputTree.children == []:
        errLog.append(
            'cannot evaluate an empty list; perhaps "null" was intended')
        return errLog  # can return and skip recursion since no children

    # get the operator from the first child
    operator = inputTree.children[0]

    # check for a valid function to evaluate
    if operator.type.getType() not in FLEX_TYPES:
        errLog.append(
            f"{operator.data} is not a function that can be evaluted")

    # special check for "if" operator
    if operator.data == "if":  # setting special check for 2nd/3rd args same and changing the if-outtype

        # checking number of provided arguments
        argCount = len(inputTree.children) - 1
        if argCount != 3:
            errLog.append(f"the if function requires 3 arguments but {argCount} were provided")

        # check the types of the arguments fulfill 'if' restrictions (cond = bool, both branches output the same type)
        else:

            # remove temps from the children of the Node object
            # index starts at 1 to skip the "if" token
            for c in inputTree.children[1:]:
                # accumulating any errs found from inside the if
                errLog = remTemps0(c, errLog)

            # default a FLEX_TYPES type to be a boolean
            if inputTree.children[1].type.getType() in FLEX_TYPES:
                inputTree.children[1].type = RacType((None, Type.BOOL))

            # check for a boolean type for the first argument of "if"
            if not inputTree.children[1].type.isType("BOOL"):
                errLog.append("argument #1 of an if function must be Boolean")

            # get both the True and False branches of the "if"
            n1, n2 = inputTree.children[2], inputTree.children[3]
            typ1, typ2 = n1.type.getType(), n2.type.getType()

            # override any flex types in either branch
            if typ1 in FLEX_TYPES and typ2 not in FLEX_TYPES:
                copyDetails(n2, n1)
            elif typ1 not in FLEX_TYPES and typ2 in FLEX_TYPES:
                copyDetails(n1, n2)

            # check type of the branches
            if typ1 != typ2:
                errLog.append(f"final arguments of an if function must match, but {typ1} and {typ2} provided")

            # both branches are functions, check for matching domains and ranges
            elif typ1 == Type.FUNCTION:
                if n1.type.getDomain() != n2.type.getDomain():
                    errLog.append(
                        "function domains must match for both if branches")
                elif n1.type.getRange() != n2.type.getRange():  # note: range err not caught if domains don't match. but ok
                    errLog.append(
                        "function ranges must match for both if branches")
                else:
                    # both if branchs are functions with same ins/outs
                    copyDetails(n1, inputTree)
            else:  # both if branch types are the same, but aren't functions
                # TODO: potential problem if both ANYs. for now, just propogate ANY up.
                inputTree.type = n1.type

    # at this point, ifs are taken care of, so after the ( it's either a Temp/Any/Param or non-if function
    elif not operator.type.isType("FUNCTION"):

        # pass up the type of the operator to its parent Node
        inputTree.type = RacType(
            (operator.type.getDomain(), operator.type.getRange()))
        
        if operator.type.getType() not in FLEX_TYPES: #NOTE: is an outtype of any/param/temp impossible?
        # operator is a function
        if operator.type.getType() == Type.FUNCTION: #TODO: the type=Function needs to be bundled with in/out
        #TODO:  example: ((addn x) y) = (x+y). so addn has type: "FUNC: int-> (int->list)"
        #TODO: but until we make that change, we will have to approve all higher order Functions as legit
        # this is a placeholder. really needs to be inputTree.type=Func:(operator.out.in)->(operator.out.out)
            inputTree.type=([Type.ANY], Type.ANY)
            inputTree.numArgs = None #TODO: this needs to be length(operator.out.in) or look at definition window

    # continue removing Type.TEMPs from the children of the Node
    if inputTree.data != "if":  # since already did recursion in the special case, so avoiding repitition
        for c in inputTree.children[1:]:
            errLog = remTemps0(c, errLog)

    # @Steve not particularly sure how to refactor this last case to work with the new type specification
   
    # last case is where the operator is a temp/any/param, such as (x 3 4) in "(if (x = +) (x 3 4) 7)"
    if operator.getRange() in FLEX_TYPES: #only untested case so far
        listIns= []
        for c in inputTree.children[1:]:
            listIns.append(c.type)
        operator.type = (listIns, Type.ANY)
        operator.numArgs = len(listIns)

    # return any errors
    return errLog'''