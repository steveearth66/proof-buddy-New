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

const deleteLine = async (caseName, side, lineNumber) => {
  try {
    const response = await axiosInstance.delete(
      `${API_GATEWAY}/delete-line/${caseName}/${side}/${lineNumber}`
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

const newProof = async () => {
  try {
    const response = await axiosInstance.post(`${API_GATEWAY}/new-proof`);
    return response.data;
  } catch (error) {
    handleServiceError(error, "Error clearing session for new proof:");
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

const checkCompletion = async (caseName) => {
  try {
    const response = await axiosInstance.post(
      `${API_GATEWAY}/check-completion`,
      { case: caseName }
    );
    return response.data;
  } catch (error) {
    handleServiceError(error, "Error during induction check-completion:");
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
    handleServiceError(error, "Error fetching induction proof lines:");
    throw error;
  }
};

const getCurrentProof = async () => {
  try {
    const response = await axiosInstance.get(
      `${API_GATEWAY}/get-current-proof`
    );
    return response.data;
  } catch (error) {
    handleServiceError(error, "Error fetching current induction proof:");
    throw error;
  }
};

const getInductionProofs = async (params) => {
  try {
    const response = await axiosInstance.get(
      `${API_GATEWAY}/get-induction-proofs/`,
      { params }
    );
    return response.data;
  } catch (error) {
    handleServiceError(error, "Error fetching induction proofs:");
    throw error;
  }
};

const getInductionProof = async (proofId) => {
  try {
    const response = await axiosInstance.get(
      `${API_GATEWAY}/proof/${proofId}`
    );
    return response.data;
  } catch (error) {
    handleServiceError(error, "Error fetching induction proof:");
    throw error;
  }
};

const checkNameConflict = async (name) => {
  try {
    const response = await axiosInstance.get(
      `${API_GATEWAY}/check-name-conflict`,
      { params: { name } }
    );
    return response.data;
  } catch (error) {
    handleServiceError(error, "Error checking name conflict:");
    throw error;
  }
};

const setSessionById = async (proofId) => {
  try {
    const response = await axiosInstance.post(
      `${API_GATEWAY}/set-induction-session-by-id`, {
        proof_id: proofId
      });
    return response.data;
  } catch (error) {
    handleServiceError(error, "Error fetching induction proof:");
    throw error;
  }
};

const deleteInductionProof = async (proof_id) => {
  try {
    const response = await axiosInstance.post(
      `${API_GATEWAY}/delete-proof`, { 
      proof_id: proof_id 
    }
    );
    return response.data;
  }
  catch(error) {
    handleServiceError(error, "Error during proof deletion:");
    throw error;
  }
};

const setParameters = async (params) => {
  try {
    const response = await axiosInstance.patch(`${API_GATEWAY}/set-parameters`, params);
    return response.data;
  } catch (error) {
    handleServiceError(error, "Error setting proof parameters:");
    throw error;
  }
};

const inductionService = {
  startInductionProof,
  clearInduction,
  newProof,
  checkInduction,
  substitution,
  checkGoal,
  setCurrentProof,
  applyRule,
  deleteLine,
  checkCompletion,
  getProofLines,
  getCurrentProof,
  getInductionProofs,
  getInductionProof,
  setSessionById,
  deleteInductionProof,
  checkNameConflict,
  setParameters
};

export default inductionService;