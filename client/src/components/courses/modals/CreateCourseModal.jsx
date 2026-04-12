import React, { useState } from 'react';
import { Modal, Button, Form, Spinner, Alert } from "react-bootstrap";

export default function CreateCourseModal({ show, onHide, onCreateCourse }) {
  const [name, setName] = useState('');
  const [generateJoinCode, setGenerateJoinCode] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [status, setStatus] = useState(null); 
  const [isJoinCodeCopied, setIsJoinCodeCopied] = useState(false);

  const handleClose = () => {
    setName('');
    setGenerateJoinCode(false);
    setStatus(null);
    setIsJoinCodeCopied(false); // Reset copy state
    onHide();
  };

  const handleCopy = () => {
    if (status?.joinCode) {
      navigator.clipboard.writeText(status.joinCode);
      setIsJoinCodeCopied(true);
      
      // Reset the icon back to 'copy' after 2 seconds
      setTimeout(() => setIsJoinCodeCopied(false), 2000);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;

    setIsSubmitting(true);
    setStatus(null);
    
    const payload = {
        name: name,
        generate_join_code: generateJoinCode
    };

    const result = await onCreateCourse(payload);
    
    setIsSubmitting(false);
    
    if (result.success) {
        setName('');
        setGenerateJoinCode(false);
        
        if (result.data.join_code) {
            setStatus({ 
                type: 'success', 
                message: 'Course created successfully!', 
                joinCode: result.data.join_code 
            });
        } else {
            handleClose();
        }
    } else {
        setStatus({ type: 'danger', message: result.message });
    }
  };

  return (
    <Modal show={show} onHide={handleClose} centered>
      <Modal.Header closeButton>
          <Modal.Title>Create New Course</Modal.Title>
      </Modal.Header>
      <Modal.Body>
          {status && (
              <Alert variant={status.type} className="mb-4">
                  <div className="fw-semibold">{status.message}</div>
                  {status.joinCode && (
                      <div className="mt-3 p-3 bg-white text-dark rounded text-center border">
                          <div className="text-muted small fw-bold text-uppercase mb-2">Temporary Join Code</div>
                          
                          <div className="d-flex justify-content-center align-items-center gap-2 mb-2">
                              <code className="fs-3 text-primary mb-0">{status.joinCode}</code>
                              <Button 
                                variant={isJoinCodeCopied ? "success" : "outline-secondary"} 
                                size="sm" 
                                onClick={handleCopy}
                                title="Copy to clipboard"
                              >
                                {isJoinCodeCopied ? <i className="fa-solid fa-check"></i> : <i className="fa-regular fa-copy"></i>}
                              </Button>
                          </div>

                          <div className="text-danger small mt-2 fw-semibold">
                              <i className="fa-solid fa-triangle-exclamation me-1"></i>
                              Save this now. It will not be shown again.
                          </div>
                      </div>
                  )}
              </Alert>
          )}

          {!(status && status.type === 'success') && (
              <Form id="create-course-form" onSubmit={handleSubmit}>
                  <Form.Group className="mb-3">
                      <Form.Label className="fw-semibold">Course Name</Form.Label>
                      <Form.Control 
                        type="text" 
                        placeholder="e.g., CS 101: Discrete Math" 
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        required
                        autoFocus 
                      />
                  </Form.Group>
                  
                  <Form.Group className="mb-3" controlId="formBasicCheckbox">
                    <Form.Check 
                      type="checkbox" 
                      label="Generate an enrollment join code (Valid for 7 days)" 
                      checked={generateJoinCode}
                      onChange={(e) => setGenerateJoinCode(e.target.checked)}
                    />
                    <Form.Text className="text-muted">
                      You can always generate or disable join codes later from the course settings.
                    </Form.Text>
                  </Form.Group>
              </Form>
          )}
      </Modal.Body>
      <Modal.Footer className="bg-light border-top-0">
          {status && status.type === 'success' ? (
              <Button variant="primary" onClick={handleClose} className="w-100">
                  Done
              </Button>
          ) : (
              <>
                  <Button variant="outline-secondary" onClick={handleClose} disabled={isSubmitting}>Cancel</Button>
                  <Button variant="primary" type="submit" form="create-course-form" disabled={isSubmitting || !name.trim()}>
                      {isSubmitting ? <Spinner size="sm" animation="border" /> : "Create Course"}
                  </Button>
              </>
          )}
      </Modal.Footer>
    </Modal>
  );
}