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
        return { success: true, data: response.data, status: response.status }; 
    } catch (error) {
        // Catch the duplicate email scenario
        if (error.response?.status === 409) {
            return { 
                success: false, 
                requires_disambiguation: true, 
                candidates: error.response.data.candidates,
                message: error.response.data.message 
            };
        }
        const errorMessage = error.response?.data?.message || "Error adding student.";
        return { success: false, message: errorMessage };
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

const setCourseStatus = async (courseId, newStatus) => {
    try {
        const response = await axiosInstance.patch(`${API_GATEWAY}/courses/${courseId}`, { is_active: newStatus });
        return response.data;
    } catch (error) {
        handleServiceError(error, "Error toggling course status:");
        throw error;
    }
};

const updateCourseDescription = async (courseId, newDescription) => {
    try {
        const response = await axiosInstance.patch(`${API_GATEWAY}/courses/${courseId}`, { description: newDescription });
        return response.data; 
    } catch (error) {
        console.error("Error updating course:", error);
        handleServiceError(error, "Error updating course:");
        throw error;
    }
};

const updateCourseTerm = async (courseId, newTerm) => {
    try {
        const response = await axiosInstance.patch(`${API_GATEWAY}/courses/${courseId}`, { term: newTerm });
        return response.data; 
    } catch (error) {
        console.error("Error updating course:", error);
        handleServiceError(error, "Error updating course description:");
        throw error;
    }
};

const getInstructorLibrary = async () => {
    try {
        const response = await axiosInstance.get(`${API_GATEWAY}/instructor/library`);
        return response.data;
    } catch (error) {
        handleServiceError(error, "Error fetching library:");
        throw error;
    }
};

const deleteAssignment = async (assignmentId) => {
    try {
        const response = await axiosInstance.delete(`${API_GATEWAY}/assignments/detail/${assignmentId}`);
        if (response.status == 204)
            return { success: true };
        else return { success: false, message: response.message };
    } catch (error) {
        handleServiceError(error, "Error deleting assignment:");
        return { success: false, message: error.response?.data?.message || "Failed to delete assignment." };
    }
};

const updateAssignment = async (assignmentId, assignment) => {
    try {
        const response = await axiosInstance.patch(`${API_GATEWAY}/assignments/detail/${assignmentId}`, assignment);
        return response.data;
    } catch (error) {
        handleServiceError(error, "Error updating assignment:");
        throw error;
    }
};

const joinCourse = async (code) => {
    try {
        const response = await axiosInstance.post(`${API_GATEWAY}/join-course`, { code });
        return { success: true, course: response.data.course };
    } catch (error) {
        handleServiceError(error, "Error joining course:");
        return { 
            success: false, 
            message: error.response?.data?.message || "Failed to join course. Please try again." 
        };
    }
};

const leaveCourse = async (courseId) => {
    try {
        await axiosInstance.post(`${API_GATEWAY}/leave-course`, { course: courseId });
        return { success: true };
    } catch (error) {
        return { success: false, message: error.response?.data?.message || "Failed to leave course." };
    }
};

const startAssignmentProof = async (assignmentId, proofId, proofType) => {
    try {
        const response = await axiosInstance.post(`${API_GATEWAY}/assignments/${assignmentId}/start-assignment-proof`, {
            proof_id: proofId,
            proof_type: proofType
        });
        return response.data; // Expecting { success: true, new_proof_id: 123, type: 'equationalproof' }
    } catch (error) {
        console.error("Error starting proof:", error);
        alert(error.response?.data?.message || "Failed to start assignment.");
        return null;
    }
};

const getStudentAssignmentStatus = async (assignmentId) => {
    try {
        const response = await axiosInstance.get(`${API_GATEWAY}/assignments/${assignmentId}/progress`);
        return response.data;
    } catch (error) {
        console.error("Error getting student proof status:", error);
        throw error;
    }
};

const getCourseInvitations = async (courseId) => {
    try {
        const response = await axiosInstance.get(`${API_GATEWAY}/courses/${courseId}/invitations`);
        return response.data;
    } catch (error) {
        console.error("Error fetching course invitations:", error);
        throw error;
    }
};

const cancelInvitation = async (courseId, invitationId) => {
    try {
        const response = await axiosInstance.delete(`${API_GATEWAY}/courses/${courseId}/invitations`, {
            data: { invitation_id: invitationId }
        });
        return response.data;
    } catch (error) {
        console.error("Error cancelling invitation:", error);
        throw error;
    }
};

const getMyInvitations = async () => {
    try {
        const response = await axiosInstance.get(`${API_GATEWAY}/invitations/me`);
        return response.data;
    } catch (error) {
        console.error("Error fetching student invitations:", error);
        return [];
    }
};

const respondToInvitation = async (invitationId, action) => {
    try {
        const response = await axiosInstance.post(`${API_GATEWAY}/invitations/me`, {
            invitation_id: invitationId,
            action: action
        });
        return response.data;
    } catch (error) {
        console.error(`Error ${action}ing invitation:`, error);
        throw error;
    }
};

const courseService = { 
    getCourses, 
    createCourse, 
    leaveCourse, 
    checkUser, 
    updateCourseDescription, 
    updateCourseTerm, 
    startAssignmentProof, 
    getAssignments, 
    getCourse, 
    createAssignment, 
    removeStudent, 
    addStudent, 
    regenerateJoinCode, 
    setCourseStatus, 
    getInstructorLibrary, 
    deleteAssignment, 
    updateAssignment,
    joinCourse,
    getStudentAssignmentStatus,
    getCourseInvitations,
    cancelInvitation,
    getMyInvitations,
    respondToInvitation
};

export default courseService;