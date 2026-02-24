**Equational Reasoning**

Test 1: Basic Duplicate Creation - Monday 02/02/2026
1. Create proof "Project_Alpha" with content "Version 1"
2. Create another proof "Project_Alpha" with content "Version 2"
3. erify only "Version 2" appears in proof list
4. Verify "Version 1" is not visible in UI

Results: Failed due to misunderstanding (both proofs co-exist)

Test 2: Data Integrity Verification - Tuesday 02/03//2026
1. Create proof "Budget_Q1" with unique description "Original"
2. Create proof "Budget_Q1" with unique description "Updated"
3. Verify UI shows "Updated" content
4. Check browser console/network for any errors

Results: Passed, because “Updated”, in addition to “Original” show up in the UI

Test 3: Delete Operation - Wednesday 02/05/2026
1. Create proof "TempDoc" → Create duplicate "TempDoc"
2. Delete "TempDoc" from UI
3. Verify deletion completes without error
4. Verify no proofs named "TempDoc" remain visible

Results: Failed, because I deleted the overridden TempDoc proof from the UI, but the database still has both duplicates 

Test 4: Empty/Null Name Handling 02/09/20226
1. Create a proof with no name (“”) with an arbitrary tag # value
2. Provide the LHS and RHS goals, given that the chosen proof type is “Equational Reasoning”
3. lick “Start Equational Reasoning Proof”
4. You will see a “Name is required” error and the empty field is red w/ a “Please provide a proof name” message

Results: Passed, because the proof name is a required field, like the RHS and LHS goals.

Test 5: Special Character Safety 02/10/2026
1. Create a proof with a random name and tag containing special characters
2. Provide the LHS and RHS goals, given that the chosen proof type is “Equational Reasoning”
3. Click “Start Equational Reasoning Proof”
4. You will see a “Confirm Start Proof” pop-up; click Start Proof”
5. You will be routed to the proof page

Results: Passed, because the proof name was not left empty

Test 6: Multi-Account Same Name 02/11/2026
1. Create an ER proof with a student account
2. Create a duplicate ER proof with a teacher account
3. Both should have the same name and tag
4. Both should exist in the database

Results: Passed

Test 7: Saving an Empty Proof 02/12/2026
1. Create an ER proof with a student/teacher  account
2. Provide a name and tag
3. Click “Start Equational Reasoning Proof”
4. You will see a “Confirm Start Proof” pop-up; click Start Proof”

Results: Passed, because the incomplete proof is saved to the database and it will be found in ‘All Proofs’.

Test 8: Line Highlights (rules highlight, and results highlight) 02/14/2026
1. Create and start an ER proof with a nonempty name, tag as well as LHS and RHS goals
2. Click “Start Equational Reasoning Proof”
3. The current LHS should be the same as the first line of the proof
4. Click on the second line and provide the LHS rule, and click “Generate and check”
5. Both lines of the proof should be highlighted with the proof result also circled with a red line.

Result: Passed, because both the rules and the results are uniquely highlighted. 

Test 9: Line Overlap (Target expression is bigger than the results expression) 02/15/2026
1. Create and start an ER proof with a nonempty name, tag as well as LHS and RHS goals
2. Click “Start Equational Reasoning Proof”
3. The current LHS should be the same as the first line of the proof
4. Click on the second line and provide the LHS rule, and click “Generate and check”
5. The target expression (the first line) is bigger than the results expression (the second line)

Result: Passed.

**Induction Rackets**

Test 10: Creating an Induction Racket Proof Wherein the Leap Variable Already Exists
1. Create and start an IR proof with a nonempty name, tag, induction variable, anchor variable, and leap variable as well as the left hand side goal and right hand side goal.
2. Also create a new UDF with a label, type, expression and click “Create Definition”
3. Start with the Base Case by providing the first two lines, in the form of the UDF in terms of the base value. Click “Check proof” to validate the base case before starting the leap case.
4. After seeing a green banner confirming “base case completed”, switch over the leap case. Repeat step 3 without creating a new UDF for the leap case. Afterwards click “Check proof” to validate the completion of the entire proof.
5. Now create a separate proof with an identical leap variable by repeating steps 1-4.
6. After completing it check the database and confirm that both proofs exist.

Result: Passed, because having a same leap variable won’t cause overwriting of the previous proof

Test 11: Creating an Induction Racket Proof Wherein the Anchor Variable Already Exists
1. Create and start an IR proof with a nonempty name, tag, induction variable, anchor variable, and leap variable as well as the left hand side goal and right hand side goal.
2. Also create a new UDF with a label, type, expression and click “Create Definition”
3. Start with the Base Case by providing the first two lines, in the form of the UDF in terms of the base value. Click “Check proof” to validate the base case before starting the leap case.
4. After seeing a green banner confirming “base case completed”, switch over the leap case. Repeat step 3 without creating a new UDF for the leap case. Afterwards click “Check proof” to validate the completion of the entire proof.
5. Now create a separate proof with an identical anchor variable by repeating steps 1-4.
6. After completing it check the database and confirm that both proofs exist.

Result: Passed, because having a same anchor variable won’t cause overwriting of the previous proof

Test 12: Creating an Induction Racket Proof Wherein the Induction Variable Already Exists
1. Create and start an IR proof with a nonempty name, tag, induction variable, anchor variable, and leap variable as well as the left hand side goal and right hand side goal.
2. Also create a new UDF with a label, type, expression and click “Create Definition”
3. Start with the Base Case by providing the first two lines, in the form of the UDF in terms of the base value. Click “Check proof” to validate the base case before starting the leap case.
4. After seeing a green banner confirming “base case completed”, switch over the leap case. Repeat step 3 without creating a new UDF for the leap case. Afterwards click “Check proof” to validate the completion of the entire proof.
5. Now create a separate proof with an identical anchor variable by repeating steps 1-4.
6. After completing it check the database and confirm that both proofs exist.

Result: Passed, because having a same induction variable won’t cause overwriting of the previous proof

Test 13: Creating an Induction Racket Proof to Test for Page Resizing
1. Create and start an IR proof with a nonempty name, tag, induction variable, anchor variable, and leap variable as well as the left hand side goal and right hand side goal.
2. Also create a new UDF with a label, type, expression and click “Create Definition”
Start with the Base Case by providing the first two lines, in the form of the UDF in terms of the base value. Click “Check proof” to validate the base case before starting the leap case.
3. After seeing a green banner confirming “base case completed”, switch over the leap case. Repeat step 3 without creating a new UDF for the leap case. Afterwards click “Check proof” to validate the completion of the entire proof.
4. Click on the browser context and resize the page to see Proof Buddy’s CSS responsiveness. 

Result: passed

Test 14: Test for the Collapsible
1. Create and start an IR proof with a nonempty name, tag, induction variable, anchor variable, and leap variable as well as the left hand side goal and right hand side goal.
2. Also create a new UDF with a label, type, expression and click “Create Definition”
Start with the Base Case by providing the first two lines, in the form of the UDF in terms of the base value. Click “Check proof” to validate the base case before starting the leap case.
3. After seeing a green banner confirming “base case completed”, switch over the leap case. Repeat step 3 without creating a new UDF for the leap case. Afterwards click “Check proof” to validate the completion of the entire proof.
4. Click on the collapsible and observe the new UI differences.

Result: passed

Test 15: Test for the Placeholder Text and Warnings in Induction 
1. Create and start an IR proof with a nonempty name, tag, induction variable, anchor variable, and leap variable as well as the left hand side goal and right hand side goal.
2. Now delete the value provided to one of the fields.
3. You will see the error messages for the empty fields and the placeholder text will reappear

Result: passed
