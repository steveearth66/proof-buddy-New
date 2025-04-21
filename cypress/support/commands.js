Cypress.Commands.add("login", () => {
    const username = Cypress.env("username");
    const password = Cypress.env("password");
  
    if (!username || !password) {
      throw new Error("Missing CYPRESS credentials. Add them to cypress.env.json");
    }
  
    cy.get('input[name="username"]').type(username);
    cy.get('input[name="password"]').type(password, { log: false });
    cy.get('button[type="submit"]').click();
  });