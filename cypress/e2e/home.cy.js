describe('Home Page', () => {
  it('loads successfully', () => {
    cy.visit('/');
    cy.contains('Proof Buddy');
  })
})