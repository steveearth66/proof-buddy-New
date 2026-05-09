import React, { useEffect, useState } from 'react';
import { Modal, Button, Form, Table, OverlayTrigger, Tooltip, Spinner } from "react-bootstrap";
import NumberedPagination from '../../Pagination';
import courseService from '../../../services/courseServices';

export default function AddAssignmentModal({ show, onHide, onExited, courseId, onSaveAssignment, assignment = null }) {  
  const isEditMode = !!assignment;

  // --- View State ---
  const [currentView, setCurrentView] = useState('form'); 
  
  const [libraryProofs, setLibraryProofs] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (show) {
      const loadLibrary = async () => {
        setIsLoading(true);
        const data = await courseService.getInstructorLibrary();
        setLibraryProofs(data);
        setIsLoading(false);
      };
      loadLibrary();
    }
  }, [show]);

  useEffect(() => {
    if (show) {
      if (assignment) {
        setTitle(assignment.title || '');
        setDueDate(assignment.due_date ? assignment.due_date.substring(0, 16) : '');
        setSelectedProofs((assignment.proofs || []).map(p => ({ ...p, isOriginal: true })));
      } else {
        setTitle('');
        setDueDate('');
        setSelectedProofs([]);
      }
    }
  }, [show, assignment]);

  // --- Pagination State ---
  const [proofPage, setProofPage] = useState(1);
  const proofsPerPage = 5;
  const totalProofPages = Math.ceil(libraryProofs.length / proofsPerPage) || 1;
  const paginatedInstructorProofs = libraryProofs.slice((proofPage - 1) * proofsPerPage, proofPage * proofsPerPage);

  // --- Form State ---
  const [title, setTitle] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title || !dueDate || selectedProofs.length === 0) return;

    setIsSubmitting(true);

    const payload = {
        id: assignment?.id,
        title: title,
        description: assignment?.description || "No Description Provided",
        due_date: dueDate,
        course: courseId,
        proofs: selectedProofs.map(p => ({
            id: p.id,
            type: p.type
        }))
    };

    try {
      let success = false;
        success = await onSaveAssignment(payload);

      if (success) {
        onHide();
        setCurrentView('form');
      }
    } catch (error) {
      console.error("Submission error:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  // --- Selection & Drag State ---
  const [selectedProofs, setSelectedProofs] = useState([]);
  const [draggedIndex, setDraggedIndex] = useState(null);

  // --- Handlers ---
  const handleToggleProof = (proof) => {
    setSelectedProofs(prev => {
      const isSelected = prev.some(p => p.id === proof.id);
      if (isSelected) return prev.filter(p => p.id !== proof.id);
      return [...prev, proof];
    });
  };

  const handleRemoveProof = (id) => {
    const proofToRemove = selectedProofs.find(p => p.id === id);
    if (!proofToRemove) return;
    const confirmed = window.confirm(
        `Are you sure you want to remove "${proofToRemove.title}" from this assignment?\nIf you add the proof back, it will use the current version of the selected proof, not the version that was originally used.`
    );

    if (confirmed) {
        setSelectedProofs(prev => prev.filter(p => p.id !== id));
    }
  };

  // --- Drag and Drop Logic ---
  const handleDragStart = (e, index) => {
    setDraggedIndex(index);
    setTimeout(() => { e.target.style.opacity = '0.5'; }, 0);
  };

  const handleDragEnter = (e, targetIndex) => {
    e.preventDefault();
    if (draggedIndex === null || draggedIndex === targetIndex) return;

    setSelectedProofs(prev => {
      const newProofs = [...prev];
      const draggedItem = newProofs[draggedIndex];
      newProofs.splice(draggedIndex, 1);
      newProofs.splice(targetIndex, 0, draggedItem);
      return newProofs;
    });
    setDraggedIndex(targetIndex); 
  };

  const handleDragEnd = (e) => {
    setDraggedIndex(null);
    e.target.style.opacity = '1'; 
  };

  // --- Render Helpers ---
  
  // View 1: The Library (Selecting Proofs)
  const renderLibraryView = () => (
    <>
      <Modal.Header>
        <Modal.Title>
          <Button variant="link" className="text-decoration-none p-0 me-3 text-dark" onClick={() => setCurrentView('form')}>
            <i className="fa-solid fa-arrow-left"></i>
          </Button>
          Select Proofs
        </Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <Table size="sm" bordered hover className="align-middle mb-2">
          <thead className="table-light">
            <tr>
              <th style={{ width: '0%' }} className="text-center">Select</th>
              <th>Proof Name</th>
              <th>Category</th>
              <th>Type</th>
            </tr>
          </thead>
          <tbody>
            {paginatedInstructorProofs.map(proof => {
              const selectionRecord = selectedProofs.find(p => p.title === proof.title && p.type === proof.type);
              return (
                <tr key={proof.id} onClick={() => handleToggleProof(proof)} style={{ cursor: selectionRecord?.isOriginal ? 'not-allowed' : 'pointer' }}>                
                  <td className="text-center">
                    <Form.Check 
                      type="checkbox"
                      checked={!!selectionRecord}
                      disabled={selectionRecord?.isOriginal}
                      onChange={() => handleToggleProof(proof)}
                      onClick={(e) => e.stopPropagation()} 
                    />
                  </td>
                  <td className="fw-semibold">{proof.title}</td>
                  <td>{proof.category}</td>
                  <td>{proof.displayType}</td>
                </tr>
              )
            })}
          </tbody>
        </Table>

        <div className="d-flex justify-content-end mb-4">
          <NumberedPagination currentPage={proofPage} totalPages={totalProofPages} onPageChange={({ page }) => setProofPage(page)} />
        </div>
      </Modal.Body>
      <Modal.Footer className="bg-light border-top-0">
        <Button variant="primary" onClick={() => setCurrentView('form')}>
          Done Selecting ({selectedProofs.length})
        </Button>
      </Modal.Footer>
    </>
  );

  // View 2: The Main Form (Reordering & Naming)
  const renderFormView = () => (
    <>
      <Modal.Header closeButton>
        <Modal.Title>{(isEditMode) ? "Edit" : "Create"} Assignment</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <div className="d-flex justify-content-between align-items-center mb-3">
          <h6 className="mb-0">Selected Proofs</h6>
          <Button variant="outline-primary" size="sm" onClick={() => setCurrentView('library')}>
            <i className="fa-solid fa-plus me-2"></i>Add Proofs
          </Button>
        </div>

        <Table size="sm" bordered hover className="align-middle mb-4">
          <thead className="table-light">
            <tr>
              <th style={{ width: '0%' }}></th> 
              <th>Proof Name</th>
              <th>Category</th>
              <th>Type</th>
              <th style={{ width: '0%' }} className="text-center">Action</th>
            </tr>
          </thead>
          <tbody>
            {selectedProofs.length > 0 ? (
              selectedProofs.map((proof, index) => {
                console.log(proof);
                const selectionRecord = selectedProofs.find(p => p.title === proof.title && p.type === proof.type);
                return (
                  <tr 
                    key={proof.id}
                    draggable
                    onDragStart={(e) => handleDragStart(e, index)}
                    onDragEnter={(e) => handleDragEnter(e, index)}
                    onDragEnd={handleDragEnd}
                    onDragOver={(e) => e.preventDefault()}
                    style={{ cursor: draggedIndex === index ? 'grabbing' : 'grab' }}
                  >
                    <td className="text-center text-muted"><i className="fa-solid fa-grip-vertical"></i></td>
                    <td className="fw-semibold">{proof.title}</td>
                    <td>{proof.category}</td>
                    <td>{proof.displayType}</td>
                    <td className="text-center">
                      {proof.is_locked ? (
                        <OverlayTrigger overlay={<Tooltip>Cannot remove: Students have already started this proof.</Tooltip>}>
                          <span className="d-inline-block">
                            <Button variant="outline-secondary" size="sm" disabled style={{ pointerEvents: 'none' }}>
                              <i className="fa-solid fa-lock"></i>
                            </Button>
                          </span>
                        </OverlayTrigger>
                      ) : (
                        <Button 
                          variant="outline-danger" 
                          size="sm" 
                          onClick={() => handleRemoveProof(proof.id)}
                        >
                          <i className="fa-solid fa-trash-can"></i>
                        </Button>
                      )}
                    </td>
                  </tr>
                )
              })
            ) : (
              <tr>
                <td colSpan="5" className="text-center py-4 text-muted">
                  No proofs added yet. Click "Add Proofs" to select from the library.
                </td>
              </tr>
            )}
          </tbody>
        </Table>

        <Form id="create-assignment-form" onSubmit={handleSubmit}>
          <Form.Group className="mb-3">
            <Form.Label className="fw-semibold">Assignment Name</Form.Label>
            <Form.Control 
              type="text" 
              placeholder="Enter Assignment Name" 
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label className="fw-semibold">Set Due Date</Form.Label>
            <Form.Control 
              type="datetime-local" 
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
              required
            />
          </Form.Group>
        </Form>
      </Modal.Body>
      <Modal.Footer className="bg-light border-top-0">
        <Button variant="outline-secondary" onClick={onHide} disabled={isSubmitting}>Cancel</Button>
        <Button 
          variant="primary" 
          type="submit" 
          form="create-assignment-form"
          disabled={selectedProofs.length === 0 || isSubmitting || !title || !dueDate}
        >
          {isSubmitting ? <Spinner size="sm" animation="border" /> : (isEditMode ? "Save Changes" : "Publish Assignment")}
        </Button>
      </Modal.Footer>
    </>
  );

  return (
    <Modal 
      show={show} 
      onHide={() => {
        onHide();
        setTimeout(() => setCurrentView('form'), 300); // Reset view smoothly after closing
      }} 
      onExited={onExited}
      size="lg" 
      centered
    >
      {currentView === 'library' ? renderLibraryView() : renderFormView()}
    </Modal>
  );
}