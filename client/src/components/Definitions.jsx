import "../scss/_definitions.scss";
import Form from "react-bootstrap/Form";
import Col from "react-bootstrap/Col";
import Row from "react-bootstrap/Row";
import Button from "react-bootstrap/esm/Button";
import Accordion from "react-bootstrap/Accordion";
import validateField from "../utils/definitionsFormValidation";
import { useInputState } from "../hooks/useInputState";
import { useFormValidation } from "../hooks/useFormValidation";
import { useFormSubmit } from "../hooks/useFormSubmit";
import { useState } from "react";

export default function Definitions({ toggleDefinitionsWindow }) {
  const [showCreateDefinition, setShowCreateDefinition] = useState(false);

  return (
    <div className="overlay">
      <div className="card">
        {showCreateDefinition ? (
          <CreateDefinition onUpdate={setShowCreateDefinition} />
        ) : (
          <ShowDefinitions
            onUpdate={setShowCreateDefinition}
            toggleDefinitionsWindow={toggleDefinitionsWindow}
          />
        )}
      </div>
    </div>
  );
}

function CreateDefinition({ onUpdate }) {
  const initialValues = {
    label: "",
    type: "",
    expression: ""
  };

  const [formValues, handleChange] = useInputState(initialValues);
  const [validationMessages, handleBlur, setAllTouched, isFormValid] =
    useFormValidation(formValues, validateField);
  const [validated, setValidated] = useState(false);

  const handleCreateDefinition = async () => {
    const definition = {
      label: formValues.label,
      type: formValues.type,
      expression: formValues.expression
    };

    const definitions = JSON.parse(sessionStorage.getItem("definitions")) || [];
    let exists = false;

    definitions.forEach((def) => {
      if (def.label === definition.label) {
        alert("Definition already exists.");
        exists = true;
      }
    });

    if (!exists) {
      definitions.push(definition);
      sessionStorage.setItem("definitions", JSON.stringify(definitions));
      alert("Definition created successfully.");
    }
  };

  const { handleSubmit } = useFormSubmit(
    isFormValid,
    setValidated,
    setAllTouched,
    handleCreateDefinition
  );

  return (
    <div className="create-definition">
      <p className="title"> Create a new definition </p>
      <Form
        className="form"
        noValidate
        validated={validated}
        onSubmit={handleSubmit}
      >
        <Row>
          <Col>
            <Form.Floating>
              <Form.Control
                type="text"
                id="definitionLabel"
                name="label"
                placeholder="Enter Label"
                value={formValues.label}
                onBlur={() => handleBlur("label")}
                onChange={handleChange}
                isInvalid={!!validationMessages.label}
                required
              />
              <label htmlFor="definitionLabel">Label</label>
              <Form.Control.Feedback type="invalid">
                {validationMessages.label}
              </Form.Control.Feedback>
            </Form.Floating>
          </Col>
          <Col>
            <Form.Floating>
              <Form.Control
                type="text"
                id="definitionType"
                name="type"
                placeholder="Enter Type"
                value={formValues.type}
                onBlur={() => handleBlur("type")}
                onChange={handleChange}
                isInvalid={!!validationMessages.type}
                required
              />
              <label htmlFor="definitionType">Type</label>
              <Form.Control.Feedback type="invalid">
                {validationMessages.type}
              </Form.Control.Feedback>
            </Form.Floating>
          </Col>
        </Row>
        <Row>
          <Col>
            <Form.Floating>
              <Form.Control
                type="text"
                id="definitionExpression"
                name="expression"
                placeholder="Enter Expression"
                value={formValues.expression}
                onBlur={() => handleBlur("expression")}
                onChange={handleChange}
                isInvalid={!!validationMessages.expression}
                required
              />
              <label htmlFor="definitionExpression">Expression</label>
              <Form.Control.Feedback type="invalid">
                {validationMessages.expression}
              </Form.Control.Feedback>
            </Form.Floating>
          </Col>
        </Row>
        <div className="button-row">
          <Button variant="outline-danger" onClick={() => onUpdate(false)}>
            Go Back
          </Button>
          <Button variant="outline-primary" type="submit">
            Create Definition
          </Button>
        </div>
      </Form>
    </div>
  );
}

function ShowDefinitions({ onUpdate, toggleDefinitionsWindow }) {
  const definitions = JSON.parse(sessionStorage.getItem("definitions")) || [];

  return (
    <div className="definitions-container">
      <p className="title">User definitions</p>
      <div className="definitions">
        {definitions.length === 0 && <p>No definitions found.</p>}
        {definitions.map((def, index) => (
          <Definition key={index} definition={def} eventKey={index} />
        ))}
      </div>
      <div className="button-row">
        <Button variant="danger" onClick={toggleDefinitionsWindow}>
          Close Definitions Window
        </Button>
        <Button onClick={() => onUpdate(true)}>Create New Definition</Button>
      </div>
    </div>
  );
}

function Definition({ definition, eventKey }) {
  return (
    <Accordion>
      <Accordion.Item eventKey={eventKey}>
        <Accordion.Header>
          <p className="definition-label">{definition.label}</p>
        </Accordion.Header>
        <Accordion.Body>
          <p>Type: {definition.type}</p>
          <p>Expression: {definition.expression}</p>
        </Accordion.Body>
      </Accordion.Item>
    </Accordion>
  );
}