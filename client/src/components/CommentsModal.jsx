import React, { useState, useEffect } from "react";
import Modal from "react-bootstrap/Modal";
import Button from "react-bootstrap/Button";
import Form from 'react-bootstrap/Form';

export default function CommentsModal({
    show,
    onHide,
    onSave,
    studentComment,
    instructorComment,
    onStudentCommentChange,
    OnInstructorCommentChange,
    isStudent
}) {
    return (
        <Modal show={show} onHide={onHide} centered>
            <Modal.Header closeButton>
                <Modal.Title>Comments</Modal.Title>
            </Modal.Header>
            <Modal.Body>
                <Form.Group>
                    <Form.Label>Instructor Comment</Form.Label>
                    <Form.Control
                        as="textarea"
                        rows={4}
                        value={instructorComment}
                        onChange={(e) => OnInstructorCommentChange(e.target.value)}
                        readOnly={isStudent}
                    />
                </Form.Group>
                <Form.Group>
                    <Form.Label>Student Comment</Form.Label>
                    <Form.Control
                        as="textarea"
                        rows={4}
                        value={studentComment}
                        onChange={(e) => onStudentCommentChange(e.target.value)}
                        readOnly={!isStudent}
                    />
                </Form.Group>
            </Modal.Body>
            <Modal.Footer>
                <Button variant="secondary" onClick={onHide}>
                    Cancel
                </Button>
                <Button variant="primary" onClick={onSave}>
                    Save
                </Button>
            </Modal.Footer>
        </Modal>
    )
}