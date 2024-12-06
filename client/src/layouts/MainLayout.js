import React from 'react';
import Header from '../components/Header';
import Footer from '../components/Footer';
import '../scss/_main-layout.scss';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

/**
 * MainLayout serves as a layout wrapper for the application.
 */
const MainLayout = ({ children }) => {
  return (
    <>
      <ToastContainer
        position="top-right"
        autoClose={5000}
        hideProgressBar={false}
        newestOnTop={false}
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="light"
      />
      <Header />
      <main className="main-container">{children}</main>
      <Footer />
    </>
  );
};

export default MainLayout;
