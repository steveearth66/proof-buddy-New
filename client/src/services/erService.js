import axiosInstance from "../utils/axiosInstance";
import { handleServiceError } from "../utils/serviceErrorHandling";

const API_GATEWAY = "/api/v1/proof";

// this function used to convert children list to id list rather than nodes
/*
const subChildIDS = (expr) => {
  if (expr === null || expr === undefined || expr === "") {
    return;
  }
  for (let i = 0; i < expr.children.length; i++) {
    let child = expr.children[i];
    expr.children[i] = child.startPosition;
    subChildIDS(child);
  }
};
*/

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
    //console.log("before", response.data); // checking to see if we can change nodes to id's here
    //subChildIDS(response.data.jsonTree);
    //console.log("after", response.data); // checking to see if backend successfully changed children to id's
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
  //console.log("Payload sent to backend (erService.js):", payLoad); // DEBUG REMOVE
  try {
    const response = await axiosInstance.post(
      `${API_GATEWAY}/er-generate`,
      payLoad
    );
    //console.log("line num?(erService.js):", response.data.lineNum); // test to see if lineNum shows up in the response
    return response.data;
  } catch (error) {
    handleServiceError(error, "Error during racket generation:");
    throw error;
  }
};

/**
 * Generate the racket for the provided rule.
 *
 * @param {Object} payLoad - The object contains proof rule & start position of highlight.
 * @returns {Promise<Object>} - The response data from the server.
 */
const loadProof = async (payLoad) => {
  //console.log("Payload sent to backend (erService.js):", payLoad); // DEBUG REMOVE
  try {
    const response = await axiosInstance.post(
      `${API_GATEWAY}/set-proof`,
      payLoad
    );
    //console.log("line num?(erService.js):", response.data.lineNum); // test to see if lineNum shows up in the response
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
  return new Promise((resolve, reject) => {
    axiosInstance
      .post(`${API_GATEWAY}/er-save`, proof)
      .then((response) => {
        resolve(response.data);
      })
      .catch((error) => {
        handleServiceError(error, "Error during proof saving:");
        reject(error);
      });
  });
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

const getRacketProof = async (id) => {
  try {
    const response = await axiosInstance.get(`${API_GATEWAY}/proofs/${id}`);
    return response.data;
  } catch (error) {
    handleServiceError(error, "Error during getting racket proof:");
    throw error;
  }
};

const getUserDefinitions = async () => {
  try {
    const response = await axiosInstance.get(`${API_GATEWAY}/get-definitions`);
    return response.data;
  } catch (error) {
    handleServiceError(error, "Error during getting user definitions:");
    throw error;
  }
};

const useDefinition = async (id) => {
  try {
    const response = await axiosInstance.get(`${API_GATEWAY}/use-definition/${id}`);
    return response.data;
  } catch (error) {
    handleServiceError(error, "Error during definition usage:");
    throw error;
  }
};

const removeDefinition = async (id) => {
  try {
    await axiosInstance.delete(`${API_GATEWAY}/remove-definition/${id}/`);
    return true;
  } catch (error) {
    handleServiceError(error, "Error during definition removal:");
    throw error;
  }
};

const editDefinition = async (definition) => {
  try {
    const response = await axiosInstance.post(`${API_GATEWAY}/edit-definition/`, definition);
    return response.data;
  } catch (error) {
    handleServiceError(error, "Error during definition update:");
    throw error;
  }
};

const deleteDefinition = async (id) => {
  try {
    await axiosInstance.delete(`${API_GATEWAY}/delete-definition/${id}/`);
    return true;
  } catch (error) {
    handleServiceError(error, "Error during definition deletion:");
    throw error;
  }
};

const deleteLine = async (side) => {
  try {
    await axiosInstance.delete(`${API_GATEWAY}/delete-line/${side}`);
    return true;
  } catch (error) {
    handleServiceError(error, "Error during line deletion:");
    throw error;
  }
};

const erService = {
  checkGoal,
  loadProof,
  racketGeneration,
  createDefinition,
  completeProof,
  clearProof,
  substitution,
  saveProof,
  getRacketProofs,
  getRacketProof,
  getUserDefinitions,
  useDefinition,
  editDefinition,
  deleteDefinition,
  removeDefinition,
  deleteLine
};

export default erService;
