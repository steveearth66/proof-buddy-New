import React, { useState } from 'react';
import { Modal, Button, Form, Table } from "react-bootstrap";
import NumberedPagination from '../../Pagination'; 

const MOCK_INSTRUCTOR_PROOFS = [
  { id: 1, title: 'Modus Ponens - Intro', category: 'Logic', difficulty: 'Easy' },
  { id: 2, title: 'De Morgan\'s Laws', category: 'Set Theory', difficulty: 'Medium' },
  { id: 3, title: 'Predicate Logic Basics', category: 'Logic', difficulty: 'Medium' },
  { id: 4, title: 'Induction Example 1', category: 'Number Theory', difficulty: 'Hard' },
  { id: 5, title: 'Induction Example 2', category: 'Number Theory', difficulty: 'Hard' }
];

export default function AddAssignmentModal({ show, onHide }) {
  const [proofPage, setProofPage] = useState(1);
  const proofsPerPage = 5;

  const totalProofPages = Math.ceil(MOCK_INSTRUCTOR_PROOFS.length / proofsPerPage) || 1;
  const paginatedInstructorProofs = MOCK_INSTRUCTOR_PROOFS.slice((proofPage - 1) * proofsPerPage, proofPage * proofsPerPage);

  return (
    <Modal show={show} onHide={onHide} size="lg" centered>
      <Modal.Header closeButton>
          <Modal.Title>Create Assignment</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <h6 className="mb-3">Select a Proof to Assign</h6>
        <Table size="sm" bordered hover className="align-middle mb-2">
          <thead className="table-light">
            <tr>
              <th>Proof Name</th>
              <th>Category</th>
              <th>Difficulty</th>
              <th className="text-center">Action</th>
            </tr>
          </thead>
          <tbody>
            {paginatedInstructorProofs.map(proof => (
              <tr key={proof.id}>
                <td className="fw-semibold">{proof.title}</td>
                <td>{proof.category}</td>
                <td>{proof.difficulty}</td>
                <td className="text-center">
                  <Button variant="outline-primary" size="sm">Select</Button>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
        
        <div className="d-flex justify-content-end mb-4">
           <NumberedPagination currentPage={proofPage} totalPages={totalProofPages} onPageChange={({ page }) => setProofPage(page)} />
        </div>

        <Form>
          <Form.Group className="mb-3">
              <Form.Label className="fw-semibold">Set Due Date</Form.Label>
              <Form.Control type="date" />
          </Form.Group>
        </Form>
      </Modal.Body>
      <Modal.Footer className="bg-light border-top-0">
          <Button variant="outline-secondary" onClick={onHide}>Cancel</Button>
          <Button variant="primary" onClick={onHide}>Publish Assignment</Button>
      </Modal.Footer>
    </Modal>
  );
}