import { useEffect, useState } from "react";
import MainLayout from "../layouts/MainLayout";
import erService from "../services/erService";
import Card from "react-bootstrap/Card";
import Row from "react-bootstrap/Row";
import Col from "react-bootstrap/Col";
import Container from "react-bootstrap/Container";
import Button from "react-bootstrap/esm/Button";

export default function Proofs() {
  const [proofs, setProofs] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const proofs = await erService.getRacketProofs();
        setProofs(proofs);
      } catch (error) {
        console.error("Error fetching proofs:", error);
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
        {proofs.map((proof) => (
          <ProofCard key={proof.tag} {...proof} />
        ))}
      </Container>
    </MainLayout>
  );
}

function ProofCard(proof) {
  return (
    <Card className="mb-2" style={{ height: "100px" }}>
      <Card.Body>
        <Row>
          <Col>
            <p>Name: {proof.name}</p>
          </Col>
          <Col>
            <p>Tag: {proof.tag}</p>
          </Col>
          <Col>
            <p>LHS Goal: {proof.lhs}</p>
          </Col>
          <Col>
            <p>RHS Goal: {proof.rhs}</p>
          </Col>
          <Col>
            <p>Is Complete: {proof.isComplete}</p>
          </Col>
          <Col>
            <Button variant="primary">Open Proof</Button>
          </Col>
        </Row>
      </Card.Body>
    </Card>
  );
}
