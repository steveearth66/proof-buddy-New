import React, { useState, useEffect, useMemo, useRef } from 'react';
import { Table, Button, Form, Badge, Card, Row, Col, Spinner } from "react-bootstrap";
import AddAssignmentModal from './modals/AddAssignmentModal';
import useSortableTable from '../../hooks/useSortableTable';

const MOCK_STUDENTS = [
  { id: 1, name: 'Student One', email: 'student1@example.com' },
  { id: 2, name: 'Student Two', email: 'student2@example.com' },
  { id: 3, name: 'Student Three', email: 'student3@example.com' }
];

export default function InstructorCourseView({ course, assignments, onBack, onToggleStatus, onRegenerateJoinCode }) {
  const [assignmentPage, setAssignmentPage] = useState(1);
  const [showAddAssignmentModal, setShowAddAssignmentModal] = useState(false);
  const [newStudentEmail, setNewStudentEmail] = useState("");
  const itemsPerPage = 10;

  const [expiresAt, setExpiresAt] = useState(course.join_code_expires_at);

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

  // join code generation
  // --- New Join Code States ---
  const [newCode, setNewCode] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isCopied, setIsCopied] = useState(false);

  const handleGenerateCode = async () => {
    setIsGenerating(true);
    setNewCode(null);
    
    const response = await onRegenerateJoinCode(course.id); 
    
    if (response && response.join_code) {
        setNewCode(response.join_code);
        setExpiresAt(response.join_code_expires_at);
    }
    setIsGenerating(false);
  };

  const handleCopy = () => {
    if (newCode) {
      navigator.clipboard.writeText(newCode);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    }
  };

  const isCodeActive = expiresAt && new Date(expiresAt) > new Date();
  const formattedExpiration = expiresAt 
      ? new Date(expiresAt).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }) 
      : "No code generated";

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
                checked={course.is_active}
                onChange={() => onToggleStatus(course.id, course.is_active)}
                className="mb-1 me-0"
              />
              <span className="text-muted small fw-semibold">
                {course.is_active ? "Active" : "Archived / Hidden"}
              </span>
            </Col>
          </Row>

          <hr className="text-muted my-3" />
          <Row className="align-items-center">
            <Col md={4}>
              <h6 className="mb-1 fw-bold">Enrollment Code</h6>
              <div className="text-muted small">Generate a temporary 7-day code for students to join.</div>
            </Col>
            
            <Col md={4} className="mt-2 mt-md-0">
              {newCode ? (
                 <div className="p-2 border rounded bg-white text-center shadow-sm">
                   <div className="text-success small fw-bold mb-1">New Code Generated!</div>
                   <div className="d-flex justify-content-center align-items-center gap-2">
                       <code className="fs-5 text-primary mb-0">{newCode}</code>
                       <Button 
                         variant={isCopied ? "success" : "outline-secondary"} 
                         size="sm" 
                         onClick={handleCopy}
                         title="Copy to clipboard"
                       >
                         {isCopied ? <i className="fa-solid fa-check"></i> : <i className="fa-regular fa-copy"></i>}
                       </Button>
                   </div>
                   <div className="text-danger fw-semibold mt-1" style={{ fontSize: '0.75rem' }}>
                     <i className="fa-solid fa-triangle-exclamation me-1"></i>
                     Save this now. It will be hidden later.
                   </div>
                 </div>
              ) : (
                 <Button 
                   variant="outline-primary" 
                   size="sm" 
                   onClick={handleGenerateCode} 
                   disabled={isGenerating}
                   className="w-100 fw-semibold"
                 >
                   {isGenerating ? (
                     <Spinner size="sm" animation="border" />
                   ) : (
                     <><i className="fa-solid fa-arrows-rotate me-2"></i>Generate New Code</>
                   )}
                 </Button>
              )}
            </Col>
            <Col md={4} className="d-flex flex-column align-items-start align-items-md-end mt-2 mt-md-0">
              <span className={`small fw-bold mb-1 ${isCodeActive ? 'text-success' : 'text-danger'}`}>
                  {isCodeActive ? "Currently Accepting Students" : "Enrollment Closed"}
              </span>
              {expiresAt && (
                  <span className="text-muted small fw-semibold">
                    {isCodeActive ? "Expires: " : "Expired: "} 
                    {formattedExpiration}
                  </span>
              )}
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