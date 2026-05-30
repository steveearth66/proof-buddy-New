import React, { useState, useRef, useEffect } from 'react';
import { Modal, Button, Table, Badge, Spinner } from "react-bootstrap";
import axios from 'axios'; // Ensure you use your project's fetch/axios instance
import courseService from '../../../services/courseServices';
import '../../../scss/_assignment-progress-modal.scss';
import { useNavigate } from 'react-router-dom';

export default function ViewAssignmentProgressModal({ show, onHide, assignment }) {

  // --- State ---
  // matrixData now cleanly holds both the columns (proofs) and the rows (students)
  const [matrixData, setMatrixData] = useState({ columns: [], students: [] });
  const [isLoading, setIsLoading] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  const navigate = useNavigate();
  
  const scrollContainerRef = useRef(null);

  // --- API Fetching Logic ---
  useEffect(() => {
  if (show && assignment?.id) {
    let isMounted = true;

    const fetchProgressData = async () => {
      setIsLoading(true);
      try {
        const data = await courseService.getStudentAssignmentStatus(assignment.id);
        
        if (isMounted && data) {
          setMatrixData(data);
        }
      } catch (error) {
        console.error("Dashboard failed to load:", error);
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    fetchProgressData();

    return () => { isMounted = false; };
  } else {
    setMatrixData({ columns: [], students: [] });
  }
}, [show, assignment?.id]);

  // --- Helpers ---
  const getStatusData = (student, proofId) => {
    return student?.statuses?.[proofId] || { status: 'not started', cloned_proof_id: null, proof_type: null }; 
  };

  // Renders the status using the Student Dashboard UI language
  const renderStatusDisplay = (status) => {
    switch (status?.toLowerCase()) {
      case 'complete':
        return (
          <div className="d-flex align-items-center justify-content-center text-nowrap">
            <i className="fa-solid fa-circle-check text-success me-2"></i>
            <span className="align-middle" style={{ paddingTop: '2px' }}>Completed</span>
          </div>
        );

      case 'late':
        return (
          <div className="d-flex align-items-center justify-content-center text-nowrap">
            <i className="fa-solid fa-clock text-danger me-2"></i>
      <span className="align-middle text-danger" style={{ paddingTop: '2px' }}>Completed (Late)</span>
          </div>
        );
      
      case 'in progress':
        return (
          <div className="d-flex align-items-center justify-content-center text-nowrap">
            <i className="fa-solid fa-circle-half-stroke text-warning me-2"></i>
            <span className="align-middle" style={{ paddingTop: '2px' }}>In Progress</span>
          </div>
        );
      
      case 'not started':
        return (
          <div className="d-flex align-items-center justify-content-center text-nowrap">
            <i className="fa-regular fa-circle text-secondary me-2"></i>
            <span className="align-middle" style={{ paddingTop: '2px' }}>Not Started</span>
          </div>
        );
      
      default:
        return <span className="text-muted">-</span>;
    }
  };

  // --- Scroll Tracking Logic ---
  const handleScroll = () => {
    if (scrollContainerRef.current) {
      setIsScrolled(scrollContainerRef.current.scrollLeft > 0);
    }
  };

  // --- Render ---
  return (
    <Modal id="assignment-status-modal" show={show} onHide={onHide} size="xl" centered>
      <Modal.Header closeButton>
        <Modal.Title>{assignment?.title} - Student Progress</Modal.Title>
      </Modal.Header>
      
      <Modal.Body>
        {/* 1. Show Loading State */}
        {isLoading ? (
          <div className="text-center py-5">
            <Spinner animation="border" variant="primary" />
            <p className="text-muted mt-2">Fetching student progress...</p>
          </div>
        ) : 
        
        /* 2. Show Error/Empty State if backend returned no columns */
        matrixData.columns.length === 0 ? (
          <p className="text-muted text-center py-4">No proofs assigned to this assignment.</p>
        ) : 
        
        /* 3. Show the Data Matrix */
        (
          <div 
            className="overflow-x-auto matrix-wrapper" 
            ref={scrollContainerRef} 
            onScroll={handleScroll}
          >
            <Table bordered hover className={`text-center align-middle mb-0 ${isScrolled ? 'is-scrolled' : ''}`} style={{ borderTop: 'none !important' }}>              
              
              <thead className="table-light">
                <tr style={{ borderTop: 'none' }}>
                  <th className="text-start sticky-top sticky-column">Student</th>
                  {/* Render Columns dynamically from API */}
                  {matrixData.columns.map((col) => (
                    <th key={col.id} style={{ minWidth: '130px' }}>
                      {col.title}
                    </th>
                  ))}
                </tr>
              </thead>
              
              <tbody>
                {/* Map over Students */}
                {matrixData.students.map((student) => (
                  <tr key={student.id}>
                    
                    <td className="text-start fw-bold text-nowrap sticky-column">
                      {student.username} <span className="text-muted fw-normal ms-1">({student.email})</span>
                    </td>
                    
                    {/* Intersect using the columns array */}
                    {matrixData.columns.map((col) => {
                      const statusData = getStatusData(student, col.id);
                      const hasStarted = !!statusData.cloned_proof_id;
                      
                      return (
                        <td 
                          key={`${student.id}-${col.id}`}
                          style={{ cursor: hasStarted ? 'pointer' : 'default' }}
                          onClick={() => {
                            if (hasStarted) {
                              navigate(statusData.proof_type == 'equationalproof' ? '/equational-reasoning-new' : '/induction-racket', { 
                                state: { id: statusData.cloned_proof_id } 
                              });
                            }
                          }}
                        >
                          {renderStatusDisplay(statusData.status)}
                        </td>
                      );
                    })}
                    
                  </tr>
                ))}
                
                {/* Empty state for students */}
                {matrixData.students.length === 0 && (
                    <tr>
                      <td colSpan={matrixData.columns.length + 1} className="text-center py-4 text-muted">
                        No students enrolled.
                      </td>
                    </tr>
                )}
              </tbody>

            </Table>
          </div>
        )}
      </Modal.Body>
      
      <Modal.Footer className="bg-light border-top-0">
        <Button variant="secondary" onClick={onHide}>Close</Button>
      </Modal.Footer>
    </Modal>
  );
}