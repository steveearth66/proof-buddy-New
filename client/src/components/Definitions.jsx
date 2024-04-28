import "../scss/_definitions.scss";
import Form from "react-bootstrap/Form";
import Col from "react-bootstrap/Col";
import Row from "react-bootstrap/Row";
import Alert from "react-bootstrap/Alert";
import Button from "react-bootstrap/esm/Button";
import Accordion from "react-bootstrap/Accordion";
import validateField from "../utils/definitionsFormValidation";
import { useInputState } from "../hooks/useInputState";
import { useFormValidation } from "../hooks/useFormValidation";
import { useFormSubmit } from "../hooks/useFormSubmit";
import { useState } from "react";
import erService from "../services/erService";

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

function CreateDefinition({
  onUpdate,
  label,
  type,
  expression,
  notes,
  edit,
  updateDefinition
}) {
  const initialValues = {
    label: label || "",
    type: type || "",
    expression: expression || "",
    notes: notes || ""
  };

  const [formValues, handleChange] = useInputState(initialValues);
  const [validationMessages, handleBlur, setAllTouched, isFormValid] =
    useFormValidation(formValues, validateField);
  const [validated, setValidated] = useState(false);
  const [errors, setErrors] = useState([]);
  const [successMessage, setSuccessMessage] = useState("");

  const handleReset = () => {
    formValues.label = "";
    formValues.type = "";
    formValues.expression = "";
    formValues.notes = "";
    setValidated(false);
    setErrors([]);
  };

  const handleCreateDefinition = async () => {
    const definition = {
      label: formValues.label,
      type: formValues.type,
      expression: formValues.expression,
      notes: formValues.notes
    };

    const definitions = JSON.parse(sessionStorage.getItem("definitions")) || [];
    let exists = false;

    if (edit) {
      const response = await erService.createDefinition(definition);
      setErrors([]);

      if (response.status === 200) {
        updateDefinition(definition);
        setSuccessMessage("Definition updated successfully.");
        return;
      } else {
        setErrors(["Failed to update definition."]);
        return;
      }
    }

    definitions.forEach((def) => {
      if (def.label === definition.label) {
        setErrors(["Definition with this label already exists."]);
        exists = true;
      }
    });

    if (!exists) {
      const response = await erService.createDefinition(definition);
      setErrors([]);

      if (response.status === 200) {
        definitions.push(definition);
        sessionStorage.setItem("definitions", JSON.stringify(definitions));
        setSuccessMessage("Definition created successfully.");
        handleReset();
      } else {
        setErrors(["Failed to create definition."]);
      }
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
      {edit ? (
        <p className="title"> Edit definition </p>
      ) : (
        <p className="title"> Create a new definition </p>
      )}

      {errors.length > 0 && (
        <Alert variant="danger">
          {errors.map((error, index) => (
            <p key={index}>{error}</p>
          ))}
        </Alert>
      )}

      {successMessage && <Alert variant="success">{successMessage}</Alert>}

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
              />
              <label htmlFor="definitionExpression">Expression</label>
              <Form.Control.Feedback type="invalid">
                {validationMessages.expression}
              </Form.Control.Feedback>
            </Form.Floating>
          </Col>
        </Row>
        <Row>
          <Col>
            <Form.Control
              type="text"
              id="definitionNotes"
              name="notes"
              placeholder="Enter Notes"
              value={formValues.notes}
              onBlur={() => handleBlur("notes")}
              onChange={handleChange}
              as="textarea"
              rows={4}
            />
          </Col>
        </Row>
        <div className="def-button-row">
          <Button variant="outline-danger" onClick={() => onUpdate(false)}>
            Go Back
          </Button>
          <Button variant="outline-primary" type="submit">
            {edit ? "Update" : "Create"} Definition
          </Button>
        </div>
      </Form>
    </div>
  );
}

function ShowDefinitions({ onUpdate, toggleDefinitionsWindow }) {
  const [definitions, setDefinitions] = useState(
    JSON.parse(sessionStorage.getItem("definitions")) || []
  );
  const [definitionToEdit, setDefinitionToEdit] = useState({});
  const [edit, setEdit] = useState(false);

  const deleteDefinition = (label) => {
    const confirm = window.confirm(
      "Are you sure you want to delete this definition?"
    );
    if (!confirm) return;

    const definitions = JSON.parse(sessionStorage.getItem("definitions")) || [];
    const updatedDefinitions = definitions.filter((def) => def.label !== label);
    sessionStorage.setItem("definitions", JSON.stringify(updatedDefinitions));
    setDefinitions(updatedDefinitions);
  };

  const updateDefinition = ({ label, type, expression, notes }) => {
    const updatedDefinitions = definitions.map((def) => {
      if (def.label === label) {
        return { label, type, expression, notes };
      } else {
        return def;
      }
    });
    sessionStorage.setItem("definitions", JSON.stringify(updatedDefinitions));
    setDefinitions(updatedDefinitions);
  };

  const updateEdit = (definition) => {
    setDefinitionToEdit(definition);
    setEdit(true);
  };

  if (edit) {
    return (
      <CreateDefinition
        onUpdate={() => setEdit(false)}
        label={definitionToEdit.label}
        type={definitionToEdit.type}
        expression={definitionToEdit.expression}
        notes={definitionToEdit.notes}
        edit={edit}
        updateDefinition={updateDefinition}
      />
    );
  } else {
    return (
      <div className="definitions-container">
        <p className="title">User definitions</p>
        <div className="definitions">
          {definitions.length === 0 && <p>No definitions found.</p>}
          {definitions.map((def, index) => (
            <Definition
              key={index}
              definition={def}
              eventKey={index}
              deleteDefinition={deleteDefinition}
              updateEdit={updateEdit}
            />
          ))}
        </div>
        <div className="def-button-row">
          <Button variant="danger" onClick={toggleDefinitionsWindow}>
            Close Definitions Window
          </Button>
          <Button onClick={() => onUpdate(true)}>Create New Definition</Button>
        </div>
      </div>
    );
  }
}

function Definition({ definition, eventKey, deleteDefinition, updateEdit }) {
  return (
    <Accordion>
      <Accordion.Item eventKey={eventKey}>
        <Accordion.Header>
          <p className="definition-label">{definition.label}</p>
        </Accordion.Header>
        <Accordion.Body>
          <p>Type: {definition.type}</p>
          <p>Expression: {definition.expression}</p>
          {definition.notes && <p>Notes: {definition.notes}</p>}
          <div className="def-button-row">
            <Button
              variant="outline-primary"
              onClick={() => updateEdit(definition)}
            >
              Edit
            </Button>
            <Button
              variant="outline-danger"
              onClick={() => deleteDefinition(definition.label)}
            >
              Delete
            </Button>
          </div>
        </Accordion.Body>
      </Accordion.Item>
    </Accordion>
  );
}