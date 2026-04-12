import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import MainLayout from '../layouts/MainLayout';
import { Container } from "react-bootstrap";
import userService from '../services/userService';

import StudentCatalog from '../components/courses/StudentCatalog';
import StudentCourseView from '../components/courses/StudentCourseView';
import InstructorCatalog from '../components/courses/InstructorCatalog';
import InstructorCourseView from '../components/courses/InstructorCourseView';
import courseService from '../services/courseServices'

import "../scss/_courses.scss";

export default function Courses() {
  const [courses, setCourses] = useState([]);
  const [assignments, setAssignments] = useState([]);
  
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [currentUserType, setCurrentUserType] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadInitialData() {
      try {
        const profile = await userService.getUserProfile();
        setCurrentUserType(profile);
        
        // Fetch real courses from your backend
        const fetchedCourses = await courseService.getCourses();
        setCourses(fetchedCourses);
      } catch (error) {
        console.error("Failed to load initial data", error);
      } finally {
        setIsLoading(false);
      }
    }
    loadInitialData();
  }, []);

  // Handler to hit the API and update state
  const handleCreateCourse = async (courseData) => {
    try {
      const newCourse = await courseService.createCourse(courseData);
      setCourses(prev => [...prev, newCourse]);
      
      // Return the full course object so the modal can extract the join code
      return { success: true, data: newCourse }; 
    } catch (error) {
      console.error("Failed to create course", error);
      // Return a structured error
      return { success: false, message: "Failed to create course. Please try again." };
    }
  };

  if (!currentUserType) {
    return <MainLayout><Container className="mt-5 text-center text-muted">Loading...</Container></MainLayout>;
  }

  const isStudent = currentUserType.is_student;

  // Handler to pass down to children
  const handleViewCourse = async (courseId) => {
    const course = courses.find(c => c.id === courseId);
    setSelectedCourse(course);

    try {
      const fetchedAssignments = await courseService.getAssignments(courseId);
      setAssignments(fetchedAssignments);
    } catch (error) {
      console.error("failed to load assignments", error);
      toast.error("Could not load assignments for this course.");
    }
  };

  const handleToggleCourseStatus = async (courseId, currentStatus) => {
    const newStatus = !currentStatus;

    // 1. Optimistic Update (Immediate UI response)
    setCourses(prev => prev.map(c => c.id === courseId ? { ...c, is_active: newStatus } : c));
    if (selectedCourse?.id === courseId) {
      setSelectedCourse(prev => ({ ...prev, is_active: newStatus }));
    }

    // 2. Background Database Sync
    try {
      await courseService.toggleCourseStatus(courseId, newStatus);
    } catch (error) {
      // 3. Rollback on failure
      console.error("Failed to update status", error);
      alert("Failed to save status change to the server.");
      
      setCourses(prev => prev.map(c => c.id === courseId ? { ...c, is_active: currentStatus } : c));
      if (selectedCourse?.id === courseId) {
        setSelectedCourse(prev => ({ ...prev, is_active: currentStatus }));
      }
    }
  };

  const handleRegenerateJoinCode = async (courseId) => {
    try {
      const response = await courseService.regenerateJoinCode(courseId);
      return response; 
    } catch (error) {
      console.error("Failed to regenerate join code", error);
      alert("Failed to generate a new join code. Please try again.");
      return null;
    }
  };

  const handleUpdateCourse = (updatedCourse) => {
    setCourses(prev => prev.map(c => c.id === updatedCourse.id ? updatedCourse : c));
    setSelectedCourse(updatedCourse);
  };

  const handleCreateAssignment = async (payload) => {
    try {
      const newAssignment = await courseService.createAssignment(payload);
      
      setAssignments(prev => [...prev, newAssignment]);
      return true;
    } catch (error) {
      console.error("Failed to create assignment", error);
      toast.error("Failed to create assignment. Please check your inputs.");
      return false;
    }
  };

  const handleDeleteAssignment = async (assignmentId) => {
      const result = await courseService.deleteAssignment(assignmentId);
      
      if (result.success) {
        // Remove it from the local UI state instantly
        setAssignments(prev => prev.filter(a => a.id !== assignmentId));
        return true;
      } else {
        toast.error(result.message);
        return false;
      }
  };

  return (
    <MainLayout>
      <Container className="my-4 py-4 bg-white rounded shadow-sm border">

        {!selectedCourse ? (
          isStudent ? (
            <StudentCatalog courses={courses} onViewCourse={handleViewCourse} />
          ) : (
            <InstructorCatalog 
              courses={courses} 
              onViewCourse={handleViewCourse} 
              onToggleStatus={handleToggleCourseStatus} 
              onCreateCourse={handleCreateCourse} 
            />
          )
        ) : (
          isStudent ? (
            <StudentCourseView
              course={selectedCourse}
              assignments={assignments}
              onBack={() => setSelectedCourse(null)}
            />
          ) : (
            <InstructorCourseView
              course={selectedCourse}
              assignments={assignments}
              onBack={() => setSelectedCourse(null)}
              onToggleStatus={handleToggleCourseStatus}
              onRegenerateJoinCode={handleRegenerateJoinCode}
              onUpdateCourse={handleUpdateCourse}
              onCreateAssignment={handleCreateAssignment}
              onDeleteAssignment={handleDeleteAssignment}
            />
          )
        )}

      </Container>
    </MainLayout>
  );
}