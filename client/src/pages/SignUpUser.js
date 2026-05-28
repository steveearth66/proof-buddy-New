import React, { useState } from 'react';
import { useNavigate } from "react-router-dom";
import Button from "react-bootstrap/Button";
import Container from "react-bootstrap/Container";
import Form from "react-bootstrap/Form";
import Col from "react-bootstrap/Col";
import Row from "react-bootstrap/Row";
import Alert from "react-bootstrap/Alert";
import Spinner from "react-bootstrap/Spinner";
import MainLayout from "../layouts/MainLayout";
import authService from "../services/authService";
import validateField from "../utils/formValidationUtils";
import { useInputState } from "../hooks/useInputState";
import { usePasswordVisibility } from "../hooks/usePasswordVisibility";
import { useFormValidation } from "../hooks/useFormValidation";
import { useFormSubmit } from "../hooks/useFormSubmit";
import "../scss/_forms.scss";
import "../scss/_signup.scss";

/**
 * SignUpUser component facilitates the registration process for new users,
 * supporting roles as student or instructor.
 * It incorporates several custom hooks for form management, including state handling, validation, and submission.
 * Upon successful registration, users are redirected for email verification with a token stored in cookies.
 */
const SignUpUser = ({ role }) => {
  const initialValues = {
    username: "",
    email: "",
    password: "",
    confirmPassword: ""
  };
  const [formValues, handleChange] = useInputState(initialValues);
  const [passwordType, toggleVisibility] = usePasswordVisibility();
  const [serverError, setServerError] = useState(null);
  const [validationMessages, handleBlur, setAllTouched, isFormValid] =
    useFormValidation(formValues, validateField);
  const [validated, setValidated] = useState(false);
  const [accountCreated, setAccountCreated] = useState(false); // NOTE: remove after permanent email verification solution is found
  const navigate = useNavigate();

  const handleSignUpUser = async () => {
    const userData = {
      username: formValues.username,
      email: formValues.email,
      password: formValues.password,
      is_instructor: role === "instructor"
    };

    try {
      setServerError(null);
      const response = await authService.registerUser(userData);
      if (response.message === "Account created!") {
        // NOTE: uncomment after permanent email verification solution is found
        //navigate("/verify-email", { state: { email: formValues.email } });
        setAccountCreated(true); // NOTE: remove after permanent email verification solution is found
      }
    } catch (error) {
      setServerError(error?.response?.data?.message || "Sign up failed. Please try again.");
    }
  };

  const { handleSubmit } = useFormSubmit(
    isFormValid,
    setValidated,
    setAllTouched,
    handleSignUpUser
  );

  // NOTE: remove after permanent email verification solution is found
  if (accountCreated) {
    setTimeout(() => {
      navigate("/");
    }, 2500);
  }

  return (
    <MainLayout>
      <Container className="signup-container">
        <Row className="justify-content-md-center">
          <Col xs={15} md={10} lg={5}>
            <h1>
              Sign up as {role === "student" ? "a" : "an"} {role}
            </h1>
            {(serverError?.username ||
              serverError?.email ||
              serverError?.password) && (
              <Alert variant={"danger"}>
                There was an error creating your account
              </Alert>
            )}

            {/*NOTE: remove after email verification solution is found*/}
            {
              accountCreated && (
                <Alert variant={"success"}>
                  Account created! Redirecting to home page...
                  <Spinner className="float-end" animation="border"/>
                </Alert>
              )
            }

            <Form noValidate validated={validated} onSubmit={handleSubmit}>
              <Form.Group className="signup-username">
                <Form.Floating className="mb-3">
                  <Form.Control
                    id="signupUsername"
                    name="username"
                    type="text"
                    placeholder="Enter username"
                    value={formValues.username}
                    onBlur={() => {
                      handleBlur("username");
                      setServerError({ ...serverError, username: null });
                    }}
                    onChange={handleChange}
                    isInvalid={
                      !!validationMessages.username || !!serverError?.username
                    }
                    required
                  />
                  <label htmlFor="signupUsername">Username</label>
                  <Form.Control.Feedback type="invalid">
                    {validationMessages.username || serverError?.username}
                  </Form.Control.Feedback>
                </Form.Floating>
              </Form.Group>

              <Form.Group className="signup-email">
                <Form.Floating className="mb-3">
                  <Form.Control
                    id="signupEmail"
                    name="email"
                    type="email"
                    placeholder="Enter email"
                    value={formValues.email}
                    onBlur={() => {
                      handleBlur("email");
                      setServerError({ ...serverError, email: null });
                    }}
                    onChange={handleChange}
                    isInvalid={
                      !!validationMessages.email || !!serverError?.email
                    }
                    required
                  />
                  <label htmlFor="signupEmail">Email</label>
                  <Form.Control.Feedback type="invalid">
                    {validationMessages.email || serverError?.email}
                  </Form.Control.Feedback>
                </Form.Floating>
              </Form.Group>

              <Form.Group className="signup-password">
                <Form.Floating className="mb-3">
                  <Form.Control
                    id="signupPassword"
                    name="password"
                    type={passwordType}
                    placeholder="Enter password"
                    value={formValues.password}
                    onBlur={() => {
                      handleBlur("password");
                      setServerError({ ...serverError, password: null });
                    }}
                    onChange={handleChange}
                    isInvalid={
                      !!validationMessages.password || !!serverError?.password
                    }
                    required
                  />
                  <label htmlFor="signupPassword">Password</label>
                  <i
                    className={`fa-solid ${passwordType === "text" ? "fa-eye" : "fa-eye-slash"}`}
                    onClick={toggleVisibility}
                  ></i>
                  <Form.Control.Feedback type="invalid">
                    {validationMessages.password || serverError?.password}
                  </Form.Control.Feedback>
                </Form.Floating>
              </Form.Group>

              <Form.Group className="signup-confirm-password">
                <Form.Floating className="mb-3">
                  <Form.Control
                    id="signupConfirmPassword"
                    name="confirmPassword"
                    type="password"
                    placeholder="Enter confirm password"
                    value={formValues.confirmPassword}
                    onBlur={() => handleBlur("confirmPassword")}
                    onChange={handleChange}
                    isInvalid={!!validationMessages.confirmPassword}
                    required
                  />
                  <label htmlFor="signupConfirmPassword">
                    Confirm Password
                  </label>
                  <Form.Control.Feedback type="invalid">
                    {validationMessages.confirmPassword ||
                      "Please confirm your password."}
                  </Form.Control.Feedback>
                </Form.Floating>
              </Form.Group>

              <div className="text-center">
                <Button variant="primary" type="submit" className="form-submit">
                  Sign up
                </Button>
              </div>
            </Form>
          </Col>
        </Row>
      </Container>
    </MainLayout>
  );
};

export default SignUpUser;
