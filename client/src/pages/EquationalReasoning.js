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
import { ProofComplete, Substitution, PersistentPad } from "../components";
import ClickableRowNumber from "../components/ClickableRowNumber";
import "../scss/_forms.scss";
import "../scss/_er-racket.scss";

import OffcanvasRuleSet from "../components/OffcanvasRuleSet";
import { useOffcanvas } from "../hooks/useOffcanvas";
import { useDefinitionsWindow } from "../hooks/useDefinitionsWindow";
import { useDynamicHeight } from "../hooks/useDynamicHeight";

import {
  Definitions
} from "../components";

/**
 * EquationalReasoning - Full-featured component with 3-pane layout
 * Header | Middle (proof lines) | Footer (binding pane)
 */
const EquationalReasoning = () => {
  // Form state (persistent in header)
  const [proofName, setProofName] = useState("");
  const [proofTag, setProofTag] = useState("");
  const [lhsGoal, setLhsGoal] = useState("");
  const [rhsGoal, setRhsGoal] = useState("");
  
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
    
    if (!lhsGoal.trim() || !rhsGoal.trim()) {
      setErrors(["Both LHS and RHS goals are required"]);
      return;
    }
    
    if (lhsGoal.trim() === rhsGoal.trim()) {
      setErrors(["LHS and RHS goals cannot be identical"]);
      return;
    }
    
    try {
      const response = await equationalService.setCurrentProof({
        lhsPremise: lhsGoal.trim(),
        rhsPremise: rhsGoal.trim(),
        definitions: []
      });
      
      if (response.isValid) {
        setRacketFields({
          LHS: [{
            racket: lhsGoal.trim(),
            rule: "Premise",
            lineNumber: 0,
            selectedNode: 0,
            startPosition: 0,
            jsonTree: response.lhsJsonTree || {}
          }],
          RHS: [{
            racket: rhsGoal.trim(),
            rule: "Premise",
            lineNumber: 0,
            selectedNode: 0,
            startPosition: 0,
            jsonTree: response.rhsJsonTree || {}
          }]
        });
        
        setCurrentLHS(lhsGoal.trim());
        setCurrentRHS(rhsGoal.trim());
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

  // Hook for getting available height for scrollable proof area
    const availableHeight = useDynamicHeight();
  
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
                    type="text"
                    placeholder="Name"
                    value={proofName}
                    onChange={(e) => setProofName(e.target.value)}
                    disabled={proofStarted}
                  />
                  <label># Name</label>
                </Form.Floating>
              </Form.Group>
              
              <Form.Group as={Col} md="3" className="er-proof-tag">
                <Form.Floating className="mb-3">
                  <Form.Control
                    type="text"
                    placeholder="Tag"
                    value={proofTag}
                    onChange={(e) => setProofTag(e.target.value)}
                    disabled={proofStarted}
                  />
                  <label># Tag</label>
                </Form.Floating>
              </Form.Group>
            </Row>
          
            <Row className="g-5">
              <Form.Group as={Col} md="4" className="er-proof-goal-lhs" style={{ marginLeft: '450px' }}>
                <Form.Floating className="mb-3">
                  <Form.Control
                    type="text"
                    placeholder="LHS Goal"
                    value={lhsGoal}
                    onChange={(e) => setLhsGoal(e.target.value)}
                    disabled={proofStarted}
                    required
                  />
                  <label>LHS Goal</label>
                </Form.Floating>
              </Form.Group>
              
              <Form.Group as={Col} md="4" className="er-proof-goal-rhs">
                <Form.Floating className="mb-3">
                  <Form.Control
                    type="text"
                    placeholder="RHS Goal"
                    value={rhsGoal}
                    onChange={(e) => setRhsGoal(e.target.value)}
                    disabled={proofStarted}
                    required
                  />
                  <label>RHS Goal</label>
                </Form.Floating>
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
            <div style={{ position: 'fixed', left: '10px', top: '215px', zIndex: 9999, color: '#F2A007', fontWeight: 'bold', fontSize: '20px' }}>
              CURRENT = {showSide}
            </div>
            <div style={{ position: 'fixed', left: '10px', top: '245px', zIndex: 9999 }}>
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
        <div style={{ position: 'fixed', right: '375px', top: '65px', zIndex: 9999 }}>
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
            {racketFields[showSide].map((line, idx) => {
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
                      rulePlaceholder={idx === 0 ? `${showSide} Premise` : "Rule"}
                      isRuleInvalid={false}
                      ruleValidationError=""
                      isEditRow={false}
                    />
                  </Col>
                </Row>
              );
            })}
            
            {/* Blank line for next entry */}
            <Row className="racket-rule-row" id={`racket-row-${racketFields[showSide].length}`}>
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
            </Row>
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
