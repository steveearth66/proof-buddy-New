import axiosInstance from "../utils/axiosInstance";
import { handleServiceError } from "../utils/serviceErrorHandling";

const API_GATEWAY = "/api/v1/induction";

const checkInduction = async (induction) => {
  try {
    const response = await axiosInstance.post(
      `${API_GATEWAY}/start-induction-proof`,
      induction
    );
    return response.data;
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

const createDefinition = async (definition) => {
  try {
    const response = await axiosInstance.post(
      `${API_GATEWAY}/add-definitions`,
      definition
    );
    return response.data;
  } catch (error) {
    handleServiceError(error, "Error during definition creation:");
    throw error;
  }
};

const inductionService = {
  checkInduction,
  clearInduction,
  createDefinition
};

export default inductionService;
