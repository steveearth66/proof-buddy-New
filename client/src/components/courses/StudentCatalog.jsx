import React, { useState, useEffect } from 'react';
import { Card, ListGroup, Badge, Alert, Table, Button, OverlayTrigger, Tooltip } from "react-bootstrap";
import NumberedPagination from '../Pagination';
import JoinCourseModal from './modals/JoinCourseModal';
import useSortableTable from '../../hooks/useSortableTable';
import courseService from '../../services/courseServices';

export default function StudentCatalog({ courses, onViewCourse, onJoinCourse, onLeaveCourse, onRefreshCourses }) {
  const [coursePage, setCoursePage] = useState(1);
  const [showJoinModal, setShowJoinModal] = useState(false);
  const [invitations, setInvitations] = useState([]);
  const [loadingInvites, setLoadingInvites] = useState(false);
  const itemsPerPage = 10;

  useEffect(() => {
    fetchInvitations();
  }, [courses]);

  const fetchInvitations = async () => {
    setLoadingInvites(true);
    const data = await courseService.getMyInvitations();
    if (data) setInvitations(data);
    setLoadingInvites(false);
  };

  const handleInvitationResponse = async (invitationId, action) => {
    const result = await courseService.respondToInvitation(invitationId, action);
    if (result) {
        setInvitations(prev => prev.filter(inv => inv.id !== invitationId));
        if (action === 'accept') {
            onRefreshCourses(); 
        }
    }
  };

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
      {invitations.length > 0 && (
        <Card className="mb-5 border-primary shadow-sm bg-light">
          <Card.Header className="bg-primary text-white d-flex align-items-center py-2">
            <i className="fa-solid fa-envelope-open-text me-2"></i>
            <h5 className="mb-0 fs-6">Pending Course Invitations</h5>
          </Card.Header>
          <ListGroup variant="flush">
            {invitations.map((invite) => (
              <ListGroup.Item key={invite.id} className="py-3 bg-transparent">
                <div className="d-flex justify-content-between align-items-center">
                  <div>
                    <div className="fw-bold text-dark">{invite.course_name}</div>
                    <div className="text-muted small">
                      Invited on {new Date(invite.sent_at).toLocaleDateString()}
                    </div>
                  </div>
                  <div className="d-flex gap-2">
                    <Button 
                      variant="success" 
                      size="sm" 
                      className="px-3"
                      onClick={() => handleInvitationResponse(invite.id, 'accept')}
                    >
                      <i className="fa-solid fa-check me-1"></i> Accept
                    </Button>
                    <Button 
                      variant="outline-secondary" 
                      size="sm"
                      onClick={() => handleInvitationResponse(invite.id, 'reject')}
                    >
                      Decline
                    </Button>
                  </div>
                </div>
              </ListGroup.Item>
            ))}
          </ListGroup>
        </Card>
      )}

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
            <th style={{ width: 'auto' }}>Description</th>
            <th className="text-center" style={{ width: '1%', whiteSpace: 'nowrap' }}>Action</th>
          </tr>
        </thead>
        <tbody>
          {paginatedCourses.length > 0 ? (
            paginatedCourses.map((course) => (
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
                    overlay={
                      <Tooltip className="danger-tooltip" style={{ position:"fixed" }} id={`tooltip-leave-${course.id}`}>
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
          ))
          ) : (
            <tr>
              <td colSpan="5" className="text-center py-3 text-muted">
                <i className="fa-solid fa-graduation-cap fa-3x mb-3 d-block opacity-25"></i>
                You aren't enrolled in any courses yet.
              </td>
            </tr>
          )}
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