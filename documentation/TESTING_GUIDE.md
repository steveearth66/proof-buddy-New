# Equational Reasoning Component - Test Guide

## 🎯 Test Checklist

### Prerequisites:
✅ Django server running on http://localhost:8000
✅ React dev server running on http://localhost:3000
✅ Browser opened to http://localhost:3000/equational-reasoning

---

## Test 1: Basic Proof Workflow
**Goal**: Prove that `(+ 1 2) = 3`

1. **Login** (if not already logged in)
   
2. **Fill Start Proof Form**:
   - Proof Name: `Simple Addition`
   - Tag: `test`
   - Left Hand Side Goal: `(+ 1 2)`
   - Right Hand Side Goal: `3`
   - Click "Start Proof"

3. **Expected**: 
   - ✅ Toast notification: "Proof started!"
   - ✅ See proof interface with LHS premise showing `(+ 1 2)`
   - ✅ Current Side indicator shows "LHS"

4. **Apply Rule**:
   - In the Rule input field, type: `eval +`
   - Press Enter (or click "Generate & Check")

5. **Expected**:
   - ✅ Toast notification: "Rule applied!"
   - ✅ New line appears: `3` with rule `(eval +)`
   - ✅ Now you have 2 lines on LHS

6. **Check Completion**:
   - Click "Check Proof Completion"

7. **Expected**:
   - ✅ Toast notification: "Proof complete! 🎉"
   - ✅ Confetti animation appears!
   - ✅ Modal shows proof is complete

---

## Test 2: Substitution with "eval if" (Bug Fix Verification)
**Goal**: Verify the isMatch fix works

1. **Start New Proof**:
   - Refresh page or clear cache
   - LHS Goal: `(if #t 5 10)`
   - RHS Goal: `5`
   - Click "Start Proof"

2. **Open Substitution Modal**:
   - Click "Substitution" button

3. **Apply Substitution**:
   - Select line 0 (the premise)
   - Rule: `eval if`
   - Substitution: (leave empty)
   - Click "Apply" or "Submit"

4. **Expected**:
   - ✅ Toast notification: "Substitution applied!"
   - ✅ Line updated to: `5`
   - ✅ NO ERROR about type mismatch or node comparison

5. **Check Completion**:
   - Should show proof complete (LHS=5, RHS=5)

---

## Test 3: LHS/RHS Toggle
**Goal**: Test switching between sides

1. **Start Proof**: LHS: `(+ 2 3)`, RHS: `(+ 1 4)`

2. **Work on LHS**:
   - Rule: `eval +`
   - Should get: `5`

3. **Toggle to RHS**:
   - Click "Switch to Right Hand Side"

4. **Expected**:
   - ✅ Current Side shows "RHS"
   - ✅ See RHS premise: `(+ 1 4)`
   - ✅ Rule input is cleared

5. **Work on RHS**:
   - Rule: `eval +`
   - Should get: `5`

6. **Check Completion**:
   - Both sides = 5, proof should be complete!

---

## Test 4: Clear Line
**Goal**: Test deleting proof lines

1. **Generate a few lines**:
   - Start with LHS: `(+ 1 2)`
   - Apply `eval +` → get `3`

2. **Try to clear premise (line 0)**:
   - Click "Clear" on line 0

3. **Expected**:
   - ✅ Toast error: "Cannot clear premise"
   - ✅ Line 0 remains unchanged

4. **Clear line 1**:
   - Click "Clear" on line 1 (the `3`)

5. **Expected**:
   - ✅ Toast: "Line cleared"
   - ✅ Line 1 shows "(empty)"

---

## Test 5: Error Handling
**Goal**: Test validation and error messages

1. **Empty Goals**:
   - Try to start proof with empty LHS or RHS
   - **Expected**: Error message displayed

2. **Identical Goals**:
   - LHS: `3`, RHS: `3`
   - **Expected**: "LHS and RHS goals cannot be identical"

3. **Invalid Rule**:
   - Try rule: `invalid rule name`
   - **Expected**: Backend error displayed in toast

4. **Empty Rule**:
   - Click "Generate & Check" without entering a rule
   - **Expected**: "Please enter a rule"

---

## 🐛 Known Issues to Watch For:

- If substitution modal doesn't appear, check browser console for component import errors
- If confetti doesn't show, check that ProofComplete component is imported correctly
- If authentication redirect happens, make sure you're logged in

---

## ✅ Success Criteria:

All of the following should work:
1. ✅ Start proof with LHS/RHS goals
2. ✅ Apply rules to generate new lines
3. ✅ Substitution works (especially "eval if")
4. ✅ LHS/RHS toggle switches sides correctly
5. ✅ Completion check detects when LHS = RHS
6. ✅ Confetti appears on completion
7. ✅ Clear line works (except premise)
8. ✅ Error messages display correctly

---

## 📝 Report Any Issues:

If something doesn't work:
1. Check browser console (F12) for JavaScript errors
2. Check Django server terminal for backend errors
3. Verify the API endpoints are responding
4. Note the exact error message and steps to reproduce
