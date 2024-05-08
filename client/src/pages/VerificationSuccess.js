import React, { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import Container from 'react-bootstrap/Container';
import Button from 'react-bootstrap/Button';
import MainLayout from '../layouts/MainLayout';
import '../scss/_email-verification.scss';
import authService from '../services/authService';

/**
 * VerificationSuccess component displays a success message after a user has successfully
 * verified their email or reset their password, depending on the context.
 */
const VerificationSuccess = ({ context }) => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const activateAccount = async (activationToken) => {
      await authService.activateAccount(activationToken);
    };
    
    if (searchParams.get('token')) {
      activateAccount(searchParams.get('token'));
    }

  }, [searchParams])

  const handleGoHome = () => {
    navigate('/');
  };

  return (
    <MainLayout>
      <Container>
        <div className='email-verification-container'>
          {context === 'emailSuccess' ? (
            <h1>Email Verified!</h1>
          ) : (
            <h1>Password Reset Successfully!</h1>
          )}

          <p>Please proceed to login and access your account.</p>
          <p>Or click the button below to go the homepage.</p>
          <div className='button-wrap'>
            <Button className='orange-btn' onClick={handleGoHome}>Go to Homepage</Button>
          </div>
        </div>
      </Container>
    </MainLayout>
  );
};

export default VerificationSuccess;
