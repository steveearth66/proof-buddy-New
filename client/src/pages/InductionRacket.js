import React, { useState, useEffect } from "react";
import Dropdown from "react-bootstrap/Dropdown";
import Button from "react-bootstrap/Button";
import Container from "react-bootstrap/Container";
import Form from "react-bootstrap/Form";
import Col from "react-bootstrap/Col";
import Row from "react-bootstrap/Row";
import Alert from "react-bootstrap/Alert";
import { toast } from "react-toastify";
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
import {
  Definitions,
  ProofComplete,
  PersistentPad,
  Substitution
} from "../components";
import { useDefinitionsWindow } from "../hooks/useDefinitionsWindow";
import inductionService from "../services/inductionService";

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
    leapVariable: "",
    inductionType: "integers"
  };

  const [showSide, toggleSide] = useToggleSide();
  const [formValues, handleChange] = useInputState(initialValues);
  const [validationMessages, handleBlur, setAllTouched, isFormValid] =
    useFormValidation(formValues, validateField);
  const [validated, setValidated] = useState(false);
  const {
    isGoalChecked,
    checkGoal,
    goalValidationMessage,
    enhancedHandleChange,
    proofValidationMessage,
    clearProofValidationMessage
  } = useInductionCheck(handleChange);
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
    updateShowSubstitution,
    showSubstitution,
    closeSubstitution,
    substituteFieldWithApiCheck,
    substitutionErrors,
    sendProofComplete
  ] = useRacketRuleFields(
    startPosition,
    currentRacket,
    formValues.proofName,
    formValues.proofTag,
    showSide
  );
  const [currentLHS, currentRHS] = useCurrentRacketValues(racketRuleFields, formValues, isGoalChecked);
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
    convertFormToJSON
  );

  const handleHighlight = (startPosition) => {
    setStartPosition(startPosition);
  };

  useEffect(() => {
    sessionStorage.removeItem("highlights");
    sessionStorage.removeItem("definitions");

    const clearProof = async () => {
      await inductionService.clearInduction();
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

    const sendProofComplete = async () => {};

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

  /**
   * Parse a top-level function application like "(f x y)".
   * Returns { name: 'f', params: ['x','y'] } or null if not a simple paren application.
   */
  const parseTopLevelApplication = (s) => {
    if (!s) return null;
    const trimmed = s.trim();
    if (!trimmed.startsWith("(")) return null;
    // Find matching top-level ) for the first '('
    let depth = 0;
    for (let i = 0; i < trimmed.length; i++) {
      const ch = trimmed[i];
      if (ch === "(") depth++;
      else if (ch === ")") depth--;
      if (depth === 0) {
        // take substring from 1 to i-1
        const inner = trimmed.slice(1, i).trim();
        if (inner.length === 0) return null;
        // split by whitespace but keep symbols intact
        const tokens = inner.split(/\s+/);
        if (tokens.length >= 1) {
          const name = tokens[0];
          const params = tokens.slice(1);
          return { name, params };
        }
        return null;
      }
    }
    return null;
  };

  /**
   * Validates:
   * - induction variable is a parameter of a (top-level) function in LHS or RHS goal
   * - anchor/induction value is a nonnegative integer
   * - leap variable does not appear in LHS, RHS, or equal induction variable
   *
   * On success, calls checkGoal(...) to proceed.
   *
   * Uses exact error messages requested:
   * "Induction variable must be a parameter of a function in your goal."
   * "Anchor value must be a nonnegative integer."
   * "Leap variable must not overlap with variables in the goal."
   */
  const validateAndStart = async (
    side,
    proofName,
    proofTag,
    leapGoalForSide,
    anchorGoalForSide,
    inductionVariable,
    inductionValue,
    leapVariable,
    inductionType,
    isAnchorFlag
  ) => {
    // Determine which goal strings to check based on the side and isAnchorFlag
    const leftGoal = isAnchorFlag
      ? formValues.lHSAnchorGoal
      : formValues.lHSLeapGoal;
    const rightGoal = isAnchorFlag
      ? formValues.rHSAnchorGoal
      : formValues.rHSLeapGoal;

    // Choose the side-specific goals passed in (these args are same as existing checkGoal)
    const selectedLeapGoal = leapGoalForSide || "";
    const selectedAnchorGoal = anchorGoalForSide || "";

    // 1) Validate inductionValue is a nonnegative integer
    if (!/^\d+$/.test(inductionValue || "")) {
      toast.error("Anchor value must be a nonnegative integer.");
      return;
    }
    const parsedVal = parseInt(inductionValue, 10);
    if (isNaN(parsedVal) || parsedVal < 0) {
      toast.error("Anchor value must be a nonnegative integer.");
      return;
    }

    // 2) Validate leapVariable does not appear in LHS, RHS, or equal inductionVariable
    if (leapVariable && inductionVariable && leapVariable === inductionVariable) {
      toast.error("Leap variable must not overlap with variables in the goal.");
      return;
    }

    const leapVarWord = leapVariable ? `\\b${escapeRegExp(leapVariable)}\\b` : null;
    if (leapVarWord) {
      const re = new RegExp(leapVarWord);
      // Check both side goals (the "goal" strings visible in form)
      if (re.test(leftGoal) || re.test(rightGoal) || re.test(selectedLeapGoal) || re.test(selectedAnchorGoal)) {
        toast.error("Leap variable must not overlap with variables in the goal.");
        return;
      }
    }

    // 3) Validate inductionVariable appears as a parameter of a (top-level) function in either LHS or RHS goal
    const ivar = inductionVariable ? inductionVariable.trim() : "";
    if (!ivar) {
      toast.error("Induction variable must be a parameter of a function in your goal.");
      return;
    }

    const leftApp = parseTopLevelApplication(leftGoal);
    const rightApp = parseTopLevelApplication(rightGoal);
    const leapApp = parseTopLevelApplication(selectedLeapGoal);
    const anchorApp = parseTopLevelApplication(selectedAnchorGoal);

    const appearsInParams = (app) => {
      if (!app || !app.params) return false;
      return app.params.some((p) => p === ivar);
    };

    // Check any of the parsed top-level applications for the induction variable as a parameter
    if (
      !appearsInParams(leftApp) &&
      !appearsInParams(rightApp) &&
      !appearsInParams(leapApp) &&
      !appearsInParams(anchorApp)
    ) {
      toast.error("Induction variable must be a parameter of a function in your goal.");
      return;
    }

    try {
    const inductionData = {
      side: side,
      proof_name: proofName,
      proof_tag: proofTag,
      lhs_leap_goal: formValues.lHSLeapGoal,
      rhs_leap_goal: formValues.rHSLeapGoal,
      lhs_anchor_goal: formValues.lHSAnchorGoal,
      rhs_anchor_goal: formValues.rHSAnchorGoal,
      induction_variable: inductionVariable,
      anchor_value: inductionValue,
      leap_variable: leapVariable,
      induction_type: inductionType,
      is_anchor: isAnchorFlag
    };

    console.log('Sending induction data to backend:', inductionData);
    
    const response = await inductionService.startInductionProof(inductionData);
    console.log('Backend response:', response);
    
    if (response.data && response.data.proof_id) {
      toast.success('Induction proof started successfully!');
      sessionStorage.setItem('current_proof_id', response.data.proof_id);
    } else {
      toast.error('Unexpected response from server');
    }
    
  } catch (error) {
    console.error('Error sending induction data:', error);
    
    if (error.response && error.response.data) {
      const errorData = error.response.data;
      toast.error(`Failed to start induction proof: ${errorData.error || 'Unknown error'}`);
    } else {
      toast.error('Failed to connect to server');
    }
  }

    // All validations passed — proceed to call existing checkGoal
    checkGoal(
      side,
      proofName,
      proofTag,
      leapGoalForSide,
      anchorGoalForSide,
      inductionVariable,
      inductionValue,
      leapVariable,
      inductionType,
      isAnchorFlag
    );
  };

  // small helper to escape regex special chars
  const escapeRegExp = (string) => {
    return string.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  };

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

        {showSubstitution && (
          <Substitution
            show={showSubstitution}
            handleClose={() => closeSubstitution()}
            racketRuleFields={racketRuleFields[showSide]}
            handleSubstitution={substituteFieldWithApiCheck}
            errors={substitutionErrors}
          />
        )}

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
                  type="radio"
                  id="integers"
                  label="Integers"
                  name="inductionType"
                  value="integers"
                  onChange={handleChange}
                  defaultChecked
                />
                <Form.Check
                  type="radio"
                  id="lists"
                  label="Lists"
                  name="inductionType"
                  value="lists"
                  onChange={handleChange}
                  disabled
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
                      clearProofValidationMessage();
                    }}
                    onChange={handleChange}
                    isInvalid={
                      !!validationMessages.proofName ||
                      !!proofValidationMessage.name
                    }
                    required
                  />
                  <label htmlFor="eRProofName">Name</label>
                  <Form.Control.Feedback type="invalid" tooltip>
                    {validationMessages.proofName ||
                      proofValidationMessage.name}
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
                      clearProofValidationMessage();
                    }}
                    onChange={handleChange}
                    isInvalid={
                      !!proofValidationMessage.tag || !!validationMessages.tag
                    }
                    required
                  />
                  <label htmlFor="eRProofTag"># Tag</label>
                  <Form.Control.Feedback type="invalid" tooltip>
                    {proofValidationMessage.tag || validationMessages.tag}
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
                    onBlur={() => {
                      handleBlur("inductionVariable");
                      clearProofValidationMessage();
                    }}
                    onChange={handleChange}
                    isInvalid={
                      !!validationMessages.inductionVariable ||
                      !!proofValidationMessage.inductionVariable
                    }
                    required
                  />
                  <label htmlFor="eRInductionVariable">IVar</label>
                  <Form.Control.Feedback type="invalid" tooltip>
                    {validationMessages.inductionVariable ||
                      proofValidationMessage.inductionVariable}
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
                    onBlur={() => {
                      handleBlur("inductionValue");
                      clearProofValidationMessage();
                    }}
                    onChange={handleChange}
                    isInvalid={
                      !!validationMessages.inductionValue ||
                      !!proofValidationMessage.inductionValue
                    }
                    required
                  />
                  <label htmlFor="eRInductionValue">AVal</label>
                  <Form.Control.Feedback type="invalid" tooltip>
                    {validationMessages.inductionValue ||
                      proofValidationMessage.inductionValue}
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
                    onBlur={() => {
                      handleBlur("leapVariable");
                      clearProofValidationMessage();
                    }}
                    onChange={handleChange}
                    isInvalid={
                      !!validationMessages.leapVariable ||
                      !!proofValidationMessage.leapVariable
                    }
                    required
                  />
                  <label htmlFor="eRLeapVariable">LVar</label>
                  <Form.Control.Feedback type="invalid" tooltip>
                    {validationMessages.leapVariable ||
                      proofValidationMessage.leapVariable}
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
                  <Dropdown.Item href="#">IH</Dropdown.Item>
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
                        onChange={enhancedHandleChange}
                        isInvalid={
                          !!validationMessages.lHSAnchorGoal ||
                          !!goalValidationMessage.LHS.AnchorGoal
                        }
                        required
                      />
                      <label htmlFor="eRProofLHSAnchor">LHS Anchor Goal</label>
                      <Form.Control.Feedback type="invalid" tooltip>
                        {validationMessages.lHSAnchorGoal ||
                          goalValidationMessage.LHS.AnchorGoal}
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
                        onChange={enhancedHandleChange}
                        isInvalid={
                          !!validationMessages.rHSAnchorGoal ||
                          !!goalValidationMessage.RHS.AnchorGoal
                        }
                        required
                      />
                      <label htmlFor="eRProofRHSAnchorGoal">
                        RHS Anchor Goal
                      </label>
                      <Form.Control.Feedback type="invalid" tooltip>
                        {validationMessages.rHSAnchorGoal ||
                          goalValidationMessage.RHS.AnchorGoal}
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
                        onBlur={() => handleBlur("lHSLeapGoal")}
                        onChange={enhancedHandleChange}
                        isInvalid={
                          !!validationMessages.lHSLeapGoal ||
                          !!goalValidationMessage.LHS.LeapGoal
                        }
                        required
                      />
                      <label htmlFor="eRProofLHSLeapGoal">LHS Leap Goal</label>
                      <Form.Control.Feedback type="invalid" tooltip>
                        {validationMessages.lHSLeapGoal ||
                          goalValidationMessage.LHS.LeapGoal}
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
                        value={formValues.rHSLeapGoal}
                        onBlur={() => handleBlur("rHSLeapGoal")}
                        onChange={enhancedHandleChange}
                        isInvalid={
                          !!validationMessages.rHSLeapGoal ||
                          !!goalValidationMessage.RHS.LeapGoal
                        }
                        required
                      />
                      <label htmlFor="eRProofRHSLeapGoal">RHS Leap Goal</label>
                      <Form.Control.Feedback type="invalid" tooltip>
                        {validationMessages.rHSLeapGoal ||
                          goalValidationMessage.RHS.LeapGoal}
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
                    value={lhsValue || currentLHS}
                    onChange={(e) => setLhsValue(e.target.value)}
                    onFocus={(e) => {
                      if (showSide !== "LHS") {
                        e.target.blur();
                        return;
                      }
                      if (!lhsValue && currentLHS) {
                        setLhsValue(currentLHS);
                      }
                    }}
                    style={{ cursor: showSide === "LHS" ? "text" : "not-allowed" }}
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
                    value={rhsValue || currentRHS}
                    onChange={(e) => setRhsValue(e.target.value)}
                    onFocus={(e) => {
                      if (showSide !== "RHS") {
                        e.target.blur();
                        return;
                      }
                      if (!rhsValue && currentRHS) {
                        setRhsValue(currentRHS);
                      }
                    }}
                    style={{ cursor: showSide === "RHS" ? "text" : "not-allowed" }}
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

            {!isGoalChecked[showSide]?.LeapGoal &&
              !isGoalChecked[showSide]?.AnchorGoal && (
                <Row className="goal-btn-wrap">
                  <Button
                    className="orange-btn"
                    onClick={() =>
                      validateAndStart(
                        showSide,
                        formValues.proofName,
                        formValues.proofTag,
                        showSide === "LHS"
                          ? formValues.lHSLeapGoal
                          : formValues.rHSLeapGoal,
                        showSide === "LHS"
                          ? formValues.lHSAnchorGoal
                          : formValues.rHSAnchorGoal,
                        formValues.inductionVariable,
                        formValues.inductionValue,
                        formValues.leapVariable,
                        formValues.inductionType,
                        isAnchor
                      )
                    }
                  >
                    Start Induction Proof
                  </Button>
                </Row>
              )}

            {[isGoalChecked][showSide]?.LeapGoal &&
              isGoalChecked[showSide]?.AnchorGoal && (
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
                            startPosition={0}
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
                                startPosition={0}
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
                            startPosition={0}
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
                                startPosition={0}
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
                        <Button
                          className="orange-btn green-btn"
                          onClick={() => updateShowSubstitution()}
                        >
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
                          <Dropdown.Item onClick={exportJSON()}>
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
