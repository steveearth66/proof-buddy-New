import { useEffect, useState } from 'react';
import MainLayout from '../layouts/MainLayout';
import erService from '../services/erService';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Container from 'react-bootstrap/Container';
import Button from 'react-bootstrap/esm/Button';
import InputGroup from 'react-bootstrap/InputGroup';
import Spinner from 'react-bootstrap/Spinner';
import Form from 'react-bootstrap/Form';
import Modal from 'react-bootstrap/Modal';
import { toast } from "react-toastify";
import { Link } from 'react-router-dom';
import '../scss/_proof-card.scss';
import NumberedPagination from '../components/Pagination';
import equationalService from '../services/equationalService';

export default function Proofs() {
  const [proofObject, setProofObject] = useState({});
  const [query, setQuery] = useState('');
  const [deleteTargetId, setDeleteTargetId] = useState(null);

  const queryProofs = async ({ page = 1 }) => {
    try {
      const proofsData = await equationalService.getRacketProofs({ query, page });
      setProofObject(proofsData);
    } catch (error) {
      console.error('Error fetching proofs:', error);
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        const proofsData = await equationalService.getRacketProofs({});
        setProofObject(proofsData);
      } catch (error) {
        console.error('Error fetching proofs:', error);
      }
    };
    fetchData();
  }, []);

  const handleDelete = async () => {
    if (!deleteTargetId) return;

    try {
      await equationalService.deleteRacketProof(deleteTargetId);
      
      // Get Page Number to load after deletion
      const isLastItemOnPage = proofObject.proofs.length === 1;
      const isNotFirstPage = proofObject.currentPage > 1;
      const pageToLoad = (isLastItemOnPage && isNotFirstPage) ? proofObject.currentPage - 1 : proofObject.currentPage;
      
      // Close Modal
      setDeleteTargetId(null);
      toast.success("Proof deleted.");

      await queryProofs({ page: pageToLoad });
    } catch (error) {
      console.error('Error deleting proof:', error);
      toast.error("Failed to delete proof.");
    }
  };

  return (
    <MainLayout>
      <Container>
        <Row>
          <Col>
            <h1>All Proofs</h1>
          </Col>
        </Row>
        <div className="proof-layout">
          <div className="search">
            <InputGroup>
              <Form.Control
                placeholder="Search for a proof"
                aria-label="Search for a proof"
                aria-describedby="basic-addon2"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              <Button
                variant="outline-secondary"
                id="button-addon2"
                onClick={queryProofs}
              >
                Search
              </Button>
            </InputGroup>
          </div>
          <div className="proofs">
            {Object.keys(proofObject).length === 0 ? (
              <Spinner animation="border" role="status">
                <span className="visually-hidden">Loading...</span>
              </Spinner>
            ) : (
              proofObject.proofs?.map((proof) => (
                <ProofCard key={`${proof.tag}-${proof.name}`} 
                            proof={proof} 
                            onDelete={(id) => setDeleteTargetId(id)}/>
              ))
            )}
            {proofObject.proofs?.length === 0 && <p className='not-found'>No proofs found</p>}
          </div>

          {/* Confirmation Modal */}
          <Modal show={!!deleteTargetId} onHide={() => setDeleteTargetId(null)} centered>
            <Modal.Header closeButton>
              <Modal.Title>Confirm Deletion</Modal.Title>
            </Modal.Header>
            <Modal.Body>
              Are you sure you want to delete this proof? This action cannot be undone.
            </Modal.Body>
            <Modal.Footer>
              <Button variant="secondary" onClick={() => setDeleteTargetId(null)}>
                Cancel
              </Button>
              <Button variant="danger" onClick={handleDelete}>
                Delete Proof
              </Button>
            </Modal.Footer>
          </Modal>

          <NumberedPagination {...proofObject} onPageChange={queryProofs} />
        </div>
      </Container>
    </MainLayout>
  );
}

function ProofCard({ proof, onDelete }) {
  return (
    <div className="proof-card">
      <Button
        className="btn btn-sm"
        onClick={() => onDelete(proof.id)}
        style={{ 
          position: 'absolute', 
          top: '8px', 
          right: '8px'
        }}
        variant="outline-danger"
        aria-label="Delete"
      >
        <i className="fa-solid fa-trash-can"></i>
      </Button>
      <p style={{ marginRight: "1.5em" }}>
        <b>Proof:</b> {proof.name} - {proof.tag}
      </p>
      <p>
        <b>Completed:</b> {proof.isComplete ? 'True' : 'False'}
      </p>
      <Link to={`/equational-reasoning-new`} state={{ id: proof.id }}>
        <Button variant="outline-secondary" style={{ width: '100%' }}>
          View Proof
        </Button>
      </Link>
    </div>
  );
}
