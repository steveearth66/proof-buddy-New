import React, { useState, useMemo } from 'react';
import { Table, Button, Form } from "react-bootstrap";
import NumberedPagination from '../Pagination';
import CreateCourseModal from './modals/CreateCourseModal';
import useSortableTable from '../../hooks/useSortableTable';

export default function InstructorCatalog({ courses, onViewCourse, onToggleStatus, onToggleJoinCode, onEditJoinCode  }) {
  const [coursePage, setCoursePage] = useState(1);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const itemsPerPage = 10;

  // 2. Consume the Hook
  const {
    sortedData: sortedCourses,
    handleSort,
    getSortIcon,
    handleMouseDown
  } = useSortableTable(courses);

  const totalCoursePages = Math.ceil(sortedCourses.length / itemsPerPage) || 1;
  const paginatedCourses = sortedCourses.slice(
    (coursePage - 1) * itemsPerPage,
    coursePage * itemsPerPage
  );

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2 className="mb-0" style={{ color: '#0a3d62' }}>Instructor View: My Courses</h2>
        <Button variant="primary" onClick={() => setShowCreateModal(true)}>
          <i className="fa-solid fa-plus me-2"></i>Create Course
        </Button>
      </div>

      <Table striped bordered hover responsive className="align-middle">
        <thead className="table-light">
          <tr>
            <th style={{ cursor: 'pointer', width: '10%' }} onClick={() => handleSort('name')} onMouseDown={handleMouseDown}>
              Course Name <i className={`ms-1 ${getSortIcon('name')}`}></i>
            </th>
            <th style={{ width: '1%', whiteSpace: 'nowrap' }}>Join Code</th>
            <th style={{ width: '1%', whiteSpace: 'nowrap' }}>Status</th>
            <th style={{ width: '1%', whiteSpace: 'nowrap' }}>Students</th>
            <th style={{ width: '1%', whiteSpace: 'nowrap' }} className="text-center">Action</th>
          </tr>
        </thead>
        <tbody>
          {paginatedCourses.map((course) => (
            <tr key={course.id}>
              <td onClick={() => onViewCourse(course.id)} className="fw-semibold" style={{ cursor: 'pointer' }}>{course.name}</td>
              <td>
                {course.isJoinCodeActive ? (
                  <code className="bg-light px-2 py-1 rounded fw-semibold text-primary">{course.joinCode}</code>
                ) : (
                  <span className="text-muted text-decoration-line-through small"><i className="fa-solid fa-lock me-1"></i>{course.joinCode}</span>
                )}
              </td>              
              <td>
                <Form.Check
                  type="switch"
                  id={`switch-${course.id}`}
                  label={course.isActive ? "Active" : "Disabled"}
                  checked={course.isActive}
                  onChange={() => onToggleStatus(course.id)}
                />
              </td>
              <td><i className="fa-solid fa-users text-muted me-2"></i>32</td>
              <td className="text-center">
                <Button variant="outline-primary" style={{ whiteSpace: 'nowrap' }} size="sm" onClick={() => onViewCourse(course.id)}>
                  <i className="fa-solid fa-gear me-2"></i>Manage
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </Table>

      <div className="d-flex justify-content-between align-items-center mt-3 text-muted small">
        <span>Showing {sortedCourses.length > 0 ? (coursePage - 1) * itemsPerPage + 1 : 0} to {Math.min(coursePage * itemsPerPage, sortedCourses.length)} of {sortedCourses.length} entries</span>
        <NumberedPagination currentPage={coursePage} totalPages={totalCoursePages} onPageChange={({ page }) => setCoursePage(page)} />
      </div>

      <CreateCourseModal show={showCreateModal} onHide={() => setShowCreateModal(false)} />
    </div>
  );
}