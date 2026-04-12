import React, { useState } from 'react';
import { Modal, Button, Form, Alert, Spinner } from "react-bootstrap";

export default function JoinCourseModal({ show, onHide, onJoin }) {
  const [joinCode, setJoinCode] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    
    setIsLoading(true);
    setError(null);

    const result = await onJoin(joinCode);

    setIsLoading(false);

    if (result.success) {
        setJoinCode("");
        onHide();
    } else {
        setError(result.message);
    }
  };

return (
    <Modal show={show} onHide={() => { onHide(); setError(null); }} centered>
      <Modal.Header closeButton>
          <Modal.Title><i className="fa-solid fa-graduation-cap me-2 text-primary"></i>Join a Course</Modal.Title>
      </Modal.Header>
      <Modal.Body>
          {error && <Alert variant="danger" className="py-2 small">{error}</Alert>}
          <Form onSubmit={handleSubmit}>
              <Form.Group className="mb-3">
                  <Form.Label className="fw-semibold">Course Join Code</Form.Label>
                  <Form.Control 
                    type="text" 
                    placeholder="e.g., MATHROCKS" 
                    autoFocus 
                    value={joinCode} 
                    onChange={(e) => {
                        setJoinCode(e.target.value);
                        setError(null); // Clear error when they start typing again
                    }} 
                  />
                  <Form.Text className="text-muted">Enter the unique code provided by your instructor to enroll.</Form.Text>
              </Form.Group>
          </Form>
      </Modal.Body>
      <Modal.Footer className="bg-light border-top-0">
          <Button variant="outline-secondary" onClick={onHide} disabled={isLoading}>Cancel</Button>
          <Button variant="primary" onClick={handleSubmit} disabled={!joinCode.trim() || isLoading}>
            {isLoading ? <Spinner size="sm" animation="border" /> : <><i className="fa-solid fa-check me-2"></i>Join</>}
          </Button>
      </Modal.Footer>
    </Modal>
  );
}