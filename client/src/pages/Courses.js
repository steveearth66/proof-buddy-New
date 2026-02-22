import React, { useState, useMemo } from 'react';
import MainLayout from '../layouts/MainLayout';
import { Container, Table, Button, Modal, Form } from "react-bootstrap";
import NumberedPagination from '../components/Pagination'; 
import "../scss/_courses.scss";

// Mock Data
const INITIAL_COURSES = [
  { id: 1, name: 'CS 101: Discrete Math', instructor: 'Prof. Johnson', term: 'Fall 2023', description: 'Introduction to logic, sets, and proofs.' },
  { id: 2, name: 'PHIL 202: Symbolic Logic', instructor: 'Prof. Lee', term: 'Fall 2023', description: 'Formal logic and its applications.' },
  { id: 3, name: 'CS 202: Data Structures', instructor: 'Prof. Davis', term: 'Spring 2024', description: 'Fundamental data structures and algorithms.' }
];

const MOCK_ASSIGNMENTS = [
  { 
    id: 101, title: 'Homework 1: Propositional Logic', dueDate: '10/27/23', courseId: 1,
    proofs: [
      { id: 1011, title: 'Modus Ponens - Intro', status: 'Completed' },
      { id: 1012, title: 'De Morgan\'s Laws', status: 'In Progress' }
    ]
  },
  { 
    id: 102, title: 'Homework 2: Predicate Logic', dueDate: '11/10/23', courseId: 1,
    proofs: [
      { id: 1021, title: 'Predicate Logic Basics', status: 'Not Started' },
      { id: 1022, title: 'Universal Instantiation', status: 'Not Started' }
    ]
  },
  { 
    id: 103, title: 'Homework 1: Data Types', dueDate: '11/15/23', courseId: 3,
    proofs: [
      { id: 1031, title: 'Induction Example 1', status: 'Completed' }
    ]
  }
];

export default function CourseCatalog() {
  const [courses] = useState(INITIAL_COURSES);
  const [assignments] = useState(MOCK_ASSIGNMENTS);
  const [selectedCourse, setSelectedCourse] = useState(null);
  const [expandedAssignments, setExpandedAssignments] = useState([]);

  // --- Modals ---
  const [showJoinModal, setShowJoinModal] = useState(false);
  const [joinCode, setJoinCode] = useState("");

  // --- Sorting & Pagination State ---
  const [coursePage, setCoursePage] = useState(1);
  const [assignmentPage, setAssignmentPage] = useState(1);
  const itemsPerPage = 10; 

  // Config looks like: { key: 'name', direction: 'asc' }
  const [courseSortConfig, setCourseSortConfig] = useState(null);
  const [assignmentSortConfig, setAssignmentSortConfig] = useState(null);

  // --- Sorting Logic ---
  const handleSort = (key, config, setConfig) => {
    let direction = 'asc';
    if (config && config.key === key && config.direction === 'asc') {
      direction = 'desc';
    }
    setConfig({ key, direction });
  };

  const getSortIcon = (key, config) => {
    if (!config || config.key !== key) return "fa-solid fa-sort text-muted";
    return config.direction === 'asc' ? "fa-solid fa-sort-up text-primary" : "fa-solid fa-sort-down text-primary";
  };

  // --- Process Courses (Sort then Paginate) ---
  const sortedCourses = useMemo(() => {
    let sortableCourses = [...courses];
    if (courseSortConfig !== null) {
      sortableCourses.sort((a, b) => {
        if (a[courseSortConfig.key] < b[courseSortConfig.key]) {
          return courseSortConfig.direction === 'asc' ? -1 : 1;
        }
        if (a[courseSortConfig.key] > b[courseSortConfig.key]) {
          return courseSortConfig.direction === 'asc' ? 1 : -1;
        }
        return 0;
      });
    }
    return sortableCourses;
  }, [courses, courseSortConfig]);

  const totalCoursePages = Math.ceil(sortedCourses.length / itemsPerPage) || 1;
  const paginatedCourses = sortedCourses.slice((coursePage - 1) * itemsPerPage, coursePage * itemsPerPage);

  // --- Process Assignments (Filter, Sort, then Paginate) ---
  const sortedAssignments = useMemo(() => {
    let filtered = selectedCourse ? assignments.filter(a => a.courseId === selectedCourse.id) : [];
    if (assignmentSortConfig !== null) {
      filtered.sort((a, b) => {
        let aValue = a[assignmentSortConfig.key];
        let bValue = b[assignmentSortConfig.key];

        // Handle date sorting specifically for the dueDate column
        if (assignmentSortConfig.key === 'dueDate') {
          aValue = new Date(aValue);
          bValue = new Date(bValue);
        }

        if (aValue < bValue) return assignmentSortConfig.direction === 'asc' ? -1 : 1;
        if (aValue > bValue) return assignmentSortConfig.direction === 'asc' ? 1 : -1;
        return 0;
      });
    }
    return filtered;
  }, [assignments, selectedCourse, assignmentSortConfig]);

  const totalAssignmentPages = Math.ceil(sortedAssignments.length / itemsPerPage) || 1;
  const paginatedAssignments = sortedAssignments.slice((assignmentPage - 1) * itemsPerPage, assignmentPage * itemsPerPage);

  // --- Action Handlers ---
  const toggleAssignment = (assignmentId) => {
    setExpandedAssignments(prev => 
      prev.includes(assignmentId) ? prev.filter(id => id !== assignmentId) : [...prev, assignmentId]
    );
  };

  const handleProofAction = (proof) => {
    if (proof.status === 'Completed') {
      console.log(`Viewing submission for ${proof.title}`);
    } else {
      console.log(`Starting/Continuing proof for ${proof.title}`);
    }
  };

  const getButtonProps = (status) => {
    if (status === 'Completed') return { variant: 'secondary', icon: 'fa-solid fa-eye', text: 'View Submission' };
    if (status === 'In Progress') return { variant: 'primary', icon: 'fa-solid fa-rotate-right', text: 'Continue Assignment' };
    return { variant: 'success', icon: 'fa-solid fa-play', text: 'Start Assignment' };
  };

  const handleViewCourse = (courseId) => {
    const course = courses.find(c => c.id === courseId);
    setSelectedCourse(course);
    setAssignmentPage(1); 
    setAssignmentSortConfig(null); // Reset assignment sort when entering a new course
    setExpandedAssignments([]); // Collapse all rows
  };

  const handleJoinSubmit = () => {
    console.log("Attempting to join course with code:", joinCode);
    setShowJoinModal(false);
    setJoinCode(""); 
  };

  return (
    <MainLayout>
      <Container className="my-4 py-4 bg-white rounded shadow-sm border">
        
        {!selectedCourse ? (
          <div>
            <div className="d-flex justify-content-between align-items-center mb-4">
              <h2 className="mb-0" style={{ color: '#0a3d62' }}>Course Catalog</h2>
              <Button variant="primary" onClick={() => setShowJoinModal(true)}>
                <i className="fa-solid fa-plus me-2"></i>Join a Course
              </Button>
            </div>

            <Table striped bordered hover responsive className="align-middle">
              <thead className="table-light">
                <tr>
                  <th 
                    style={{ cursor: 'pointer' }} 
                    onClick={() => handleSort('name', courseSortConfig, setCourseSortConfig)}
                  >
                    Course Name <i className={`ms-1 ${getSortIcon('name', courseSortConfig)}`}></i>
                  </th>
                  <th 
                    style={{ cursor: 'pointer' }} 
                    onClick={() => handleSort('instructor', courseSortConfig, setCourseSortConfig)}
                  >
                    Instructor <i className={`ms-1 ${getSortIcon('instructor', courseSortConfig)}`}></i>
                  </th>
                  <th 
                    style={{ cursor: 'pointer' }} 
                    onClick={() => handleSort('term', courseSortConfig, setCourseSortConfig)}
                  >
                    Term <i className={`ms-1 ${getSortIcon('term', courseSortConfig)}`}></i>
                  </th>
                  <th>Description</th>
                  <th className="text-center">Action</th>
                </tr>
              </thead>
              <tbody>
                {/* Map over paginatedCourses here (same as before) */}
                {paginatedCourses.map((course) => (
                  <tr key={course.id}>
                    <td className="fw-semibold">{course.name}</td>
                    <td>{course.instructor}</td>
                    <td>{course.term}</td>
                    <td>{course.description}</td>
                    <td className="text-center">
                      <Button variant="outline-primary" size="sm" onClick={() => handleViewCourse(course.id)}>
                        <i className="fa-solid fa-arrow-right-to-bracket me-2"></i>Enter Course
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
            
            <div className="d-flex justify-content-between align-items-center mt-3 text-muted small">
              <span>
                Showing {sortedCourses.length > 0 ? (coursePage - 1) * itemsPerPage + 1 : 0} to {Math.min(coursePage * itemsPerPage, sortedCourses.length)} of {sortedCourses.length} entries
              </span> 
              <NumberedPagination 
                currentPage={coursePage} 
                totalPages={totalCoursePages} 
                onPageChange={({ page }) => setCoursePage(page)} 
              />
            </div>
          </div>
        ) : (
          <div>
            <div className="mb-4">
              <Button variant="link" className="text-decoration-none p-0 mb-2 text-muted" onClick={() => setSelectedCourse(null)}>
                <i className="fa-solid fa-arrow-left me-2"></i>Back to Catalog
              </Button>
              <h2 style={{ color: '#0a3d62' }}>{selectedCourse.name}</h2>
            </div>

            <h4 className="mb-3">Assignments</h4>
            
            <Table striped bordered hover responsive className="align-middle">
              <thead className="table-light">
                <tr>
                  <th 
                    style={{ cursor: 'pointer', width: '40%' }}
                    onClick={() => handleSort('title', assignmentSortConfig, setAssignmentSortConfig)}
                  >
                    Assignment <i className={`ms-1 ${getSortIcon('title', assignmentSortConfig)}`}></i>
                  </th>
                  <th 
                    style={{ cursor: 'pointer' }}
                    onClick={() => handleSort('dueDate', assignmentSortConfig, setAssignmentSortConfig)}
                  >
                    Due Date <i className={`ms-1 ${getSortIcon('dueDate', assignmentSortConfig)}`}></i>
                  </th>
                  <th>Status</th>
                  <th className="text-center">Action</th>
                </tr>
              </thead>
              <tbody>
                {paginatedAssignments.length > 0 ? (
                  paginatedAssignments.map((assignment) => {
                    const isExpanded = expandedAssignments.includes(assignment.id);
                    const totalProofs = assignment.proofs.length;
                    const completedProofs = assignment.proofs.filter(p => p.status === 'Completed').length;
                    const isFullyComplete = totalProofs > 0 && completedProofs === totalProofs;

                    return (
                      <React.Fragment key={assignment.id}>
                        <tr className={isExpanded ? "table-active" : ""}>
                          <td className="fw-semibold">
                            <Button 
                              variant="link" 
                              className="text-decoration-none p-0 me-3 text-dark text-start"
                              onClick={() => toggleAssignment(assignment.id)}
                            >
                              <i className={`fa-solid fa-chevron-${isExpanded ? 'down' : 'right'} text-primary`} style={{ width: '20px' }}></i>
                              {assignment.title}
                            </Button>
                          </td>
                          <td>{assignment.dueDate}</td>
                          <td>
                            {isFullyComplete ? (
                              <span className="text-success fw-semibold"><i className="fa-solid fa-check me-2"></i>Completed</span>
                            ) : (
                              <span className="text-muted">{completedProofs} / {totalProofs} Proofs Completed</span>
                            )}
                          </td>
                          <td className="text-center">
                            {/* Actions for the entire assignment could go here if needed */}
                          </td>
                        </tr>

                        {isExpanded && (
                          <tr>
                            <td colSpan="4" className="p-0 border-bottom-0">
                              <div className="bg-light p-3 border-start border-4 border-primary">
                                <h6 className="text-muted mb-3"><i className="fa-solid fa-list-check me-2"></i>Proofs for {assignment.title}</h6>
                                <Table size="sm" bordered hover className="mb-0 bg-white shadow-sm">
                                  <thead className="table-light">
                                    <tr>
                                      <th>Proof Name</th>
                                      <th>Status</th>
                                      <th className="text-center">Action</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {assignment.proofs.map((proof) => {
                                      const btnInfo = getButtonProps(proof.status);
                                      return (
                                        <tr key={proof.id}>
                                          <td className="fw-medium">{proof.title}</td>
                                          <td>
                                            {proof.status === 'Completed' && <i className="fa-solid fa-circle-check text-success me-2"></i>}
                                            {proof.status === 'In Progress' && <i className="fa-solid fa-circle-half-stroke text-warning me-2"></i>}
                                            {proof.status === 'Not Started' && <i className="fa-regular fa-circle text-secondary me-2"></i>}
                                            {proof.status}
                                          </td>
                                          <td className="text-center" style={{ width: '200px' }}>
                                            <Button variant={btnInfo.variant} size="sm" className="w-100" onClick={() => handleProofAction(proof)}>
                                              <i className={`${btnInfo.icon} me-2`}></i>{btnInfo.text}
                                            </Button>
                                          </td>
                                        </tr>
                                      )
                                    })}
                                  </tbody>
                                </Table>
                              </div>
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    )
                  })
                ) : (
                  <tr>
                    <td colSpan="4" className="text-center py-4 text-muted">
                      <i className="fa-solid fa-folder-open mb-2 fs-4 d-block"></i>
                      No assignments found for this course.
                    </td>
                  </tr>
                )}
              </tbody>
            </Table>

            <div className="d-flex justify-content-between align-items-center mt-3 text-muted small">
               <span>
                  Showing {sortedAssignments.length > 0 ? (assignmentPage - 1) * itemsPerPage + 1 : 0} to {Math.min(assignmentPage * itemsPerPage, sortedAssignments.length)} of {sortedAssignments.length} entries
               </span>
              {sortedAssignments.length > 0 && (
                <NumberedPagination 
                  currentPage={assignmentPage} 
                  totalPages={totalAssignmentPages} 
                  onPageChange={({ page }) => setAssignmentPage(page)} 
                />
              )}
            </div>
          </div>
        )}

      </Container>
      
      {/* Join Course Modal */}
      <Modal show={showJoinModal} onHide={() => setShowJoinModal(false)} centered>
        <Modal.Header closeButton>
            <Modal.Title>
                <i className="fa-solid fa-graduation-cap me-2 text-primary"></i>
                Join a Course
            </Modal.Title>
        </Modal.Header>
        <Modal.Body>
            <Form>
                <Form.Group className="mb-3" controlId="courseJoinCode">
                    <Form.Label className="fw-semibold">Course Join Code</Form.Label>
                    <Form.Control 
                        type="text" 
                        placeholder="e.g., MATHROCKS" 
                        autoFocus
                        value={joinCode}
                        onChange={(e) => setJoinCode(e.target.value)}
                    />
                    <Form.Text className="text-muted">
                        Enter the unique code provided by your instructor to enroll.
                    </Form.Text>
                </Form.Group>
            </Form>
        </Modal.Body>
        <Modal.Footer className="bg-light border-top-0">
            <Button variant="outline-secondary" onClick={() => setShowJoinModal(false)}>
                Cancel
            </Button>
            <Button variant="primary" onClick={handleJoinSubmit} disabled={!joinCode.trim()}>
                <i className="fa-solid fa-check me-2"></i>Join
            </Button>
        </Modal.Footer>
      </Modal>
    </MainLayout>
  );
}