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
// import { useExportToLocalMachine } from "../hooks/useExportToLocalMachine"; // removed to clean warnings
import {
  Definitions,
  ProofComplete,
  // PersistentPad, // removed to clean warnings
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
    lHSGoal: "",
    rHSGoal: "",
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
  const [startPosition, _setStartPosition] = useState(0); // setStartPosition removed to clean warnings
  const [currentRacket, setCurrentRacket] = useState("");
  // const [
  //   ,
  //   addFieldWithApiCheck,
  //   ,
  //   validationErrors,
  //   serverError,
  //   racketErrors,
  //   deleteLastLine,
  //   updateShowSubstitution,
  //   showSubstitution,
  //   closeSubstitution,
  //   substituteFieldWithApiCheck,
  //   substitutionErrors,
  //   sendProofComplete
  // ] = useRacketRuleFields(
  //   startPosition,
  //   currentRacket,
  //   formValues.proofName,
  //   formValues.proofTag,
  //   showSide
  // ); // removed to clean warnings
  const [
    racketRuleFields,
    addFieldWithApiCheck,
    , // handleFieldChange
    , // validationErrors - removed to clean warnings
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
  const [inductiveHypothesisLHS, setInductiveHypothesisLHS] = useState("");
  const [inductiveHypothesisRHS, setInductiveHypothesisRHS] = useState("");
  const [isOffcanvasActive, toggleOffcanvas] = useOffcanvas();
  const [showDefinitionsWindow, toggleDefinitionsWindow] =
    useDefinitionsWindow();
  const [showProofComplete, setShowProofComplete] = useState(false);
  const [proofComplete, setProofComplete] = useState(false);
  const [leftPremise, setLeftPremise] = useState({});
  const [rightPremise, setRightPremise] = useState({});
  const [isAnchor, setIsAnchor] = useState(false);
  const [proofStarted, setProofStarted] = useState(false);

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
  // const convertFormToJSON = () => {
  //   let EquationalReasoningObject = {
  //     name: formValues.proofName,
  //     leftRacketsAndRules: racketRuleFields.LHS,
  //     rightRacketsAndRules: racketRuleFields.RHS
  //   };
  //
  //   return convertToJSON(EquationalReasoningObject);
  // }; // removed to clean warnings

  // const exportJSON = useExportToLocalMachine(
  //   formValues.proofName,
  //   convertFormToJSON
  // ); // removed to clean warnings

  // const handleHighlight = (startPosition) => {
  //   setStartPosition(startPosition);
  // }; // removed to clean warnings

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

    // keep currentRacket in sync with active side goal for payloads
    const sideGoal = showSide === "LHS" ? formValues.lHSGoal : formValues.rHSGoal;
    if (sideGoal !== undefined) {
      setCurrentRacket(sideGoal);
    }
  }, [formValues, showSide]); // added showSide to clean warnings

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
    let depth = 0;
    for (let i = 0; i < trimmed.length; i++) {
      const ch = trimmed[i];
      if (ch === "(") depth++;
      else if (ch === ")") depth--;
      if (depth === 0) {
        const inner = trimmed.slice(1, i).trim();
        if (inner.length === 0) return null;
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
    goalForSide,
    inductionVariable,
    inductionValue,
    leapVariable,
    inductionType,
    isAnchorFlag
  ) => {
    const leftGoal = formValues.lHSGoal;
    const rightGoal = formValues.rHSGoal;
    const selectedGoal = goalForSide || "";

    if (!/^\d+$/.test(inductionValue || "")) {
      toast.error("Anchor value must be a nonnegative integer.");
      return;
    }
    const parsedVal = parseInt(inductionValue, 10);
    if (isNaN(parsedVal) || parsedVal < 0) {
      toast.error("Anchor value must be a nonnegative integer.");
      return;
    }

    if (leapVariable && inductionVariable && leapVariable === inductionVariable) {
      toast.error("Leap variable must not overlap with variables in the goal.");
      return;
    }

    const leapVarWord = leapVariable ? `\\b${escapeRegExp(leapVariable)}\\b` : null;
    if (leapVarWord) {
      const re = new RegExp(leapVarWord);
      if (re.test(leftGoal) || re.test(rightGoal) || re.test(selectedGoal)) {
        toast.error("Leap variable must not overlap with variables in the goal.");
        return;
      }
    }

    const ivar = inductionVariable ? inductionVariable.trim() : "";
    if (!ivar) {
      toast.error("Induction variable must be a parameter of a function in your goal.");
      return;
    }

    const leftApp = parseTopLevelApplication(leftGoal);
    const rightApp = parseTopLevelApplication(rightGoal);
    const selectedApp = parseTopLevelApplication(selectedGoal);

    const appearsInParams = (app) => {
      if (!app || !app.params) return false;
      return app.params.some((p) => p === ivar);
    };

    if (
      !appearsInParams(leftApp) &&
      !appearsInParams(rightApp) &&
      !appearsInParams(selectedApp)
    ) {
      toast.error("Induction variable must be a parameter of a function in your goal.");
      return;
    }

    if (!inductiveHypothesisLHS || inductiveHypothesisLHS.trim() === "") {
      toast.error("Inductive hypothesis for LHS must be provided.");
      return;
    }

    if (!inductiveHypothesisRHS || inductiveHypothesisRHS.trim() === "") {
      toast.error("Inductive hypothesis for RHS must be provided.");
      return;
    }

    try {
      const inductionData = {
        side: side,
        proof_name: proofName,
        proof_tag: proofTag,
        lhs_leap_goal: formValues.lHSGoal,
        rhs_leap_goal: formValues.rHSGoal,
        lhs_anchor_goal: formValues.lHSGoal,
        rhs_anchor_goal: formValues.rHSGoal,
        induction_variable: inductionVariable,
        anchor_value: inductionValue,
        leap_variable: leapVariable,
        induction_type: inductionType,
        is_anchor: isAnchorFlag,
        inductive_hypothesis_lhs: inductiveHypothesisLHS,
        inductive_hypothesis_rhs: inductiveHypothesisRHS
      };

      console.log('=== SENDING INDUCTION DATA ===');
      console.log(inductionData);
      
      const response = await inductionService.startInductionProof(inductionData);
      
      console.log('=== RESPONSE RECEIVED ===');
      console.log('Status:', response.status);
      console.log('Data:', response.data);

      if (response && response.data) {
        if (response.status === 201 || response.status === 200) {
          const genericDef = response.data.generic_definition_created;
          
          if (genericDef) {
            let generics = [];
            try {
              const storedGenerics = sessionStorage.getItem('generics');
              generics = storedGenerics ? JSON.parse(storedGenerics) : [];
            } catch (e) {
              console.error('Error parsing generics:', e);
              generics = [];
            }
            
            const newGeneric = {
              id: genericDef.id || `generic_${Date.now()}`,
              label: genericDef.name,
              type: genericDef.type,
              notes: genericDef.description || `Generic variable for leap case in induction on ${inductionVariable}`,
              restrictions: {
                assumption: 'Non-negative',
                neverNull: false
              },
              enabled: true
            };
            
            const existingIndex = generics.findIndex(g => g.label === newGeneric.label);
            
            if (existingIndex >= 0) {
              generics[existingIndex] = newGeneric;
            } else {
              generics.push(newGeneric);
            }
            
            sessionStorage.setItem('generics', JSON.stringify(generics));
            
            const event = new CustomEvent('genericsUpdated', {
              detail: { 
                newGeneric: newGeneric,
                allGenerics: generics 
              }
            });
            window.dispatchEvent(event);
            
            toast.success(`Generic variable "${genericDef.name}" created for leap case`);
          }

          const proofId = response.data.proof_id || response.data.id;
          
          if (proofId) {
            toast.success('Induction proof started successfully!');
            sessionStorage.setItem('current_proof_id', proofId);
            
            // Set proof as started and current case
            setProofStarted(true);
            
            // Substitute the induction variable with anchor value in the premise
            const substitutedLHS = formValues.lHSGoal.replace(
              new RegExp(`\\b${inductionVariable}\\b`, 'g'),
              inductionValue
            );
            const substitutedRHS = formValues.rHSGoal.replace(
              new RegExp(`\\b${inductionVariable}\\b`, 'g'),
              inductionValue
            );
            
            // Update the premise with substituted values
            if (side === 'LHS') {
              setLeftPremise({
                racket: substitutedLHS,
                rule: "Premise",
                startPosition: 0
              });
            } else {
              setRightPremise({
                racket: substitutedRHS,
                rule: "Premise",
                startPosition: 0
              });
            }
          }
          
          // Call checkGoal to proceed
          checkGoal(
            side,
            proofName,
            proofTag,
            goalForSide,
            goalForSide,
            inductionVariable,
            inductionValue,
            leapVariable,
            inductionType,
            isAnchorFlag
          );
          
        } else {
          toast.error(`Server returned status: ${response.status}`);
        }
      } else {
        toast.error('No response data received from server');
      }
    } catch (error) {
      console.error('=== ERROR IN INDUCTION PROOF ===');
      console.error('Error object:', error);
      
      if (error.response) {
        console.error('Error response data:', error.response.data);
        console.error('Error response status:', error.response.status);
        
        const errorData = error.response.data;
        const errorMessage = errorData.error || errorData.details || 'Unknown server error';
        toast.error(`Failed to start induction proof: ${errorMessage}`);
      } else if (error.request) {
        console.error('No response received:', error.request);
        toast.error('Cannot connect to server. Please check your connection.');
      } else {
        console.error('Error message:', error.message);
        toast.error(`Error: ${error.message}`);
      }
      
      return;
    }
  };

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
              <Form.Group as={Col} md="6" className="er-proof-goal-lhs">
                <Form.Floating className="mb-3">
                  <Form.Control
                    id="eRProofLHSGoal"
                    name="lHSGoal"
                    type="text"
                    placeholder="LHS Goal"
                    value={formValues.lHSGoal}
                    onBlur={() => handleBlur("lHSGoal")}
                    onChange={enhancedHandleChange}
                    isInvalid={
                      !!validationMessages.lHSGoal ||
                      !!goalValidationMessage.LHS.Goal
                    }
                    required
                  />
                  <label htmlFor="eRProofLHSGoal">LHS Goal</label>
                  <Form.Control.Feedback type="invalid" tooltip>
                    {validationMessages.lHSGoal ||
                      goalValidationMessage.LHS.Goal}
                  </Form.Control.Feedback>
                </Form.Floating>
              </Form.Group>
              <Form.Group as={Col} md="6" className="er-proof-goal-rhs">
                <Form.Floating className="mb-3">
                  <Form.Control
                    id="eRProofRHSGoal"
                    name="rHSGoal"
                    type="text"
                    placeholder="RHS Goal"
                    value={formValues.rHSGoal}
                    onBlur={() => handleBlur("rHSGoal")}
                    onChange={enhancedHandleChange}
                    isInvalid={
                      !!validationMessages.rHSGoal ||
                      !!goalValidationMessage.RHS.Goal
                    }
                    required
                  />
                  <label htmlFor="eRProofRHSGoal">RHS Goal</label>
                  <Form.Control.Feedback type="invalid" tooltip>
                    {validationMessages.rHSGoal ||
                      goalValidationMessage.RHS.Goal}
                  </Form.Control.Feedback>
                </Form.Floating>
              </Form.Group>
            </Row>

            {!isAnchor && (
              <Row className="g-5">
                <Form.Group as={Col} md="5" className="er-inductive-hypothesis-lhs">
                  <Form.Floating className="mb-3">
                    <Form.Control
                      id="eRInductiveHypothesisLHS"
                      name="inductiveHypothesisLHS"
                      type="text"
                      placeholder="Inductive Hypothesis LHS"
                      value={inductiveHypothesisLHS}
                      onChange={(e) => setInductiveHypothesisLHS(e.target.value)}
                    />
                    <label htmlFor="eRInductiveHypothesisLHS">IH LHS</label>
                  </Form.Floating>
                </Form.Group>
                <Col md="2" className="d-flex align-items-center justify-content-center">
                  <span style={{ fontSize: '34px' }}>=</span>
                </Col>
                <Form.Group as={Col} md="5" className="er-inductive-hypothesis-rhs">
                  <Form.Floating className="mb-3">
                    <Form.Control
                      id="eRInductiveHypothesisRHS"
                      name="inductiveHypothesisRHS"
                      type="text"
                      placeholder="Inductive Hypothesis RHS"
                      value={inductiveHypothesisRHS}
                      onChange={(e) => setInductiveHypothesisRHS(e.target.value)}
                    />
                    <label htmlFor="eRInductiveHypothesisRHS">IH RHS</label>
                  </Form.Floating>
                </Form.Group>
              </Row>
            )}

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

            {!isAnchor && (
            <Form.Text
              as={"div"}
              id="formSeparator"
              className="form-separator"
              style={{ marginTop: '-10px' }}
            ></Form.Text> )}

            {isAnchor && (
            <Form.Text
              as={"div"}
              id="formSeparator"
              className="form-separator"
              style={{ marginTop: '10px' }}
            ></Form.Text> )}
          </div>

          <div className="form-bottom-part">

            <Row className="switch-btn-wrap" style={{ marginTop: '380.5px' }}>
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
                  {isAnchor ? "Switch to Leap Case" : "Switch to Base Case"}
                </Button>
              </Col>
            </Row>

            {!proofStarted && 
              !isGoalChecked[showSide]?.LeapGoal &&
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
                          ? formValues.lHSGoal
                          : formValues.rHSGoal,
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

              {proofStarted && (
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

                    {/* Rest of the racket-rule content stays the same */}
                    {showSide === "LHS" && (
                      <div className="racket-rule-lhs" id="racket-rule-lhs">
                        {/* LHS content */}
                      </div>
                    )}

                    {showSide === "RHS" && (
                      <div className="racket-rule-rhs" id="racket-rule-rhs">
                        {/* RHS content */}
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
                              const prevStart = showSide === "LHS" ? (leftPremise.startPosition ?? 0) : (rightPremise.startPosition ?? 0);
                              const prevRacket = showSide === "LHS" ? (leftPremise.racket || formValues.lHSGoal) : (rightPremise.racket || formValues.rHSGoal);
                              // ensure currentRacket is populated for payloads
                              setCurrentRacket(prevRacket);
                              addFieldWithApiCheck(showSide, "", prevStart, prevRacket);
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

                  {/* <div className="proof-opr-wrap">
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
                  </div> */}
                </div>
              )}
          </div>
        </Form>
      </Container>
    </MainLayout>
  );
};

export default InductionRacket;
