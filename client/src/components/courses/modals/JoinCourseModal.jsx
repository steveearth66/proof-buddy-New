import React, { useState } from 'react';
import { Modal, Button, Form } from "react-bootstrap";

export default function JoinCourseModal({ show, onHide, onJoin }) {
  const [joinCode, setJoinCode] = useState("");

  const handleSubmit = () => {
    onJoin(joinCode);
    setJoinCode("");
    onHide();
  };

  return (
    <Modal show={show} onHide={onHide} centered>
      <Modal.Header closeButton>
          <Modal.Title><i className="fa-solid fa-graduation-cap me-2 text-primary"></i>Join a Course</Modal.Title>
      </Modal.Header>
      <Modal.Body>
          <Form>
              <Form.Group className="mb-3">
                  <Form.Label className="fw-semibold">Course Join Code</Form.Label>
                  <Form.Control 
                    type="text" 
                    placeholder="e.g., MATHROCKS" 
                    autoFocus 
                    value={joinCode} 
                    onChange={(e) => setJoinCode(e.target.value)} 
                  />
                  <Form.Text className="text-muted">Enter the unique code provided by your instructor to enroll.</Form.Text>
              </Form.Group>
          </Form>
      </Modal.Body>
      <Modal.Footer className="bg-light border-top-0">
          <Button variant="outline-secondary" onClick={onHide}>Cancel</Button>
          <Button variant="primary" onClick={handleSubmit} disabled={!joinCode.trim()}>
            <i className="fa-solid fa-check me-2"></i>Join
          </Button>
      </Modal.Footer>
    </Modal>
  );
}