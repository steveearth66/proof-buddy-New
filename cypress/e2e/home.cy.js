describe('Home Page', () => {
  it('loads successfully', () => {
    cy.visit('http://localhost:3000/');
    cy.contains('Proof Buddy');
  })
})