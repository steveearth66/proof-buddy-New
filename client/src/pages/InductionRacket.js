import React, { useState, useEffect } from "react";
import Dropdown from "react-bootstrap/Dropdown";
import Button from "react-bootstrap/Button";
import Container from "react-bootstrap/Container";
import Form from "react-bootstrap/Form";
import Col from "react-bootstrap/Col";
import Row from "react-bootstrap/Row";
import Alert from "react-bootstrap/Alert";
import MainLayout from "../layouts/MainLayout";
import validateField from "../utils/inductionFormValidation";
import OffcanvasRuleSet from "../components/OffcanvasRuleSet";
import { useToggleSide } from "../hooks/useToggleSide";
import { useOffcanvas } from "../hooks/useOffcanvas";
import { useInputState } from "../hooks/useInputState";
import { useFormValidation } from "../hooks/useFormValidation";
import useInductionCheck from "../hooks/useInductionCheck";
import { useRacketRuleFields } from "../hooks/useRacketRuleFields";
import { useCurrentRacketValues } from "../hooks/useCurrentRacketValues";
import { useFormSubmit } from "../hooks/useFormSubmit";
import "../scss/_forms.scss";
import "../scss/_er-racket.scss";
import { useExportToLocalMachine } from "../hooks/useExportToLocalMachine";
import { Definitions, ProofComplete, PersistentPad } from "../components";
import { useDefinitionsWindow } from "../hooks/useDefinitionsWindow";
import erService from "../services/erService";

/**
 * InductionRacket component facilitates the Equational Reasoning Racket.
 */
const InductionRacket = () => {
  const initialValues = {
    proofName: "",
    proofTag: "",
    lHSLeapGoal: "",
    rHSLeapGoal: "",
    lHSAnchorGoal: "",
    rHSAnchorGoal: "",
    inductionVariable: "",
    inductionValue: "",
    leapVariable: ""
  };

  const [showSide, toggleSide] = useToggleSide();
  const [formValues, handleChange] = useInputState(initialValues);
  const [validationMessages, handleBlur, setAllTouched, isFormValid] =
    useFormValidation(formValues, validateField);
  const [validated, setValidated] = useState(false);
  const { isGoalChecked, checkGoal } = useInductionCheck(handleChange);
  const [startPosition, setStartPosition] = useState(0);
  const [currentRacket, setCurrentRacket] = useState("");
  const [
    racketRuleFields,
    addFieldWithApiCheck,
    handleFieldChange,
    validationErrors,
    serverError,
    racketErrors,
    deleteLastLine,
    sendProofComplete
  ] = useRacketRuleFields(
    startPosition,
    currentRacket,
    formValues.proofName,
    formValues.proofTag,
    showSide
  );
  const [currentLHS, currentRHS] = useCurrentRacketValues(racketRuleFields);
  const [lhsValue, setLhsValue] = useState("");
  const [rhsValue, setRhsValue] = useState("");
  const [isOffcanvasActive, toggleOffcanvas] = useOffcanvas();
  const [showDefinitionsWindow, toggleDefinitionsWindow] =
    useDefinitionsWindow();
  const [showProofComplete, setShowProofComplete] = useState(false);
  const [proofComplete, setProofComplete] = useState(false);
  const [leftPremise, setLeftPremise] = useState({});
  const [rightPremise, setRightPremise] = useState({});
  const [isAnchor, setIsAnchor] = useState(false);

  const handleERRacketSubmission = async () => {
    alert("We are stilling working on proof submission!");
  };

  const { handleSubmit } = useFormSubmit(
    isFormValid,
    setValidated,
    setAllTouched,
    handleERRacketSubmission
  );

  /**
   * Creates JSON object of the target incoming parameter (which should be a JavaScript Object)
   */
  const convertToJSON = (target) => {
    return JSON.stringify(target);
  };

  /**
   * Returns a JSON object of the present form
   */
  const convertFormToJSON = () => {
    //This is a Front End Proof Object placeholder
    //In the future we will be using a Proof Object sent from the python-server
    let EquationalReasoningObject = {
      name: formValues.proofName,
      leftRacketsAndRules: racketRuleFields.LHS,
      rightRacketsAndRules: racketRuleFields.RHS
    };

    return convertToJSON(EquationalReasoningObject);
  };

  const exportJSON = useExportToLocalMachine(
    formValues.proofName,
    convertFormToJSON()
  );

  const handleHighlight = (startPosition) => {
    setStartPosition(startPosition);
  };

  useEffect(() => {
    sessionStorage.removeItem("highlights");
    sessionStorage.removeItem("definitions");

    const clearProof = async () => {
      await erService.clearProof();
    };

    clearProof();
  }, []);

  useEffect(() => {
    if (formValues.rHSGoal !== "") {
      setRightPremise({
        racket: formValues.rHSGoal,
        rule: "Premise",
        startPosition: 0
      });
    }

    if (formValues.lHSGoal !== "") {
      setLeftPremise({
        racket: formValues.lHSGoal,
        rule: "Premise",
        startPosition: 0
      });
    }
  }, [formValues]);

  useEffect(() => {
    const removeBlankRackets = () => {
      racketRuleFields.LHS.splice(-1);
      racketRuleFields.RHS.splice(-1);
    };

    const sendProofComplete = async () => {
      try {
        await erService.completeProof({
          name: formValues.proofName,
          tag: formValues.proofTag,
          leftRacketsAndRules: racketRuleFields.LHS,
          rightRacketsAndRules: racketRuleFields.RHS,
          lHSGoal: formValues.lHSGoal,
          rHSGoal: formValues.rHSGoal,
          leftPremise,
          rightPremise
        });
      } catch (error) {
        console.error(error);
      }
    };

    if (lhsValue !== "" && rhsValue !== "" && currentLHS !== "") {
      if (currentLHS === currentRHS || currentLHS === rhsValue) {
        removeBlankRackets();
        setShowProofComplete(true);
        setProofComplete(true);
        sendProofComplete();
        setTimeout(() => {
          setShowProofComplete(false);
        }, 5000);
      }
    }
  }, [
    currentLHS,
    currentRHS,
    racketRuleFields,
    lhsValue,
    rhsValue,
    formValues.proofName,
    formValues.proofTag,
    formValues.lHSGoal,
    formValues.rHSGoal,
    leftPremise,
    rightPremise,
    sendProofComplete
  ]);

  return (
    <MainLayout>
      <Container className="er-racket-container">
        <OffcanvasRuleSet
          isActive={isOffcanvasActive}
          toggleFunction={toggleOffcanvas}
        ></OffcanvasRuleSet>
        {showDefinitionsWindow && (
          <Definitions toggleDefinitionsWindow={toggleDefinitionsWindow} />
        )}

        {showProofComplete && <ProofComplete />}

        <Form
          noValidate
          validated={validated}
          className="er-racket-form"
          onSubmit={handleSubmit}
        >
          <div className="form-top-section">
            <Row className="page-header-row">
              <Col>
                <h1>Induction: Racket</h1>
              </Col>
              <Col className="check-row">
                <Form.Check
                  type="checkbox"
                  id="lists"
                  label="Lists"
                  name="lists"
                />
                <Form.Check
                  type="checkbox"
                  id="integers"
                  label="Integers"
                  name="integers"
                />
              </Col>
            </Row>

            <Row>
              <Form.Group as={Col} md="3" className="er-proof-name">
                <Form.Floating className="mb-3">
                  <Form.Control
                    id="eRProofName"
                    name="proofName"
                    type="text"
                    placeholder="Enter name"
                    value={formValues.proofName}
                    onBlur={() => {
                      handleBlur("proofName");
                      // clearProofValidationMessage();
                    }}
                    onChange={handleChange}
                    isInvalid={!!validationMessages.proofName}
                    required
                  />
                  <label htmlFor="eRProofName">Name</label>
                  <Form.Control.Feedback type="invalid" tooltip>
                    {validationMessages.proofName}
                  </Form.Control.Feedback>
                </Form.Floating>
              </Form.Group>
              <Form.Group as={Col} md="3" className="er-proof-tag">
                <Form.Floating className="mb-3">
                  <Form.Control
                    id="eRProofTag"
                    name="proofTag"
                    type="text"
                    placeholder="Enter tag"
                    value={formValues.proofTag}
                    onBlur={() => {
                      handleBlur("proofTag");
                    }}
                    onChange={handleChange}
                    // isInvalid={!!proofValidationMessage.tag}
                    required
                  />
                  <label htmlFor="eRProofTag"># Tag</label>
                  <Form.Control.Feedback type="invalid" tooltip>
                    {/* {proofValidationMessage.tag} */}
                  </Form.Control.Feedback>
                </Form.Floating>
              </Form.Group>
              <Form.Group as={Col} md="1" className="er-induction-variable">
                <Form.Floating className="mb-3">
                  <Form.Control
                    id="eRInductionVariable"
                    name="inductionVariable"
                    type="text"
                    placeholder="Induction Variable"
                    value={formValues.inductionVariable}
                    onBlur={() => handleBlur("inductionVariable")}
                    onChange={handleChange}
                    isInvalid={!!validationMessages.inductionVariable}
                    required
                  />
                  <label htmlFor="eRInductionVariable">AVar</label>
                  <Form.Control.Feedback type="invalid" tooltip>
                    {validationMessages.inductionVariable}
                  </Form.Control.Feedback>
                </Form.Floating>
              </Form.Group>
              <Form.Group as={Col} md="1" className="er-induction-value">
                <Form.Floating className="mb-3">
                  <Form.Control
                    id="eRInductionValue"
                    name="inductionValue"
                    type="text"
                    placeholder="Induction Value"
                    value={formValues.inductionValue}
                    onBlur={() => handleBlur("inductionValue")}
                    onChange={handleChange}
                    isInvalid={!!validationMessages.inductionValue}
                    required
                  />
                  <label htmlFor="eRInductionValue">AVal</label>
                  <Form.Control.Feedback type="invalid" tooltip>
                    {validationMessages.inductionValue}
                  </Form.Control.Feedback>
                </Form.Floating>
              </Form.Group>
              <Form.Group as={Col} md="1" className="er-leap-variable">
                <Form.Floating className="mb-3">
                  <Form.Control
                    id="eRLeapVariable"
                    name="leapVariable"
                    type="text"
                    placeholder="Leap Variable"
                    value={formValues.leapVariable}
                    onBlur={() => handleBlur("leapVariable")}
                    onChange={handleChange}
                    isInvalid={!!validationMessages.leapVariable}
                    required
                  />
                  <label htmlFor="eRLeapVariable">LVal</label>
                  <Form.Control.Feedback type="invalid" tooltip>
                    {validationMessages.leapVariable}
                  </Form.Control.Feedback>
                </Form.Floating>
              </Form.Group>
              <Dropdown
                as={Col}
                className="d-inline proof-dropdown-btn proof-utilities"
              >
                <Dropdown.Toggle id="dropdown-autoclose-true">
                  Proof Utilities
                </Dropdown.Toggle>

                <Dropdown.Menu>
                  <Dropdown.Item onClick={toggleDefinitionsWindow} href="#">
                    Definitions
                  </Dropdown.Item>
                  <Dropdown.Item onClick={toggleOffcanvas} href="#">
                    View Rule Set
                  </Dropdown.Item>
                </Dropdown.Menu>
              </Dropdown>
            </Row>

            <Row className="g-5">
              {isAnchor ? (
                <>
                  <Form.Group as={Col} md="6" className="er-proof-goal-lhs">
                    <Form.Floating className="mb-3">
                      <Form.Control
                        id="eRProofLHSAnchorGoal"
                        name="lHSAnchorGoal"
                        type="text"
                        placeholder="LHS Anchor Goal"
                        value={formValues.lHSAnchorGoal}
                        onBlur={() => handleBlur("lHSAnchorGoal")}
                        // onChange={enhancedHandleChange}
                        isInvalid={!!validationMessages.lHSAnchorGoal}
                        required
                      />
                      <label htmlFor="eRProofLHSAnchor">LHS Anchor Goal</label>
                      <Form.Control.Feedback type="invalid" tooltip>
                        {validationMessages.lHSAnchorGoal}
                      </Form.Control.Feedback>
                    </Form.Floating>
                  </Form.Group>
                  <Form.Group as={Col} md="6" className="er-proof-goal-rhs">
                    <Form.Floating className="mb-3">
                      <Form.Control
                        id="eRProofRHSAnchorGoal"
                        name="rHSAnchorGoal"
                        type="text"
                        placeholder="RHS Anchor Goal"
                        value={formValues.rHSAnchorGoal}
                        onBlur={() => handleBlur("rHSAnchorGoal")}
                        // onChange={enhancedHandleChange}
                        isInvalid={!!validationMessages.rHSAnchorGoal}
                        required
                      />
                      <label htmlFor="eRProofRHSAnchorGoal">
                        RHS Anchor Goal
                      </label>
                      <Form.Control.Feedback type="invalid" tooltip>
                        {validationMessages.rHSAnchorGoal}
                      </Form.Control.Feedback>
                    </Form.Floating>
                  </Form.Group>
                </>
              ) : (
                <>
                  <Form.Group as={Col} md="6" className="er-proof-goal-lhs">
                    <Form.Floating className="mb-3">
                      <Form.Control
                        id="eRProofLHSLeapGoal"
                        name="lHSLeapGoal"
                        type="text"
                        placeholder="Leap Goal"
                        value={formValues.lHSLeapGoal}
                        onBlur={() => handleBlur("leapGoal")}
                        // onChange={enhancedHandleChange}
                        isInvalid={!!validationMessages.lHSLeapGoal}
                        required
                      />
                      <label htmlFor="eRProofLHSLeapGoal">LHS Leap Goal</label>
                      <Form.Control.Feedback type="invalid" tooltip>
                        {validationMessages.lHSLeapGoal}
                      </Form.Control.Feedback>
                    </Form.Floating>
                  </Form.Group>
                  <Form.Group as={Col} md="6" className="er-proof-goal-rhs">
                    <Form.Floating className="mb-3">
                      <Form.Control
                        id="eRProofRHSLeapGoal"
                        name="rHSLeapGoal"
                        type="text"
                        placeholder="RHS Leap Goal"
                        value={formValues.rHSAnchor}
                        onBlur={() => handleBlur("rHSLeapGoal")}
                        // onChange={enhancedHandleChange}
                        isInvalid={!!validationMessages.rHSLeapGoal}
                        required
                      />
                      <label htmlFor="eRProofRHSLeapGoal">RHS Leap Goal</label>
                      <Form.Control.Feedback type="invalid" tooltip>
                        {validationMessages.rHSLeapGoal}
                      </Form.Control.Feedback>
                    </Form.Floating>
                  </Form.Group>
                </>
              )}
            </Row>

            <Row className="er-current-state">
              <Form.Group
                as={Col}
                md="5"
                className={`er-proof-current-lhs ${showSide === "LHS" ? "active" : ""}`}
              >
                <Form.Floating className="mb-3">
                  <Form.Control
                    id="eRProofCurrentLHS"
                    name="proofCurrentLHS"
                    type="text"
                    placeholder="Current LHS"
                    value={currentLHS === "" ? lhsValue : currentLHS}
                    readOnly
                  />
                  <label htmlFor="eRProofCurrentLHS">Current LHS</label>
                </Form.Floating>
              </Form.Group>

              <Form.Group
                as={Col}
                md="5"
                className={`er-proof-current-rhs ${showSide === "RHS" ? "active" : ""}`}
              >
                <Form.Floating className="mb-3">
                  <Form.Control
                    id="eRProofCurrentRHS"
                    name="proofCurrentRHS"
                    type="text"
                    placeholder="Current RHS"
                    value={currentRHS === "" ? rhsValue : currentRHS}
                    readOnly
                  />
                  <label htmlFor="eRProofCurrentRHS">Current RHS</label>
                </Form.Floating>
              </Form.Group>
            </Row>

            <Form.Text
              as={"div"}
              id="formSeparator"
              className="form-separator"
            ></Form.Text>
          </div>

          <div className="form-bottom-part">
            <Row className="switch-btn-wrap">
              <Col>
                <Button
                  variant="secondary"
                  size="lg"
                  className="switch-btn"
                  onClick={toggleSide}
                >
                  {showSide === "LHS"
                    ? "Switch to Right Hand Side ⋙"
                    : "⋘ Switch to Left Hand Side"}
                </Button>
              </Col>
              <Col>
                <Button
                  variant="secondary"
                  size="lg"
                  className="switch-btn"
                  onClick={() => setIsAnchor((prev) => !prev)}
                >
                  {isAnchor ? "Switch to Leap Case" : "Switch to Anchor Case"}
                </Button>
              </Col>
            </Row>

            {!isGoalChecked[showSide] && (
              <Row className="goal-btn-wrap">
                <Button
                  className="orange-btn"
                  onClick={() =>
                    checkGoal(
                      showSide,
                      formValues[`${showSide[0].toLowerCase()}HSGoal`],
                      formValues.proofName,
                      formValues.proofTag,
                      formValues.lHSGoal,
                      formValues.rHSGoal
                    )
                  }
                >
                  Check {showSide} Goal
                </Button>
              </Row>
            )}

            {[isGoalChecked][showSide] && (
              <div className="racket-rule-container-wrap">
                <div className="racket-rule-wrap" id="racket-rule">
                  {serverError && (
                    <Alert variant={"danger"}>{serverError}</Alert>
                  )}

                  {racketErrors.length > 0 && (
                    <Alert variant={"danger"} className="scroll-error">
                      {racketErrors.map((error, index) => (
                        <span key={`racket-error-${index}`}>{error}</span>
                      ))}
                    </Alert>
                  )}

                  {proofComplete && (
                    <Alert variant={"success"}>Proof Complete!</Alert>
                  )}

                  {showSide === "LHS" && (
                    <div className="racket-rule-lhs" id="racket-rule-lhs">
                      {/* Static Row Always Present */}
                      <Row className="racket-rule-row">
                        <PersistentPad
                          equation={formValues.lHSGoal}
                          onHighlightChange={(startPosition) => {
                            handleHighlight(startPosition);
                            setCurrentRacket(formValues.lHSGoal);
                            handleChange({
                              target: {
                                name: "proofCurrentLHSGoal",
                                value: formValues.lHSGoal
                              }
                            });
                            setLeftPremise({
                              racket: formValues.lHSGoal,
                              rule: "Premise",
                              startPosition
                            });
                          }}
                          side={showSide}
                        />

                        <Form.Group
                          as={Col}
                          md="4"
                          className="er-proof-premise"
                        >
                          <Form.Floating className="mb-3">
                            <Form.Control
                              id="eRProofLHSPremise"
                              name="proofeRProofLHSPremise"
                              type="text"
                              value="Premise"
                              placeholder="LHS Premise"
                              onChange={handleChange}
                              readOnly
                            />
                            <label htmlFor="eRProofLHSPremise">
                              LHS Premise
                            </label>
                          </Form.Floating>
                        </Form.Group>
                      </Row>

                      {/* Dynamically Added Racket and Rule Fields */}
                      {racketRuleFields.LHS.map((field, index) =>
                        field.deleted ? null : (
                          <Row
                            className="racket-rule-row"
                            key={`LHS-field-${index}`}
                          >
                            <PersistentPad
                              equation={field.racket}
                              onHighlightChange={(startPosition) => {
                                handleHighlight(startPosition);
                                setCurrentRacket(
                                  racketRuleFields.LHS.slice(-2)[0].racket
                                );
                                handleFieldChange(
                                  showSide,
                                  index,
                                  "racket",
                                  field.racket,
                                  startPosition
                                );
                              }}
                              side={showSide}
                            />

                            <Form.Group
                              as={Col}
                              md="4"
                              className="er-proof-rule"
                            >
                              <Form.Floating className="mb-3">
                                <Form.Control
                                  id={`eRProofLHSRule-${index}`}
                                  name={`eRProofLHSRule_${index}`}
                                  type="text"
                                  placeholder="LHS Rule"
                                  value={field.rule}
                                  onChange={(e) =>
                                    handleFieldChange(
                                      showSide,
                                      index,
                                      "rule",
                                      e.target.value
                                    )
                                  }
                                  isInvalid={!!validationErrors.LHS[index]}
                                  required
                                />
                                <label htmlFor={`eRProofLHSRule-${index}`}>
                                  LHS Rule
                                </label>
                                <Form.Control.Feedback type="invalid" tooltip>
                                  {validationErrors.LHS[index]}
                                </Form.Control.Feedback>
                              </Form.Floating>
                            </Form.Group>
                          </Row>
                        )
                      )}
                    </div>
                  )}

                  {showSide === "RHS" && (
                    <div className="racket-rule-rhs" id="racket-rule-rhs">
                      {/* Static Row Always Present */}
                      <Row className="racket-rule-row">
                        <PersistentPad
                          equation={formValues.rHSGoal}
                          onHighlightChange={(startPosition) => {
                            handleHighlight(startPosition);
                            setCurrentRacket(formValues.rHSGoal);
                            handleChange({
                              target: {
                                name: "proofCurrentRHSGoal",
                                value: formValues.rHSGoal
                              }
                            });
                            setRightPremise({
                              racket: formValues.rHSGoal,
                              rule: "Premise",
                              startPosition
                            });
                          }}
                          side={showSide}
                        />

                        <Form.Group
                          as={Col}
                          md="4"
                          className="er-proof-premise"
                        >
                          <Form.Floating className="mb-3">
                            <Form.Control
                              id="eRProofRHSPremise"
                              name="proofeRProofRHSPremise"
                              type="text"
                              value="Premise"
                              placeholder="RHS Premise"
                              onChange={handleChange}
                              readOnly
                            />
                            <label htmlFor="eRProofRHSPremise">
                              RHS Premise
                            </label>
                          </Form.Floating>
                        </Form.Group>
                      </Row>

                      {/* Dynamically Added Racket and Rule Fields */}
                      {racketRuleFields.RHS.map((field, index) =>
                        field.deleted ? null : (
                          <Row
                            className="racket-rule-row"
                            key={`RHS-field-${index}`}
                          >
                            <PersistentPad
                              equation={field.racket}
                              onHighlightChange={(startPosition) => {
                                handleHighlight(startPosition);
                                setCurrentRacket(
                                  racketRuleFields.RHS.slice(-2)[0].racket
                                );
                                handleFieldChange(
                                  showSide,
                                  index,
                                  "racket",
                                  field.racket,
                                  startPosition
                                );
                              }}
                              side={showSide}
                            />

                            <Form.Group
                              as={Col}
                              md="4"
                              className="er-proof-rule"
                            >
                              <Form.Floating className="mb-3">
                                <Form.Control
                                  id={`eRProofRHSRule-${index}`}
                                  name={`eRProofRHSRule_${index}`}
                                  type="text"
                                  placeholder="RHS Rule"
                                  value={field.rule}
                                  onChange={(e) =>
                                    handleFieldChange(
                                      showSide,
                                      index,
                                      "rule",
                                      e.target.value
                                    )
                                  }
                                  isInvalid={!!validationErrors.RHS[index]}
                                  required
                                />
                                <label htmlFor={`eRProofRHSRule-${index}`}>
                                  RHS Rule
                                </label>
                                <Form.Control.Feedback type="invalid" tooltip>
                                  {validationErrors.RHS[index]}
                                </Form.Control.Feedback>
                              </Form.Floating>
                            </Form.Group>
                          </Row>
                        )
                      )}
                    </div>
                  )}
                </div>

                <div className="button-row-wrap">
                  <Row className="button-row">
                    <Col md="8">
                      <Button
                        className="orange-btn delete-btn"
                        onClick={() => deleteLastLine(showSide)}
                      >
                        Delete Line
                      </Button>
                    </Col>
                    <Col md="4" className="rules-btn-grp">
                      <Button
                        className="orange-btn green-btn"
                        onClick={() => {
                          addFieldWithApiCheck(showSide);
                          if (showSide === "LHS") {
                            setLhsValue(formValues.lHSGoal);
                          } else {
                            setRhsValue(formValues.rHSGoal);
                          }
                        }}
                      >
                        Generate & Check
                      </Button>
                      <Button className="orange-btn green-btn">
                        Substitution
                      </Button>
                    </Col>
                  </Row>
                </div>

                <div className="proof-opr-wrap">
                  <Row className="proof-oprs">
                    <Dropdown
                      as={Col}
                      className="d-inline proof-dropdown-btn proof-operations"
                    >
                      <Dropdown.Toggle id="dropdown-autoclose-true">
                        File Operations
                      </Dropdown.Toggle>

                      <Dropdown.Menu>
                        <Dropdown.Item onClick={exportJSON}>
                          Download Proof
                        </Dropdown.Item>
                        <Dropdown.Item href="#">Upload Proof</Dropdown.Item>
                        <Dropdown.Item href="#">Save Proof</Dropdown.Item>
                        <Dropdown.Item href="#">Submit Proof</Dropdown.Item>
                      </Dropdown.Menu>
                    </Dropdown>
                  </Row>
                </div>
              </div>
            )}
          </div>
        </Form>
      </Container>
    </MainLayout>
  );
};

export default InductionRacket;
