//changed file name from AuthService to authService
import axiosInstance from '../utils/axiosInstance';
import { handleServiceError } from '../utils/serviceErrorHandling';

const API_ENDPOINT = "/api/v1/auth";

/**
 * Retrieves the profile information of the currently authenticated user.
 *
 * @returns {Promise<Object>} - The user's profile data as returned by the server.
 */
const getUserProfile = async () => {
  try {
    const response = await axiosInstance.get(`${API_ENDPOINT}/profile`);
    return response.data;
  } catch (error) {
    handleServiceError(error, 'Error fetching user profile:');
    throw error;
  }
};

const logout = async () => {
  try {
    await axiosInstance.post(`${API_ENDPOINT}/logout`);
  } catch (error) {
    handleServiceError(error, "Error logging out:");
    throw error;
  }
};

const userService = {
  getUserProfile,
  logout
};

export default userService;
