import axiosInstance from "../utils/axiosInstance";
import { handleServiceError } from "../utils/serviceErrorHandling";

const API_GATEWAY = "/api/v1/assignments";

const getTerms = async () => {
    try {
        const response = await axiosInstance.get(`${API_GATEWAY}/terms`);
        return response.data;
    } catch (error) {
        handleServiceError(error, "Error fetching terms:");
        throw error;
    }
};

const checkUser = async (student) => {
    try {
        const data = { student };
        await axiosInstance.post(`${API_GATEWAY}/check-user`, data);
        return true;
    } catch (error) {
        handleServiceError(error, "Error checking user:");
        return false;
    }
};

const createTerm = async (term) => {
    try {
        const response = await axiosInstance.post(`${API_GATEWAY}/terms`, term);
        return response.data;
    } catch (error) {
        handleServiceError(error, "Error creating term:");
        throw error;
    }
};

const termService = {
    getTerms, checkUser, createTerm
};

export default termService;