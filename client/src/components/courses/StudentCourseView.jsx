import React, { useState, useMemo } from 'react';
import { Table, Button } from "react-bootstrap";
import NumberedPagination from '../Pagination';
import useSortableTable from '../../hooks/useSortableTable';

export default function StudentCourseView({ course, assignments, onBack }) {
  const [assignmentPage, setAssignmentPage] = useState(1);
  const [expandedAssignments, setExpandedAssignments] = useState([]);
  const itemsPerPage = 10;

  // 2. Filter assignments for THIS course, memoized for performance
  const currentAssignments = useMemo(() => {
    return assignments.filter(a => a.courseId === course.id);
  }, [assignments, course.id]);

  // 3. Pass the filtered assignments into the sorting hook
  const {
    sortedData: sortedAssignments,
    handleSort,
    getSortIcon,
    handleMouseDown
  } = useSortableTable(currentAssignments);

  // 4. Paginate
  const totalAssignmentPages = Math.ceil(sortedAssignments.length / itemsPerPage) || 1;
  const paginatedAssignments = sortedAssignments.slice(
    (assignmentPage - 1) * itemsPerPage,
    assignmentPage * itemsPerPage
  );

  const toggleAssignment = (assignmentId) => {
    setExpandedAssignments(prev => prev.includes(assignmentId) ? prev.filter(id => id !== assignmentId) : [...prev, assignmentId]);
  };

  const getButtonProps = (status) => {
    if (status === 'Completed') return { variant: 'secondary', icon: 'fa-solid fa-eye', text: 'View Submission' };
    if (status === 'In Progress') return { variant: 'primary', icon: 'fa-solid fa-rotate-right', text: 'Continue Assignment' };
    return { variant: 'success', icon: 'fa-solid fa-play', text: 'Start Assignment' };
  };

  const handleProofAction = (proof) => {
    if (proof.status === 'Completed') {
      console.log(`Viewing submission for ${proof.title}`);
    } else {
      console.log(`Starting/Continuing proof for ${proof.title}`);
    }
  };

  return (
    <div>
      <div className="mb-4">
        <Button variant="link" className="text-decoration-none p-0 mb-2 text-muted" onClick={onBack}>
          <i className="fa-solid fa-arrow-left me-2"></i>Back to Catalog
        </Button>
        <h2 style={{ color: '#0a3d62' }}>{course.name}</h2>
      </div>

      <h4 className="mb-3">Assignments</h4>
      <Table striped bordered hover responsive className="align-middle">
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
              style={{ cursor: 'pointer', width: '15%', whiteSpace: 'nowrap' }} 
              onClick={() => handleSort('dueDate')} 
              onMouseDown={handleMouseDown}
            >
              Due Date <i className={`ms-1 ${getSortIcon('dueDate')}`}></i>
            </th>
            <th style={{ width: '20%' }}>Status</th>
            <th className="text-center" style={{ width: '1%', whiteSpace: 'nowrap' }}>Action</th>
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
                      <Button variant="link" className="text-decoration-none p-0 me-3 text-dark text-start" onClick={() => toggleAssignment(assignment.id)}>
                        <i className={`fa-solid fa-chevron-${isExpanded ? 'down' : 'right'} text-primary`} style={{ width: '20px' }}></i>{assignment.title}
                      </Button>
                    </td>
                    <td>{assignment.dueDate}</td>
                    <td>
                      {isFullyComplete ? <span className="text-success fw-semibold"><i className="fa-solid fa-check me-2"></i>Completed</span> : <span className="text-muted">{completedProofs} / {totalProofs} Proofs</span>}
                    </td>
                    <td className="text-center"></td>
                  </tr>

                  {isExpanded && (
                    <tr>
                      <td colSpan="4" className="p-0 border-bottom-0">
                        <div className="bg-light p-3 border-start border-4 border-primary">
                          <Table size="sm" bordered hover className="mb-0 bg-white shadow-sm">
                            <thead className="table-light">
                              <tr>
                                <th style={{ width: '25%' }}>Proof Name</th>
                                <th style={{ width: '2%', whiteSpace: 'nowrap' }}>Status</th>
                                <th className="text-center" style={{ width: '1%', whiteSpace: 'nowrap' }}>Action</th>
                              </tr>
                            </thead>
                            <tbody>
                              {assignment.proofs.map((proof) => {
                                const btnInfo = getButtonProps(proof.status);
                                return (
                                  <tr key={proof.id}>
                                    <td className="fw-medium align-middle">{proof.title}</td>
                                    
                                    <td style={{ whiteSpace: 'nowrap' }}>
                                      <div className="d-flex align-items-center">
                                        {proof.status === 'Completed' && <i className="fa-solid fa-circle-check text-success me-2"></i>}
                                        {proof.status === 'In Progress' && <i className="fa-solid fa-circle-half-stroke text-warning me-2"></i>}
                                        {proof.status === 'Not Started' && <i className="fa-regular fa-circle text-secondary me-2"></i>}
                                        <span className="align-middle" style={{ paddingTop: '2px' }}>{proof.status}</span>
                                      </div>
                                    </td>
                                    <td className="text-center" style={{ width: '200px' }}>
                                      <Button variant={btnInfo.variant} size="sm" className="w-100" style={{ whiteSpace: 'nowrap' }} onClick={() => handleProofAction(proof)}>
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
        <span>Showing {sortedAssignments.length > 0 ? (assignmentPage - 1) * itemsPerPage + 1 : 0} to {Math.min(assignmentPage * itemsPerPage, sortedAssignments.length)} of {sortedAssignments.length} entries</span>
        {sortedAssignments.length > 0 && <NumberedPagination currentPage={assignmentPage} totalPages={totalAssignmentPages} onPageChange={({ page }) => setAssignmentPage(page)} />}
      </div>
    </div>
  );
}