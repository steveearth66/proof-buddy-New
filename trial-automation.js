/**
 * Automated trial scenario for ProofBuddy Induction mode
 * 
 * Prerequisites:
 *   npm install puppeteer (run this in the root directory)
 * 
 * This script automates:
 *   1. Logout of any current account
 *   2. Login as steveTeacher3
 *   3. Select Induction mode
 *   4. Enable (f n) definition
 *   5. Fill proof form with specific values
 */

const puppeteer = require('puppeteer');

const CREDENTIALS = {
  username: 'steveTeacher3',
  password: 'Password#4ProofBuddy'
};

const PROOF_CONFIG = {
  name: 'n',
  tag: 'n',
  ivar: 'n',
  aval: '0',
  avar: 'k',
  lhsGoal: '(f n)',
  rhsGoal: '(quotient (* n (+ n 1)) 2)',
  lhsIH: '(f k)',
  rhsIH: '(quotient (* k (+ k 1)) 2)'
};

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function runTrial() {
  console.log('Starting ProofBuddy automated trial...');
  
  const browser = await puppeteer.launch({
    headless: false,
    defaultViewport: null,
    args: ['--start-maximized']
  });

  const page = await browser.newPage();
  
  // Enable console logging from the page
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  
  try {
    // Navigate to the application
    console.log('Navigating to http://localhost:3000...');
    await page.goto('http://localhost:3000', { waitUntil: 'networkidle2' });
    await sleep(1000);

    // Step 1: Check if already logged in
    console.log('Checking if already logged in...');
    const hasLogout = await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button, a'));
      return buttons.some(btn => btn.textContent.includes('Logout'));
    });
    
    if (hasLogout) {
      console.log('Already logged in, logging out first...');
      await page.evaluate(() => {
        const buttons = Array.from(document.querySelectorAll('button, a'));
        const logoutBtn = buttons.find(btn => btn.textContent.includes('Logout'));
        if (logoutBtn) logoutBtn.click();
      });
      await sleep(2000);
      console.log('Logged out successfully');
    } else {
      console.log('Not logged in');
    }

    // Step 2: Click "Log In" button to show login form
    console.log('Clicking Log In button...');
    const loginBtnClicked = await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button, a'));
      const loginBtn = buttons.find(btn => btn.textContent.trim() === 'Log In');
      if (loginBtn) {
        loginBtn.click();
        return true;
      }
      return false;
    });
    
    if (!loginBtnClicked) {
      throw new Error('Could not find Log In button');
    }
    
    await sleep(1500);
    console.log('Login form should be visible');
    
    // Wait for and fill username
    console.log(`Filling username: ${CREDENTIALS.username}...`);
    await page.waitForSelector('input[name="username"]', { timeout: 5000 });
    await page.type('input[name="username"]', CREDENTIALS.username);
    
    // Fill password
    console.log('Filling password...');
    await page.waitForSelector('input[name="password"]');
    await page.type('input[name="password"]', CREDENTIALS.password);
    
    // Click login submit button
    console.log('Clicking submit button...');
    const submitClicked = await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button[type="submit"]'));
      if (buttons.length > 0) {
        buttons[0].click();
        return true;
      }
      return false;
    });
    
    if (!submitClicked) {
      throw new Error('Could not find submit button');
    }
    
    await sleep(3000);
    console.log('Login submitted, waiting for page to load...');

    await sleep(3000);
    console.log('Login submitted, waiting for page to load...');

    // Step 3: Select Induction mode from dropdown
    console.log('Looking for Type of Proof dropdown...');
    await sleep(1000);
    
    // Click the dropdown to open it
    const dropdownClicked = await page.evaluate(() => {
      const dropdown = document.querySelector('select') || 
                       document.querySelector('[role="combobox"]') ||
                       document.querySelector('.dropdown-toggle');
      if (dropdown) {
        dropdown.click();
        return true;
      }
      return false;
    });
    
    if (!dropdownClicked) {
      console.log('Could not find dropdown, trying direct navigation...');
      await page.goto('http://localhost:3000/#/induction-racket', { waitUntil: 'networkidle2' });
      await sleep(2000);
    } else {
      console.log('Dropdown opened, selecting Equational Reasoning: Induction...');
      await sleep(500);
      
      const optionSelected = await page.evaluate(() => {
        // Try select element first
        const select = document.querySelector('select');
        if (select) {
          const options = Array.from(select.options);
          const inductionOption = options.find(opt => 
            opt.textContent.includes('Equational Reasoning: Induction') ||
            opt.textContent.includes('Induction')
          );
          if (inductionOption) {
            select.value = inductionOption.value;
            select.dispatchEvent(new Event('change', { bubbles: true }));
            return true;
          }
        }
        
        // Try dropdown menu items
        const menuItems = Array.from(document.querySelectorAll('.dropdown-item, [role="option"]'));
        const inductionItem = menuItems.find(item => 
          item.textContent.includes('Equational Reasoning: Induction')
        );
        if (inductionItem) {
          inductionItem.click();
          return true;
        }
        
        return false;
      });
      
      if (optionSelected) {
        console.log('Induction mode selected');
        await sleep(2000);
      } else {
        throw new Error('Could not find Induction option in dropdown');
      }
    }

    // Click "Let's Begin" button
    console.log('Clicking Let\'s Begin button...');
    await sleep(500);
    
    const beginClicked = await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button, a, input[type="submit"]'));
      const beginBtn = buttons.find(btn => 
        btn.textContent.includes("Let's Begin") || 
        btn.textContent.includes("Let's begin") ||
        btn.textContent.includes("Begin")
      );
      if (beginBtn) {
        beginBtn.click();
        return true;
      }
      return false;
    });
    
    if (!beginClicked) {
      throw new Error('Could not find Let\'s Begin button');
    }
    
    console.log('Let\'s Begin clicked, waiting for page to load...');
    await sleep(2000);

    // Step 4: Click Proof Utilities to access definitions
    console.log('Clicking Proof Utilities...');
    
    const utilitiesClicked = await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button, a, div[role="button"]'));
      const utilitiesBtn = buttons.find(btn => 
        btn.textContent.includes('Proof Utilities') ||
        btn.textContent.includes('Utilities')
      );
      if (utilitiesBtn) {
        utilitiesBtn.click();
        return true;
      }
      return false;
    });
    
    if (!utilitiesClicked) {
      throw new Error('Could not find Proof Utilities button');
    }
    
    console.log('Proof Utilities opened, selecting Definitions...');
    await sleep(500);
    
    const definitionsClicked = await page.evaluate(() => {
      const items = Array.from(document.querySelectorAll('button, a, li, div[role="menuitem"]'));
      const defItem = items.find(item => 
        item.textContent.includes('Definitions') ||
        item.textContent.includes('Definition')
      );
      if (defItem) {
        defItem.click();
        return true;
      }
      return false;
    });
    
    if (!definitionsClicked) {
      throw new Error('Could not find Definitions menu item');
    }
    
    console.log('Definitions panel opened');
    await sleep(1000);

    // Step 5: Enable (f n) definition
    console.log('Looking for (f n) definition checkbox...');
    
    const checkboxFound = await page.evaluate(() => {
      const checkboxes = Array.from(document.querySelectorAll('input[type="checkbox"]'));
      for (const checkbox of checkboxes) {
        const parent = checkbox.parentElement || checkbox.parentNode;
        const text = parent.textContent;
        if (text.includes('(f n)') || text.includes('f n')) {
          if (!checkbox.checked) {
            checkbox.click();
            return 'clicked';
          }
          return 'already-checked';
        }
      }
      return false;
    });
    
    if (checkboxFound === 'clicked') {
      console.log('Enabled (f n) definition');
      await sleep(500);
    } else if (checkboxFound === 'already-checked') {
      console.log('(f n) definition already enabled');
    } else {
      console.log('Warning: Could not find (f n) definition checkbox');
    }

    // Close Proof Utilities/Definitions panel
    console.log('Closing Proof Utilities...');
    await page.keyboard.press('Escape');
    await sleep(500);

    // Step 6: Fill in the proof configuration form
    console.log('Filling proof configuration form...');
    
    // Fill Name field
    console.log('Filling name field...');
    await page.waitForSelector('input[name="name"]', { timeout: 5000 });
    await page.click('input[name="name"]', { clickCount: 3 });
    await page.type('input[name="name"]', PROOF_CONFIG.name);
    
    // Fill Tag field
    console.log('Filling tag field...');
    await page.click('input[name="tag"]', { clickCount: 3 });
    await page.type('input[name="tag"]', PROOF_CONFIG.tag);
    
    // Fill Induction Variable (ivar)
    console.log('Filling ivar field...');
    await page.click('input[name="ivar"]', { clickCount: 3 });
    await page.type('input[name="ivar"]', PROOF_CONFIG.ivar);
    
    // Fill Anchor Value (aval)
    console.log('Filling aval field...');
    await page.click('input[name="aval"]', { clickCount: 3 });
    await page.type('input[name="aval"]', PROOF_CONFIG.aval);
    
    // Fill Anchor Variable (avar)
    console.log('Filling avar field...');
    await page.click('input[name="avar"]', { clickCount: 3 });
    await page.type('input[name="avar"]', PROOF_CONFIG.avar);

    // Step 6: Fill goal expressions
    console.log('Filling goal expressions...');
    
    // Try different selectors for LHS/RHS goals
    const lhsGoalFilled = await page.evaluate((value) => {
      const selectors = ['input[name="lhsGoal"]', 'textarea[name="lhsGoal"]', 'input[placeholder*="LHS"]', 'textarea[placeholder*="LHS"]'];
      for (const selector of selectors) {
        const elem = document.querySelector(selector);
        if (elem) {
          elem.value = value;
          elem.dispatchEvent(new Event('input', { bubbles: true }));
          elem.dispatchEvent(new Event('change', { bubbles: true }));
          return true;
        }
      }
      return false;
    }, PROOF_CONFIG.lhsGoal);
    
    if (lhsGoalFilled) {
      console.log('LHS Goal filled');
    } else {
      console.log('Warning: Could not find LHS Goal field');
    }
    
    const rhsGoalFilled = await page.evaluate((value) => {
      const selectors = ['input[name="rhsGoal"]', 'textarea[name="rhsGoal"]', 'input[placeholder*="RHS"]', 'textarea[placeholder*="RHS"]'];
      for (const selector of selectors) {
        const elem = document.querySelector(selector);
        if (elem) {
          elem.value = value;
          elem.dispatchEvent(new Event('input', { bubbles: true }));
          elem.dispatchEvent(new Event('change', { bubbles: true }));
          return true;
        }
      }
      return false;
    }, PROOF_CONFIG.rhsGoal);
    
    if (rhsGoalFilled) {
      console.log('RHS Goal filled');
    } else {
      console.log('Warning: Could not find RHS Goal field');
    }

    // Step 7: Fill Induction Hypothesis expressions
    console.log('Filling induction hypothesis expressions...');
    
    const lhsIHFilled = await page.evaluate((value) => {
      const selectors = ['input[name="lhsIH"]', 'textarea[name="lhsIH"]'];
      for (const selector of selectors) {
        const elem = document.querySelector(selector);
        if (elem) {
          elem.value = value;
          elem.dispatchEvent(new Event('input', { bubbles: true }));
          elem.dispatchEvent(new Event('change', { bubbles: true }));
          return true;
        }
      }
      return false;
    }, PROOF_CONFIG.lhsIH);
    
    if (lhsIHFilled) {
      console.log('LHS IH filled');
    } else {
      console.log('Warning: Could not find LHS IH field');
    }
    
    const rhsIHFilled = await page.evaluate((value) => {
      const selectors = ['input[name="rhsIH"]', 'textarea[name="rhsIH"]'];
      for (const selector of selectors) {
        const elem = document.querySelector(selector);
        if (elem) {
          elem.value = value;
          elem.dispatchEvent(new Event('input', { bubbles: true }));
          elem.dispatchEvent(new Event('change', { bubbles: true }));
          return true;
        }
      }
      return false;
    }, PROOF_CONFIG.rhsIH);
    
    if (rhsIHFilled) {
      console.log('RHS IH filled');
    } else {
      console.log('Warning: Could not find RHS IH field');
    }

    console.log('\n=== Form filled successfully! ===');
    console.log('Automation complete. You can now interact with the proof manually.');
    console.log('Browser will remain open. Close it manually when done.\n');
    
    await page.screenshot({ path: 'screenshot-final.png' });
    console.log('Screenshot saved to screenshot-final.png');
    
    // Keep browser open for manual interaction
    // await browser.close();

  } catch (error) {
    console.error('Error during automation:', error.message);
    console.error('Stack:', error.stack);
    await browser.close();
    process.exit(1);
  }
}

runTrial();
