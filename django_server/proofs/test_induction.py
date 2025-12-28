"""
Induction proof tests - complete induction proof demonstrations including base case 
and leap step for both LHS and RHS sides
"""

import os
from expression_tree.ERProofEngine import ERProofLine
from expression_tree.IndProofs import IndProof
from expression_tree.ERCommon import findNode
from expression_tree.ERRuleset import recursiveReplaceNodes, IH
from .test_helpers import show_node_ids
import builtins

SHOW_DETAILS = False  # flip to True locally to see full step logs
_real_print = builtins.print


def print(*args, always=False, **kwargs):
    if SHOW_DETAILS or always:
        _real_print(*args, **kwargs)

totalFails = 0

print("[Summary] IndProofs - Reading test parameters from file", always=True)

# Read induction test inputs from file
test_file = os.path.join(os.path.dirname(__file__), "indTest.txt")
with open(test_file, 'r') as f:
    lines = [line.strip() for line in f.readlines() if line.strip()]

# Print the raw file content with headers (only when detailed)
if SHOW_DETAILS:
    print("[Summary] Induction Parameters From File:")
    for line in lines[:9]:
        print(f"  {line}")
    print()

# Strip everything up to and including the colon
def extract_value(line):
    if ':' in line:
        return line.split(':', 1)[1].strip()
    return line.strip()

struct = extract_value(lines[0])
ivar = extract_value(lines[1])
aval = extract_value(lines[2])
lvar = extract_value(lines[3])
fname = extract_value(lines[4])
ftype = extract_value(lines[5])
fdef = extract_value(lines[6])
lhsPremise = extract_value(lines[7])
rhsPremise = extract_value(lines[8])

inderrs = 0
indProof = IndProof()
from expression_tree.ERCommon import Node
indProof.struct = struct
indProof.indVar = Node(ivar)
indProof.anchorVal = Node(aval)
indProof.leapVar = Node(lvar)

s2 = fname.lstrip("(")               # remove leading (
flet = s2.split()[0]            # split on whitespace, take first

indProof.baseCase.addUDF(fname, ftype, fdef)
indProof.leapStep.addUDF(fname, ftype, fdef)
currLineNum = 9
currExpStr = f"({flet} {aval})"
if currExpStr != extract_value(lines[currLineNum]):
    print(f"ERROR: expected first line of base case to be {currExpStr} but got {extract_value(lines[currLineNum])}", always=True)
else:
    print(f"PASS: first line of base case is {currExpStr}")
pl = ERProofLine(currExpStr)
while currLineNum + 1 < len(lines):
    currLineNum += 1
    targetID = extract_value(lines[currLineNum])
    if targetID =="-1":
        print("End of base case proof")
        break
    currLineNum += 1
    currRuleStr = extract_value(lines[currLineNum])
    print(f"Applying rule {currRuleStr} to node ID {targetID} which is {findNode(pl.exprTree, int(targetID),[])[0]}")
    pl.applyRule(currRuleStr, int(targetID))
    currLineNum += 1
    expectedExpStr = extract_value(lines[currLineNum])
    if str(pl.exprTree) == expectedExpStr:
        print(f"PASS: after applying rule, expression is {expectedExpStr}") 
    else:
        print(f"FAIL: after applying rule, expected expression {expectedExpStr} but got {pl.exprTree}", always=True)
        inderrs += 1
    if inderrs > 0 or SHOW_DETAILS:
        print(f"Completed LHS base case with {inderrs} errors\n", always=True)

rpl = ERProofLine("(quotient (* 0 1) 2)")
if SHOW_DETAILS:
    show_node_ids(rpl.exprTree)

# Test case: Create a simple proof and test __str__ method using addProofLine paradigm
print("\n\nTesting IndProof base case LHS with addProofLine paradigm:\n")
indproof2 = IndProof()

print(f"Induction test parameters from indTest.txt:")
print(f"  form: {struct}")
print(f"  ind var: {ivar}")
print(f"  anchor: {aval}")
print(f"  leap var: {lvar}")
print(f"  func label: {fname}")
print(f"  func type: {ftype}")
print(f"  func def: {fdef}")
print(f"  trying to prove: {lhsPremise}  =  {rhsPremise}")
print()

# Initialize IndProof with structure and induction parameters
indproof2.struct = struct
indproof2.ivar = ivar
indproof2.aval = aval
indproof2.lvar = lvar
indproof2.lhsPremise = lhsPremise
indproof2.rhsPremise = rhsPremise

# Create the base case as a TwoSidedProof
baseCaseProof = indproof2.baseCase
baseCaseProof.LHS.removeUDF('f')
baseCaseProof.LHS.addUDF(fname, ftype, fdef)
if baseCaseProof.LHS.errLog:
    print(f"Error adding UDF to base case LHS: {baseCaseProof.LHS.errLog}", always=True)
    baseCaseProof.LHS.errLog.clear()

# Start with the LHS premise and substitute ivar -> aval using the engine's AST substitution helper
lhs_line = ERProofLine(lhsPremise, baseCaseProof.LHS.debug, baseCaseProof.LHS.ruleSet, generics=baseCaseProof.LHS.generics)
if lhs_line.errLog:
    print(f"Error parsing lhsPremise '{lhsPremise}': {lhs_line.errLog}", always=True)
    lhs_line.errLog.clear()
anchor_line = ERProofLine(aval, baseCaseProof.LHS.debug, baseCaseProof.LHS.ruleSet, generics=baseCaseProof.LHS.generics)
if anchor_line.errLog:
    print(f"Error parsing anchor '{aval}': {anchor_line.errLog}", always=True)
    anchor_line.errLog.clear()
if lhs_line.exprTree and anchor_line.exprTree:
    recursiveReplaceNodes(lhs_line.exprTree, [ivar], [anchor_line.exprTree])
    premise_expr = str(lhs_line.exprTree)
    print(f"Line 0 added as premise: {premise_expr}")
    baseCaseProof.LHS.addProofLine(premise_expr)
else:
    print("Could not build base case premise due to parse errors", always=True)

# Now apply rules from the file using the new paradigm - LHS first
currLineNum = 9
step = 1
while currLineNum + 1 < len(lines):
    currLineNum += 1
    targetID = extract_value(lines[currLineNum])
    if targetID == "-1":
        print("End of base case LHS proof")
        break
    currLineNum += 1
    ruleStr = extract_value(lines[currLineNum])
    currLineNum += 1
    expectedExpStr = extract_value(lines[currLineNum])
    
    prev = baseCaseProof.LHS.getPrevRacket()
    baseCaseProof.LHS.addProofLine(prev, ruleStr, int(targetID))
    
    if baseCaseProof.LHS.errLog:
        print(f"Error applying '{ruleStr}' to node {targetID}: {baseCaseProof.LHS.errLog}", always=True)
        baseCaseProof.LHS.errLog.clear()
    else:
        if str(baseCaseProof.LHS.proofLines[-1].exprTree) == expectedExpStr:
            print(f"PASS: Line {step} applied '{ruleStr}' to node {targetID}, result: {expectedExpStr}")
        else:
            print(f"FAIL: Line {step} applied '{ruleStr}' to node {targetID}, expected {expectedExpStr} but got {baseCaseProof.LHS.proofLines[-1].exprTree}", always=True)
    step += 1

if SHOW_DETAILS:
    print(f"\nComplete IndProof base case LHS proof:\n")
    print(baseCaseProof.LHS)
    print(f"\nBase case LHS proof has {len(baseCaseProof.LHS.proofLines)} lines")

# Now build the RHS base case proof
print(f"\n\nBuilding IndProof base case RHS:\n")

baseCaseProof.RHS.removeUDF('f')
baseCaseProof.RHS.addUDF(fname, ftype, fdef)
if baseCaseProof.RHS.errLog:
    print(f"Error adding UDF to base case RHS: {baseCaseProof.RHS.errLog}", always=True)
    baseCaseProof.RHS.errLog.clear()

# Start with the RHS premise and substitute ivar -> aval using the engine's AST substitution helper
rhs_line = ERProofLine(rhsPremise, baseCaseProof.RHS.debug, baseCaseProof.RHS.ruleSet, generics=baseCaseProof.RHS.generics)
if rhs_line.errLog:
    print(f"Error parsing rhsPremise '{rhsPremise}': {rhs_line.errLog}", always=True)
    rhs_line.errLog.clear()
anchor_line_rhs = ERProofLine(aval, baseCaseProof.RHS.debug, baseCaseProof.RHS.ruleSet, generics=baseCaseProof.RHS.generics)
if anchor_line_rhs.errLog:
    print(f"Error parsing anchor '{aval}': {anchor_line_rhs.errLog}", always=True)
    anchor_line_rhs.errLog.clear()
if rhs_line.exprTree and anchor_line_rhs.exprTree:
    recursiveReplaceNodes(rhs_line.exprTree, [ivar], [anchor_line_rhs.exprTree])
    rhs_premise_expr = str(rhs_line.exprTree)
    print(f"RHS Line 0 added as premise: {rhs_premise_expr}")
    baseCaseProof.RHS.addProofLine(rhs_premise_expr)
else:
    print("Could not build RHS base case premise due to parse errors", always=True)

# Now apply RHS rules from the file
# currLineNum is at "highlight node: -1" from LHS terminator
# Skip: "rule: -1" line, then "expected: (quotient...)" line (RHS premise, already added)
# Then we'll be positioned to read the first RHS rule's "highlight node:" line
currLineNum += 1  # Skip "rule: -1"
currLineNum += 1  # Skip blank or "expected: ..." line for RHS premise

step = 1
while currLineNum + 1 < len(lines):
    currLineNum += 1
    targetID = extract_value(lines[currLineNum])
    if targetID == "-1":
        print("End of base case RHS proof")
        break
    currLineNum += 1
    ruleStr = extract_value(lines[currLineNum])
    currLineNum += 1
    expectedExpStr = extract_value(lines[currLineNum])
    
    prev = baseCaseProof.RHS.getPrevRacket()
    baseCaseProof.RHS.addProofLine(prev, ruleStr, int(targetID))
    
    if baseCaseProof.RHS.errLog:
        print(f"Error applying '{ruleStr}' to node {targetID}: {baseCaseProof.RHS.errLog}", always=True)
        baseCaseProof.RHS.errLog.clear()
    else:
        if str(baseCaseProof.RHS.proofLines[-1].exprTree) == expectedExpStr:
            print(f"PASS: Line {step} applied '{ruleStr}' to node {targetID}, result: {expectedExpStr}")
        else:
            print(f"FAIL: Line {step} applied '{ruleStr}' to node {targetID}, expected {expectedExpStr} but got {baseCaseProof.RHS.proofLines[-1].exprTree}", always=True)
    step += 1

if SHOW_DETAILS:
    print(f"\nComplete IndProof base case RHS proof:\n")
    print(baseCaseProof.RHS)
    print(f"\nBase case RHS proof has {len(baseCaseProof.RHS.proofLines)} lines")

# Check if LHS and RHS final expressions match
if len(baseCaseProof.LHS.proofLines) > 0 and len(baseCaseProof.RHS.proofLines) > 0:
    lhs_final = str(baseCaseProof.LHS.proofLines[-1].exprTree)
    rhs_final = str(baseCaseProof.RHS.proofLines[-1].exprTree)
    if lhs_final == rhs_final:
        indproof2.baseCase.isComplete = True
        print(f"\nBase case proven: LHS = RHS = {lhs_final}", always=True)
    else:
        indproof2.baseCase.isComplete = False
        print(f"\nBase case not yet complete: LHS = {lhs_final}, RHS = {rhs_final}", always=True)
else:
    indproof2.baseCase.isComplete = False

# Build the induction hypothesis by replacing ivar with lvar in both premises
print(f"\n\nBuilding induction hypothesis:\n")

# Create indHypLHS by substituting ivar -> lvar in lhsPremise
lhs_hyp_line = ERProofLine(lhsPremise, baseCaseProof.LHS.debug, baseCaseProof.LHS.ruleSet, generics=baseCaseProof.LHS.generics)
if lhs_hyp_line.errLog:
    print(f"Error parsing lhsPremise for hypothesis '{lhsPremise}': {lhs_hyp_line.errLog}", always=True)
    lhs_hyp_line.errLog.clear()
lvar_line = ERProofLine(lvar, baseCaseProof.LHS.debug, baseCaseProof.LHS.ruleSet, generics=baseCaseProof.LHS.generics)
if lvar_line.errLog:
    print(f"Error parsing leap var '{lvar}': {lvar_line.errLog}", always=True)
    lvar_line.errLog.clear()
if lhs_hyp_line.exprTree and lvar_line.exprTree:
    recursiveReplaceNodes(lhs_hyp_line.exprTree, [ivar], [lvar_line.exprTree])
    indproof2.indHypLHS = lhs_hyp_line.exprTree
    print(f"Induction hypothesis LHS: {indproof2.indHypLHS}")
else:
    print("Could not build indHypLHS due to parse errors", always=True)

# Create indHypRHS by substituting ivar -> lvar in rhsPremise
rhs_hyp_line = ERProofLine(rhsPremise, baseCaseProof.RHS.debug, baseCaseProof.RHS.ruleSet, generics=baseCaseProof.RHS.generics)
if rhs_hyp_line.errLog:
    print(f"Error parsing rhsPremise for hypothesis '{rhsPremise}': {rhs_hyp_line.errLog}", always=True)
    rhs_hyp_line.errLog.clear()
lvar_line_rhs = ERProofLine(lvar, baseCaseProof.RHS.debug, baseCaseProof.RHS.ruleSet, generics=baseCaseProof.RHS.generics)
if lvar_line_rhs.errLog:
    print(f"Error parsing leap var '{lvar}': {lvar_line_rhs.errLog}", always=True)
    lvar_line_rhs.errLog.clear()
if rhs_hyp_line.exprTree and lvar_line_rhs.exprTree:
    recursiveReplaceNodes(rhs_hyp_line.exprTree, [ivar], [lvar_line_rhs.exprTree])
    indproof2.indHypRHS = rhs_hyp_line.exprTree
    print(f"Induction hypothesis RHS: {indproof2.indHypRHS}")
else:
    print("Could not build indHypRHS due to parse errors", always=True)

# Register IH apply rule using the built induction hypothesis, so we can apply it later.
if indproof2.indHypLHS is not None and indproof2.indHypRHS is not None:
    ih_rule = IH(indproof2.indHypLHS, indproof2.indHypRHS)
    # Make available in both baseCase and leapStep contexts
    indproof2.baseCase.ruleSet['apply']['IH'] = ih_rule
    indproof2.leapStep.ruleSet['apply']['IH'] = ih_rule

print(f"\nCreating generics for leap step: {lvar} of type {struct}\n")
leapstep = indproof2.leapStep
# Don't re-add UDF to leap step; IH rule already has the hypothesis encoded
leapstep.addGeneric(lvar, struct)

# Build the leap step premises by replacing ivar with (+ lvar 1)
print(f"\n\nBuilding leap step premises:\n")

# Parse (+ lvar 1) as the successor node
leap_successor_expr = f"(+ {lvar} 1)"
leap_successor_line = ERProofLine(leap_successor_expr, indproof2.leapStep.LHS.debug, indproof2.leapStep.LHS.ruleSet, generics=indproof2.leapStep.LHS.generics)
if leap_successor_line.errLog:
    print(f"Error parsing leap successor '{leap_successor_expr}': {leap_successor_line.errLog}", always=True)
    leap_successor_line.errLog.clear()

# Create leap step LHS premise by substituting ivar -> (+ lvar 1) in lhsPremise
lhs_leap_line = ERProofLine(lhsPremise, indproof2.leapStep.LHS.debug, indproof2.leapStep.LHS.ruleSet, generics=indproof2.leapStep.LHS.generics)
if lhs_leap_line.errLog:
    print(f"Error parsing lhsPremise for leap step '{lhsPremise}': {lhs_leap_line.errLog}", always=True)
    lhs_leap_line.errLog.clear()
if lhs_leap_line.exprTree and leap_successor_line.exprTree:
    recursiveReplaceNodes(lhs_leap_line.exprTree, [ivar], [leap_successor_line.exprTree])
    indproof2.leapStep.LHS.premise = lhs_leap_line.exprTree
    print(f"Leap step LHS premise: {indproof2.leapStep.LHS.premise}")
else:
    print("Could not build leap step LHS premise due to parse errors", always=True)

# Create leap step RHS premise by substituting ivar -> (+ lvar 1) in rhsPremise
rhs_leap_line = ERProofLine(rhsPremise, indproof2.leapStep.RHS.debug, indproof2.leapStep.RHS.ruleSet, generics=indproof2.leapStep.RHS.generics)
if rhs_leap_line.errLog:
    print(f"Error parsing rhsPremise for leap step '{rhsPremise}': {rhs_leap_line.errLog}", always=True)
    rhs_leap_line.errLog.clear()
# Reuse or create another leap_successor for RHS
leap_successor_line_rhs = ERProofLine(leap_successor_expr, indproof2.leapStep.RHS.debug, indproof2.leapStep.RHS.ruleSet, generics=indproof2.leapStep.RHS.generics)
if leap_successor_line_rhs.errLog:
    print(f"Error parsing leap successor for RHS '{leap_successor_expr}': {leap_successor_line_rhs.errLog}", always=True)
    leap_successor_line_rhs.errLog.clear()
if rhs_leap_line.exprTree and leap_successor_line_rhs.exprTree:
    recursiveReplaceNodes(rhs_leap_line.exprTree, [ivar], [leap_successor_line_rhs.exprTree])
    indproof2.leapStep.RHS.premise = rhs_leap_line.exprTree
    print(f"Leap step RHS premise: {indproof2.leapStep.RHS.premise}")
else:
    print("Could not build leap step RHS premise due to parse errors", always=True)

print(f"\n\nTesting leap step LHS proof from indTest.txt:\n")

if indproof2.leapStep.LHS.premise is None:
    print("Cannot test leap step LHS because no premise was built", always=True)
else:
    # Move past the base case RHS terminator and onto the leap step section
    currLineNum += 1  # skip the trailing "rule: -1" after the RHS block
    currLineNum += 1  # now at the leap step LHS expected line

    leap_lhs_expected = extract_value(lines[currLineNum])
    leap_lhs_expr = str(indproof2.leapStep.LHS.premise)
    if leap_lhs_expr == leap_lhs_expected:
        print(f"PASS: leap step LHS premise matches file: {leap_lhs_expr}")
    else:
        print(f"FAIL: leap step LHS premise expected {leap_lhs_expected} but got {leap_lhs_expr}", always=True)

    indproof2.leapStep.LHS.addProofLine(leap_lhs_expr)
    if indproof2.leapStep.LHS.errLog:
        print(f"Error adding leap step LHS premise: {indproof2.leapStep.LHS.errLog}", always=True)
        indproof2.leapStep.LHS.errLog.clear()

    step = 1
    while currLineNum + 1 < len(lines):
        currLineNum += 1
        targetID = extract_value(lines[currLineNum])
        if targetID == "-1":
            print("End of leap step LHS proof")
            break
        currLineNum += 1
        ruleStr = extract_value(lines[currLineNum])
        currLineNum += 1
        expectedExpStr = extract_value(lines[currLineNum])

        prev = indproof2.leapStep.LHS.getPrevRacket()
        num_lines_before = len(indproof2.leapStep.LHS.proofLines)
        indproof2.leapStep.LHS.addProofLine(prev, ruleStr, int(targetID))

        if indproof2.leapStep.LHS.errLog:
            print(f"Error applying '{ruleStr}' to node {targetID}: {indproof2.leapStep.LHS.errLog}", always=True)
            indproof2.leapStep.LHS.errLog.clear()
        else:
            num_lines_after = len(indproof2.leapStep.LHS.proofLines)
            if num_lines_after > num_lines_before:
                result_expr = str(indproof2.leapStep.LHS.proofLines[-1].exprTree)
                if result_expr == expectedExpStr:
                    print(f"PASS: Line {step} applied '{ruleStr}' to node {targetID}, result: {expectedExpStr}")
                else:
                    print(f"FAIL: Line {step} applied '{ruleStr}' to node {targetID}, expected {expectedExpStr} but got {result_expr}", always=True)
            else:
                print(f"WARNING: Line {step} applied '{ruleStr}' but no line was added (count: {num_lines_before} -> {num_lines_after})", always=True)
        step += 1

    if SHOW_DETAILS:
        print(f"\nComplete leap step LHS proof:\n")
        print(indproof2.leapStep.LHS)
        print(f"\nLeap step LHS proof has {len(indproof2.leapStep.LHS.proofLines)} lines")

print(f"\n\nTesting leap step RHS proof from indTest.txt:\n")

if indproof2.leapStep.RHS.premise is None:
    print("Cannot test leap step RHS because no premise was built", always=True)
else:
    # currLineNum should be at the leap step RHS expected line after LHS terminator
    currLineNum += 1  # skip the trailing "rule: -1" after the LHS block
    currLineNum += 1  # now at the leap step RHS expected line

    leap_rhs_expected = extract_value(lines[currLineNum])
    leap_rhs_expr = str(indproof2.leapStep.RHS.premise)
    if leap_rhs_expr == leap_rhs_expected:
        print(f"PASS: leap step RHS premise matches file: {leap_rhs_expr}")
    else:
        print(f"FAIL: leap step RHS premise expected {leap_rhs_expected} but got {leap_rhs_expr}", always=True)

    indproof2.leapStep.RHS.addProofLine(leap_rhs_expr)
    if indproof2.leapStep.RHS.errLog:
        print(f"Error adding leap step RHS premise: {indproof2.leapStep.RHS.errLog}", always=True)
        indproof2.leapStep.RHS.errLog.clear()

    step = 1
    while currLineNum + 1 < len(lines):
        currLineNum += 1
        targetID = extract_value(lines[currLineNum])
        if targetID == "-1":
            print("End of leap step RHS proof")
            break
        currLineNum += 1
        ruleStr = extract_value(lines[currLineNum])
        currLineNum += 1
        expectedExpStr = extract_value(lines[currLineNum])

        prev = indproof2.leapStep.RHS.getPrevRacket()
        num_lines_before = len(indproof2.leapStep.RHS.proofLines)
        
        # Check if this is a math rewrite rule with a substitution node
        if 'rewrite math with' in ruleStr:
            # Extract the substitution expression after "with"
            parts = ruleStr.split(' with ', 1)
            if len(parts) == 2:
                subst_expr = parts[1].strip()
                print(f"DEBUG: Math rewrite at node {targetID}")
                print(f"  Rule: {parts[0].strip()}")
                print(f"  Substitution: {subst_expr}")
                indproof2.leapStep.RHS.addProofLine(prev, parts[0].strip(), int(targetID), subst_expr)
            else:
                indproof2.leapStep.RHS.addProofLine(prev, ruleStr, int(targetID))
        else:
            indproof2.leapStep.RHS.addProofLine(prev, ruleStr, int(targetID))

        if indproof2.leapStep.RHS.errLog:
            print(f"Error applying '{ruleStr}' to node {targetID}: {indproof2.leapStep.RHS.errLog}", always=True)
            indproof2.leapStep.RHS.errLog.clear()
        else:
            num_lines_after = len(indproof2.leapStep.RHS.proofLines)
            if num_lines_after > num_lines_before:
                result_expr = str(indproof2.leapStep.RHS.proofLines[-1].exprTree)
                if result_expr == expectedExpStr:
                    print(f"PASS: Line {step} applied '{ruleStr}' to node {targetID}, result: {expectedExpStr}")
                else:
                    print(f"FAIL: Line {step} applied '{ruleStr}' to node {targetID}, expected {expectedExpStr} but got {result_expr}", always=True)
            else:
                print(f"WARNING: Line {step} applied '{ruleStr}' but no line was added (count: {num_lines_before} -> {num_lines_after})", always=True)
        step += 1

    if SHOW_DETAILS:
        print(f"\nComplete leap step RHS proof:\n")
        print(indproof2.leapStep.RHS)
        print(f"\nLeap step RHS proof has {len(indproof2.leapStep.RHS.proofLines)} lines")

# Check if LHS and RHS final expressions match for the leap step
print(f"\n\nVerifying leap step completion:\n")
if len(indproof2.leapStep.LHS.proofLines) > 0 and len(indproof2.leapStep.RHS.proofLines) > 0:
    lhs_final = str(indproof2.leapStep.LHS.proofLines[-1].exprTree)
    rhs_final = str(indproof2.leapStep.RHS.proofLines[-1].exprTree)
    if lhs_final == rhs_final:
        indproof2.leapStep.isComplete = True
        print(f"[PASS] LEAP STEP COMPLETE: LHS = RHS = {lhs_final}", always=True)
    else:
        indproof2.leapStep.isComplete = False
        print(f"[FAIL] Leap step not yet complete:", always=True)
        print(f"  LHS final: {lhs_final}", always=True)
        print(f"  RHS final: {rhs_final}", always=True)
else:
    indproof2.leapStep.isComplete = False
    print(f"[FAIL] Leap step incomplete: missing proof lines", always=True)

# Final check: verify entire induction proof is complete
summary_status = "PASS" if (indproof2.baseCase.isComplete and indproof2.leapStep.isComplete) else "FAIL"
print("\n[Summary] Induction Proof Status", always=True)
print(f"Base case: {'complete' if indproof2.baseCase.isComplete else 'incomplete'}; "
      f"Leap step: {'complete' if indproof2.leapStep.isComplete else 'incomplete'}", always=True)
if summary_status == "PASS":
    print(f"Result: Induction proof complete — {lhsPremise} = {rhsPremise}", always=True)
else:
    print("Result: Induction proof incomplete", always=True)

# Show full induction proof summary using __str__ on indproof2
if SHOW_DETAILS:
    print("\n[Summary] Induction Proof Output")
    print(indproof2)

print("\nInduction proof tests completed!\n", always=True)
