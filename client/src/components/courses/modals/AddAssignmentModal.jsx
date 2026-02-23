import React, { useState } from 'react';
import { Modal, Button, Form, Table, OverlayTrigger, Tooltip } from "react-bootstrap";
import NumberedPagination from '../../Pagination';

const MOCK_INSTRUCTOR_PROOFS = [
  { id: 1, title: 'Modus Ponens - Intro', category: 'Logic', difficulty: 'Easy' },
  { id: 2, title: 'De Morgan\'s Laws', category: 'Set Theory', difficulty: 'Medium' },
  { id: 3, title: 'Predicate Logic Basics', category: 'Logic', difficulty: 'Medium' },
  { id: 4, title: 'Induction Example 1', category: 'Number Theory', difficulty: 'Hard' },
  { id: 5, title: 'Induction Example 2', category: 'Number Theory', difficulty: 'Hard' }
];

export default function AddAssignmentModal({ show, onHide }) {
  // --- View State (The Magic Fix) ---
  // 'form' = the main assignment screen | 'library' = the proof selection screen
  const [currentView, setCurrentView] = useState('form'); 

  // --- Pagination State ---
  const [proofPage, setProofPage] = useState(1);
  const proofsPerPage = 5;
  const totalProofPages = Math.ceil(MOCK_INSTRUCTOR_PROOFS.length / proofsPerPage) || 1;
  const paginatedInstructorProofs = MOCK_INSTRUCTOR_PROOFS.slice((proofPage - 1) * proofsPerPage, proofPage * proofsPerPage);

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

  const handleRemoveProof = (id) => setSelectedProofs(prev => prev.filter(p => p.id !== id));

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
              <th>Difficulty</th>
            </tr>
          </thead>
          <tbody>
            {paginatedInstructorProofs.map(proof => (
              <tr key={proof.id} onClick={() => handleToggleProof(proof)} style={{ cursor: 'pointer' }}>
                <td className="text-center">
                  <Form.Check 
                    type="checkbox"
                    checked={selectedProofs.some(p => p.id === proof.id)}
                    onChange={() => handleToggleProof(proof)}
                    onClick={(e) => e.stopPropagation()} 
                  />
                </td>
                <td className="fw-semibold">{proof.title}</td>
                <td>{proof.category}</td>
                <td>{proof.difficulty}</td>
              </tr>
            ))}
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
        <Modal.Title>Create Assignment</Modal.Title>
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
              <th>Difficulty</th>
              <th style={{ width: '0%' }} className="text-center">Action</th>
            </tr>
          </thead>
          <tbody>
            {selectedProofs.length > 0 ? (
              selectedProofs.map((proof, index) => (
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
                  <td>{proof.difficulty}</td>
                  <td className="text-center">
                    <OverlayTrigger placement="left" overlay={<Tooltip id={`tooltip-remove-${proof.id}`}>Remove From Assignment</Tooltip>}>
                      <Button variant="outline-danger" size="sm" onClick={() => handleRemoveProof(proof.id)}>
                        <i className="fa-solid fa-trash-can"></i>
                      </Button>
                    </OverlayTrigger>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="5" className="text-center py-4 text-muted">
                  No proofs added yet. Click "Add Proofs" to select from the library.
                </td>
              </tr>
            )}
          </tbody>
        </Table>

        <Form>
          <Form.Group className="mb-3">
            <Form.Label className="fw-semibold">Assignment Name</Form.Label>
            <Form.Control type="text" placeholder="Enter Assignment Name" />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label className="fw-semibold">Set Due Date</Form.Label>
            <Form.Control type="date" />
          </Form.Group>
        </Form>
      </Modal.Body>
      <Modal.Footer className="bg-light border-top-0">
        <Button variant="outline-secondary" onClick={onHide}>Cancel</Button>
        <Button variant="primary" onClick={onHide} disabled={selectedProofs.length === 0}>
          Publish Assignment
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
      size="lg" 
      centered
    >
      {currentView === 'library' ? renderLibraryView() : renderFormView()}
    </Modal>
  );
}