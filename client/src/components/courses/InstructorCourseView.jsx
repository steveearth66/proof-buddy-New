import React, { useState, useEffect, useMemo, useRef } from 'react';
import { Table, Button, Form, Badge, Card, Row, Col, InputGroup } from "react-bootstrap";
import AddAssignmentModal from './modals/AddAssignmentModal';
import useSortableTable from '../../hooks/useSortableTable';

const MOCK_STUDENTS = [
  { id: 1, name: 'Student One', email: 'student1@example.com' },
  { id: 2, name: 'Student Two', email: 'student2@example.com' },
  { id: 3, name: 'Student Three', email: 'student3@example.com' }
];

export default function InstructorCourseView({ course, assignments, onBack, onToggleStatus, onToggleJoinCode, onEditJoinCode }) {
  const [assignmentPage, setAssignmentPage] = useState(1);
  const [showAddAssignmentModal, setShowAddAssignmentModal] = useState(false);
  const [newStudentEmail, setNewStudentEmail] = useState("");
  const itemsPerPage = 10;

  // 2. Filter & Hook
  const currentAssignments = useMemo(() => {
    return assignments.filter(a => a.courseId === course.id);
  }, [assignments, course.id]);

  const {
    sortedData: sortedAssignments,
    handleSort,
    getSortIcon,
    handleMouseDown
  } = useSortableTable(currentAssignments);

  // 3. Paginate
  const totalAssignmentPages = Math.ceil(sortedAssignments.length / itemsPerPage) || 1;
  const paginatedAssignments = sortedAssignments.slice(
    (assignmentPage - 1) * itemsPerPage,
    assignmentPage * itemsPerPage
  );

  const [editJoinCode, setEditJoinCode] = useState(false);
  const [joinCodeInput, setJoinCodeInput] = useState(course.joinCode);
  const joinCodeRef = useRef(null);

  // Keep input in sync if course changes externally
  useEffect(() => {
    setJoinCodeInput(course.joinCode);
  }, [course.joinCode]);

  // Submit the new code when the user clicks away from the input  
  const handleCodeBlur = () => {
    const cleanedCode = joinCodeInput.trim().toUpperCase();
    if (cleanedCode !== course.joinCode && cleanedCode !== "") {
      onEditJoinCode(course.id, cleanedCode);
    } else {
      setJoinCodeInput(course.joinCode); // keep last value if empty
    }
    setEditJoinCode(false);
  };

  const handleKeyDownJoinCode = (e) => {
    if (e.key === 'Enter') {
      e.target.blur();
    } else if (e.key === 'Escape') {
      setJoinCodeInput(course.joinCode);
      setEditJoinCode(false);
    }
  };

  return (
    <div>
      <div className="mb-4">
        <Button variant="link" className="text-decoration-none p-0 mb-2 text-muted" onClick={onBack}>
          <i className="fa-solid fa-arrow-left me-2"></i>Back to Courses
        </Button>
        <h2 style={{ color: '#0a3d62' }}>Manage Course: {course.name}</h2>
      </div>
      <Card className="mb-4 shadow-sm border-0 bg-light w-100 p-1">
        <Card.Body>
          <Row className="align-items-center mb-3">
            <Col md={8}>
              <h6 className="mb-1 fw-bold">Course Visibility</h6>
              <div className="text-muted small">Determines if the course and its contents are visible to enrolled students.</div>
            </Col>
            <Col md={4} className="d-flex flex-column align-items-start align-items-md-end mt-2 mt-md-0">
              <Form.Check
                type="switch"
                id="course-active-switch"
                checked={course.isActive}
                onChange={() => onToggleStatus(course.id)}
                className="mb-1 me-0"
              />
              <span className="text-muted small fw-semibold">
                {course.isActive ? "Active" : "Archived / Hidden"}
              </span>
            </Col>
          </Row>

          <hr className="text-muted my-3" />
          <Row className="align-items-center">
            <Col md={4}>
              <h6 className="mb-1 fw-bold">Enrollment Code</h6>
              <div className="text-muted small">Share this code to allow new students to join.</div>
            </Col>
            <Col md={4} className="mt-2 mt-md-0">
              <InputGroup size="sm">
                <InputGroup.Text className="bg-white"><i className="fa-solid fa-key text-muted"></i></InputGroup.Text>
                <Form.Control
                  ref={joinCodeRef}
                  type="text"
                  value={joinCodeInput}
                  onChange={(e) => setJoinCodeInput(e.target.value)}
                  onBlur={handleCodeBlur}
                  onKeyDown={handleKeyDownJoinCode}
                  disabled={!course.isJoinCodeActive || !editJoinCode}
                  className="fw-semibold font-monospace border-end-0"
                />
                <InputGroup.Text className="bg-white p-0">
                  <button
                    type="button"
                    className={`edit-icon-btn px-2 ${(!course.isJoinCodeActive || editJoinCode) ? "edit-code-btn-off" : ""}`}
                    onClick={() => {
                      setEditJoinCode(true);
                      setTimeout(() => joinCodeRef.current?.focus(), 0);
                    }}
                    disabled={!course.isJoinCodeActive || editJoinCode}
                  >
                    <i className="fa-solid fa-pen"></i>
                  </button>
                </InputGroup.Text>
              </InputGroup>
            </Col>
            <Col md={4} className="d-flex flex-column align-items-start align-items-md-end mt-2 mt-md-0">
              <Form.Check
                type="switch"
                id="joincode-active-switch"
                checked={course.isJoinCodeActive}
                onChange={() => onToggleJoinCode(course.id)}
                className="mb-1"
              />
              <span className="text-muted small fw-semibold">
                {course.isJoinCodeActive ? "Accepting Students" : "Disabled"}
              </span>
            </Col>
          </Row>
        </Card.Body>
      </Card>

      <div className="d-flex justify-content-between align-items-center mb-3">
        <h4 className="mb-0">Assignments</h4>
        <Button variant="primary" size="sm" onClick={() => setShowAddAssignmentModal(true)}>
          <i className="fa-solid fa-plus me-2"></i>Add Assignment
        </Button>
      </div>

      <Table striped bordered hover responsive className="align-middle mb-4">
        <thead className="table-light">
          <tr>
            <th
              style={{ cursor: 'pointer', width: 'auto' }}
              onClick={() => handleSort('title')}
              onMouseDown={handleMouseDown}
            >
              Assignment <i className={`ms-1 ${getSortIcon('title')}`}></i>
            </th>
            <th
              style={{ cursor: 'pointer', width: '10%', whiteSpace: 'nowrap' }}
              onClick={() => handleSort('dueDate')}
              onMouseDown={handleMouseDown}
            >
              Due Date <i className={`ms-1 ${getSortIcon('dueDate')}`}></i>
            </th>
            <th style={{ width: '12%' }}>Status</th>
            <th className="text-center" style={{ width: '1%', whiteSpace: 'nowrap' }}>Action</th>
          </tr>
        </thead>
        <tbody>
          {paginatedAssignments.map((assignment) => (
            <tr key={assignment.id}>
              <td className="fw-semibold">{assignment.title}</td>
              <td>{assignment.dueDate}</td>
              <td>
                <Badge
                  bg={assignment.status === 'Open' ? 'success' : 'secondary'}
                  className='w-100 py-2 text-uppercase letter-spacing-1'
                  style={{ fontSize: '0.85rem' }}
                >
                  {assignment.status}
                </Badge>
              </td>
              <td className="text-center" style={{ whiteSpace: 'nowrap' }}>
                <Button variant="outline-secondary" size="sm" className="me-2"><i className="fa-solid fa-pen"></i></Button>
                <Button variant="outline-danger" size="sm"><i className="fa-solid fa-trash"></i></Button>
              </td>
            </tr>
          ))}
        </tbody>
      </Table>

      {/* Student Roster */}
      <h4 className="mb-3">Enrolled Students</h4>
      <Table striped bordered hover responsive className="align-middle">
        <thead className="table-light">
          <tr>
            <th style={{ width: '15%', whiteSpace: 'nowrap' }}>Name</th>
            <th style={{ width: '0%', whiteSpace: 'nowrap' }}>Email</th>
            <th className="text-center" style={{ width: '0%', whiteSpace: 'nowrap' }}>Action</th>
          </tr>
        </thead>
        <tbody>
          {MOCK_STUDENTS.map(student => (
            <tr key={student.id}>
              <td className="fw-semibold">{student.name}</td>
              <td >{student.email}</td>
              <td className="text-center">
                <Button variant="outline-danger" size="sm">Remove</Button>
              </td>
            </tr>
          ))}
        </tbody>
      </Table>

      <div className="mt-3 p-3 bg-light rounded border">
        <h6 className="mb-3">Add Student Manually</h6>
        <Form className="d-flex gap-2 mb-1" onSubmit={(e) => { e.preventDefault(); console.log("Add student:", newStudentEmail) }}>
          <Form.Control type="email" placeholder="Student Email Address" value={newStudentEmail} onChange={e => setNewStudentEmail(e.target.value)} style={{ maxWidth: '300px' }} />
          <Button variant="primary" type="submit" disabled={!newStudentEmail}>Add Student</Button>
        </Form>
      </div>

      <AddAssignmentModal show={showAddAssignmentModal} onHide={() => setShowAddAssignmentModal(false)} />
    </div>
  );
}