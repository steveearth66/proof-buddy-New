from .ERProofEngine import ERProof

err_strings = [
    # expected errs
    ("(cons 1 null)", ['Cannot apply logic rule to cons']),  # bad operation
    # too many args
    ("(or #t #t #t)", ['or only takes 2 arguments, but 3 were provided']),
    # too few args
    ("(and 3)", ['and only takes 2 arguments, but 1 was provided']),
    # no args
    ("(implies)", ['implies only takes 2 arguments, but 0 were provided']),
    ("(and 1 #t)", [
     # bad type
     'and takes in types [BOOL, BOOL], but provided inputs were [INT, BOOL]']),
    # bad type
    ("(not 1)", ['not takes in types [BOOL], but provided inputs were [INT]']),
    # too many args
    ("(not #t #f)", ['not only takes 1 arguments, but 2 were provided']),
    # insufficiently resolved
    ("(or #t (and #f #f))", ['insufficiently resolved arguments'])
]

good_strgs = [
    # expected output
    ("(not #t)", "#f"),
    ("(not #f)", "#t"),
    ("(and #t #t)", "#t"),
    ("(or #f #f)", "#f"),
    ("(implies #f #f)", "#t"),
    ("(implies #t #f)", "#f"),
    # ("(nand #t #f)", "#t"),
    # ("(iff #f #f)", "#t"),
    # ("(iff #f #t)", "#f"),
    # ("(nor #f #f)", "#t"),
    ("(xor #t #t)", "#f")
]

# def testErrs(expr):
#    exprList,errLog = preProcess(expr,errLog=[])
#    if errLog!=[]:
#        return errLog,None
#    decTree, errLog = decorateTree(labelTree(buildTree(exprList,)[0]),errLog)
#    if errLog!=[]:
#        return errLog,None
#    errLog = remTemps(decTree, errLog)
#    if errLog!=[]:
#        return errLog,None
#    decTree, errLog = checkFunctions(decTree,errLog)
#    if errLog!=[]:
#        return errLog,None
#    errLog = decTree.applyRule("logic", errLog)
#    if errLog!=[]:
#        return errLog,None
#    return [],decTree

print("\nLogic testing Errs:\n")
fails = 0
for trial in err_strings+good_strgs:
    expr, expected = trial
    print("input:", expr)
    proof = ERProof()
    proof.addProofLine(expr, 'logic')

    ans = str(proof.errLog if proof.errLog != [] else proof.getPrevRacket())
    word = "errors" if isinstance(expected, list) else "output"
    expected = str(expected)
    if ans == expected:
        print(f"PASS: expected {word}: {ans}\n")
    else:
        print(f"FAIL! expected {word}: {expected} but got: {ans}\n")
        fails = +1
print("all tests passed!\n" if fails == 0 else f"number of fails: {fails}\n")