import axiosInstance from "../utils/axiosInstance";
import { handleServiceError } from "../utils/serviceErrorHandling";

const API_GATEWAY = 'api/v1/proofs';

const deleteProof = async (id) => {
    return new Promise((resolve, reject) => {
        axiosInstance
        .delete(`${API_GATEWAY}/delete-proof/${id}`)
        .then((response) => {
            resolve(response.data);
        })
        .catch((error) => {
            handleServiceError(error);
            reject(error);
        })
    })
}

const editProof = async (data, id) => {
    return new Promise((resolve, reject) => {
        axiosInstance
        .put(`${API_GATEWAY}/edit-proof/${id}`, data)
        .then((response) => {
            resolve(response.data);
        })
        .catch((error) => {
            handleServiceError(error);
            reject(error);
        })
    })
}