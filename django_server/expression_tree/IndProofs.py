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
                 baseCase: TwoSidedProof = None, #the base case proof, LHS=RHS is ivar replaced with aval
                 indHypLHS: Node = None, #the induction hypothesis LHS, is LHS with ivar replaced with lvar
                 indHypRHS: Node = None, #the induction hypothesis RHS, is RHS with ivar replaced with lvar
                 leapStep: TwoSidedProof = None): #the leap step proof, LHS=RHS is ivar replaced with (+ lvar 1) or (cons a L) etc, a.type= ANY??

        if errList is None:
            self.errList = []
        if (struct:=str(struct).lower()) not in (ALL_STRUCTS:=STRUCTURE_TYPES+ USER_STRUCTS):
            self.errList.append(f"Invalid structure type: {struct}. Must be one of {ALL_STRUCTS}.")
            self.isValid = False
        else:
            self.struct = struct
        if not isinstance(baseCase, TwoSidedProof):
            baseCase = TwoSidedProof()
        if not isinstance(leapStep, TwoSidedProof):
            leapStep = TwoSidedProof()
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
            if not isinstance(indHypLHS, Node):
                self.errList.append("Induction hypothesis LHS should be a list.")
                self.isValid = False
            else:
                self.indHypLHS = indHypLHS
            if not isinstance(indHypRHS, Node):
                self.errList.append("Induction hypothesis RHS should be a list.")
                self.isValid = False
            else:
                self.indHypRHS = indHypLHS
            if not isinstance(baseCase, TwoSidedProof):
                self.errList.append("Base case should be a twosided ERProof.")
                self.isValid = False
            else:
                self.baseCase = baseCase
            if not isinstance(leapStep, TwoSidedProof):
                self.errList.append("Leap step should be a twosided ERProof.")
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
        self.indHypLHS = indHypLHS if indHypLHS  is not None else Node()
        self.indHypRHS = indHypRHS if indHypRHS  is not None else Node()
        self.baseCase = baseCase if baseCase is not None else ERProof()
        self.leapStep = leapStep if leapStep is not None else ERProof()

        #first we validate the inputs and turn the strings into Nodes
        # (initial validation is handled by callers/tests)

    def __str__(self) -> str:
        """Render a structured induction proof summary with aligned sections.

        Order:
        - Format (int or list)
        - Function definition
        - To Prove
        - Base case (LHS then RHS) + status
        - Inductive Hypothesis (LHS = RHS)
        - Leap step (LHS then RHS) + status
        - Conclusion (entire proof complete or not)
        """

        def to_str(node_or_val) -> str:
            try:
                return str(node_or_val) if node_or_val is not None else ""
            except Exception:
                return ""

        def indent_block(text: str, levels: int = 1) -> str:
            if not text:
                return ""
            prefix = "    " * levels
            return "\n".join(prefix + line for line in text.splitlines())

        # Gather primary parameters with graceful fallbacks
        fmt = getattr(self, 'struct', '')
        ivar_raw = getattr(self, 'indVar', None) or getattr(self, 'ivar', None)
        aval_raw = getattr(self, 'anchorVal', None) or getattr(self, 'aval', None)
        lvar_raw = getattr(self, 'leapVar', None) or getattr(self, 'lvar', None)

        lhsPrem = to_str(getattr(self, 'lhsPremise', None))
        rhsPrem = to_str(getattr(self, 'rhsPremise', None))

        ih_lhs = to_str(getattr(self, 'indHypLHS', None))
        ih_rhs = to_str(getattr(self, 'indHypRHS', None))

        # Handle both Node and string forms
        ivar = to_str(ivar_raw.data if isinstance(ivar_raw, Node) else ivar_raw)
        aval = to_str(aval_raw.data if isinstance(aval_raw, Node) else aval_raw)
        lvar = to_str(lvar_raw.data if isinstance(lvar_raw, Node) else lvar_raw)

        # Function definition (from available UDFs, if any)
        func_label = ""
        func_type = ""
        func_body = ""
        try:
            # Prefer baseCase rule set; TwoSidedProof shares ruleSet across LHS/RHS
            defs = {}
            if hasattr(self, 'baseCase') and self.baseCase and hasattr(self.baseCase, 'ruleSet'):
                defs = {label: rule for label, rule in self.baseCase.ruleSet['apply'].items()
                        if hasattr(rule, 'ruleType') and str(rule.ruleType) == 'definition'}
            if not defs and hasattr(self, 'leapStep') and self.leapStep and hasattr(self.leapStep, 'ruleSet'):
                defs = {label: rule for label, rule in self.leapStep.ruleSet['apply'].items()
                        if hasattr(rule, 'ruleType') and str(rule.ruleType) == 'definition'}
            if defs:
                # Pick deterministic first label (prefer 'f' or lowercase, then sorted)
                first_label = 'f' if 'f' in defs else sorted(defs.keys())[0]
                udf = defs[first_label]
                # Build signature (label + params), type, and body strings
                sig_params = getattr(udf, 'params', [])
                func_label = f"({udf.label} {' '.join(sig_params)})" if sig_params else f"({udf.label})"
                func_type = to_str(getattr(udf, 'racType', ''))
                func_body = to_str(getattr(udf, 'body', ''))
        except Exception:
            pass

        # Proof sections - indent proofs under LHS/RHS headers with consistent alignment
        base_lhs_lines = str(self.baseCase.LHS).splitlines() if hasattr(self, 'baseCase') and self.baseCase else []
        base_lhs_str = "\n".join("        " + line for line in base_lhs_lines) if base_lhs_lines else ""
        
        base_rhs_lines = str(self.baseCase.RHS).splitlines() if hasattr(self, 'baseCase') and self.baseCase else []
        base_rhs_str = "\n".join("        " + line for line in base_rhs_lines) if base_rhs_lines else ""
        
        base_status = 'complete' if bool(getattr(self.baseCase, 'complete', False)) else 'incomplete'

        leap_lhs_lines = str(self.leapStep.LHS).splitlines() if hasattr(self, 'leapStep') and self.leapStep else []
        leap_lhs_str = "\n".join("        " + line for line in leap_lhs_lines) if leap_lhs_lines else ""
        
        leap_rhs_lines = str(self.leapStep.RHS).splitlines() if hasattr(self, 'leapStep') and self.leapStep else []
        leap_rhs_str = "\n".join("        " + line for line in leap_rhs_lines) if leap_rhs_lines else ""
        
        leap_status = 'complete' if bool(getattr(self.leapStep, 'complete', False)) else 'incomplete'

        # Overall conclusion
        overall_complete = bool(getattr(self.baseCase, 'complete', False)) and bool(getattr(self.leapStep, 'complete', False))
        conclusion = 'Proof complete' if overall_complete else 'Proof incomplete'

        # Compose output with aligned headers
        lines: list[str] = []
        lines.append("Induction Proof")
        lines.append(f"  Format: {fmt}")
        if func_label or func_type or func_body:
            lines.append(f"  Function: {func_label} : {func_type}".rstrip())
            lines.append(f"  Definition: {func_body}".rstrip())
        lines.append(f"  To Prove: {lhsPrem} = {rhsPrem}")
        lines.append(f"  Base Case: anchored at {ivar} = {aval}")
        lines.append("    LHS:")
        if base_lhs_str:
            lines.append(base_lhs_str)
        lines.append("    RHS:")
        if base_rhs_str:
            lines.append(base_rhs_str)
        lines.append(f"  Base Case Status: {base_status}")
        lines.append(f"  Inductive Hypothesis: {ih_lhs} = {ih_rhs}")
        lines.append("  Leap Step:")
        lines.append("    LHS:")
        if leap_lhs_str:
            lines.append(leap_lhs_str)
        lines.append("    RHS:")
        if leap_rhs_str:
            lines.append(leap_rhs_str)
        lines.append(f"  Leap Step Status: {leap_status}")
        lines.append(f"  Conclusion: {conclusion}")

        return "\n".join(lines)