import logger from '../utils/logger';

/**
 * Retrieves Django API base URL from environment variables with a fallback to a default value.
 * @returns {string} API Base URL.
 */
const getApiBaseUrl = () => {
  const defaultUrl = "http://localhost:8000";
  const envUrl = process.env.REACT_APP_BACKEND_API_BASE_URL;

  if (!envUrl) {
    logger.warn(
      `Backend API base url is not set. Using default URL: ${defaultUrl}`
    );
  }

  return envUrl || defaultUrl;
};

const apiConfig = {
  apiBaseUrl: getApiBaseUrl()
};

export default apiConfig;
