import { useEffect, useState, useCallback, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
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
import inductionService from '../services/inductionService';

const PROOF_TYPES = {
  EQUATIONAL: 'EQUATIONAL',
  INDUCTION: 'INDUCTION'
};

const PROOF_CONFIG = {
  EQUATIONAL: {
    service: equationalService,
    fetchMethod: 'getRacketProofs',
    deleteMethod: 'deleteRacketProof',
    viewRoute: '/equational-reasoning-new',
    label: 'Equational'
  },
  INDUCTION: {
    service: inductionService,
    fetchMethod: 'getInductionProofs',
    deleteMethod: 'deleteInductionProof',
    viewRoute: '/induction-racket',
    label: 'Induction'
  }
};

export default function Proofs() {
  const [searchParams] = useSearchParams();
  const initialType = searchParams.get('type') === 'induction'
    ? PROOF_TYPES.INDUCTION
    : PROOF_TYPES.EQUATIONAL;
  const [proofType, setProofType] = useState(initialType);
  const [proofObject, setProofObject] = useState({});
  const [query, setQuery] = useState('');
  const [deleteTargetId, setDeleteTargetId] = useState(null);
  const uploadFileRef = useRef(null);
  const currentStrategy = PROOF_CONFIG[proofType];
  
  const queryProofs = useCallback(async ({ page = 1 } = {}) => {
    try {
      // Dynamic call based on the selected proof type
      const proofsData = await currentStrategy.service[currentStrategy.fetchMethod]({ query, page });
      setProofObject(proofsData);
    } catch (error) {
      console.error(`Error fetching ${proofType} proofs:`, error);
      setProofObject({ proofs: [] });
    }
  }, [proofType, query, currentStrategy]);

  useEffect(() => {
    queryProofs();
  }, [queryProofs]);

  const handleUploadFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const text = await file.text();
      const proofData = JSON.parse(text);
      const expectedType = proofType === PROOF_TYPES.INDUCTION ? 'induction' : 'equational';
      if (proofData.proofType !== expectedType) {
        toast.error(`This file is not an ${expectedType} proof.`);
        return;
      }
      const result = await currentStrategy.service.uploadProof(proofData);
      toast.success(`Proof "${result.proofName}" uploaded successfully.`);
      await queryProofs();
    } catch (error) {
      console.error('Error uploading proof:', error);
      toast.error('Failed to upload proof. The file may be invalid or corrupted.');
    }
  };

  const handleDelete = async () => {
    if (!deleteTargetId) return;

    try {
      await currentStrategy.service[currentStrategy.deleteMethod](deleteTargetId);
      
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
        <Row className="align-items-center">
          <Col><h1>All {currentStrategy.label} Proofs</h1></Col>
          <Col xs="auto">
            <Button
              variant="outline-primary"
              onClick={() => { uploadFileRef.current.value = ''; uploadFileRef.current.click(); }}
            >
              upload proof from a saved file
            </Button>
            <input
              type="file"
              accept=".json"
              ref={uploadFileRef}
              onChange={handleUploadFileChange}
              style={{ display: 'none' }}
            />
          </Col>
          <Col xs="auto">
            {/* Toggle between types */}
            <Form.Select 
              value={proofType} 
              onChange={(e) => {
                setProofType(e.target.value);
                setQuery(''); // Clear search when switching types
              }}
            >
              <option value={PROOF_TYPES.EQUATIONAL}>Equational Proofs</option>
              <option value={PROOF_TYPES.INDUCTION}>Induction Proofs</option>
            </Form.Select>
          </Col>
        </Row>

        <div className="proof-layout">
          <div className="search">
            <InputGroup>
              <Form.Control
                placeholder={`Search ${currentStrategy.label} proofs...`}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              <Button variant="outline-secondary" onClick={() => queryProofs()}>
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
                <ProofCard 
                  key={`${proof.id}`} 
                  proof={proof} 
                  config={currentStrategy}
                  onDelete={(id) => setDeleteTargetId(id)}
                />
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

          <NumberedPagination {...proofObject} onPageChange={(page) => queryProofs(page)} />
        </div>
      </Container>
    </MainLayout>
  );
}

function ProofCard({ proof, onDelete, config }) {
  const lhs = proof.lhs || proof.lhs_leap_goal || '';
  const rhs = proof.rhs || proof.rhs_leap_goal || '';
  const complete = proof.isComplete || proof.is_complete;
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
      {(lhs || rhs) && (
        <p className={`proof-goal proof-goal--${complete ? 'complete' : 'incomplete'}`}>
          <b>Goal:</b> {lhs} = {rhs}
        </p>
      )}
      <p>
        <b>Completed:</b> {complete ? 'True' : 'False'}
      </p>
      {/* Route is now dynamic based on config */}
      <Link to={config.viewRoute} state={{ id: proof.id }}>
        <Button variant="outline-secondary" style={{ width: '100%' }}>
          Open Proof
        </Button>
      </Link>
      <Link to={config.viewRoute} state={{ id: proof.id, playMode: true }}>
        <Button variant="outline-primary" style={{ width: '100%', marginTop: '0.5rem' }}>
          <i className="fa-solid fa-play" style={{ marginRight: '0.4rem' }}></i>
          Run Proof
        </Button>
      </Link>
    </div>
  );
}
