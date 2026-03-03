**Proof Buddy Test Automation Markdown**

**Context**

This markdown describes the purpose and nature of the test automation. This test automation serves as a starting point for automating test scenarios for Equational Reasoning and beyond. While more test cases can be automated for Equational Reasoning, this automation also serves as a starting point for the Induction Racket page test scenarios. This, along with the manual test case markdown file, can help future QA Engineers/Test Automation Engineers get started with the Proof Buddy project.  

**Location/Directory**

The equational.reasoning.spec.js file is located within the tests directory right below the node modules and test results subdirectories. The manual test case markdown file is also located along the same subdirectory for ease of reference.

**How to Run/Execute**

To run this file, please ensure that you are changing the directory into the tests subfolder in the terminal command line interface. Afterwords, run the following command: npx playwright test tests/equational.reasoning.spec.js --headed OR npx playwright test tests/equational.reasoning.spec.js if you chose not to view the browser while the test execution is underway.

**Review Results**

The test results can be viewed in the terminal command line after the test execution is finished. Also, when the test script fails, the terminal provides the exact line where the point of failure occurs. This can greatly help with future troubleshooting, as well.
