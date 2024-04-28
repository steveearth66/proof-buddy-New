from ERProofEngine import ERProof

err_strings= [
    #expected errs
    ("(cons 1 null)",['Cannot apply logic rule to cons']), #bad operation
    ("(or #t #t #t)",['or only takes 2 arguments, but 3 were provided'] ),  #too many args
    ("(and 3)",['and only takes 2 arguments, but 1 was provided']), #too few args
    ("(implies)",['implies only takes 2 arguments, but 0 were provided']), #no args
    ("(and 1 #t)",['and takes in types [BOOL, BOOL], but provided inputs were [INT, BOOL]']), #bad type
    ("(not 1)",['not takes in types [BOOL], but provided inputs were [INT]']), #bad type
    ("(not #t #f)",['not only takes 1 arguments, but 2 were provided']), #too many args
    ("(or #t (and #f #f))",['insufficiently resolved arguments']) #insufficiently resolved
]
    
good_strgs = [
    #expected output
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
#    errLog = decTree.applyRule("logic", errLog)
#    if errLog!=[]:
#        return errLog,None
#    return [],decTree

print("\nLogic testing Errs:\n")
fails = 0
for trial in err_strings+good_strgs:
    expr,expected = trial
    print("input:",expr)
    proof = ERProof(expr)

    if proof.errLog == []:
        proof.applyRule('logic', 0)

    ans = str(proof.errLog if proof.errLog!=[] else proof.exprTree)
    word = "errors" if isinstance(expected,list) else "output"
    expected=str(expected)
    if ans == expected:
        print(f"PASS: expected {word}: {ans}\n")
    else:
        print(f"FAIL! expected {word}: {expected} but got: {ans}\n")
        fails=+1
print("all tests passed!\n" if fails==0 else f"number of fails: {fails}\n")