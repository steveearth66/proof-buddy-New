import axiosInstance from "../utils/axiosInstance";
import { handleServiceError } from "../utils/serviceErrorHandling";

const API_GATEWAY = "/api/v1/equational";

const setCurrentProof = async (data) => {
  try {
    const response = await axiosInstance.post(
      `${API_GATEWAY}/set-current-proof`,
      data
    );
    return response.data;
  } catch (error) {
    handleServiceError(error, "Error during equational reasoning engine setup:");
    throw error;
  }
};

const applyRule = async (data) => {
  try {
    const response = await axiosInstance.post(
      `${API_GATEWAY}/apply-rule`,
      data
    );
    return response.data;
  } catch (error) {
    handleServiceError(error, "Error during equational reasoning apply-rule:");
    throw error;
  }
};

const deleteLine = async (side, lineNumber) => {
  try {
    const response = await axiosInstance.delete(
      `${API_GATEWAY}/delete-line/${side}/${lineNumber}`
    );
    return response.data;
  } catch (error) {
    handleServiceError(error, "Error during equational reasoning delete-line:");
    throw error;
  }
};

const substitution = async (data) => {
  try {
    const response = await axiosInstance.post(
      `${API_GATEWAY}/substitution`,
      data
    );
    return response.data;
  } catch (error) {
    handleServiceError(error, "Error during equational reasoning substitution:");
    throw error;
  }
};

const checkCompletion = async () => {
  try {
    const response = await axiosInstance.post(
      `${API_GATEWAY}/check-completion`
    );
    return response.data;
  } catch (error) {
    handleServiceError(error, "Error during equational reasoning check-completion:");
    throw error;
  }
};

const getProofLines = async () => {
  try {
    const response = await axiosInstance.get(
      `${API_GATEWAY}/get-proof-lines`
    );
    return response.data;
  } catch (error) {
    handleServiceError(error, "Error fetching equational reasoning proof lines:");
    throw error;
  }
};

const equationalService = {
  setCurrentProof,
  applyRule,
  deleteLine,
  substitution,
  checkCompletion,
  getProofLines
};

export default equationalService;
