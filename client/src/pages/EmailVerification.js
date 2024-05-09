import Container from 'react-bootstrap/Container';
import MainLayout from '../layouts/MainLayout';
import '../scss/_email-verification.scss';
import { useLocation } from 'react-router-dom';
import { useState } from 'react';
import Button from 'react-bootstrap/esm/Button';
import authService from '../services/authService';

/**
 * The EmailVerification component renders a user interface for email verification.
 * It guides the user through the process of verifying their email address.
 */
const EmailVerification = () => {
  const [serverMessage, setServerMessage] = useState({ message: '', type: '' });
  const location = useLocation();

  const handleResendEmail = async () => {
    try {
      const response = await authService.resendActivationEmail(location.state?.email)
      setServerMessage({ message: response.message, type: 'success' });
    } catch (error) {
      setServerMessage({ message: error.message, type: 'error' });
    }
  }

  return (
    <MainLayout>
      <Container>
        <div className="email-verification-container">
          <h1>Almost there...</h1>
          <p>Please verify your email, then head over to the login page to access your account.</p>
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

export default EmailVerification;
