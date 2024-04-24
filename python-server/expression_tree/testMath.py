from recParser import buildTree, preProcess
from Labeler import labelTree
from Decorator import decorateTree, remTemps, checkFunctions

test_strings= [
    #expected errs
    "(cons 1 null)", #bad operation
    "(+ 1 1 1)",  #too many args
    "(* 3)", #too few args
    "(-)", #no args
    "(expt 0 0)", #undef
    "(expt 3 -1)", #fraction, not a legal input due to -1
    "(+ 1 #t)", #bad type
    "(+ 1 2 3)", #too many args
    "(+ 1 (+ 2 3))", #insufficiently resolved
    "(quotient 3 0)", #div by 0
    "(remainder 2 0)", #div by 0
    "(< 2 #f)", #bad type
    

    #expected answer in comments
    "(expt 1 1)", # 1
    "(expt 2 0)", # 1
    "(expt 0 2)", # 0
    "(quotient 0 2)", #0
    "(expt 2 1)", # 2
    "(quotient 7 3)", # 2
    "(+ 1 2)", #3
    "(< 3 4)", #True
    "(< 4 3)" #False
]

print("\nMath testing:\n")
for expr in test_strings:
    print("input:",expr)
    errLog = []
    exprList,errLog = preProcess(expr,errLog=[])
    if errLog!=[]:
        print(errLog)
    else:
        decTree, errLog = decorateTree(labelTree(buildTree(exprList,)[0]),errLog)
        if errLog!=[]:
            print(errLog,"\n")
        else:
            errLog = remTemps(decTree, errLog)
            if errLog!=[]:
                print(errLog,"\n")
            else:
                decTree, errLog = checkFunctions(decTree,errLog)
                if errLog!=[]:
                    print(errLog,"\n")
                else:
                    errLog = decTree.applyRule("math", errLog)
                    if errLog!=[]:
                        print(errLog,"\n")
                    else:
                        print("after rule:", decTree, "\n")