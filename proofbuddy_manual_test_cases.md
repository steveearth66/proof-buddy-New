Test 1: Basic Duplicate Creation
1. Create proof "Project_Alpha" with content "Version 1"
2. Create another proof "Project_Alpha" with content "Version 2"
3. Verify only "Version 2" appears in proof list
4. Verify "Version 1" is not visible in UI
Result: Failed due to misunderstanding (both proofs co-exist)

Test 2: Data Integrity Verification
1. Create proof "Name" with unique description "Original"
2. Create proof "Name" with unique description "Updated"
3. Verify UI shows "Updated" content
4. Check browser console/network for any errors
Result: Passed, because “Updated”, in addition to “Original” show up in the UI

Test 3: Delete Operation
1. Create proof "TempDoc" → Create duplicate "TempDoc"
2. Delete "TempDoc" from UI
3. Verify deletion completes without error
4. Verify no proofs named "TempDoc" remain visible
Result: Failed, because I deleted the overridden TempDoc proof from the UI, but the database still has both duplicates 

Test 4: Empty/Null Name Handling
1. Create a proof with no name (“”) with an arbitrary tag # value
2. Provide the LHS and RHS goals, given that the chosen proof type is “Equational Reasoning”
3. Click “Start Equational Reasoning Proof”
4. You will see a “Name is required” error and the empty field is red w/ a “Please provide a proof name” message
Result: Passed, because the proof name is a required field, like the RHS and LHS goals.


Test 5: Special Character Safety
1. Create a proof with a random name and tag containing special characters
2. Provide the LHS and RHS goals, given that the chosen proof type is “Equational Reasoning”
3. Click “Start Equational Reasoning Proof”
4. You will see a “Confirm Start Proof” pop-up; click Start Proof”
5. You will be routed to the proof page
Result: Passed, because the proof name was not left empty

Test 6: Multi-Account Same Name
1. Create an ER proof with a student account
2. Create a duplicate ER proof with a teacher account
3. Both should have the same name and tag
4. Both should exist in the database
Result: Passed

Test 7: Saving an Empty Proof
1. Create an ER proof with a student/teacher  account
2. Provide a name and tag
3. Click “Start Equational Reasoning Proof”
4. You will see a “Confirm Start Proof” pop-up; click Start Proof”
Result: Passed, because the incomplete proof is saved to the database and it will be found in ‘All Proofs’.

Test 8: Line Highlights (rules highlight, and results highlight)
1. Create and start an ER proof with a nonempty name, tag as well as LHS and RHS goals
2. Click “Start Equational Reasoning Proof”
3. The current LHS should be the same as the first line of the proof
4. Click on the second line and provide the LHS rule, and click “Generate and check”
5. Both lines of the proof should be highlighted with the proof result also circled with a red line.
Result: Passed, because both the rules and the results are uniquely highlighted. 

Test 9: Line Overlap (Target expression is bigger than the results expression)
1. Create and start an ER proof with a nonempty name, tag as well as LHS and RHS goals
2. Click “Start Equational Reasoning Proof”
3. The current LHS should be the same as the first line of the proof
4. Click on the second line and provide the LHS rule, and click “Generate and check”
5. The target expression (the first line) is bigger than the results expression (the second line)
Result: Passed.
