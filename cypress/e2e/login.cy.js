describe('Login button', () => {
    it('should redirect to login page', () => {
        cy.visit('/');
        cy.get('a.login').click();
        cy.url().should('include', '#/login');
    });
});

describe('Login', () => {
    it('logins successfully', () => {
        cy.visit('http://localhost:3000/#/login');
        cy.login();
    })
})