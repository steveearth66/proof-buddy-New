import { useState, useEffect } from "react";
import validateField from "../utils/substitutionFormValidation";
import Modal from "react-bootstrap/Modal";
import Form from "react-bootstrap/Form";
import Row from "react-bootstrap/Row";
import Col from "react-bootstrap/Col";
import Alert from "react-bootstrap/Alert";
import { useInputState } from "../hooks/useInputState";
import { useFormValidation } from "../hooks/useFormValidation";
import { useFormSubmit } from "../hooks/useFormSubmit";

export default function Substitution({
  show,
  handleClose,
  racketRuleFields,
  handleSubstitution,
  errors
}) {
  const initialValues = {
    substitution: "",
    rule: ""
  };

  const [formValues, handleChange] = useInputState(initialValues);
  const [validationMessages, handleBlur, setAllTouched, isFormValid] =
    useFormValidation(formValues, validateField);
  const [validated, setValidated] = useState(false);

  const handleSubstitutionSubmit = async () => {
    const valid = await handleSubstitution(formValues);

    if (!valid) {
      setValidated(false);
    }
  };

  const { handleSubmit } = useFormSubmit(
    isFormValid,
    setValidated,
    setAllTouched,
    handleSubstitutionSubmit
  );

  useEffect(() => {
    const undeletedProofLines = racketRuleFields.filter((line) => {
      return !line.deleted;
    });
    const lastUnDeletedFieldIndex = undeletedProofLines.length - 1;

    if (undeletedProofLines.length > 0) {
      const ruleValue = undeletedProofLines[lastUnDeletedFieldIndex].rule;
      if (ruleValue.trim().length > 0) {
        handleChange({ target: { name: "rule", value: ruleValue } });
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <Modal show={show} onHide={handleClose} size="xl">
      <Form validated={validated} onSubmit={handleSubmit}>
        <Modal.Header closeButton>
          <Modal.Title>Substitution</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Row>
            {errors.length > 0 && (
              <Alert variant="danger" className="scroll-error">
                {errors.map((error, index) => (
                  <span key={`racket-error-${index}`}>{error}</span>
                ))}
              </Alert>
            )}
          </Row>
          <Row>
            <Form.Group as={Col} md="8">
              <Form.Floating className="mb-3">
                <Form.Control
                  name="substitution"
                  type="text"
                  placeholder="Enter the substitution"
                  value={formValues.substitution}
                  onBlur={() => handleBlur("substitution")}
                  onChange={handleChange}
                  isInvalid={validationMessages.substitution}
                  required
                />
                <label>Substitution</label>
                <Form.Control.Feedback type="invalid">
                  {validationMessages.substitution}
                </Form.Control.Feedback>
              </Form.Floating>
            </Form.Group>
            <Form.Group as={Col} md="4">
              <Form.Floating className="mb-3">
                <Form.Control
                  name="rule"
                  type="text"
                  placeholder="Rule"
                  value={formValues.rule}
                  onBlur={() => handleBlur("rule")}
                  onChange={handleChange}
                  isInvalid={validationMessages.rule}
                  required
                />
                <label>Rule</label>
                <Form.Control.Feedback type="invalid">
                  {validationMessages.rule}
                </Form.Control.Feedback>
              </Form.Floating>
            </Form.Group>
          </Row>
        </Modal.Body>
        <Modal.Footer>
          <button className="btn btn-primary">Submit</button>
        </Modal.Footer>
      </Form>
    </Modal>
  );
}
