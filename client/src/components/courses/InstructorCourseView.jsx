import React, { useState, useEffect, useMemo, useRef } from 'react';
import { Table, Button, Form, Badge, Card, Row, Col, InputGroup, Spinner, Alert, ListGroup, OverlayTrigger, Tooltip, Nav } from "react-bootstrap";
import AddAssignmentModal from './modals/AddAssignmentModal';
import useSortableTable from '../../hooks/useSortableTable';
import courseService from '../../services/courseServices';
import ViewAssignmentProgressModal from './modals/ViewAssignmentProgressModal';
import { Eye } from "react-bootstrap-icons";

export default function InstructorCourseView({ course, assignments, onBack, onToggleStatus, onRegenerateJoinCode, onUpdateCourse, onSaveAssignment, onDeleteAssignment, onRefreshAssignments }) {
  const [assignmentPage, setAssignmentPage] = useState(1);
  const [showAddAssignmentModal, setShowAddAssignmentModal] = useState(false);
  const [addAssignmentMode, setAddAssignmentMode] = useState(null);
  const [editAssignment, setEditAssignment] = useState(null);
  const [showAssignmentProgressModal, setShowAssignmentProgressModal] = useState(false);
  const [viewAssignment, setViewAssignment] = useState(null);
  const [newStudentEmail, setNewStudentEmail] = useState("");
  const itemsPerPage = 10;

  const initialSeason = course.term ? course.term.split(' ')[0] : 'Fall';
  const initialYear = course.term ? course.term.split(' ')[1] : new Date().getFullYear();
  const [editSeason, setEditSeason] = useState(initialSeason);
  const [editYear, setEditYear] = useState(initialYear);

  const [candidateList, setCandidateList] = useState([]);
  const [expiresAt, setExpiresAt] = useState(course.join_code_expires_at);
  const [isAddingStudent, setIsAddingStudent] = useState(false);
  const [studentFeedback, setStudentFeedback] = useState(null);

  const [windowWidth, setWindowWidth] = useState(window.innerWidth);

  const [shareRequestsTab, setShareRequestsTab] = useState('incoming');
  const [incomingShares, setIncomingShares] = useState([]);
  const [outgoingShares, setOutgoingShares] = useState([]);
  const [isProcessingShare, setIsProcessingShare] = useState(false);

  const fetchShareRequests = async () => {
    try {
      const data = await courseService.getSharedAssignments(course.id);
      onRefreshAssignments();
      if (data) {
        setIncomingShares(data.incoming || []);
        setOutgoingShares(data.sent || []);
      }
    } catch (err) {
      console.error("Error populating component share request arrays:", err);
    }
  };

  useEffect(() => {
    const handleResize = () => setWindowWidth(window.innerWidth);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const [invitations, setInvitations] = useState([]);
  useEffect(() => {
    const fetchInvitations = async () => {
        const data = await courseService.getCourseInvitations(course.id);
        if (data) setInvitations(data);
    };
    fetchInvitations();
    fetchShareRequests();
  }, [course.id]);

  const handleResolveShare = async (shareRequestId, action) => {
    if (action === 'reject' && !window.confirm("Are you sure you want to decline this shared assignment package?")) return;
    
    setIsProcessingShare(true);
    try {
      await courseService.respondToShareRequest(shareRequestId, action);
      await fetchShareRequests();
    } catch (err) {
      alert("Error processing share request choice.");
    } finally {
      setIsProcessingShare(false);
    }
  };

  const handleCancelShareRequest = async (shareRequestId) => {
    if (!window.confirm("Are you sure you want to revoke this outbound share request? This will delete the staged copy.")) return;

    try {
      await courseService.cancelShareRequest(shareRequestId);
      await fetchShareRequests();
    } catch (err) {
      alert("Failed to cancel share request.");
    }
  };

  const handleSaveAssignment = async (payload) => {
    let success = true;
    try {
      if (payload.copy_mode === 'external') {
        const sharePayload = {
          source_course_id: parseInt(payload.source_course_id),
          target_course_id: parseInt(payload.course),
          title: payload.title,
          description: payload.description,
          due_date: payload.due_date,
          proofs: payload.proofs
        };
        await courseService.sendAssignmentShare(sharePayload);
      } else {
        await onSaveAssignment(payload);
      }
    } catch (error) {
      console.error("Failed to execute assignment save transaction:", error);
      success = false;
    } finally {
      fetchShareRequests();
    }
    return success;
  };

  // Define your dynamic width
  const dueDateWidth = 
    windowWidth < 768  ? '20%' : 
    windowWidth < 992  ? '15%' : 
    windowWidth < 1200 ? '12%' : '10%';

  const handleAddStudent = async (e, specificUsername = null) => {
    if (e) e.preventDefault();
      
    const identifierToSubmit = specificUsername || newStudentEmail.trim();
    if (!identifierToSubmit) return;

    setIsAddingStudent(true);
    setStudentFeedback(null);
    setCandidateList([]); 

    const payload = {
      course: course.id,
      student: identifierToSubmit
    };

    const result = await courseService.addStudent(payload);
    
    setIsAddingStudent(false);

    // 1Check for 204 (Already enrolled)
    if (result && result.status === 204) {
      setStudentFeedback({ 
        type: 'warning', 
        message: 'Student is already enrolled in this course.' 
      });
    }
    // Handle Disambiguation (Multiple users found)
    else if (result && result.requires_disambiguation) {
      setStudentFeedback({ 
        type: 'warning', 
        message: result.message 
      });
      setCandidateList(result.candidates);
    }
    else if (result && result.status === 200) {
        const updatedInvite = result.data.invitation;
        setInvitations(prev => prev.map(inv => inv.id === updatedInvite.id ? updatedInvite : inv));
        setNewStudentEmail("");
        setStudentFeedback({ type: 'info', message: 'Existing invitation has been reset to pending.' });
    }
    // Handle 201 Created or 200 OK (Invitation object returned)
    else if (result && result.data?.id) { 
      setInvitations(prev => {
          const filtered = prev.filter(inv => inv.student.id !== result.data.student.id);
          return [result.data, ...filtered];
      });

      setNewStudentEmail("");
      setStudentFeedback({ 
          type: 'success', 
          message: 'Invitation sent successfully! The student must now accept it.' 
      });
      
      // Auto-clear success message
      setTimeout(() => setStudentFeedback(null), 4000);
    } 
    // Handle Errors (404, 403, 400, etc.)
    else {
      setStudentFeedback({ 
        type: 'danger', 
        message: result?.data?.message || 'Failed to process request. Please try again.' 
      });
    }
  };

  const handleCancelInvitation = async (invitationId) => {
    if (!window.confirm("Are you sure you want to cancel this invitation?")) return;

    const success = await courseService.cancelInvitation(course.id, invitationId);
    if (success !== null) {
        setInvitations(prev => prev.filter(i => i.id !== invitationId));
    }
  };

  const handleRemoveStudent = async (studentIdentifier) => {
    if (!window.confirm(`Are you sure you want to remove ${studentIdentifier} from the course?`)) return;

    const payload = {
        course: course.id,
        student: studentIdentifier
    };

    const success = await courseService.removeStudent(payload);

    if (success) {
        const updatedCourse = {
            ...course,
            students: course.students.filter(s => s.email !== studentIdentifier && s.username !== studentIdentifier)
        };
        onUpdateCourse(updatedCourse);
    } else {
        alert("Failed to remove student. Please try again.");
    }
  };

  // 2. Filter & Hook
  const currentAssignments = useMemo(() => {
    return assignments.filter(a => a.course === course.id);
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

  const handleDeleteAssignmentClick = async (assignment) => {
    if (window.confirm(`Are you sure you want to delete "${assignment.title}"? This cannot be undone.`)) {
      await onDeleteAssignment(assignment.id);
    }
  };

  const handleViewStudentProgress = async (assignment) => {
    setViewAssignment(assignment);
    setShowAssignmentProgressModal(true);
  };

  const handleEditAssignment = async (assignment) => {
    setEditAssignment(assignment);
    setAddAssignmentMode("edit");
    setShowAddAssignmentModal(true);
  };

  const handleCopyAssignment = async (assignment) => {
    setEditAssignment(assignment);
    setAddAssignmentMode("copy");
    setShowAddAssignmentModal(true);
  };

  const [isEditingTerm, setIsEditingTerm] = useState(false);

  // --- Description State ---
  const [editDescription, setEditDescription] = useState(course?.description || "");
  const [isEditingDescription, setIsEditingDescription] = useState(false);

  // --- Handlers ---
  const handleUpdateField = async (field, value) => {
      
  };

  const handleTermSave = async () => {
      const newTerm = `${editSeason} ${editYear}`;
      if (newTerm !== course.term) {
          const updatedCourse = await courseService.updateCourseTerm(course.id, newTerm); 
          if (updatedCourse) onUpdateCourse(updatedCourse);
      }
      setIsEditingTerm(false); // Close edit mode
  };

  const handleDescriptionSave = async () => {
      if (editDescription !== course.description) {
          const updatedCourse = await courseService.updateCourseDescription(course.id, editDescription); 
          if (updatedCourse) onUpdateCourse(updatedCourse);
      }
      setIsEditingDescription(false); // Close edit mode
  };

  const cancelTermEdit = () => {
      // Reset to original values and close
      setEditSeason(initialSeason);
      setEditYear(initialYear);
      setIsEditingTerm(false);
  };

  const cancelDescriptionEdit = () => {
      setEditDescription(course?.description || "");
      setIsEditingDescription(false);
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
                checked={course.is_active}
                onChange={() => onToggleStatus(course.id, course.is_active)}
                className="mb-1 me-0"
              />
              <span className="text-muted small fw-semibold">
                {course.is_active ? "Active" : "Archived / Hidden"}
              </span>
            </Col>
          </Row>
          
          {/* COURSE TERM ROW */}
          <hr className="text-muted my-3" />
          <Row className="align-items-center">
            <Col md={9}>
              <h6 className="mb-1 fw-bold">Course Term</h6>
              <div className="text-muted small">Select the academic season and year.</div>
            </Col>
            
            <Col md={3}>
              {!isEditingTerm ? (
                <div className="d-flex justify-content-between align-items-center bg-white border rounded p-1 ps-2">
                  <span className="fw-semibold small">{course.term || "Not Set"}</span>
                  <Button variant="light" size="sm" onClick={() => setIsEditingTerm(true)}>
                    <i className="fa-solid fa-pen text-muted"></i>
                  </Button>
                </div>
              ) : (
                <div className="d-flex flex-column gap-2">
                  <div className="d-flex gap-2">
                    <Form.Select size="sm" value={editSeason} onChange={(e) => setEditSeason(e.target.value)}>
                        <option value="Spring">Spring</option>
                        <option value="Summer">Summer</option>
                        <option value="Fall">Fall</option>
                        <option value="Winter">Winter</option>
                    </Form.Select>
                    
                    <Form.Control 
                      type="number" size="sm" min="2020" max="2100"
                      value={editYear} onChange={(e) => setEditYear(e.target.value)}
                      style={{ width: '100px' }}
                    />
                  </div>
                  <div className="d-flex gap-1 justify-content-end">
                    <Button variant="outline-secondary" size="sm" onClick={cancelTermEdit}>Cancel</Button>
                    <Button variant="primary" size="sm" onClick={handleTermSave}>Save</Button>
                  </div>
                </div>
              )}
            </Col>
          </Row>

          {/* COURSE DESCRIPTION ROW */}
          <hr className="text-muted my-3" />
          <Row className="align-items-start">
            <Col md={5}>
              <h6 className="mb-1 fw-bold">Course Description</h6>
              <div className="text-muted small">Visible to students in the catalog.</div>
            </Col>
            
            <Col md={7}>
              {!isEditingDescription ? (
                <div className="bg-white border rounded p-2 position-relative" style={{ minHeight: '60px' }}>
                  <p className="mb-0 small text-muted pe-4">
                    {course.description || <span className="fst-italic">No description provided.</span>}
                  </p>
                  <Button 
                    variant="light" size="sm" 
                    className="position-absolute top-0 end-0 m-1" 
                    onClick={() => setIsEditingDescription(true)}
                  >
                    <i className="fa-solid fa-pen text-muted"></i>
                  </Button>
                </div>
              ) : (
                <div className="d-flex flex-column gap-2">
                  <Form.Control 
                    as="textarea" rows={3} size="sm"
                    value={editDescription} 
                    onChange={(e) => setEditDescription(e.target.value)}
                    placeholder="Enter course description..."
                  />
                  <div className="d-flex gap-1 justify-content-end">
                    <Button variant="outline-secondary" size="sm" onClick={cancelDescriptionEdit}>Cancel</Button>
                    <Button variant="primary" size="sm" onClick={handleDescriptionSave}>Save</Button>
                  </div>
                </div>
              )}
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
        <Button variant="primary" size="sm" onClick={() => {setAddAssignmentMode("create"); setShowAddAssignmentModal(true);}}>
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
              style={{ cursor: 'pointer', width: dueDateWidth, whiteSpace: 'nowrap' }}
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
          {paginatedAssignments.length > 0 ? (
            paginatedAssignments.map((assignment) => {
              // Calculate if the assignment is still open based on the due date
              const isOpen = new Date(assignment.due_date) > new Date();
              
              return (
                <tr key={assignment.id}>
                  <td className="fw-semibold">
                    {assignment.title}
                    <div className="text-muted small" style={{ fontSize: '0.75rem' }}>
                      {assignment.proofs?.length || 0} proof{assignment.proofs?.length === 1 ? "" : "s"} attached
                    </div>
                  </td>
                  <td>
                    {new Date(assignment.due_date).toLocaleDateString([], { 
                        month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit', hour12: true 
                    })}
                  </td>
                  <td>
                    <Badge
                      bg={isOpen ? 'success' : 'secondary'}
                      className='w-100 py-2 text-uppercase letter-spacing-1'
                      style={{ fontSize: '0.85rem' }}
                    >
                      {isOpen ? 'Open' : 'Closed'}
                    </Badge>
                  </td>
                  <td className="text-center" style={{ whiteSpace: 'nowrap' }}>
                    <OverlayTrigger placement="top" overlay={<Tooltip style={{ position:"fixed" }} id={`tooltip-view-${assignment.id}`}>Edit Assignment</Tooltip>}>
                      <Button variant="outline-secondary" size="sm" className="me-1" onClick={(e) => {e.currentTarget.blur(); handleEditAssignment(assignment);}}><i className="fa-solid fa-pen"></i></Button>
                    </OverlayTrigger>
                    <OverlayTrigger placement="top" overlay={<Tooltip style={{ position:"fixed" }} id={`tooltip-view-${assignment.id}`}>View Student Progress</Tooltip>}>
                      <Button variant="outline-secondary" size="sm" className="me-1" onClick={(e) => {e.currentTarget.blur(); handleViewStudentProgress(assignment);}}><Eye></Eye></Button>
                    </OverlayTrigger>
                    <OverlayTrigger placement="top" overlay={<Tooltip style={{ position:"fixed" }} id={`tooltip-view-${assignment.id}`}>Copy Assignment</Tooltip>}>
                      <Button variant="outline-secondary" size="sm" className="me-1" onClick={(e) => {e.currentTarget.blur(); handleCopyAssignment(assignment);}}><i className="fa-solid fa-copy"></i></Button>
                    </OverlayTrigger>
                    <OverlayTrigger placement="top" overlay={<Tooltip style={{ position:"fixed" }} id={`tooltip-delete-assignment-${assignment.id}`}>Delete Assignment</Tooltip>}>
                      <Button variant="outline-danger" size="sm" onClick={(e) => {e.currentTarget.blur(); handleDeleteAssignmentClick(assignment);}}><i className="fa-solid fa-trash"></i></Button>
                    </OverlayTrigger>
                  </td>
                </tr>
              );
            })
          ) : (
            <tr>
              <td colSpan="4" className="text-center py-4 text-muted">
                No assignments created yet. Click "Add Assignment" to get started!
              </td>
            </tr>
          )}
        </tbody>
      </Table>

      {(outgoingShares.length > 0 || incomingShares.length > 0) && (
        <Card className="mb-4 shadow-sm border-0 bg-light p-3">
          <div className="d-flex justify-content-between align-items-center mb-2">
            <h5 className="mb-0 text-dark fw-bold">
              <i className="fa-solid fa-share-nodes me-2 text-primary"></i>Shared Assignment Packages
            </h5>
            {incomingShares.length > 0 && (
              <Badge bg="danger" pill className="ms-2">{incomingShares.length} Pending</Badge>
            )}
          </div>
          <p className="text-muted small mb-3">
            Review incoming shared assignments or check the state of assignments you pushed out to a colleague.
          </p>

          <Nav variant="pills" className="mb-3" activeKey={shareRequestsTab} onSelect={(k) => setShareRequestsTab(k)}>
            <Nav.Item>
              <Nav.Link eventKey="incoming" className="small py-1">
                Incoming Packages ({incomingShares.length})
              </Nav.Link>
            </Nav.Item>
            <Nav.Item>
              <Nav.Link eventKey="outgoing" className="small py-1">
                Sent Tracking ({outgoingShares.length})
              </Nav.Link>
            </Nav.Item>
          </Nav>

          {shareRequestsTab === 'incoming' ? (
            <Table striped bordered hover responsive size="sm" className="bg-white align-middle mb-0 small shadow-sm rounded">
              <thead className="table-secondary">
                <tr>
                  <th>Sender</th>
                  <th>Assignment Title</th>
                  <th>Included Proof Elements</th>
                  <th className="text-center" style={{ width: '1%' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {incomingShares.length > 0 ? (
                  incomingShares.map((req) => (
                    <tr key={req.share_request_id}>
                      <td className="fw-semibold">@{req.sender_username}</td>
                      <td>
                        <div className="fw-bold text-primary">{req.assignment.title}</div>
                        <div className="text-muted text-truncate" style={{ maxWidth: '280px' }}>
                          {req.assignment.description}
                        </div>
                      </td>
                      <td>
                        <div className="d-flex flex-wrap gap-1">
                          {req.assignment.proofs?.map((p, i) => (
                            <Badge key={i} bg="info" className="text-dark bg-opacity-10 border border-info-subtle">
                              {p.name} ({p.type === 'equationalproof' ? 'Eq' : 'Ind'})
                            </Badge>
                          ))}
                        </div>
                      </td>
                      <td className="text-center" style={{ whiteSpace: 'nowrap' }}>
                        <Button 
                          variant="success" size="sm" className="me-1 py-0 px-2 fw-semibold"
                          onClick={() => handleResolveShare(req.share_request_id, 'accept')}
                          disabled={isProcessingShare}
                        >
                          Accept
                        </Button>
                        <Button 
                          variant="outline-danger" size="sm" className="py-0 px-2"
                          onClick={() => handleResolveShare(req.share_request_id, 'reject')}
                          disabled={isProcessingShare}
                        >
                          Decline
                        </Button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="4" className="text-center py-3 text-muted fst-italic">
                      No incoming assignment sharing requests found for this course.
                    </td>
                  </tr>
                )}
              </tbody>
            </Table>
          ) : (
            <Table striped bordered hover responsive size="sm" className="bg-white align-middle mb-0 small shadow-sm rounded">
              <thead className="table-secondary">
                <tr>
                  <th>Target Destination Course</th>
                  <th>Assignment Title</th>
                  <th className="text-center">Status</th>
                  <th className="text-center" style={{ width: '1%' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {outgoingShares.length > 0 ? (
                  outgoingShares.map((req) => (
                    <tr key={req.share_request_id}>
                      <td>
                        <div className="fw-semibold">{req.target_course_name}</div>
                        <div className="small text-muted">Recipient: {req.recipient_instructor}</div>
                      </td>
                      <td className="fw-bold text-dark">{req.assignment_title}</td>
                      <td className="text-center">
                        <Badge bg={req.status === 'pending' ? 'warning' : req.status === 'accepted' ? 'success' : 'danger'} className="text-capitalize px-2 py-1">
                          {req.status}
                        </Badge>
                      </td>
                      <td className="text-center">
                        {req.status === 'pending' && (
                          <Button variant="outline-danger" size="sm" className="py-0 px-2" onClick={() => handleCancelShareRequest(req.share_request_id)}>
                            Revoke
                          </Button>
                        )}
                        {req.status === 'rejected' && (
                          <Button variant="outline-secondary" size="sm" className="py-0 px-2" onClick={() => handleCancelShareRequest(req.share_request_id)}>
                            Clear
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="4" className="text-center py-3 text-muted fst-italic">
                      You haven't initiated any shared packages from this course environment.
                    </td>
                  </tr>
                )}
              </tbody>
            </Table>
          )}
        </Card>
      )}

      {/* Student Roster */}
      <h4 className="mb-3">Enrolled Students</h4>
      <Table striped bordered hover responsive className="align-middle">
        <thead className="table-light">
          <tr>
            <th style={{ width: '15%', whiteSpace: 'nowrap' }}>Username</th>
            <th style={{ width: '15%', whiteSpace: 'nowrap' }}>Email</th>
            <th className="text-center" style={{ width: '0%', whiteSpace: 'nowrap' }}>Action</th>
          </tr>
        </thead>
        <tbody>
          {course.students && course.students.length > 0 ? (
              course.students.map(student => (
                <tr key={student.id}>
                  <td className="text-muted">{student.username}</td>
                  <td>{student.email}</td>
                  <td className="text-center">
                    <Button variant="outline-danger" size="sm" onClick={() => handleRemoveStudent(student.username)}>
                        Remove
                    </Button>
                  </td>
                </tr>
              ))
          ) : (
              <tr>
                  <td colSpan="4" className="text-center py-4 text-muted">
                      No students enrolled in this course yet. Share the Join Code to invite them!
                  </td>
              </tr>
          )}
        </tbody>
      </Table>

      {invitations && invitations.length > 0 && (
        <>
          <h4 className="mb-3">Invited Students</h4>
          <Table striped bordered hover responsive className="align-middle mb-4">
            <thead className="table-light">
              <tr>
                <th style={{ width: '30%' }}>Student</th>
                <th style={{ width: '5%' }}>Status</th>
                <th style={{ width: '5%' }}>Sent On</th>
                <th className="text-center" style={{ width: '1%' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {invitations.length > 0 ? (
                invitations.map((invite) => (
                  <tr key={invite.id}>
                    <td>
                      <div className="fw-semibold text-muted">{invite.student.username}</div>
                      <div className="small text-muted">{invite.student.email}</div>
                    </td>
                    <td style={{ verticalAlign: 'middle' }}>
                      <div 
                        className={`text-center text-uppercase fw-bold rounded-pill py-1 px-2`}
                        style={{ 
                          fontSize: '0.7rem',
                          backgroundColor: invite.status === 'pending' ? '#fff3cd' : '#f8d7da',
                          color: invite.status === 'pending' ? '#856404' : '#721c24',
                          border: `1px solid ${invite.status === 'pending' ? '#ffeeba' : '#f5c6cb'}`
                        }}
                      >
                        {invite.status}
                      </div>
                    </td>
                    <td className="small text-muted">
                      {new Date(invite.sent_at).toLocaleDateString()}
                    </td>
                    <td className="text-center">
                      <div className="d-flex justify-content-center gap-2">
                        {invite.status === 'rejected' && (
                          <OverlayTrigger overlay={<Tooltip style={{ position:"fixed" }}>Try sending this invitation again</Tooltip>}>
                            <Button 
                              variant="outline-primary" 
                              size="sm" 
                              onClick={() => handleAddStudent(null, invite.student.username)}
                            >
                              <i className="fa-solid fa-rotate-right me-1"></i> Resend
                            </Button>
                          </OverlayTrigger>
                        )}
                        
                        <OverlayTrigger overlay={<Tooltip style={{ position:"fixed" }}>Withdraw this invitation</Tooltip>}>
                          <Button 
                            variant="outline-danger" 
                            size="sm" 
                            onClick={() => handleCancelInvitation(invite.id)}
                          >
                            <i className="fa-solid fa-xmark me-1"></i> Cancel
                          </Button>
                        </OverlayTrigger>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="4" className="text-center py-4 text-muted">
                    No pending or rejected invitations.
                  </td>
                </tr>
              )}
            </tbody>
          </Table>
        </>
      )}
      <div className="mt-3 p-3 bg-light rounded border">
        <h6 className="mb-3">Add Student Manually</h6>
        {studentFeedback && (
            <Alert variant={studentFeedback.type} className="py-2 px-3 small mb-2">
                {studentFeedback.message}
            </Alert>
        )}
        <Form className="d-flex gap-2 mb-1" onSubmit={handleAddStudent}>
          <Form.Control 
            type="text" 
            placeholder="Student Email or Username" 
            value={newStudentEmail} 
            onChange={e => {
                setNewStudentEmail(e.target.value);
                setCandidateList([]); // Hide candidates if they start typing again
                setStudentFeedback(null);
            }} 
            style={{ maxWidth: '300px' }} 
            required
          />
          <Button variant="primary" type="submit" disabled={!newStudentEmail || isAddingStudent}>
            {isAddingStudent ? <Spinner size="sm" animation="border" /> : "Add Student"}
          </Button>
        </Form>

        {candidateList.length > 0 && (
            <div className="mt-3" style={{ maxWidth: '400px' }}>
                <span className="text-muted small fw-bold mb-2 d-block">Select the correct student:</span>
                <ListGroup>
                    {candidateList.map(candidate => (
                        <ListGroup.Item 
                            key={candidate.username} 
                            className="d-flex justify-content-between align-items-center"
                        >
                            <div>
                                <div className="fw-semibold">{candidate.name}</div>
                                <div className="text-muted small">@{candidate.username}</div>
                            </div>
                            <Button 
                                variant="outline-primary" 
                                size="sm" 
                                onClick={() => handleAddStudent(null, candidate.username)}
                            >
                                Select
                            </Button>
                        </ListGroup.Item>
                    ))}
                </ListGroup>
            </div>
        )}
      </div>

      <AddAssignmentModal 
        show={showAddAssignmentModal} 
        onHide={() => setShowAddAssignmentModal(false)}
        onExited={() => setEditAssignment(null)}        
        courseId={course.id} 
        onSaveAssignment={handleSaveAssignment}
        mode={addAssignmentMode}
        assignment={editAssignment}
      />

      <ViewAssignmentProgressModal
        show={showAssignmentProgressModal}
        onHide={() => setShowAssignmentProgressModal(false)}
        assignment={viewAssignment}
        students={course.students}
        instructor={course.instructor}
      />

    </div>
  );
}