import Container from 'react-bootstrap/Container';
import MainLayout from '../layouts/MainLayout';
import '../scss/_email-verification.scss';

/**
 * The EmailVerification component renders a user interface for email verification.
 * It guides the user through the process of verifying their email address.
 */
const EmailVerification = () => {

  return (
    <MainLayout>
      <Container>
        <div className="email-verification-container">
          <h1>Almost there...</h1>
          <p>Please verify your email, then head over to the login page to access your account.</p>
        </div>
      </Container>
    </MainLayout>
  );
};

export default EmailVerification;
