import sympy as sp
from ERProofEngine import *

MathFuncs = ["+","-","*","expt", "quotient","remainder"] #relational functions are not included since they don't return ints

#takes a tree and returns set of all functions called
# currently in progress
def funcSet(exprTree, ansSet=set()):
    if not isinstance(exprTree,Node) or exprTree.data==None or exprTree.children==[]:
        return ansSet
    for child in node.children:
        pass #TODO: complete implementation
    return True


# take as input a node which must be pure math and return a string representation in NORMAL form
def rac2Norm(racTree):
    if not isinstance(racTree,Node) or racTree.data==None or racTree.data=="": #ensuring it's a node with a nonempty string
        return "ERROR"
    return ""


#print(sp.sympify("3*x**2 - 7*y").equals(sp.sympify("x**2 + y - 8*y +2*x**2")))

proof = ERProof()
expr = "(+ 1 1)"
node = ERProofLine(expr)
proof.addProofLine(expr, "math")
print(f"before rule = {expr}, after rule = {proof.getPrevRacket() if proof.errLog == [] else proof.errLog}")