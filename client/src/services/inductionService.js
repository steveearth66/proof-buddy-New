import axiosInstance from "../utils/axiosInstance";
import { handleServiceError } from "../utils/serviceErrorHandling";

const API_GATEWAY = "/api/v1/induction";

const startInductionProof = async (induction) => {
  try {
    const response = await axiosInstance.post(
      `${API_GATEWAY}/start-induction-proof`,
      induction
    );
    return response;
  } catch (error) {
    handleServiceError(error, "Error during induction validation:");
    throw error;
  }
};

const setCurrentProof = async (data) => {
  try {
    const response = await axiosInstance.post(
      `${API_GATEWAY}/set-current-proof`,
      data
    );
    return response.data;
  } catch (error) {
    handleServiceError(error, "Error during induction engine setup:");
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
    handleServiceError(error, "Error during induction apply-rule:");
    throw error;
  }
};

const deleteLine = async (caseName, side) => {
  try {
    const response = await axiosInstance.delete(
      `${API_GATEWAY}/delete-line/${caseName}/${side}`
    );
    return response.data;
  } catch (error) {
    handleServiceError(error, "Error during induction delete-line:");
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
    handleServiceError(error, "Error during induction substitution:");
    throw error;
  }
};

const clearInduction = async () => {
  try {
    const response = await axiosInstance.post(`${API_GATEWAY}/clear-induction`);
    return response.data;
  } catch (error) {
    handleServiceError(error, "Error during induction clearing:");
    throw error;
  }
};

const checkInduction = async (data) => {
  try {
    const response = await axiosInstance.post(
      `${API_GATEWAY}/start-induction-proof`,
      data
    );
    return response.data;
  } catch (error) {
    handleServiceError(error, "Error during induction check:");
    throw error;
  }
};

const checkGoal = async (data) => {
  try {
    const response = await axiosInstance.post(
      `${API_GATEWAY}/check-goal`,
      data
    );
    return response.data;
  } catch (error) {
    handleServiceError(error, "Error during induction check-goal:");
    throw error;
  }
};

const inductionService = {
  startInductionProof,
  clearInduction,
  checkInduction,
  substitution,
  checkGoal,
  setCurrentProof,
  applyRule,
  deleteLine
};

export default inductionService;