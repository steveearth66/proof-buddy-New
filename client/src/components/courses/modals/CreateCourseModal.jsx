import React from 'react';
import { Modal, Button, Form } from "react-bootstrap";

export default function CreateCourseModal({ show, onHide }) {
  return (
    <Modal show={show} onHide={onHide} centered>
      <Modal.Header closeButton>
          <Modal.Title>Create New Course</Modal.Title>
      </Modal.Header>
      <Modal.Body>
          <Form>
              <Form.Group className="mb-3">
                  <Form.Label className="fw-semibold">Course Name</Form.Label>
                  <Form.Control type="text" placeholder="e.g., CS 101: Discrete Math" autoFocus />
              </Form.Group>
              <Form.Group className="mb-3">
                  <Form.Label className="fw-semibold">Term</Form.Label>
                  <Form.Control type="text" placeholder="e.g., Fall 2024" />
              </Form.Group>
          </Form>
      </Modal.Body>
      <Modal.Footer className="bg-light border-top-0">
          <Button variant="outline-secondary" onClick={onHide}>Cancel</Button>
          <Button variant="primary" onClick={onHide}>Create Course</Button>
      </Modal.Footer>
    </Modal>
  );
}