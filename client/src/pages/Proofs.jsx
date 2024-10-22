import { useEffect, useState } from 'react';
import MainLayout from '../layouts/MainLayout';
import erService from '../services/erService';
import Row from 'react-bootstrap/Row';
import Col from 'react-bootstrap/Col';
import Container from 'react-bootstrap/Container';
import Button from 'react-bootstrap/esm/Button';
import InputGroup from 'react-bootstrap/InputGroup';
import Pagination from 'react-bootstrap/Pagination';
import Spinner from 'react-bootstrap/Spinner';
import Form from 'react-bootstrap/Form';
import { Link } from 'react-router-dom';
import '../scss/_proof-card.scss';

export default function Proofs() {
  const [proofObject, setProofObject] = useState({});
  const [query, setQuery] = useState('');

  const queryProofs = async ({ page = 1 }) => {
    try {
      const proofsData = await erService.getRacketProofs({ query, page });
      setProofObject(proofsData);
    } catch (error) {
      console.error('Error fetching proofs:', error);
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        const proofsData = await erService.getRacketProofs({});
        setProofObject(proofsData);
      } catch (error) {
        console.error('Error fetching proofs:', error);
      }
    };
    fetchData();
  }, []);

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
                <ProofCard key={proof.tag} {...proof} />
              ))
            )}
            {proofObject.proofs?.length === 0 && <p>No proofs found</p>}
          </div>
          <Pagination>
            <Pagination.First onClick={() => queryProofs({ page: 1 })} />
            <Pagination.Prev
              onClick={() => queryProofs({ page: proofObject.currentPage - 1 })}
            />
            {Array.from({ length: proofObject.totalPages }, (_, i) => (
              <Pagination.Item
                key={i}
                active={i === proofObject.currentPage - 1}
                onClick={() => queryProofs({ page: i + 1 })}
              >
                {i + 1}
              </Pagination.Item>
            ))}
            <Pagination.Next
              onClick={() => queryProofs({ page: proofObject.currentPage + 1 })}
            />
            <Pagination.Last
              onClick={() => queryProofs({ page: proofObject.totalPages })}
            />
          </Pagination>
        </div>
      </Container>
    </MainLayout>
  );
}

function ProofCard(proof) {
  return (
    <div className="proof-card">
      <p>
        <b>Proof:</b> {proof.name} - {proof.tag}
      </p>
      <p>
        <b>Completed:</b> {proof.isComplete ? 'True' : 'False'}
      </p>
      <Link to={`/er-racket`} state={{ id: proof.id }}>
        <Button variant="outline-secondary" style={{ width: '100%' }}>
          View Proof
        </Button>
      </Link>
    </div>
  );
}
