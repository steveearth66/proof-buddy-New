from ERProofEngine import ERProof

err_strings= [
    #expected errs
    ("(cons 1 null)",['Cannot apply math rule to cons']), #bad operation
    ("(+ 1 1 1)",['+ only takes 2 arguments, but 3 were provided'] ),  #too many args
    ("(* 3)",['* only takes 2 arguments, but 1 was provided']), #too few args
    ("(-)",['- only takes 2 arguments, but 0 were provided']), #no args
    ("(expt 0 0)",['0^0 is undefined']), #undef
    ("(expt 3 -1)",['-1 contains illegal characters']), #fraction, not a legal input due to -1
    ("(+ 1 #t)",['+ takes in types [INT, INT], but provided inputs were [INT, BOOL]']), #bad type
    ("(+ 1 2 3)",['+ only takes 2 arguments, but 3 were provided']), #too many args
    ("(+ 1 (+ 2 3))",['insufficiently resolved arguments']), #insufficiently resolved
    ("(quotient 3 0)",["denominator can't be zero"]), #div by 0
    ("(remainder 2 0)",["denominator can't be zero"]), #div by 0
    ("(< 2 #f)",['< takes in types [INT, INT], but provided inputs were [INT, BOOL]'])] #bad type
    
good_strgs = [
    #expected output
    ("(expt 1 2)", 1), #expt with 1 base
    ("(expt 2 0)", 1), #expt with 0 power
    ("(expt 0 2)", 0), #expt with 0 base
    ("(quotient 0 2)", 0), #quotient with 0 numerator
    ("(expt 2 1)", 2), #expt with 1 power
    ("(quotient 7 3)", 2), #quotient with remainder
    ("(+ 1 2)", 3), #addition
    ("(< 3 4)", "#t"), #less than
    ("(< 4 3)","#f") #greater than
]

#def testErrs(expr):
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
    expr,expected = trial
    print("input:",expr)
    proof = ERProof(expr)

    if proof.errLog == []:
        proof.applyRule('math', 0)

    ans = str(proof.errLog if proof.errLog!=[] else proof.exprTree)
    word = "errors" if isinstance(expected,list) else "output"
    expected=str(expected)
    if ans == expected:
        print(f"PASS: expected {word}: {ans}\n")
    else:
        print(f"FAIL! expected {word}: {expected} but got: {ans}\n")
        fails=+1
print("all tests passed!\n" if fails==0 else f"number of fails: {fails}\n")