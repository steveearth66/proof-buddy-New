from .ERProofEngine import *

STRUCTURE_TYPES = ["int", "list"] #list of valid structure types for induction proofs
USER_STRUCTS = [] #maybe someday "tree", "graph", etc

# this is the class for Inductive Proofs
class IndProof:
    def __init__(self,
                 debug: bool = False, #debugging flag
                 errList: list = None, #list of errors encountered during proof construction
                 isValid: bool = True, #is this a valid proof? (baseCase.isValid && leapStep.isValid)
                 isComplete: bool = False, #is this a complete proof? ((baseCase.isComplete && leapStep.isComplete))
                 struct: str = "", #can be "int", or "list",or some other structure in the future ("tree", "graph", etc.)
                 # struct is a string, but ivar, aval, lvar are Nodes
                 ivar = "", #the variable being inducted over, typically n for ints, L for lists, T for trees, etc.
                 aval ="", #the anchor value, typically 0 for ints, null for lists, etc.
                 lvar = "", #the variable to use for the leap step, typically k for ints, K for lists
                 lhsPremise = "", #the left-hand side of the induction premise, e.g. (cumeSum n) for int induction
                 rhsPremise = "", #the right-hand side of the induction premise, e.g. (quotient (* n (+ n 1)) 2)
                 baseCase: ERProof = None, #the base case proof, LHS=RHS is ivar replaced with aval
                 indHyp: Node = None, #the induction hypothesis, is LHS=RHS wit ivar replaced with lvar
                 leapStep: ERProof = None): #the leap step proof, LHS=RHS is ivar replaced with (+ lvar 1) or (cons a L) etc, a.type= ANY??

        if errList is None:
            self.errList = []
        if (struct:=str(struct).lower()) not in (ALL_STRUCTS:=STRUCTURE_TYPES+ USER_STRUCTS):
            self.errList.append(f"Invalid structure type: {struct}. Must be one of {ALL_STRUCTS}.")
            self.isValid = False
        else:
            self.struct = struct
        
        # Integer Induction
        if struct == "int":
            if isinstance(ivar, Node):
                ivar = ivar.data
            if not isinstance(ivar, str) or not ivar.isalnum() or not ivar.isupper():
                self.errList.append("Inductive variable should be lowercase, typically 'n' for integers.")
                self.isValid = False
            else:
                self.ivar = Node(ivar)
            if isinstance(aval, Node):
                aval = aval.data
            if not isinstance(aval, str) or not aval.isalnum() or not aval.islower():
                pass #TODO
        
        # List Induction
        elif struct == "list":
            if not isinstance(ivar, Node):
                self.errList.append("Inductive variable should be a list, typically 'L' for lists.")
                self.isValid = False
            else:
                self.ivar = ivar
            if not isinstance(aval, Node):
                self.errList.append("Anchor value should be a list, typically '[]' for lists.")
                self.isValid = False
            else:
                self.aval = aval
            if not isinstance(lvar, Node):
                self.errList.append("Leap variable should be a list, typically 'K' for lists.")
                self.isValid = False
            else:
                self.lvar = lvar
            if not isinstance(lhsPremise, Node):
                self.errList.append("LHS premise should be a list, typically '(cumeSum L)' for lists.")
                self.isValid = False
            else:
                self.lhsPremise = lhsPremise
            if not isinstance(rhsPremise, Node):
                self.errList.append("RHS premise should be a list, typically '(quotient (* L (+ L 1)) 2)' for lists.")
                self.isValid = False
            else:
                self.rhsPremise = rhsPremise
            if not isinstance(indHyp, Node):
                self.errList.append("Induction hypothesis should be a list.")
                self.isValid = False
            else:
                self.indHyp = indHyp
            if not isinstance(baseCase, ERProof):
                self.errList.append("Base case should be an ERProof.")
                self.isValid = False
            else:
                self.baseCase = baseCase
            if not isinstance(leapStep, ERProof):
                self.errList.append("Leap step should be an ERProof.")
                self.isValid = False
            else:
                self.leapStep = leapStep
        else: # TODO: add support for other structures
            self.isValid = False
            self.errList.append(f"Inductive proofs for structure type '{struct}' are not yet implemented.")

        self.ivar = ivar if ivar is not None else Node()
        self.aval = aval if aval is not None else Node()
        self.lvar = lvar if lvar is not None else Node()
        self.lhsPremise = lhsPremise if lhsPremise is not None else Node()
        self.rhsPremise = rhsPremise if rhsPremise is not None else Node()
        self.indHyp = indHyp if indHyp is not None else Node()
        self.baseCase = baseCase if baseCase is not None else ERProof()
        self.leapStep = leapStep if leapStep is not None else ERProof()

        #first we validate the inputs and turn the strings into Nodes