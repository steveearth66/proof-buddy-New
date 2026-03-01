import { test, expect } from '@playwright/test';

const STUDENT = { username: 'student', password: 'password123!' };
const BASE_URL = 'http://localhost:3000/#/';
const LHS_GOAL = '(+ 1 1)';
const RHS_GOAL = '2';
const LHS_RULE = 'eval +';

// Helper function for login
async function login(page, credentials) {
  await page.goto(BASE_URL + "login");
  await page.fill('#loginUsername', credentials.username);
  await page.fill('#loginPassword', credentials.password);
  await page.click('button[type="submit"]');
  await page.getByRole('button', { name: 'Let\'s Begin' }).click();
}

// Helper for creating proofs
async function createProof(page, name, tag) {
  await page.getByRole('textbox', { name: 'Name' }).click();
  await page.getByRole('textbox', { name: 'Name' }).fill(name);
  await page.getByRole('textbox', { name: '# Tag' }).click();
  await page.getByRole('textbox', { name: '# Tag' }).fill(tag);
  await page.getByRole('textbox', { name: 'LHS Goal' }).click();
  await page.getByRole('textbox', { name: 'LHS Goal' }).fill(LHS_GOAL);
  await page.getByRole('textbox', { name: 'RHS Goal' }).click();
  await page.getByRole('textbox', { name: 'RHS Goal' }).fill(RHS_GOAL);
  await page.getByRole('button', { name: 'Start Equational Reasoning' }).click();
  await page.getByRole('button', { name: 'Start Proof' }).click();
  await page.getByText('001').click();
  await page.getByRole('textbox', { name: 'LHS Rule' }).nth(1).click();
  await page.getByRole('textbox', { name: 'LHS Rule' }).nth(1).fill(LHS_RULE);
  await page.getByRole('button', { name: 'Generate & Check' }).click();
  await page.locator('#dropdown-autoclose-true').click();
  await page.getByRole('button', { name: 'Check Current Proof' }).click();
  await expect(page.getByRole('heading', { name: 'Proof Complete!!!!!!!!' })).toBeVisible();
}


async function navigateToNewProofPage(page) {
  await page.getByRole('heading', { name: 'Proof Complete!!!!!!!!' }).click(); // Navigate back to proofs page
  await page.locator('#dropdown-autoclose-true').click();

  page.on("dialog", async (dialog) => {
    await dialog.accept();
  });

  await page.getByRole('button', { name: 'Clear Proof' }).click();
}

async function createDuplicateProof(page, name, tag) {
  await page.getByRole('textbox', { name: 'Name' }).click();
  await page.getByRole('textbox', { name: 'Name' }).fill(name);
  await page.getByRole('textbox', { name: '# Tag' }).click();
  await page.getByRole('textbox', { name: '# Tag' }).fill(tag);
  await page.getByRole('textbox', { name: 'LHS Goal' }).click();
  await page.getByRole('textbox', { name: 'LHS Goal' }).fill(LHS_GOAL);
  await page.getByRole('textbox', { name: 'RHS Goal' }).click();
  await page.getByRole('textbox', { name: 'RHS Goal' }).fill(RHS_GOAL);
  await page.getByRole('button', { name: 'Start Equational Reasoning' }).click();
  await page.getByRole('button', { name: 'Overwrite & Start' }).click();
  await page.getByRole('button', { name: 'Start Proof' }).click();
  await page.getByText('001').click();
  await page.getByRole('textbox', { name: 'LHS Rule' }).nth(1).click();
  await page.getByRole('textbox', { name: 'LHS Rule' }).nth(1).fill(LHS_RULE);
  await page.getByRole('button', { name: 'Generate & Check' }).click();
  await page.locator('#dropdown-autoclose-true').click();
  await page.getByRole('button', { name: 'Check Current Proof' }).click();
  await expect(page.getByRole('heading', { name: 'Proof Complete!!!!!!!!' })).toBeVisible();
  await page.getByRole('heading', { name: 'Proof Complete!!!!!!!!' }).click();
}

// TEST 1: Basic Duplicate Creation
test('Test 1: Duplicate proofs should not both appear in UI', async ({ page }) => {
  await login(page, STUDENT);
  const proofName = `AutoTest_${Date.now()}`;
  const tag = 'Version 1';

  await createProof(page, proofName, tag);

  await navigateToNewProofPage(page);

  await createDuplicateProof(page, proofName, tag); // Note: Still using Version 1 tag

  await page.goto(`${BASE_URL}proofs`);
  
  const loading = await page.locator('.proofs', { hasText: 'Loading...' });
  await loading.waitFor({ state: 'detached' });

  const content = await page.locator('.proof-card').filter({ hasText: `Proof: ${proofName} - ${tag}` });
  expect(content).toHaveCount(1);
});

// TEST 2: Proof Completion Status
test('Test 2: Check that when a proof is completed, it is marked as done in the All Proofs page', async ({ page }) => {
  await login(page, STUDENT);
  const proofName = `AutoTest_${Date.now()}`;
  const tag = 'Version 1';

  await createProof(page, proofName, tag);
  await page.goto(`${BASE_URL}proofs`);

  const loading = await page.locator('.proofs', { hasText: 'Loading...' });
  await loading.waitFor({ state: 'detached' });

  const regExp = new RegExp(`${proofName} - ${tag}.*Completed: True`, 's');
  expect(page.locator('.proof-card').nth(0)).toContainText(regExp);
});

