import axios from 'axios';
import apiConfig from '../config/apiConfig'
import Cookies from 'js-cookie';

/**
 * Creates an Axios instance with a pre-configured base URL.
 */
const axiosInstance = axios.create({
  baseURL: apiConfig.apiBaseUrl
});

/**
 * Request Interceptor
 * - Attaches the 'Authorization' header with a bearer token (if available in cookies) to every outgoing request.
 * - Ensures all requests sent by this axios instance include token authentication when the token is present.
 */
axiosInstance.interceptors.request.use(
  (config) => {
    const token = Cookies.get('accessToken');
    if (token) {
      config.headers.Authorization = `Token ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Response Interceptor
 * - Directly passes through any successful responses.
 * - Intercepts errors, specifically handling 401 Unauthorized errors globally.
 */
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      Cookies.remove("accessToken");
      location.reload();
    }
    return Promise.reject(error);
  }
);

export default axiosInstance;
