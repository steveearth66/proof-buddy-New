import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Container, Spinner, Button } from "react-bootstrap";
import { toast } from 'react-toastify';

import MainLayout from '../layouts/MainLayout';
import StudentCourseView from '../components/courses/StudentCourseView';
import InstructorCourseView from '../components/courses/InstructorCourseView';

import userService from '../services/userService';
import courseService from '../services/courseServices';

export default function CourseView() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [course, setCourse] = useState(null);
  const [assignments, setAssignments] = useState([]);
  const [userProfile, setUserProfile] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadCourseData() {
      setIsLoading(true);
      setError(null);
      try {
        const profile = await userService.getUserProfile();
        setUserProfile(profile);

        const fetchedCourse = await courseService.getCourse(id);
        const fetchedAssignments = await courseService.getAssignments(id);

        setCourse(fetchedCourse);
        setAssignments(fetchedAssignments);
      } catch (err) {
        console.error("Failed to load course details", err);
        // Check if it's a 404 (Not Found) or 403 (Forbidden)
        if (err.response?.status === 404) {
          setError("COURSE_NOT_FOUND");
        } else if (err.response?.status === 403) {
          setError("ACCESS_DENIED");
        } else {
          setError("GENERAL_ERROR");
        }
      } finally {
        setIsLoading(false);
      }
    }
    loadCourseData();
  }, [id]);

  const handleToggleCourseStatus = async (courseId, currentStatus) => {
    const newStatus = !currentStatus;

    // 1. Optimistic Update
    setCourse(prev => ({ ...prev, is_active: newStatus }));

    // 2. Background Database Sync
    try {
      await courseService.toggleCourseStatus(courseId, newStatus);
    } catch (error) {
      // 3. Rollback on failure
      console.error("Failed to update status", error);
      toast.error("Failed to save status change to the server.");
      setCourse(prev => ({ ...prev, is_active: currentStatus }));
    }
  };

  const handleRegenerateJoinCode = async (courseId) => {
    try {
      const response = await courseService.regenerateJoinCode(courseId);
      return response;
    } catch (error) {
      console.error("Failed to regenerate join code", error);
      toast.error("Failed to generate a new join code.");
      return null;
    }
  };

  const handleUpdateCourse = (updatedCourse) => {
    setCourse(updatedCourse);
  };

  const handleSaveAssignment = async (payload) => {
    try {
      let result;
      if (payload.id) {
        result = await courseService.updateAssignment(payload.id, payload);
        setAssignments(prev => prev.map(a => a.id === result.id ? result : a));
        toast.success("Assignment updated successfully!");
      } else {
        result = await courseService.createAssignment(payload);
        setAssignments(prev => [...prev, result]);
        toast.success("Assignment created successfully!");
      }
      return true;
    } catch (error) {
      const action = payload.id ? "update" : "create";
      console.error(`Failed to ${action} assignment`, error);
      toast.error(`Failed to ${action} assignment.`);
      return false;
    }
  };

  const handleDeleteAssignment = async (assignmentId) => {
    const result = await courseService.deleteAssignment(assignmentId);
    if (result.success) {
      setAssignments(prev => prev.filter(a => a.id !== assignmentId));
      toast.success("Assignment deleted.");
      return true;
    } else {
      toast.error(result.message);
      return false;
    }
  };

  // 1. Loading State
  if (isLoading) {
    return (
      <MainLayout>
        <Container className="mt-5 text-center">
          <Spinner animation="border" variant="primary" />
          <p className="mt-2 text-muted">Loading course details...</p>
        </Container>
      </MainLayout>
    );
  }

  // 2. Error State (Handling non-existent course)
  if (error) {
    return (
      <MainLayout>
        <Container className="mt-5 text-center py-5 bg-white rounded shadow-sm border">
          <i className="fa-solid fa-circle-exclamation fa-4x text-danger mb-4"></i>
          <h2 style={{ color: '#0a3d62' }}>
            {error === "COURSE_NOT_FOUND" ? "Course Not Found" : "Access Denied"}
          </h2>
          <p className="text-muted mb-4">
            {error === "COURSE_NOT_FOUND"
              ? "The course you are looking for doesn't exist or has been deleted."
              : "You do not have permission to view this course."}
          </p>
          <Button variant="primary" onClick={() => navigate('/courses')}>
            <i className="fa-solid fa-arrow-left me-2"></i>Return to Catalog
          </Button>
        </Container>
      </MainLayout>
    );
  }

  // 3. Success State
  return (
    <MainLayout>
      <Container className="my-4 py-4 bg-white rounded shadow-sm border">
        {userProfile.is_student ? (
          <StudentCourseView
            course={course}
            assignments={assignments}
            onBack={() => navigate('/courses')}
          />
        ) : (
          <InstructorCourseView
            course={course}
            assignments={assignments}
            onBack={() => navigate('/courses')}
            onToggleStatus={handleToggleCourseStatus}
            onRegenerateJoinCode={handleRegenerateJoinCode}
            onUpdateCourse={handleUpdateCourse}
            onSaveAssignment={handleSaveAssignment}
            onDeleteAssignment={handleDeleteAssignment}
          />
        )}
      </Container>
    </MainLayout>
  );
}