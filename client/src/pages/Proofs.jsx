import { useEffect, useState, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import MainLayout from '../layouts/MainLayout';
// erService removed: replaced by equationalService and inductionService
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
    const currentStrategy = PROOF_CONFIG[proofType];

  const queryProofs = useCallback(async ({ page = 1 } = {}) => {
        try {
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

  const handleDelete = async () => {
        if (!deleteTargetId) return;
        try {
                await currentStrategy.service[currentStrategy.deleteMethod](deleteTargetId);
                const isLastItemOnPage = proofObject.proofs.length === 1;
                const isNotFirstPage = proofObject.currentPage > 1;
                const pageToLoad = (isLastItemOnPage && isNotFirstPage) ? proofObject.currentPage - 1 : proofObject.currentPage;
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
                                <Col><h1>All {currentStrategy.label} Proofs</h1>h1></Col>Col>
                                <Col xs="auto">
                                            <Form.Select
                                                            value={proofType}
                                                            onChange={(e) => {
                                                                              setProofType(e.target.value);
                                                                              setQuery('');
                                                            }}
                                                          >
                                                          <option value={PROOF_TYPES.EQUATIONAL}>Equational Proofs</option>option>
                                                          <option value={PROOF_TYPES.INDUCTION}>Induction Proofs</option>option>
                                            </Form.Select>Form.Select>
                                </Col>Col>
                      </Row>Row>
              
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
                                                          </Button>Button>
                                            </InputGroup>InputGroup>
                                </div>div>
                      
                                <div className="proofs">
                                  {Object.keys(proofObject).length === 0 ? (
                        <Spinner animation="border" role="status">
                                        <span className="visually-hidden">Loading...</span>span>
                        </Spinner>Spinner>
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
                                  {proofObject.proofs?.length === 0 && <p className='not-found'>No proofs found</p>p>}
                                </div>div>
                      
                                <Modal show={!!deleteTargetId} onHide={() => setDeleteTargetId(null)} centered>
                                            <Modal.Header closeButton>
                                                          <Modal.Title>Confirm Deletion</Modal.Title>Modal.Title>
                                            </Modal.Header>Modal.Header>
                                            <Modal.Body>
                                                          Are you sure you want to delete this proof? This action cannot be undone.
                                            </Modal.Body>Modal.Body>
                                            <Modal.Footer>
                                                          <Button variant="secondary" onClick={() => setDeleteTargetId(null)}>
                                                                          Cancel
                                                          </Button>Button>
                                                          <Button variant="danger" onClick={handleDelete}>
                                                                          Delete Proof
                                                          </Button>Button>
                                            </Modal.Footer>Modal.Footer>
                                </Modal>Modal>
                      
                                <NumberedPagination {...proofObject} onPageChange={(page) => queryProofs({ page })} />
                      </div>div>
              </Container>Container>
        </MainLayout>MainLayout>
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
                        <i className="fa-solid fa-trash-can"></i>i>
                </Button>Button>
                <p style={{ marginRight: "1.5em" }}>
                        <b>Proof:</b>b> {proof.name} - {proof.tag}
                </p>p>
            {(lhs || rhs) && (
                    <p className={`proof-goal proof-goal--${complete ? 'complete' : 'incomplete'}`}>
                              <b>Goal:</b>b> {lhs} = {rhs}
                    </p>p>
                )}
                <p>
                        <b>Completed:</b>b> {complete ? 'True' : 'False'}
                </p>p>
                <Link to={config.viewRoute} state={{ id: proof.id }}>
                        <Button variant="outline-secondary" style={{ width: '100%' }}>
                                  Open Proof
                        </Button>Button>
                </Link>Link>
                <Link to={config.viewRoute} state={{ id: proof.id, playMode: true }}>
                        <Button variant="outline-primary" style={{ width: '100%', marginTop: '0.5rem' }}>
                                  <i className="fa-solid fa-play" style={{ marginRight: '0.4rem' }}></i>i>
                                  Run Proof
                        </Button>Button>
                </Link>Link>
          </div>div>
        );
}</MainLayout>
