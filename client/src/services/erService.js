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
  return new Promise((resolve, reject) => {
    axiosInstance
      .get(`${API_GATEWAY}/use-definition/${id}`)
      .then((response) => {
        resolve(response.data);
      })
      .catch((error) => {
        handleServiceError(error, "Error during definition usage:");
        reject(error);
      });
  });
};

const removeDefinition = async (id) => {
  return new Promise((resolve, reject) => {
    axiosInstance
      .delete(`${API_GATEWAY}/remove-definition/${id}/`)
      .then(() => {
        resolve(true);
      })
      .catch((error) => {
        handleServiceError(error, "Error during definition removal:");
        reject(error);
      });
  });
};

const editDefinition = async (definition) => {
  return new Promise((resolve, reject) => {
    axiosInstance
      .post(`${API_GATEWAY}/edit-definition/`, definition)
      .then((response) => {
        resolve(response.data);
      })
      .catch((error) => {
        handleServiceError(error, "Error during definition update:");
        reject(error);
      });
  });
};

const deleteDefinition = async (id) => {
  return new Promise((resolve, reject) => {
    axiosInstance
      .delete(`${API_GATEWAY}/delete-definition/${id}/`)
      .then(() => {
        resolve(true);
      })
      .catch((error) => {
        handleServiceError(error, "Error during definition deletion:");
        reject(error);
      });
  });
};

const deleteLine = async (side) => {
  return new Promise((resolve, reject) => {
    axiosInstance
      .delete(`${API_GATEWAY}/delete-line/${side}`)
      .then(() => {
        resolve(true);
      })
      .catch((error) => {
        handleServiceError(error, "Error during line deletion:");
        reject(error);
      });
  });
}

const erService = {
  checkGoal,
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
