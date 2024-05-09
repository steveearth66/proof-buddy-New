import React, { useState } from 'react';
import Container from 'react-bootstrap/Container';
import Button from 'react-bootstrap/Button';
import MainLayout from '../layouts/MainLayout';
import authService from '../services/authService';
import { useLocation } from 'react-router-dom';
import '../scss/_email-verification.scss';

/**
 * ResetPasswordVerification component displays a page instructing the user to check their email
 * for password reset instructions. It leverages custom hooks to check for the presence of a resend token
 * and to handle resending the verification email if the user did not receive it.
 */
const ResetPasswordVerification = () => {
  const [serverMessage, setServerMessage] = useState({ message: '', type: '' });
  const location = useLocation();

  const handleResendEmail = async () => {
    try {
      const response = await authService.forgotPassword(location.state?.email)
      setServerMessage({ message: response.message, type: 'success' });
    } catch (error) {
      setServerMessage({ message: error.message, type: 'error' });
    }
  }

  return (
    <MainLayout>
      <Container>
        <div className="email-verification-container">
          <h1>Check your email...</h1>
          <p>Please check your email for the instructions to reset your password.</p>
          <p>Didn't receive your confirmation email? We can try sending it again.</p>
          {serverMessage.message ? (
            <p className={`resend-message ${serverMessage.type}`}>{serverMessage.message}</p>
          ) : (
            <>
              <div className='button-wrap'>
                <Button className='orange-btn' onClick={handleResendEmail}>Send Email Again</Button>
              </div>
            </>
          )}
        </div>
      </Container>
    </MainLayout>
  );
};

export default ResetPasswordVerification;
