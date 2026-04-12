import React, { useState } from 'react';
import { Table, Button, OverlayTrigger, Tooltip } from "react-bootstrap";
import NumberedPagination from '../Pagination';
import JoinCourseModal from './modals/JoinCourseModal';
import useSortableTable from '../../hooks/useSortableTable';

export default function StudentCatalog({ courses, onViewCourse, onJoinCourse, onLeaveCourse }) {
  const [coursePage, setCoursePage] = useState(1);
  const [showJoinModal, setShowJoinModal] = useState(false);
  const itemsPerPage = 10;

  // --- Initialize the Custom Hook ---
  const {
    sortedData: sortedCourses,
    handleSort,
    getSortIcon,
    handleMouseDown
  } = useSortableTable(courses);

  // --- Process Pagination on the Sorted Data ---
  const totalCoursePages = Math.ceil(sortedCourses.length / itemsPerPage) || 1;
  const paginatedCourses = sortedCourses.slice(
    (coursePage - 1) * itemsPerPage,
    coursePage * itemsPerPage
  );

  return (
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
              style={{ cursor: 'pointer', width: '25%' }} 
              onClick={() => handleSort('name')} 
              onMouseDown={handleMouseDown}
            >
              Course Name <i className={`ms-1 ${getSortIcon('name')}`}></i>
            </th>
            <th 
              style={{ cursor: 'pointer', width: '15%' }} 
              onClick={() => handleSort('instructor')} 
              onMouseDown={handleMouseDown}
            >
              Instructor <i className={`ms-1 ${getSortIcon('instructor')}`}></i>
            </th>
            <th 
              style={{ cursor: 'pointer', width: '10%', whiteSpace: 'nowrap' }} 
              onClick={() => handleSort('term')} 
              onMouseDown={handleMouseDown}
            >
              Term <i className={`ms-1 ${getSortIcon('term')}`}></i>
            </th>
            {/* Description naturally takes up the remaining ~50% of the space */}
            <th style={{ width: 'auto' }}>Description</th>
            <th className="text-center" style={{ width: '1%', whiteSpace: 'nowrap' }}>Action</th>
          </tr>
        </thead>
        <tbody>
          {paginatedCourses.map((course) => (
            <tr key={course.id}>
              <td
                onClick={() => onViewCourse(course.id)}
                className="fw-semibold"
                style={{ cursor: 'pointer' }}
              >
                {course.name}
              </td>
              <td>
                {course.instructor?.first_name 
                  ? `${course.instructor.first_name} ${course.instructor.last_name}` 
                  : course.instructor?.username}
              </td>
              <td>{course.term}</td>
              <td>{course.description}</td>
              <td className="text-center">
                <div className="d-flex justify-content-center gap-2">
                  <Button
                    variant="outline-primary"
                    size="sm"
                    onClick={() => onViewCourse(course.id)}
                    style={{ whiteSpace: 'nowrap' }}
                  >
                    <i className="fa-solid fa-arrow-right-to-bracket me-2"></i>Enter Course
                  </Button>

                  <OverlayTrigger
                    placement="top"
                    popperConfig={{ strategy: 'fixed' }}
                    overlay={
                      <Tooltip className="danger-tooltip" id={`tooltip-leave-${course.id}`}>
                        Leave Course
                      </Tooltip>
                    }
                  >
                    <Button
                      variant="outline-danger"
                      size="sm"
                      onClick={() => {
                          if (window.confirm(`Are you sure you want to leave ${course.name}?`)) {
                              onLeaveCourse(course.id);
                          }
                      }}
                      style={{ whiteSpace: 'nowrap' }}
                    >
                      <i className="fa-solid fa-door-open"></i>
                    </Button>
                  </OverlayTrigger>
                </div>
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

      <JoinCourseModal
        show={showJoinModal}
        onHide={() => setShowJoinModal(false)}
        onJoin={onJoinCourse}
      />
    </div>
  );
}