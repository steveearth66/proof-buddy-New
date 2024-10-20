import { useEffect, useState } from "react";
import MainLayout from "../layouts/MainLayout";
import erService from "../services/erService";
// import Card from "react-bootstrap/Card";
import Row from "react-bootstrap/Row";
import Col from "react-bootstrap/Col";
import Container from "react-bootstrap/Container";
import Button from "react-bootstrap/esm/Button";
import { Link } from "react-router-dom";
import '../scss/_proof-card.scss';

export default function Proofs() {
  const [proofs, setProofs] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const proofs = await erService.getRacketProofs();
        setProofs(proofs);
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
          {proofs.map((proof) => (
            <ProofCard key={proof.tag} {...proof} />
          ))}
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
        <Button variant="outline-success" style={{ width: '100%' }}>
          View Proof
        </Button>
      </Link>
    </div>
  );
}
