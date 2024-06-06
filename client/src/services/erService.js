import axiosInstance from "../utils/axiosInstance";
import { handleServiceError } from "../utils/serviceErrorHandling";

const API_GATEWAY = "/api/v1/proof";

/**
 * Check the proof goal.
 *
 * @param {Object} goal - The object contains proof goal.
 * @returns {Promise<Object>} - The response data from the server.
 */
const checkGoal = async (goal) => {
  try {
    const response = await axiosInstance.post(
      `${API_GATEWAY}/check-goal`,
      goal
    );
    return response.data;
  } catch (error) {
    handleServiceError(error, "Error during goal validation:");
    throw error;
  }
};

/**
 * Generate the racket for the provided rule.
 *
 * @param {Object} payLoad - The object contains proof rule & start position of highlight.
 * @returns {Promise<Object>} - The response data from the server.
 */
const racketGeneration = async (payLoad) => {
  try {
    const response = await axiosInstance.post(
      `${API_GATEWAY}/er-generate`,
      payLoad
    );
    return response.data;
  } catch (error) {
    handleServiceError(error, "Error during racket generation:");
    throw error;
  }
};

const createDefinition = async (definition) => {
  try {
    const response = await axiosInstance.post(
      `${API_GATEWAY}/er-definitions`,
      definition
    );
    return response.data;
  } catch (error) {
    handleServiceError(error, "Error during definition creation:");
    throw error;
  }
};

const completeProof = async (proof) => {
  try {
    const response = await axiosInstance.post(
      `${API_GATEWAY}/er-complete`,
      proof
    );
    return response.data;
  } catch (error) {
    handleServiceError(error, "Error during proof completion:");
    throw error;
  }
};

const clearProof = async () => {
  try {
    const response = await axiosInstance.post(
      `${API_GATEWAY}/er-clear`
    );
    return response.data;
  } catch (error) {
    handleServiceError(error, "Error during proof clearing:");
    throw error;
  }
};

const substitution = async (data) => {
  try {
    const response = await axiosInstance.post(
      `${API_GATEWAY}/er-substitution`,
      data
    );
    return response.data;
  } catch (error) {
    handleServiceError(error, "Error during substitution:");
    throw error;
  }
};

const saveProof = async (proof) => {
  try {
    const response = await axiosInstance.post(`${API_GATEWAY}/er-save`, proof);
    return response.data;
  } catch (error) {
    handleServiceError(error, "Error during proof saving:");
    throw error;
  }
};

const erService = {
  checkGoal,
  racketGeneration,
  createDefinition,
  completeProof,
  clearProof,
  substitution,
  saveProof
};

export default erService;
