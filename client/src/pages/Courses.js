import React, { useState, useEffect } from 'react';
import MainLayout from '../layouts/MainLayout';
import { Container } from "react-bootstrap";
import userService from '../services/userService';

import StudentCatalog from '../components/courses/StudentCatalog';
import StudentCourseView from '../components/courses/StudentCourseView';
import InstructorCatalog from '../components/courses/InstructorCatalog';
import InstructorCourseView from '../components/courses/InstructorCourseView';
import courseService from '../services/courseServices'

import "../scss/_courses.scss";

// --- Mock Data ---
const MOCK_ASSIGNMENTS = [
  {
    id: 101, title: 'Homework 1: Propositional Logic', dueDate: '10/27/23', courseId: 1, status: 'Open',
    proofs: [
      { id: 1011, title: 'Modus Ponens - Intro', status: 'Completed' },
      { id: 1012, title: 'De Morgan\'s Laws', status: 'In Progress' }
    ]
  },
  {
    id: 102, title: 'Homework 2: Predicate Logic', dueDate: '11/10/23', courseId: 1, status: 'Open',
    proofs: [
      { id: 1021, title: 'Predicate Logic Basics', status: 'Not Started' },
      { id: 1022, title: 'Universal Instantiation', status: 'Not Started' }
    ]
  }
];

export default function Courses() {
  const [courses, setCourses] = useState([]);
  const [assignments, setAssignments] = useState(MOCK_ASSIGNMENTS);
  
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
  const handleViewCourse = (courseId) => {
    const course = courses.find(c => c.id === courseId);
    setSelectedCourse(course);
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
            />
          )
        )}

      </Container>
    </MainLayout>
  );
}