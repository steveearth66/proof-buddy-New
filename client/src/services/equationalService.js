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

const toggleVisibility = async (data) => {
  try {
    const response = await axiosInstance.post(
      `${API_GATEWAY}/toggle-visibility`,
      data
    );
    return response.data;
  } catch (error) {
    handleServiceError(error, "Error toggling visibility:");
    throw error;
  }
};

const toggleVisibilityPremise = async (data) => {
  try {
    const response = await axiosInstance.post(
      `${API_GATEWAY}/toggle-visibility-premise`,
      data
    );
    return response.data;
  } catch (error) {
    handleServiceError(error, "Error toggling visibility for premise:");
    throw error;
  }
};

const validateHiddenField = async (data) => {
  try {
    const response = await axiosInstance.post(
      `${API_GATEWAY}/validate-hidden-field`,
      data
    );
    return response.data;
  } catch (error) {
    handleServiceError(error, 'Error validating hidden field:');
    throw error;
  }
};

const validateHiddenDefinition = async ({ label, studentExpression }) => {
  try {
    const response = await axiosInstance.post(
      `${API_GATEWAY}/validate-hidden-definition`,
      { label, student_expression: studentExpression }
    );
    return response.data;
  } catch (error) {
    handleServiceError(error, 'Error validating hidden definition:');
    throw error;
  }
};

const getRacketProofs = async ({ page = 1, query = "" }) => {
  try {
    const response = await axiosInstance.get(`${API_GATEWAY}/proofs?page=${page}&query=${query}`);
    return response.data;
  } catch (error) {
    handleServiceError(error, "Error during getting racket proofs:");
    throw error;
  }
};

const getRacketProof = async (proofId) => {
  try {
    // Send POST request to match the view
    const response = await axiosInstance.post(`${API_GATEWAY}/get-user-proof`, { 
      proof_id: proofId 
    });
    return response.data;
  } catch (error) {
    console.error("Error loading proof:", error);
    throw error;
  }
};

const clearProof = async () => {
  try {
    const response = await axiosInstance.post(
      `${API_GATEWAY}/clear-proof`
    );
    return response.data;
  } catch (error) {
    handleServiceError(error, "Error during proof clearing:");
    throw error;
  }
};

const saveProof = async (proof) => {
  try {
    const response = await axiosInstance.post(
      `${API_GATEWAY}/save-proof`, 
      proof 
    );
    return response.data;
  }
  catch(error) {
    handleServiceError(error, "Error during proof saving:");
    throw error;
  }
};

const deleteRacketProof = async (proof_id) => {
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

const downloadProof = async (proofId) => {
  try {
    const response = await axiosInstance.get(`${API_GATEWAY}/download-proof?proof_id=${proofId}`);
    return response.data;
  } catch (error) {
    handleServiceError(error, "Error downloading proof:");
    throw error;
  }
};

const uploadProof = async (proofData) => {
  try {
    const response = await axiosInstance.post(`${API_GATEWAY}/upload-proof`, proofData);
    return response.data;
  } catch (error) {
    handleServiceError(error, "Error uploading proof:");
    throw error;
  }
};

const saveComment = async (data) => {
  try {
    const response = await axiosInstance.post(
      `${API_GATEWAY}/save-comment`,
      data
    );

    return response.data;

  } catch (error) {
    handleServiceError(error, "Error saving comment:");
    throw error;
  }
};

const getComments = async (params) => {
  try {
    const response = await axiosInstance.get(
      `${API_GATEWAY}/get-comments`,
      {
        params
      }
    );

    return response.data;

  } catch (error) {
    handleServiceError(error, "Error loading comments:");
    throw error;
  }
};

const equationalService = {
  setCurrentProof,
  applyRule,
  deleteLine,
  substitution,
  checkCompletion,
  getProofLines,
  toggleVisibility,
  toggleVisibilityPremise,
  validateHiddenField,
  validateHiddenDefinition,
  getRacketProofs,
  getRacketProof,
  clearProof,
  saveProof,
  deleteRacketProof,
  setParameters,
  downloadProof,
  uploadProof,
  saveComment,
  getComments
};

export default equationalService;
