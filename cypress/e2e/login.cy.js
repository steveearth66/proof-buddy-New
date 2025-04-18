describe('Login', () => {
    it('logins successfully', () => {
        cy.visit('http://localhost:3000/#/login');
        cy.login();
    })
})