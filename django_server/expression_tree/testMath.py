from .ERProofEngine import ERProof

err_strings = [
    # expected errs
    ("(cons 1 null)", ['Cannot apply math rule to cons']),  # bad operation
    # too many args
    ("(+ 1 1 1)", ['+ only takes 2 arguments, but 3 were provided']),
    # too few args
    ("(* 3)", ['* only takes 2 arguments, but 1 was provided']),
    ("(-)", ['- only takes 2 arguments, but 0 were provided']),  # no args
    ("(expt 0 0)", ['0^0 is undefined']),  # undef
    # fraction, not a legal input due to -1
    ("(expt 3 -1)", ['-1 contains illegal characters']),
    # bad type
    ("(+ 1 #t)",
     ['+ takes in types [INT, INT], but provided inputs were [INT, BOOL]']),
    # too many args
    ("(+ 1 2 3)", ['+ only takes 2 arguments, but 3 were provided']),
    # insufficiently resolved
    ("(+ 1 (+ 2 3))", ['insufficiently resolved arguments']),
    ("(quotient 3 0)", ["denominator can't be zero"]),  # div by 0
    ("(remainder 2 0)", ["denominator can't be zero"]),  # div by 0
    # bad type
    ("(< 2 #f)", ['< takes in types [INT, INT], but provided inputs were [INT, BOOL]'])]

good_strgs = [
    # expected output
    ("(expt 1 2)", 1),  # expt with 1 base
    ("(expt 2 0)", 1),  # expt with 0 power
    ("(expt 0 2)", 0),  # expt with 0 base
    ("(quotient 0 2)", 0),  # quotient with 0 numerator
    ("(expt 2 1)", 2),  # expt with 1 power
    ("(quotient 7 3)", 2),  # quotient with remainder
    ("(+ 1 2)", 3),  # addition
    ("(< 3 4)", "#t"),  # less than
    ("(< 4 3)", "#f")  # greater than
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
#    errLog = decTree.applyRule("math", errLog)
#    if errLog!=[]:
#        return errLog,None
#    return [],decTree

print("\nMath testing Errs:\n")
fails = 0
for trial in err_strings+good_strgs:
    expr, expected = trial
    print("input:", expr)
    proof = ERProof()
    proof.addProofLine(expr, 'math')

    ans = str(proof.errLog if proof.errLog != [] else proof.getPrevRacket())
    word = "errors" if isinstance(expected, list) else "output"
    expected = str(expected)
    if ans == expected:
        print(f"PASS: expected {word}: {ans}\n")
    else:
        print(f"FAIL! expected {word}: {expected} but got: {ans}\n")
        fails = +1
print("all tests passed!\n" if fails == 0 else f"number of fails: {fails}\n")