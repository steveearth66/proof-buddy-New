**PROOFBUDDY - FREQUENTLY ASKED QUESTIONS**

Version: 1.0

Date: February 23, 2026

Author: Ahsan Nadeem

**GETTING STARTED**

Q1: What is ProofBuddy?

A: A tool for creating mathematical proofs. It supports:

Equational Reasoning (ER): Equation-based proofs

Induction Racket (IR): Proofs with induction variables

Q2: How do I log in?

A: URL: https://proofbuddy.net/

Click login at the top right.

Provide your student or teacher credentials and then click login at the bottom.

**CREATING PROOFS**
Q3: How do I create a proof?

A: Click "Create New Proof"

Enter name (required), tag (optional)

Select proof type (ER or IR)

Fill required fields

Click "Start Proof" and confirm

Q4: What happens if I don't enter a name?

A: You'll see a "Name is required" error. The name field turns red until you provide one.

Q5: Can I use special characters in names/tags?

A: Yes. Special characters (@#$%) are accepted.

Q6: Can I save an incomplete proof?

A: Yes. It's saved automatically and appears in "All Proofs" to continue later.

**DUPLICATE PROOFS**
Q7: Can I create multiple proofs with the same name?

A: Yes. The system allows duplicates. Both versions remain in the database and appear in your proof list.

Q8: What happens if I delete a proof that has duplicates?

A: It disappears from the UI, but the database still retains all copies.

**INDUCTION RACKET PROOFS**
Q9: What makes IR proofs different?

A: IR proofs use:

Induction variable: What you're proving over

Anchor variable: Base case value

Leap variable: Step case value

UDFs: User-defined functions for the proof

Q10: Can I reuse induction/anchor/leap variables across proofs?

A: Yes! Testing confirms reusing these variables does not overwrite existing proofs. All proofs coexist.

**COMMON ISSUES**
Q11: I deleted a proof but it's still there after refreshing. Why?

A: Known behavior: UI deletion removes it from view but not permanently from the database. Contact an admin for complete removal.

Q12: I see duplicate proofs in my list. Is this a bug?

A: The system currently allows duplicates. Check with your instructor on whether this is expected behavior.

Q13: Fields are showing warnings. What's wrong?

A: Required fields are empty. Fill them in and the warnings disappear.

📋 **QUICK REFERENCE**
If you want to...	Do this...
Create ER proof	Name + LHS + RHS
Create IR proof	Name + induction + anchor + leap + UDF
Check base case	Click "Check proof" (green banner = success)
Report a bug	Note steps + expected/actual + screenshot