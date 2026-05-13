import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Container, Spinner } from "react-bootstrap";
import { toast } from 'react-toastify';
import MainLayout from '../layouts/MainLayout';
import StudentCatalog from '../components/courses/StudentCatalog';
import InstructorCatalog from '../components/courses/InstructorCatalog';
import userService from '../services/userService';
import courseService from '../services/courseServices';
import "../scss/_courses.scss";

export default function Courses() {
  const [courses, setCourses] = useState([]);
  const [userProfile, setUserProfile] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  // Unified fetch function used for initial load and refreshing
  const fetchData = async () => {
    try {
      const profile = await userService.getUserProfile();
      const list = await courseService.getCourses();
      setUserProfile(profile);
      setCourses(list);
    } catch (error) {
      console.error("Failed to load catalog data", error);
      toast.error("Failed to load courses.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleEnterCourse = (id) => {
    navigate(`/courses/${id}`);
  };

  const handleLeaveCourse = async (courseId) => {
    const result = await courseService.leaveCourse(courseId);
    if (result.success) {
      toast.success("Successfully left the course.");
      // Optimistically remove from list
      setCourses(prev => prev.filter(c => c.id !== courseId));
    } else {
      toast.error(result.message);
    }
  };

  const handleJoinCourse = async (code) => {
    const result = await courseService.joinCourse(code);
    if (result.success) {
      setCourses(prev => [...prev, result.course]);
      fetchData();
      return { success: true };
    } else {
      return { success: false, message: result.message };
    }
  };

  const handleCreateCourse = async (courseData) => {
    try {
      const newCourse = await courseService.createCourse(courseData);
      setCourses(prev => [...prev, newCourse]);
      return { success: true, data: newCourse };
    } catch (error) {
      console.error("Failed to create course", error);
      return { success: false, message: "Failed to create course. Please try again." };
    }
  };

  const handleToggleCourseStatus = async (courseId, currentStatus) => {
    const newStatus = !currentStatus;
    // Optimistic Update in the catalog list
    setCourses(prev => prev.map(c => c.id === courseId ? { ...c, is_active: newStatus } : c));

    try {
      await courseService.toggleCourseStatus(courseId, newStatus);
    } catch (error) {
      console.error("Failed to update status", error);
      toast.error("Failed to save status change.");
      // Rollback
      setCourses(prev => prev.map(c => c.id === courseId ? { ...c, is_active: currentStatus } : c));
    }
  };

  return (
    <MainLayout>
      <Container className="my-4 py-4 bg-white rounded shadow-sm border">
        {isLoading ? (
          <div className="text-center py-5">
            <Spinner animation="border" variant="primary" />
            <p className="mt-2 text-muted">Loading courses...</p>
          </div>
        ) : userProfile?.is_student ? (
          <StudentCatalog
            courses={courses}
            onViewCourse={handleEnterCourse}
            onJoinCourse={handleJoinCourse}
            onLeaveCourse={handleLeaveCourse}
            onRefreshCourses={fetchData}
          />
        ) : (
          <InstructorCatalog
            courses={courses}
            onViewCourse={handleEnterCourse}
            onToggleStatus={handleToggleCourseStatus}
            onCreateCourse={handleCreateCourse}
            onJoinCourse={handleJoinCourse}
          />
        )}
      </Container>
    </MainLayout>
  );
}