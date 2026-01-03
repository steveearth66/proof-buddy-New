import React, { useState } from "react";
import Button from "react-bootstrap/Button";
import Container from "react-bootstrap/Container";
import Form from "react-bootstrap/Form";
import Col from "react-bootstrap/Col";
import Row from "react-bootstrap/Row";
import { toast } from "react-toastify";
import MainLayout from "../layouts/MainLayout";
import equationalService from "../services/equationalService";
import { ProofComplete, Substitution } from "../components";
import "../scss/_forms.scss";
import "../scss/_er-racket.scss";

/**
 * EquationalReasoning - Minimal component for equational reasoning proofs
 * Simplified version without induction complexity
 */
const EquationalReasoning = () => {
  // Form state
  const [proofName, setProofName] = useState("");
  const [proofTag, setProofTag] = useState("");
  const [lhsGoal, setLhsGoal] = useState("");
  const [rhsGoal, setRhsGoal] = useState("");
  
  // Proof state
  const [proofStarted, setProofStarted] = useState(false);
  const [showSide, setShowSide] = useState("LHS"); // "LHS" or "RHS"
  const [racketFields, setRacketFields] = useState({
    LHS: [{ racket: "", rule: "", lineNumber: 0 }],
    RHS: [{ racket: "", rule: "", lineNumber: 0 }]
  });
  
  // UI state
  const [currentRule, setCurrentRule] = useState("");
  const [showSubstitution, setShowSubstitution] = useState(false);
  const [selectedLine, setSelectedLine] = useState(0); // Track which line to substitute
  const [showProofComplete, setShowProofComplete] = useState(false);
  const [errors, setErrors] = useState([]);
  
  // Start a new proof
  const handleStartProof = async (e) => {
    e.preventDefault();
    setErrors([]);
    
    // Validate inputs
    if (!lhsGoal.trim() || !rhsGoal.trim()) {
      setErrors(["Both LHS and RHS goals are required"]);
      return;
    }
    
    if (lhsGoal.trim() === rhsGoal.trim()) {
      setErrors(["LHS and RHS goals cannot be identical"]);
      return;
    }
    
    try {
      // Initialize the proof engine
      const response = await equationalService.setCurrentProof({
        lhsPremise: lhsGoal.trim(),
        rhsPremise: rhsGoal.trim(),
        definitions: []
      });
      
      if (response.isValid) {
        // Set up initial proof lines (premises)
        setRacketFields({
          LHS: [{ racket: lhsGoal.trim(), rule: "Premise", lineNumber: 0 }],
          RHS: [{ racket: rhsGoal.trim(), rule: "Premise", lineNumber: 0 }]
        });
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
  
  // Toggle between LHS and RHS
  const handleToggleSide = () => {
    setShowSide(showSide === "LHS" ? "RHS" : "LHS");
    setCurrentRule(""); // Clear rule when switching sides
  };
  
  // Apply a rule to generate next line
  const handleGenerateAndCheck = async () => {
    if (!currentRule.trim()) {
      toast.error("Please enter a rule");
      return;
    }
    
    const currentFields = racketFields[showSide];
    const lastLine = currentFields[currentFields.length - 1];
    
    if (!lastLine.racket) {
      toast.error("No expression to apply rule to");
      return;
    }
    
    try {
      const response = await equationalService.applyRule({
        side: showSide,
        currentRacket: lastLine.racket,
        rule: currentRule.trim(),
        startPosition: 0,
        selectedNode: 0,
        lineNumber: currentFields.length - 1
      });
      
      if (response.isValid) {
        // Add the new line
        const newLine = {
          racket: response.racket,
          rule: currentRule.trim(),
          lineNumber: currentFields.length
        };
        
        setRacketFields({
          ...racketFields,
          [showSide]: [...currentFields, newLine]
        });
        
        setCurrentRule(""); // Clear rule input
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
  
  // Check if proof is complete
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
  
  // Handle substitution
  const handleSubstitution = async (substitutionData) => {
    const { rule, substitution } = substitutionData;
    const currentFields = racketFields[showSide];
    const lineIndex = selectedLine; // Use the tracked selected line
    const targetLine = currentFields[lineIndex];
    
    if (!targetLine) {
      toast.error("Invalid line selected");
      return;
    }
    
    try {
      const response = await equationalService.substitution({
        side: showSide,
        currentRacket: targetLine.racket,
        rule: rule.trim(),
        substitution: substitution.trim(),
        startPosition: 0,
        selectedNode: 0,
        lineNumber: lineIndex
      });
      
      if (response.isValid) {
        // Add a new line after the selected line
        const updatedFields = [...currentFields];
        const newLine = {
          racket: response.racket,
          rule: rule.trim(),
          lineNumber: lineIndex + 1
        };
        
        // Insert the new line after the selected line
        updatedFields.splice(lineIndex + 1, 0, newLine);
        
        setRacketFields({
          ...racketFields,
          [showSide]: updatedFields
        });
        
        setShowSubstitution(false);
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
  
  // Clear a proof line
  const handleClearLine = async (lineNumber) => {
    if (lineNumber === 0) {
      toast.error("Cannot clear premise");
      return;
    }
    
    try {
      await equationalService.deleteLine(showSide, lineNumber);
      
      // Clear the line locally
      const updatedFields = [...racketFields[showSide]];
      updatedFields[lineNumber] = {
        ...updatedFields[lineNumber],
        racket: "",
        rule: ""
      };
      
      setRacketFields({
        ...racketFields,
        [showSide]: updatedFields
      });
      
      toast.success("Line cleared");
    } catch (error) {
      console.error("Error clearing line:", error);
      toast.error("Error clearing line");
    }
  };
  
  return (
    <MainLayout>
      <Container className="er-racket-container">
        <h1>Equational Reasoning</h1>
        
        {/* Error Display */}
        {errors.length > 0 && (
          <div className="alert alert-danger">
            {errors.map((err, idx) => <div key={idx}>{err}</div>)}
          </div>
        )}
        
        {/* Start Proof Form */}
        {!proofStarted && (
          <Form onSubmit={handleStartProof}>
            <Row className="mb-3">
              <Form.Group as={Col} md="6">
                <Form.Label>Proof Name</Form.Label>
                <Form.Control
                  type="text"
                  placeholder="Enter proof name"
                  value={proofName}
                  onChange={(e) => setProofName(e.target.value)}
                />
              </Form.Group>
              
              <Form.Group as={Col} md="6">
                <Form.Label>Tag</Form.Label>
                <Form.Control
                  type="text"
                  placeholder="Enter tag"
                  value={proofTag}
                  onChange={(e) => setProofTag(e.target.value)}
                />
              </Form.Group>
            </Row>
            
            <Row className="mb-3">
              <Form.Group as={Col} md="6">
                <Form.Label>Left Hand Side Goal *</Form.Label>
                <Form.Control
                  type="text"
                  placeholder="e.g., (+ 1 2)"
                  value={lhsGoal}
                  onChange={(e) => setLhsGoal(e.target.value)}
                  required
                />
              </Form.Group>
              
              <Form.Group as={Col} md="6">
                <Form.Label>Right Hand Side Goal *</Form.Label>
                <Form.Control
                  type="text"
                  placeholder="e.g., 3"
                  value={rhsGoal}
                  onChange={(e) => setRhsGoal(e.target.value)}
                  required
                />
              </Form.Group>
            </Row>
            
            <Button variant="primary" type="submit">
              Start Proof
            </Button>
          </Form>
        )}
        
        {/* Proof Interface */}
        {proofStarted && (
          <div className="proof-interface">
            {/* Side Toggle Button */}
            <div className="mb-3">
              <Button variant="warning" onClick={handleToggleSide}>
                Switch to {showSide === "LHS" ? "Right" : "Left"} Hand Side
              </Button>
              <span className="ms-3">
                Current Side: <strong>{showSide}</strong>
              </span>
            </div>
            
            {/* Proof Lines Display */}
            <div className="proof-lines mb-3">
              <h4>{showSide} Proof Lines</h4>
              {racketFields[showSide].map((line, idx) => (
                <div key={idx} className="proof-line mb-2 p-2 border">
                  <span className="line-number me-2"><strong>{idx}.</strong></span>
                  <span className="line-racket me-3">{line.racket || "(empty)"}</span>
                  <span className="line-rule text-muted">({line.rule})</span>
                  {idx > 0 && line.racket && (
                    <Button
                      size="sm"
                      variant="danger"
                      onClick={() => handleClearLine(idx)}
                      className="ms-2"
                    >
                      Clear
                    </Button>
                  )}
                </div>
              ))}
            </div>
            
            {/* Rule Input */}
            <Row className="mb-3">
              <Form.Group as={Col} md="8">
                <Form.Label>Rule</Form.Label>
                <Form.Control
                  type="text"
                  placeholder="e.g., eval +, rewrite math"
                  value={currentRule}
                  onChange={(e) => setCurrentRule(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      handleGenerateAndCheck();
                    }
                  }}
                />
              </Form.Group>
              <Form.Group as={Col} md="4" className="d-flex align-items-end">
                <Button variant="success" onClick={handleGenerateAndCheck}>
                  Generate & Check
                </Button>
              </Form.Group>
            </Row>
            
            {/* Action Buttons */}
            <div className="action-buttons mb-3">
              <Button variant="info" onClick={() => {
                // Apply substitution to the last line of current side
                const lastIndex = racketFields[showSide].length - 1;
                setSelectedLine(lastIndex);
                setShowSubstitution(true);
              }}>
                Substitution
              </Button>
              <Button variant="primary" onClick={handleCheckCompletion} className="ms-2">
                Check Proof Completion
              </Button>
            </div>
          </div>
        )}
        
        {/* Substitution Modal */}
        {showSubstitution && (
          <Substitution
            show={showSubstitution}
            handleClose={() => setShowSubstitution(false)}
            handleSubstitution={handleSubstitution}
            racketRuleFields={racketFields[showSide]}
            errors={errors}
          />
        )}
        
        {/* Proof Complete Modal */}
        {showProofComplete && (
          <ProofComplete
            show={showProofComplete}
            handleClose={() => setShowProofComplete(false)}
          />
        )}
      </Container>
    </MainLayout>
  );
};

export default EquationalReasoning;
