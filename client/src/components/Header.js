import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import Container from 'react-bootstrap/Container';
import Nav from 'react-bootstrap/Nav';
import Navbar from 'react-bootstrap/Navbar';
import NavDropdown from 'react-bootstrap/NavDropdown';
import Modal from 'react-bootstrap/Modal';
import Button from 'react-bootstrap/Button';
import { Link, useLocation } from 'react-router-dom';
import '../scss/_header.scss';

const helpContent = {
  version: {
    title: 'Version Log',
    body: (
      <>
        <p><strong>Version: 2026-10-23 04:30</strong></p>
        <p><strong>Commit: updating the version log</strong></p>
        <p>
          This build reflects the most recent Stage deployment commit. Version
          information is displayed here for traceability and release tracking.
        </p>
      </>
    ),
  },
  feedback: {
    title: 'Report Bug / Feedback',
    body: (
      <>
        <p>
          Have you found a bug or have feedback to improve the app? Please email the
          course team at <strong>se435@drexel.edu</strong> with a brief description of
          the issue, what you were doing, and any relevant screenshots or steps to
          reproduce it.
        </p>
        <p>We appreciate your feedback.</p>
      </>
    ),
  },
  about: {
    title: 'About Proof Buddy',
    body: (
      <>
        <p>
          Proof Buddy is a proof-building and reasoning support tool designed to help
          students practice formal proof construction and verification.
        </p>
        <p>
          It supports induction and equational reasoning workflows and is intended for
          coursework and learning support.
        </p>
      </>
    ),
  },
};

/**
 * Header component that renders the navigation bar at the top of the application.
 * It uses the authentication context to determine if a user is logged in and
 * changes the navigation items accordingly.
 */
const Header = () => {
  const { user } = useAuth();
  const location = useLocation();
  const [activeHelp, setActiveHelp] = useState(null);
  const allProofsHref = location.pathname.startsWith('/induction')
    ? '/proofs?type=induction'
    : '/proofs';

  const handleHelpSelection = (key) => {
    setActiveHelp(key);
  };

  const activeHelpContent = activeHelp ? helpContent[activeHelp] : null;

  return (
    <>
      <header className={`header nav-container`}>
        <Navbar collapseOnSelect expand="lg" fixed="top">
          <Container>
            <Navbar.Brand as={Link} to="/">
              Proof Buddy
            </Navbar.Brand>
            <Navbar.Toggle
              aria-controls="responsive-navbar-nav"
              aria-label="Toggle navigation"
            />
            <Navbar.Collapse id="responsive-navbar-nav">
              <Nav className="me-auto">
                {user && (
                  <>
                    <Nav.Item>
                      <Nav.Link as={Link} to="/courses" className="top-menu-item">
                        Courses
                      </Nav.Link>
                    </Nav.Item>
                    <Nav.Item>
                      <Nav.Link as={Link} to={allProofsHref} className="top-menu-item">
                        All Proofs
                      </Nav.Link>
                    </Nav.Item>
                  </>
                )}
                <NavDropdown
                  renderMenuOnMount={true}
                  title="Help"
                  id="collapsible-nav-dropdown"
                >
                  <NavDropdown.Item
                    as="button"
                    type="button"
                    onClick={() => handleHelpSelection('version')}
                  >
                    Version Log
                  </NavDropdown.Item>
                  <NavDropdown.Item
                    as="button"
                    type="button"
                    onClick={() => handleHelpSelection('feedback')}
                  >
                    Report Bug / Feedback
                  </NavDropdown.Item>
                  <NavDropdown.Divider />
                  <NavDropdown.Item
                    as="button"
                    type="button"
                    onClick={() => handleHelpSelection('about')}
                  >
                    About
                  </NavDropdown.Item>
                </NavDropdown>
              </Nav>
              {user ? (
                <Nav as={"ul"}>
                  <Nav.Item as={"li"}>
                    <Nav.Link as={Link} to="#" className="profile">
                      <i
                        className={`fa-solid ${user.is_student ? "fa-graduation-cap" : "fa-user-tie"}`}
                      ></i>{" "}
                      {user.username}
                    </Nav.Link>
                  </Nav.Item>
                  <Nav.Item as={"li"}>
                    <Nav.Link as={Link} to="/logout" className="orange-link">
                      Logout
                    </Nav.Link>
                  </Nav.Item>
                </Nav>
              ) : (
                <Nav as={"ul"}>
                  <Nav.Item as={"li"}>
                    <Nav.Link as={Link} to="/login" className="login">
                      Log In
                    </Nav.Link>
                  </Nav.Item>
                  <Nav.Item as={"li"}>
                    <Nav.Link as={Link} to="/signup" className="orange-link">
                      Sign Up
                    </Nav.Link>
                  </Nav.Item>
                </Nav>
              )}
            </Navbar.Collapse>
          </Container>
        </Navbar>
      </header>

      {activeHelpContent && (
        <Modal show={true} onHide={() => setActiveHelp(null)} centered>
          <Modal.Header closeButton>
            <Modal.Title>{activeHelpContent.title}</Modal.Title>
          </Modal.Header>
          <Modal.Body>{activeHelpContent.body}</Modal.Body>
          <Modal.Footer>
            <Button variant="primary" onClick={() => setActiveHelp(null)}>
              Close
            </Button>
          </Modal.Footer>
        </Modal>
      )}
    </>
  );
};

export default Header;
