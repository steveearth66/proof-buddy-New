import React, { useState, useEffect } from 'react';
import MainLayout from '../layouts/MainLayout';
import { Container } from "react-bootstrap";
import userService from '../services/userService';

// Import your new sub-components
import StudentCatalog from '../components/courses/StudentCatalog';
import StudentCourseView from '../components/courses/StudentCourseView';
import InstructorCatalog from '../components/courses/InstructorCatalog';
import InstructorCourseView from '../components/courses/InstructorCourseView';

import "../scss/_courses.scss";

// --- Mock Data ---
const INITIAL_COURSES = [
  { id: 1, name: 'CS 101: Discrete Math', instructor: 'Prof. Johnson', term: 'Fall 2023', description: 'Introduction to logic, sets, and proofs.', joinCode: 'MATHROCKS', isActive: true },
  { id: 2, name: 'PHIL 202: Symbolic Logic', instructor: 'Prof. Lee', term: 'Fall 2023', description: 'Formal logic and its applications.', joinCode: 'LOGIC101', isActive: false },
  { id: 3, name: 'CS 202: Data Structures', instructor: 'Prof. Davis', term: 'Spring 2024', description: 'Fundamental data structures and algorithms.', joinCode: 'TREES24', isActive: true }
];

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

export default function CourseCatalog() {
  const [courses, setCourses] = useState(INITIAL_COURSES);
  const [assignments, setAssignments] = useState(MOCK_ASSIGNMENTS);
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [currentUserType, setCurrentUserType] = useState(null);

  useEffect(() => {
    async function loadUser() {
      const profile = await userService.getUserProfile();
      setCurrentUserType(profile);
    }
    loadUser();
  }, []);

  if (!currentUserType) {
    return <MainLayout><Container className="mt-5 text-center text-muted">Loading...</Container></MainLayout>;
  }

  const isStudent = currentUserType.is_student;

  // Handler to pass down to children
  const handleViewCourse = (courseId) => {
    const course = courses.find(c => c.id === courseId);
    setSelectedCourse(course);
  };

  return (
    <MainLayout>
      <Container className="my-4 py-4 bg-white rounded shadow-sm border">

        {!selectedCourse ? (
          isStudent ? (
            <StudentCatalog courses={courses} onViewCourse={handleViewCourse} />
          ) : (
            <InstructorCatalog courses={courses} onViewCourse={handleViewCourse} />
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
            />
          )
        )}

      </Container>
    </MainLayout>
  );
}