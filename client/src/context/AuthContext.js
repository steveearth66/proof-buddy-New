import React, { createContext, useState, useEffect, useContext } from 'react';
import Cookies from 'js-cookie';
import userService from '../services/userService';
import logger from '../utils/logger';

// Creating a context for authentication data.
const AuthContext = createContext(null);

/**
 * AuthProvider is a component that wraps its children in an AuthContext.Provider,
 * allowing them to access the authentication state and methods to manipulate it.
 */
const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);

  // Fetch user data if logged in.
  const fetchUserData = async () => {
    const token = Cookies.get("accessToken");
    if (token) {
      try {
        const userData = await userService.getUserProfile();
        setUser(userData);
      } catch (error) {
        logger.error("Error fetching user data", error);
        Cookies.remove("accessToken");
      }
    }
  };

  const login = async () => {
    await fetchUserData();
  };

  const logout = async () => {
    await userService.logout();
    Cookies.remove("accessToken");
    setUser(null);
  };

  useEffect(() => {
    fetchUserData();
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthProvider;

/**
 * useAuth is a custom hook that allows easy access to the AuthContext from any component.
 *
 * @returns {object} The context value with the current user and auth functions.
 */
export const useAuth = () => {
  return useContext(AuthContext);
};
