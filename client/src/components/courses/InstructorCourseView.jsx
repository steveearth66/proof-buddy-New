import React, { useState, useMemo } from 'react';
import { Table, Button, Form, Badge } from "react-bootstrap";
import NumberedPagination from '../Pagination';
import AddAssignmentModal from './modals/AddAssignmentModal';
import useSortableTable from '../../hooks/useSortableTable'; // 1. Import Hook

const MOCK_STUDENTS = [
  { id: 1, name: 'Student One', email: 'student1@example.com' },
  { id: 2, name: 'Student Two', email: 'student2@example.com' },
  { id: 3, name: 'Student Three', email: 'student3@example.com' }
];

export default function InstructorCourseView({ course, assignments, onBack }) {
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

  return (
    <div>
      <div className="mb-4">
        <Button variant="link" className="text-decoration-none p-0 mb-2 text-muted" onClick={onBack}>
          <i className="fa-solid fa-arrow-left me-2"></i>Back to Courses
        </Button>
        <h2 style={{ color: '#0a3d62' }}>Manage Course: {course.name}</h2>
      </div>

      <div className="bg-light p-3 rounded mb-4 border d-flex justify-content-between align-items-center">
        <div>
          <span className="fw-semibold me-3">Course Join Code:</span>
          <code className="fs-5 bg-white px-2 py-1 rounded border">{course.joinCode}</code>
        </div>
        <Form.Check type="switch" id="course-active-switch" label={course.isActive ? "Active (Students can join)" : "Disabled"} checked={course.isActive} onChange={() => console.log("Toggle Status")} />
      </div>

      <div className="d-flex justify-content-between align-items-center mb-3">
        <h4 className="mb-0">Assignments</h4>
        <Button variant="primary" size="sm" onClick={() => setShowAddAssignmentModal(true)}>
          <i className="fa-solid fa-plus me-2"></i>Add Assignment
        </Button>
      </div>

      <Table striped bordered hover responsive className="align-middle mb-5">
        <thead className="table-light">
          <tr>
            <th style={{ cursor: 'pointer' }} onClick={() => handleSort('title')} onMouseDown={handleMouseDown}>
              Assignment Title <i className={`ms-1 ${getSortIcon('title')}`}></i>
            </th>
            <th style={{ cursor: 'pointer' }} onClick={() => handleSort('dueDate')} onMouseDown={handleMouseDown}>
              Due Date <i className={`ms-1 ${getSortIcon('dueDate')}`}></i>
            </th>
            <th>Status</th>
            <th className="text-center">Action</th>
          </tr>
        </thead>
        <tbody>
          {paginatedAssignments.map((assignment) => (
            <tr key={assignment.id}>
              <td className="fw-semibold">{assignment.title}</td>
              <td>{assignment.dueDate}</td>
              <td><Badge bg={assignment.status === 'Open' ? 'success' : 'secondary'}>{assignment.status}</Badge></td>
              <td className="text-center">
                <Button variant="outline-secondary" size="sm" className="me-2"><i className="fa-solid fa-pen"></i></Button>
                <Button variant="outline-danger" size="sm"><i className="fa-solid fa-trash"></i></Button>
              </td>
            </tr>
          ))}
        </tbody>
      </Table>

      {/* ... Student Roster Block remains the same ... */}
      <h4 className="mb-3">Enrolled Students</h4>
      <Table striped bordered hover responsive className="align-middle">
        <thead className="table-light">
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th className="text-center">Action</th>
          </tr>
        </thead>
        <tbody>
          {MOCK_STUDENTS.map(student => (
            <tr key={student.id}>
              <td className="fw-semibold">{student.name}</td>
              <td>{student.email}</td>
              <td className="text-center">
                <Button variant="outline-danger" size="sm">Remove</Button>
              </td>
            </tr>
          ))}
        </tbody>
      </Table>

      <div className="mt-3 p-3 bg-light rounded border">
        <h6 className="mb-3">Add Student Manually</h6>
        <Form className="d-flex gap-2" onSubmit={(e) => { e.preventDefault(); console.log("Add student:", newStudentEmail) }}>
          <Form.Control type="email" placeholder="Student Email Address" value={newStudentEmail} onChange={e => setNewStudentEmail(e.target.value)} style={{ maxWidth: '300px' }} />
          <Button variant="primary" type="submit" disabled={!newStudentEmail}>Add Student</Button>
        </Form>
      </div>

      <AddAssignmentModal show={showAddAssignmentModal} onHide={() => setShowAddAssignmentModal(false)} />
    </div>
  );
}