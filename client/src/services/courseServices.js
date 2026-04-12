import axiosInstance from "../utils/axiosInstance";
import { handleServiceError } from "../utils/serviceErrorHandling";

const API_GATEWAY = "/api/v1/assignments";

const getCourses = async () => {
    try {
        const response = await axiosInstance.get(`${API_GATEWAY}/courses`);
        return response.data;
    } catch (error) {
        handleServiceError(error, "Error fetching courses:");
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

const createCourse = async (course) => {
    try {
        const response = await axiosInstance.post(`${API_GATEWAY}/courses`, course);
        return response.data;
    } catch (error) {
        handleServiceError(error, "Error creating course:");
        throw error;
    }
};

const getAssignments = async (courseId) => {
    try {
        const response = await axiosInstance.get(`${API_GATEWAY}/${courseId}`);
        return response.data;
    } catch (error) {
        handleServiceError(error, "Error fetching assignments:");
        throw error;
    }
};

const createAssignment = async (assignment) => {
    try {
        const response = await axiosInstance.post(`${API_GATEWAY}/`, assignment);
        return response.data;
    } catch (error) {
        handleServiceError(error, "Error creating assignment:");
        throw error;
    }
};

const getCourse = async (id) => {
    try {
        const response = await axiosInstance.get(`${API_GATEWAY}/courses/${id}`);
        return response.data;
    } catch (error) {
        handleServiceError(error, "Error fetching course:");
        throw error;
    }
};

const removeStudent = async ({ student, course }) => {
    try {
        const data = { student, course };
        console.log(data);
        await axiosInstance.post(`${API_GATEWAY}/remove-student`, data);
        return true;
    } catch (error) {
        handleServiceError(error, "Error removing student:");
        return false;
    }
};

const addStudent = async ({ student, course }) => {
    try {
        const data = { student, course };
        const response = await axiosInstance.post(`${API_GATEWAY}/add-student`, data);
        return response.data;
    } catch (error) {
        handleServiceError(error, "Error adding student:");
        return false;
    }
};

const regenerateJoinCode = async (courseId) => {
    try {
        const response = await axiosInstance.patch(`${API_GATEWAY}/courses/${courseId}`, { action: 'regenerate_code' });
        return response.data;
    } catch (error) {
        handleServiceError(error, "Error generating join code:");
        throw error;
    }
};

const toggleCourseStatus = async (courseId, newStatus) => {
    try {
        const response = await axiosInstance.patch(`${API_GATEWAY}/courses/${courseId}`, { is_active: newStatus });
        return response.data;
    } catch (error) {
        handleServiceError(error, "Error toggling course status:");
        throw error;
    }
};

const courseService = { getCourses, checkUser, createCourse, getAssignments, getCourse, createAssignment, removeStudent, addStudent, regenerateJoinCode, toggleCourseStatus };

export default courseService;