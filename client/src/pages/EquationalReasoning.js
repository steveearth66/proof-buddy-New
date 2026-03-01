import React, { useState, useRef, useCallback } from "react";
import Dropdown from "react-bootstrap/Dropdown";
import Button from "react-bootstrap/Button";
import Container from "react-bootstrap/Container";
import Form from "react-bootstrap/Form";
import Col from "react-bootstrap/Col";
import Row from "react-bootstrap/Row";
import { toast } from "react-toastify";
import MainLayout from "../layouts/MainLayout";
import equationalService from "../services/equationalService";
import { ProofComplete, Substitution, PersistentPad, RacketInput } from "../components";
import { useParenHighlight } from "../hooks/useParenHighlight";
import ClickableRowNumber from "../components/ClickableRowNumber";
import "../scss/_forms.scss";
import "../scss/_er-racket.scss";

import Alert from "react-bootstrap/Alert";
import { useInputState } from "../hooks/useInputState";
import { useGoalCheck } from "../hooks/useGoalCheck";
import { useRacketRuleFields } from "../hooks/useRacketRuleFields";
import { useFormValidation } from "../hooks/useFormValidation";
import validateField from "../utils/eRFormValidationUtils";

import OffcanvasRuleSet from "../components/OffcanvasRuleSet";
import { useOffcanvas } from "../hooks/useOffcanvas";
import { useDefinitionsWindow } from "../hooks/useDefinitionsWindow";
import { useDynamicHeight } from "../hooks/useDynamicHeight";

import {
  Definitions
} from "../components";

import {
  ARROW_KEYS,
  INITIAL_FORM_VALUES,
  INITIAL_PREMISE_STATE,
  EMPTY_INITIAL_FIELD,
  getPadRefs,
  getPadIndex,
  isFormComplete,
  convertFormToJSON,
  clearSessionData,
  updatePremises
} from "../utils/erRacketUtils";

/**
 * EquationalReasoning - Full-featured component with 3-pane layout
 * Header | Middle (proof lines) | Footer (binding pane)
 */
const EquationalReasoning = () => {
  // Current values (computed from last line)
  const [currentLHS, setCurrentLHS] = useState("");
  const [currentRHS, setCurrentRHS] = useState("");
  
  // Proof state
  const [proofStarted, setProofStarted] = useState(false);
  const [showSide, setShowSide] = useState("LHS");
  const [racketFields, setRacketFields] = useState({
    LHS: [],
    RHS: []
  });
  
  // Footer binding state
  const [userRow, setUserRow] = useState({ num: "" });
  const [isBound, setIsBound] = useState(false);
  const [footerRule, setFooterRule] = useState("");
  
  // UI state
  const [showSubstitution, setShowSubstitution] = useState(false);
  const [showProofComplete, setShowProofComplete] = useState(false);
  const [errors, setErrors] = useState([]);
  
  // Refs
  const lhsPadRefs = useRef([]);
  const rhsPadRefs = useRef([]);
  const footerPadRef = useRef(null);
  
  // Start proof
  const handleStartProof = async (e) => {
    e.preventDefault();
    setErrors([]);
    
    if (!formValues.lHSGoal.trim() || !formValues.rHSGoal.trim()) {
      setErrors(["Both LHS and RHS goals are required"]);
      return;
    }
    
    if (formValues.lHSGoal.trim() === formValues.rHSGoal.trim()) {
      setErrors(["LHS and RHS goals cannot be identical"]);
      return;
    }
    
    try {
      const response = await equationalService.setCurrentProof({
        lhsPremise: formValues.lHSGoal.trim(),
        rhsPremise: formValues.rHSGoal.trim(),
        definitions: []
      });
      
      if (response.isValid) {
        setRacketFields({
          LHS: [{
            racket: formValues.lHSGoal.trim(),
            rule: "Premise",
            lineNumber: 0,
            selectedNode: 0,
            startPosition: 0,
            jsonTree: response.lhsJsonTree || {}
          }],
          RHS: [{
            racket: formValues.rHSGoal.trim(),
            rule: "Premise",
            lineNumber: 0,
            selectedNode: 0,
            startPosition: 0,
            jsonTree: response.rhsJsonTree || {}
          }]
        });
        
        setCurrentLHS(formValues.lHSGoal.trim());
        setCurrentRHS(formValues.rHSGoal.trim());
        setProofStarted(true);
        toast.success("Proof started!");
      } else {
        setErrors(response.errors || ["Failed to start proof"]);
      }
    } catch (error) {
      console.error("Error starting proof:", error);
      setErrors(["Error starting proof"]);
    }
  };
  
  // Toggle side
  const handleToggleSide = () => {
    const newSide = showSide === "LHS" ? "RHS" : "LHS";
    setShowSide(newSide);
    unbindFooter();
  };
  
  // Bind footer to line number
  const bindFooterToRow = useCallback((rowNum) => {
    const paddedRowNum = rowNum.toString().padStart(3, "0");
    const lineIndex = parseInt(paddedRowNum, 10);
    
    // Check if line exists
    const fields = racketFields[showSide];
    if (lineIndex >= fields.length) {
      toast.error("Invalid line number");
      return;
    }
    
    setUserRow({ num: paddedRowNum });
    setIsBound(true);
    
    const field = fields[lineIndex];
    setFooterRule(field?.rule || "");
  }, [showSide, racketFields]);
  
  // Unbind footer
  const unbindFooter = useCallback(() => {
    setUserRow({ num: "" });
    setIsBound(false);
    setFooterRule("");
  }, []);
  
  // Handle row number click
  const handleRowNumberClick = (rowNum) => {
    if (!isBound) {
      bindFooterToRow(rowNum);
    }
  };
  
  // Handle field highlight
  const handleFieldHighlight = (side, lineIndex, selectedNode) => {
    setRacketFields(prev => {
      const updatedFields = [...prev[side]];
      if (updatedFields[lineIndex]) {
        updatedFields[lineIndex] = {
          ...updatedFields[lineIndex],
          selectedNode: selectedNode,
          startPosition: selectedNode
        };
      }
      return { ...prev, [side]: updatedFields };
    });
  };
  
  // Generate & Check
  const handleGenerateAndCheck = async () => {
    if (!isBound) {
      toast.error("Please bind to a line first");
      return;
    }
    
    if (!footerRule.trim()) {
      toast.error("Please enter a rule");
      return;
    }
    
    const lineIndex = parseInt(userRow.num, 10);
    const fields = racketFields[showSide];
    const sourceLine = fields[lineIndex];
    
    if (!sourceLine?.racket) {
      toast.error("No expression to apply rule to");
      return;
    }
    
    const selectedNode = footerPadRef.current?.getSelected?.() ?? sourceLine.selectedNode ?? 0;
    
    try {
      const response = await equationalService.applyRule({
        side: showSide,
        currentRacket: sourceLine.racket,
        rule: footerRule.trim(),
        startPosition: selectedNode,
        selectedNode: selectedNode,
        lineNumber: lineIndex
      });
      
      if (response.isValid) {
        const updatedFields = [...fields];
        const newLine = {
          racket: response.racket,
          rule: footerRule.trim(),
          lineNumber: lineIndex + 1,
          selectedNode: 0,
          startPosition: 0,
          jsonTree: response.jsonTree || {}
        };
        
        updatedFields.splice(lineIndex + 1, 0, newLine);
        
        setRacketFields({
          ...racketFields,
          [showSide]: updatedFields
        });
        
        // Update current value
        if (showSide === "LHS") {
          setCurrentLHS(response.racket);
        } else {
          setCurrentRHS(response.racket);
        }
        
        // Bind to new line
        bindFooterToRow(lineIndex + 1);
        setFooterRule("");
        toast.success("Rule applied!");
      } else {
        setErrors(response.errors || ["Failed to apply rule"]);
        toast.error(response.errors?.[0] || "Failed to apply rule");
      }
    } catch (error) {
      console.error("Error applying rule:", error);
      toast.error("Error applying rule");
    }
  };
  
  // Handle substitution
  const handleSubstitution = async (substitutionData) => {
    const { rule, substitution } = substitutionData;
    
    if (!isBound) {
      toast.error("Please bind to a line first");
      return;
    }
    
    const lineIndex = parseInt(userRow.num, 10);
    const fields = racketFields[showSide];
    const targetLine = fields[lineIndex];
    
    if (!targetLine) {
      toast.error("Invalid line selected");
      return;
    }
    
    const selectedNode = footerPadRef.current?.getSelected?.() ?? targetLine.selectedNode ?? 0;
    
    try {
      const response = await equationalService.substitution({
        side: showSide,
        currentRacket: targetLine.racket,
        rule: rule.trim(),
        substitution: substitution.trim(),
        startPosition: selectedNode,
        selectedNode: selectedNode,
        lineNumber: lineIndex
      });
      
      if (response.isValid) {
        const updatedFields = [...fields];
        const newLine = {
          racket: response.racket,
          rule: rule.trim(),
          lineNumber: lineIndex + 1,
          selectedNode: 0,
          startPosition: 0,
          jsonTree: response.jsonTree || {}
        };
        
        updatedFields.splice(lineIndex + 1, 0, newLine);
        
        setRacketFields({
          ...racketFields,
          [showSide]: updatedFields
        });
        
        if (showSide === "LHS") {
          setCurrentLHS(response.racket);
        } else {
          setCurrentRHS(response.racket);
        }
        
        setShowSubstitution(false);
        bindFooterToRow(lineIndex + 1);
        toast.success("Substitution applied!");
      } else {
        setErrors(response.errors || ["Failed to apply substitution"]);
        toast.error(response.errors?.[0] || "Failed to apply substitution");
      }
    } catch (error) {
      console.error("Error applying substitution:", error);
      toast.error("Error applying substitution");
    }
  };
  
  // Clear line
  const handleClearLine = async () => {
    if (!isBound) {
      toast.error("Please bind to a line first");
      return;
    }
    
    const lineIndex = parseInt(userRow.num, 10);
    
    if (lineIndex === 0) {
      toast.error("Cannot clear premise line");
      return;
    }
    
    try {
      await equationalService.deleteLine(showSide, lineIndex);
      
      const updatedFields = [...racketFields[showSide]];
      updatedFields[lineIndex] = {
        ...updatedFields[lineIndex],
        racket: "",
        rule: "",
        jsonTree: {}
      };
      
      setRacketFields({
        ...racketFields,
        [showSide]: updatedFields
      });
      
      unbindFooter();
      toast.success("Line cleared");
    } catch (error) {
      console.error("Error clearing line:", error);
      toast.error("Error clearing line");
    }
  };
  
  // Check completion
  const handleCheckCompletion = async () => {
    try {
      const response = await equationalService.checkCompletion();
      
      if (response.isComplete) {
        setShowProofComplete(true);
        toast.success("Proof complete! 🎉");
      } else {
        toast.info(response.message || "Proof incomplete");
      }
    } catch (error) {
      console.error("Error checking completion:", error);
      toast.error("Error checking completion");
    }
  };
  
  // Render footer pad
  const renderFooterPad = () => {
    if (!userRow.num) return null;
    
    const lineIndex = parseInt(userRow.num, 10);
    const field = racketFields[showSide][lineIndex];
    if (!field) return null;
    
    return (
      <PersistentPad
        ref={footerPadRef}
        equation={field.racket || ""}
        side={showSide}
        jsonTree={field.jsonTree || {}}
        lineNum={lineIndex}
        startPosition={field.selectedNode ?? 0}
        resultNode={field.resultNode}
        onHighlightChange={() => {}}
        ruleValue={footerRule}
        onRuleChange={(e) => setFooterRule(e.target.value.trim())}
        isRuleReadOnly={false}
        rulePlaceholder={`${showSide} Rule`}
        isRuleInvalid={false}
        ruleValidationError=""
        isEditRow={true}
      />
    );
  };

  const [proofComplete, setProofComplete] = useState(false);
  const [isOffcanvasActive, toggleOffcanvas] = useOffcanvas();  
  const [showDefinitionsWindow, toggleDefinitionsWindow] =
      useDefinitionsWindow();

  const [basePremises, setBasePremises] = useState({ LHS: {}, RHS: {} });

  const [baseRacketFields, setBaseRacketFields] = useState({
    LHS: [EMPTY_INITIAL_FIELD],
    RHS: [EMPTY_INITIAL_FIELD]
  });

  const racketRuleFields = baseRacketFields;

  const [leftPremise, setLeftPremise] = useState(INITIAL_PREMISE_STATE);
  const [rightPremise, setRightPremise] = useState(INITIAL_PREMISE_STATE);

  /**
   * Handle premise highlighting change.
   * Updates the premise's selectedNode so highlighting persists across toggles.
   */
  const handlePremiseHighlight = (side, selectedNode) => {
    const setPremises = setBasePremises;
    
    setPremises(prev => ({
      ...prev,
      [side]: {
        ...prev[side],
        selectedNode: selectedNode || 0
      }
    }));
  };

  // Hook for getting available height for scrollable proof area
  const availableHeight = useDynamicHeight();

  const [formValues, handleChange] = useInputState(INITIAL_FORM_VALUES);
  
  // Parenthesis highlighting hooks
  const { 
    highlightPositions: lhsGoalHighlights, 
    inputRef: lhsGoalRef, 
    handleKeyUp: lhsGoalKeyUp, 
    handleSelect: lhsGoalSelect 
  } = useParenHighlight(formValues.lHSGoal);
  
  const { 
    highlightPositions: rhsGoalHighlights, 
    inputRef: rhsGoalRef, 
    handleKeyUp: rhsGoalKeyUp, 
    handleSelect: rhsGoalSelect 
  } = useParenHighlight(formValues.rHSGoal);
  const [
    isGoalChecked,
    checkGoal,
    goalValidationMessage,
    enhancedHandleChange,
    proofValidationMessage,
    clearProofValidationMessage,
    loadRacketGoal,
    jsonTreeRep
  ] = useGoalCheck(handleChange);
  const [currentRacket, setCurrentRacket] = useState("");
  const [
    ,
    addFieldWithApiCheck,
    ,
    validationErrors,
    serverError,
    racketErrors,
    ,
    updateShowSubstitution,
    ,
    closeSubstitution,
    substituteFieldWithApiCheck,
    substitutionErrors,
    loadProofInServer
  ] = useRacketRuleFields(
    0, // Default startPosition since we now get it from pad refs
    currentRacket,
    formValues.proofName,
    formValues.proofTag,
    showSide
  );

const [validationMessages, handleBlur, setAllTouched, isFormValid] =
    useFormValidation(formValues, validateField);

function renderPersistentPadRow({
  side,
  index = 0,
  field = {},
  isPremise = false,
  padRefs,
  formValues,
  jsonTreeRep,
  handleFieldHighlight,
  validationErrors,
  isBound,
  userRow,
  handleRowNumberClick,
  leftPremise,
  rightPremise
}) {
  // Compute values based on side and isPremise
  const isLHS = side === "LHS";
  const padIndex = isPremise ? 0 : index + 1;
  const equation = isPremise
    ? formValues[isLHS ? "lHSGoal" : "rHSGoal"]
    : field.racket;
  const jsonTree = isPremise
    ? jsonTreeRep[side]
    : field.jsonTree || jsonTreeRep[side];
  const lineNum = isPremise ? 0 : index + 1;
  const ruleValue = isPremise ? "Premise" : field.rule;
  const rulePlaceholder = isPremise ? `${side} Premise` : `${side} Rule`;
  const isRuleInvalid = !isPremise && !!validationErrors[side][index];
  const ruleValidationError = validationErrors[side][index];

  // Get the correct startPosition
  // const startPosition = isPremise
  //   ? (isLHS ? leftPremise.startPosition || 0 : rightPremise.startPosition || 0)
  //   : (field.startPosition || 0);
  // Prefer selectedNode (persisted) over startPosition; hard fallback to 0
    // Show target highlight if:
    // 1. User is currently bound to the next line, OR
    // 2. The next line has already been generated (has content)
    const boundPadIndex = isBound ? parseInt(userRow.num, 10) : -1;
  const isUserBoundToNextLine = boundPadIndex === padIndex + 1;
  let startPosition;
    if (isPremise) {
      // For premise, check if line 1 exists with content OR user is bound to line 1
      const nextLineHasContent = racketRuleFields[side] && racketRuleFields[side][1]?.racket;
      const showHighlight = nextLineHasContent || isUserBoundToNextLine;
      startPosition = showHighlight
        ? (isLHS
          ? (leftPremise && (leftPremise.selectedNode ?? leftPremise.startPosition)) ?? 0
          : (rightPremise && (rightPremise.selectedNode ?? rightPremise.startPosition)) ?? 0)
        : undefined;
    } else {
      // For regular lines, check if next line has content OR user is bound to it
      const nextLineHasContent = racketRuleFields[side] && racketRuleFields[side][index + 1]?.racket;
      const showHighlight = nextLineHasContent || isUserBoundToNextLine;
      startPosition = showHighlight
        ? ((field && (field.selectedNode ?? field.startPosition)) ?? 0)
        : undefined;
    }

  const resultNodeValue = isPremise ? undefined : (field && field.resultNode);

  return (
    <Row className="racket-rule-row" id={`racket-row-${padIndex}`} key={isPremise ? `premise-${side}` : `${side}-field-${padIndex}`}>
      <Col xs="auto" style={{ minWidth: '50px', paddingRight: '5px', position: 'relative', top: '35px' }}>
        <ClickableRowNumber
          padIndex={padIndex}
          isClickable={!isBound}
          isSelected={isBound && padIndex === parseInt(userRow.num, 10)}
          onClick={() => handleRowNumberClick(padIndex)}
          title={!isBound ? 'Click to bind to footer' : ''}
        />
      </Col>
      <Col>
        <PersistentPad
          ref={el => { padRefs.current[padIndex] = el; }}
          side={side}
          equation={equation}
          jsonTree={jsonTree}
          lineNum={lineNum}
          startPosition={startPosition}
          resultNode={resultNodeValue}
          onHighlightChange={selected => handleFieldHighlight(isLHS, lineNum, selected)}
          ruleValue={ruleValue}
          onRuleChange={() => {}}
          isRuleReadOnly={true}
          rulePlaceholder={rulePlaceholder}
          isRuleInvalid={isRuleInvalid}
          ruleValidationError={ruleValidationError}
          isEditRow={false}
        />
      </Col>
    </Row>
  );
}

  return (
    <MainLayout>
      <Container 
        fluid 
        className="er-racket-container" 
        style={{ width: '100%', maxWidth: '100%' }}>
        <OffcanvasRuleSet
          isActive={isOffcanvasActive}
          toggleFunction={toggleOffcanvas}
        ></OffcanvasRuleSet>
        {showDefinitionsWindow && (
          <Definitions toggleDefinitionsWindow={toggleDefinitionsWindow} />
        )}

        {proofComplete && <ProofComplete onDismiss={() => setProofComplete(false)} />}
        
        {/* Header Pane - Proof Parameters */}
        <Form onSubmit={handleStartProof} className="er-racket-form">
          <div className="form-top-section">
            <Row className="page-header-row" style={{ alignItems: 'center' }}>
              <Col xs="auto">
                <h1 style={{ marginBottom: 0 }}>Equational Reasoning</h1>
              </Col>
              <Form.Group as={Col} md="3" className="er-proof-name">
                <Form.Floating className="mb-3">
                  <Form.Control
                    id="eRProofName"
                    name="proofName"
                    type="text"
                    placeholder="Name"
                    value={formValues.proofName}
                    onBlur={() => {
                      handleBlur("proofName");
                      clearProofValidationMessage();
                    }}
                    onChange={handleChange}
                    disabled={proofStarted}
                  />
                  <label htmlFor="eRProofName"># Name</label>
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
                    placeholder="Tag"
                    value={formValues.proofTag}
                    onBlur={() => {
                      handleBlur("proofTag");
                      clearProofValidationMessage();
                    }}
                    onChange={handleChange}
                    isInvalid={!!proofValidationMessage.tag}
                    disabled={proofStarted}
                  />
                  <label htmlFor="eRProofTag"># Tag</label>
                  <Form.Control.Feedback type="invalid" tooltip>
                    {proofValidationMessage.tag}
                  </Form.Control.Feedback>
                </Form.Floating>
              </Form.Group>
            </Row>
          
            <Row className="g-5">
              <Form.Group as={Col} md="4" className="er-proof-goal-lhs" style={{ marginLeft: '450px' }}>
                <div className="mb-3">
                  <label htmlFor="eRProofLHSGoal" className="form-label">LHS Goal</label>
                  <RacketInput
                    id="eRProofLHSGoal"
                    name="lHSGoal"
                    type="text"
                    placeholder="LHS Goal"
                    value={formValues.lHSGoal}
                    onBlur={() => handleBlur("lHSGoal")}
                    onChange={enhancedHandleChange}
                    onKeyUp={lhsGoalKeyUp}
                    onClick={lhsGoalSelect}
                    ref={lhsGoalRef}
                    highlightPositions={lhsGoalHighlights}
                    disabled={proofStarted}
                    isInvalid={
                      !!validationMessages.lHSGoal ||
                      !!goalValidationMessage.LHS
                    }
                    required
                  />
                  <Form.Control.Feedback type="invalid" tooltip>
                    {validationMessages.lHSGoal ||
                      goalValidationMessage.LHS.Goal}
                  </Form.Control.Feedback>
                </div>
              </Form.Group>
              
              <Form.Group as={Col} md="4" className="er-proof-goal-rhs">
                <div className="mb-3">
                  <label htmlFor="eRProofRHSGoal" className="form-label">RHS Goal</label>
                  <RacketInput
                    id="eRProofRHSGoal"
                    name="rHSGoal"
                    type="text"
                    placeholder="RHS Goal"
                    value={formValues.rHSGoal}
                    onBlur={() => handleBlur("rHSGoal")}
                    onChange={enhancedHandleChange}
                    onKeyUp={rhsGoalKeyUp}
                    onClick={rhsGoalSelect}
                    ref={rhsGoalRef}
                    highlightPositions={rhsGoalHighlights}
                    disabled={proofStarted}
                    isInvalid={
                      !!validationMessages.rHSGoal ||
                      !!goalValidationMessage.RHS
                    }
                    required
                  />
                  <Form.Control.Feedback type="invalid" tooltip>
                    {validationMessages.rHSGoal || goalValidationMessage.RHS}
                  </Form.Control.Feedback>
                </div>
              </Form.Group>
            </Row>
          
            {proofStarted && (
              <Row className="er-current-state" style={{ alignItems: 'center', position: 'relative' }}>
                <Form.Group as={Col} md="4"
                  className={`er-proof-current-lhs ${showSide === "LHS" ? "active" : ""}`}
                  style={{ marginLeft: '450px' }}
                >
                  <Form.Floating
                    className="mb-3"
                    style={{ 
                      border: showSide === "LHS" ? '3px solid #0d6efd' : '1px solid #ced4da',
                      borderRadius: '0.375rem'
                  }}
                  >
                    <Form.Control
                      type="text"
                      placeholder="Current LHS"
                      value={currentLHS}
                      readOnly
                      style={{ cursor: "not-allowed", border: 'none' }}
                    />
                    <label>Current LHS</label>
                  </Form.Floating>
                </Form.Group>
                
                <Form.Group as={Col} md="4"
                  className={`er-proof-current-rhs ${showSide === "RHS" ? "active" : ""}`}
                >
                  <Form.Floating
                    className="mb-3"
                    style={{ 
                      border: showSide === "RHS" ? '3px solid #0d6efd' : '1px solid #ced4da',
                      borderRadius: '0.375rem'
                    }}
                  >
                    <Form.Control
                      type="text"
                      placeholder="Current RHS"
                      value={currentRHS}
                      readOnly
                      style={{ cursor: "not-allowed", border: 'none' }}
                    />
                    <label>Current RHS</label>
                  </Form.Floating>
                </Form.Group>
              </Row>
            )}

            <Form.Text
                as={"div"}
                id="formSeparator"
                className="form-separator"
                style={{ marginTop: '10px' }}
              ></Form.Text> 
          </div>
          <div className="form-bottom-part">
            {!proofStarted && (
              <Row className="goal-btn-wrap">
                <Button 
                  type="submit" 
                  className="orange-btn"
                >
                  Start Proof
                </Button>
              </Row>
            )}
          </div>
        </Form>
        
        {/* Current Side Status */}
        {proofStarted && (
          <>
            <div style={{ position: 'fixed', left: '10px', top: '215px', zIndex: 1020, color: '#F2A007', fontWeight: 'bold', fontSize: '20px' }}>
              CURRENT = {showSide}
            </div>
            <div style={{ position: 'fixed', left: '10px', top: '245px', zIndex: 1020 }}>
              <Button 
                size="lg"
                className="switch-btn"
                onClick={handleToggleSide}
                style={{ backgroundImage: 'linear-gradient(135deg, #07294d 0, #006298 100%)', color: '#ffffff', borderColor: 'transparent' }}
                >
                {showSide === "LHS"
                    ? "Switch to Right Hand Side ⋙"
                    : "⋘ Switch to Left Hand Side"}
              </Button>
            </div>
          </>
        )}
        <div style={{ position: 'fixed', right: '375px', top: '65px', zIndex: 1020 }}>
          <Dropdown className="proof-dropdown-btn proof-utilities">
            <Dropdown.Toggle id="dropdown-proof-utils" style={{ minWidth: '200px' }}>
              Proof Utilities
            </Dropdown.Toggle>
            <Dropdown.Menu style={{ minWidth: '200px' }}>
              <Dropdown.Item onClick={toggleDefinitionsWindow} href="#">
                Definitions
              </Dropdown.Item>
              <Dropdown.Item onClick={toggleOffcanvas} href="#">
                View Rule Set
              </Dropdown.Item>
              <Dropdown.Item 
                onClick={handleCheckCompletion} 
                disabled={!proofStarted}
                style={{ 
                  color: proofStarted ? 'red' : '#999', 
                  opacity: proofStarted ? 1 : 0.4,
                  cursor: proofStarted ? 'pointer' : 'not-allowed'
                }}
              >
                Check Current Proof
              </Dropdown.Item>
            </Dropdown.Menu>
          </Dropdown>
        </div>
        
        {/* Error Display */}
        {errors.length > 0 && (
          <div className="alert alert-danger" style={{ marginTop: '15px' }}>
            {errors.map((err, idx) => <div key={idx}>{err}</div>)}
          </div>
        )}
        
        {/* Middle Pane - Proof Lines */}
        {proofStarted && (
          <div className="racket-rule-container-wrap" 
          style={{ 
            height: `${availableHeight}px`, 
            width: '100%', 
            padding: '0 25px', 
            margin: 0,
            overflowY: 'auto',
            overflowX: 'hidden'
          }}>
            <div className="racket-rule-wrap" id="racket-rule" style={{ paddingTop: '20px', paddingBottom: '150px' }}>
            {proofComplete && (
              <Alert variant={"success"}>Proof Complete!</Alert>
            )}
              {renderPersistentPadRow({
                side: showSide,
                isPremise: true,
                padRefs: getPadRefs(showSide, lhsPadRefs, rhsPadRefs),
                formValues,
                jsonTreeRep,
                startPosition: (showSide === 'LHS' ? leftPremise : rightPremise).startPosition,
                setCurrentRacket,
                handleFieldHighlight,
                validationErrors,
                isBound,
                userRow,
                handleRowNumberClick,
                leftPremise,
                rightPremise,
                setLeftPremise,
                setRightPremise
              })}
              {racketRuleFields[showSide].map((field, index) =>
                field.deleted
                  ? null
                  : renderPersistentPadRow({
                    side: showSide,
                    index,
                    field,
                    padRefs: getPadRefs(showSide, lhsPadRefs, rhsPadRefs),
                    formValues,
                    jsonTreeRep,
                    startPosition: field.startPosition,
                    setCurrentRacket,
                    handleFieldHighlight,
                    validationErrors,
                    isBound,
                    userRow,
                    handleRowNumberClick,
                    leftPremise,
                    rightPremise,
                    setLeftPremise,
                    setRightPremise
                  })
              )}
            </div>
            {/* {racketFields[showSide].map((line, idx) => {
              const boundLineIndex = isBound ? parseInt(userRow.num, 10) : -1;
              const isUserBoundToNextLine = boundLineIndex === idx + 1;
              const nextLineExists = racketFields[showSide][idx + 1]?.racket;
              const showHighlight = nextLineExists || isUserBoundToNextLine;
              
              return (
                <Row key={idx} className="racket-rule-row" id={`racket-row-${racketFields[showSide].length}`} >
                  <Col xs="auto" style={{ minWidth: '50px', paddingRight: '5px', position: 'relative', top: '35px' }}>
                    <ClickableRowNumber
                      padIndex={idx}
                      isClickable={!isBound}
                      isSelected={isBound && boundLineIndex === idx}
                      onClick={() => handleRowNumberClick(idx)}
                      title={!isBound ? "Click to bind to footer" : ""}
                    />
                  </Col>
                  <Col>
                    <PersistentPad
                      ref={(el) => {
                        const refs = showSide === "LHS" ? lhsPadRefs : rhsPadRefs;
                        refs.current[idx] = el;
                      }}
                      side={showSide}
                      equation={line.racket || ""}
                      jsonTree={line.jsonTree || {}}
                      lineNum={idx}
                      startPosition={showHighlight ? (line.selectedNode ?? 0) : undefined}
                      resultNode={line.resultNode}
                      onHighlightChange={(selected) => handleFieldHighlight(showSide, idx, selected)}
                      ruleValue={line.rule || ""}
                      onRuleChange={() => {}}
                      isRuleReadOnly={true}
                      rulePlaceholder={idx === 0 ? `${showSide} Premise` : `${showSide} Rule`}
                      isRuleInvalid={false}
                      ruleValidationError=""
                      isEditRow={false}
                    />
                  </Col>
                </Row>
              ); */}
            {/* })} */}
            
            {/* Blank line for next entry */}
            {/* <Row className="racket-rule-row" id={`racket-row-${racketFields[showSide].length}`}>
              <Col xs="auto" style={{ minWidth: '50px', paddingRight: '5px', position: 'relative', top: '35px' }}>
                <ClickableRowNumber
                  padIndex={racketFields[showSide].length}
                  isClickable={false}
                  isSelected={false}
                  onClick={() => {}}
                  title=""
                />
              </Col>
              <Col>
                <div style={{ border: '1px solid #dee2e6', padding: '10px', minHeight: '60px', backgroundColor: '#f8f9fa' }}>
                  <div style={{ color: '#6c757d', fontStyle: 'italic' }}>Next proof line will appear here</div>
                </div>
              </Col>
            </Row> */}
          </div>
        )}
        
        {/* Footer Pane - Binding Editor */}
        {proofStarted && (() => {
        // Calculate bicolor border based on bound row
        const colors = ['#DAA520', '#0066cc', '#cc0000', '#228B22']; // yellow, blue, red, green
        const padIndex = userRow.num && userRow.num !== "" ? parseInt(userRow.num, 10) : 0;
        const currentColor = colors[padIndex % 4];
        const nextColor = colors[(padIndex + 1) % 4];
        return (
          <div 
          className="floating-footer" 
          style={{
            borderTop: `3px solid transparent`,
            borderImage: `linear-gradient(to right, ${currentColor} 50%, ${nextColor} 50%) 1`
          }}>
            <Row className="input-row">
              <Col md="1">
                <Form.Floating className="mb-3">
                  <Form.Control
                    type="text"
                    placeholder="Num"
                    value={userRow.num}
                    onChange={(e) => setUserRow({ num: e.target.value })}
                    disabled={isBound}
                  />
                  <label>Num</label>
                </Form.Floating>
              </Col>
              
              {!isBound && (
                <Col md="2" className="d-flex align-items-center">
                  <Button
                    variant="primary"
                    onClick={() => bindFooterToRow(userRow.num)}
                  >
                    Fill Values
                  </Button>
                </Col>
              )}
              
              <Col md={isBound ? "9" : "7"}>
                {isBound && renderFooterPad()}
              </Col>
              {isBound && (
                  <Col md="2" className="d-flex align-items-center">
                    <Button
                      variant="secondary"
                      onClick={() => unbindFooter()}
                    >
                      Cancel
                    </Button>
                  </Col>
                )}
              </Row>
              {isBound && (
                <Row className="button-row">
                  <Col md="5"></Col>
                  <Col md="3" className="rules-btn-grp">
                    <Button
                      className="orange-btn delete-btn"
                      onClick={handleClearLine}
                      disabled={parseInt(userRow.num, 10) === 0}
                    >
                      Clear Line
                    </Button>
                  </Col>
                  <Col md="2" className="rules-btn-grp">
                    <Button
                      className="orange-btn green-btn"
                      onClick={handleGenerateAndCheck}
                    >
                      Generate & Check
                    </Button>
                  </Col>
                  <Col md="2" className="rules-btn-grp">
                    <Button
                      className="orange-btn green-btn"
                      onClick={() => setShowSubstitution(true)}
                    >
                      Substitution
                    </Button>
                  </Col>
                </Row>
              )}
          </div>
          );
        })()}
        
        {/* Modals */}
        {showSubstitution && (
          <Substitution
            show={showSubstitution}
            handleClose={() => setShowSubstitution(false)}
            handleSubstitution={handleSubstitution}
            racketRuleFields={racketFields[showSide]}
            errors={errors}
            initialRule={footerRule}
          />
        )}
        
        {showProofComplete && (
          <ProofComplete onDismiss={() => setShowProofComplete(false)} />
        )}
      </Container>
    </MainLayout>
  );
};

export default EquationalReasoning;
