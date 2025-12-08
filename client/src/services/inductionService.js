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

const inductionService = {
  startInductionProof,
  clearInduction,
  checkInduction
};

export default inductionService;