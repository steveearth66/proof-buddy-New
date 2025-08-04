import React, { useState, useEffect, useRef, useCallback } from "react";
import Dropdown from "react-bootstrap/Dropdown";
import Button from "react-bootstrap/Button";
import Container from "react-bootstrap/Container";
import Form from "react-bootstrap/Form";
import Col from "react-bootstrap/Col";
import Row from "react-bootstrap/Row";
import Alert from "react-bootstrap/Alert";
import MainLayout from "../layouts/MainLayout";
import validateField from "../utils/eRFormValidationUtils";
import OffcanvasRuleSet from "../components/OffcanvasRuleSet";
import { useToggleSide } from "../hooks/useToggleSide";
import { useOffcanvas } from "../hooks/useOffcanvas";
import { useInputState } from "../hooks/useInputState";
import { useFormValidation } from "../hooks/useFormValidation";
import { useGoalCheck } from "../hooks/useGoalCheck";
import { useRacketRuleFields } from "../hooks/useRacketRuleFields";
import { useCurrentRacketValues } from "../hooks/useCurrentRacketValues";
import { useFormSubmit } from "../hooks/useFormSubmit";
import "../scss/_forms.scss";
import "../scss/_er-racket.scss";
import { exportToLocalMachine, readFromFile } from "../hooks/useExportToLocalMachine";
import {
  Definitions,
  ProofComplete,
  PersistentPad,
  Substitution
} from "../components";
import ClickableRowNumber from "../components/ClickableRowNumber";
import { useDefinitionsWindow } from "../hooks/useDefinitionsWindow";
import erService from "../services/erService";
import { useLocation } from "react-router-dom";
import { toast } from "react-toastify";
import {
  ARROW_KEYS,
  INITIAL_FORM_VALUES,
  INITIAL_PREMISE_STATE,
  getPadRefs,
  getPadIndex,
  isFormComplete,
  convertFormToJSON,
  clearSessionData,
  updatePremises
} from "../utils/erRacketUtils";

/**
 * ERRacket component facilitates the Equational Reasoning Racket.
 */
const ERRacket = () => {
  const [footerRule, setFooterRule] = useState("");
  const [userRow, setUserRow] = useState({ num: "" });
  const [showSide, toggleSide] = useToggleSide();
  const [formValues, handleChange] = useInputState(INITIAL_FORM_VALUES);
  const [validationMessages, handleBlur, setAllTouched, isFormValid] =
    useFormValidation(formValues, validateField);
  const [validated, setValidated] = useState(false);
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
  const [racketRuleFields, setRacketRuleFields] = useState({
    LHS: [{ racket: '', jsonTree: {}, rule: '', deleted: false }],
    RHS: [{ racket: '', jsonTree: {}, rule: '', deleted: false }]
  });

  const handleFieldChange = useCallback((side, index, fieldName, value) => {
    setRacketRuleFields((prevFields) => {
      const fieldsCopy = { ...prevFields };
      if (fieldsCopy[side] && fieldsCopy[side][index]) {
        fieldsCopy[side][index] = {
          ...fieldsCopy[side][index],
          [fieldName]: value
        };
      }
      return fieldsCopy;
    });
  }, []);

  const loadRacketProof = useCallback((loadedProof) => {
    if (loadedProof) {
      console.log('loadRacketProof called with:', loadedProof);
      
      formValues.proofName = loadedProof.name;
      formValues.proofTag = loadedProof.tag;
      formValues.lHSGoal = loadedProof.lHSGoal;
      formValues.rHSGoal = loadedProof.rHSGoal;

      setLeftPremise(loadedProof.leftPremise);
      setRightPremise(loadedProof.rightPremise);

      sessionStorage.setItem('definitions', JSON.stringify(loadedProof.definitions));

      // Set the racket rule fields from the loaded proof
      setRacketRuleFields({
        LHS: loadedProof.leftRacketsAndRules || [{ racket: '', jsonTree: {}, rule: '', deleted: false }],
        RHS: loadedProof.rightRacketsAndRules || [{ racket: '', jsonTree: {}, rule: '', deleted: false }]
      });

      loadRacketGoal(loadedProof);
      loadProofInServer(loadedProof);
    }
  }, []);

  const [
    ,
    addFieldWithApiCheck,
    ,
    validationErrors,
    serverError,
    racketErrors,
    ,
    updateShowSubstitution,
    showSubstitution,
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
  const [currentLHS, currentRHS] = useCurrentRacketValues(racketRuleFields);
  const [isOffcanvasActive, toggleOffcanvas] = useOffcanvas();
  const [showDefinitionsWindow, toggleDefinitionsWindow] =
    useDefinitionsWindow();
  const [proofComplete, setProofComplete] = useState(false);
  const [leftPremise, setLeftPremise] = useState(INITIAL_PREMISE_STATE);
  const [rightPremise, setRightPremise] = useState(INITIAL_PREMISE_STATE);
  const [loadedProof, setLoadedProof] = useState(null);
  const location = useLocation();
  const [isBound, setIsBound] = useState(false);

  const handleERRacketSubmission = async () => {
    alert("We are stilling working on proof submission!");
  };

  const lhsPadRefs = useRef({});
  const rhsPadRefs = useRef({});
  const footerPadRef = useRef(null);
  const isProcessingRef = useRef(false);

  const bindFooterToRow = useCallback((rowNum) => {
    const paddedRowNum = rowNum.toString().padStart(3, "0");
    const userIndex = getPadIndex(paddedRowNum);
    const matchingRow = document.getElementById("racket-row-" + userIndex);
    
    if (!matchingRow) {
      alert("No matching row found!");
      return false;
    }

    setUserRow({ num: paddedRowNum });
    setIsBound(true);

    // Set footer rule initially to what the pad ref row has
    if (paddedRowNum !== "000") {
      const padRefs = getPadRefs(showSide, lhsPadRefs, rhsPadRefs);
      const mainPadRef = padRefs.current[userIndex];
      setFooterRule(mainPadRef?.getRuleValue() || "");
    } else {
      setFooterRule("Premise");
    }

    setTimeout(() => {
      const padRefs = getPadRefs(showSide, lhsPadRefs, rhsPadRefs);
      // Focus on the previous row to match arrow key control
      // But don't try to focus on negative index if binding to premise
      if (paddedRowNum === "000") {
        // When binding to premise (000), focus stays on premise
        padRefs.current[userIndex]?.focus();
      } else {
        // For other rows, focus on the previous row
        const previousRowIndex = userIndex - 1;
        if (previousRowIndex >= 0) {
          padRefs.current[previousRowIndex]?.focus();
        }
      }
    }, 0);

    return true;
  }, [showSide, lhsPadRefs, rhsPadRefs]);

  const unbindFooter = useCallback(() => {
    setUserRow({ num: "" });
    setIsBound(false);
  }, []);

  const handleRowNumberClick = (rowNum) => {
    // Only allow binding if footer is currently unbound
    if (!isBound) {
      bindFooterToRow(rowNum);
    }
  };

  const handleGenerateAndCheck = async () => {
    // Prevent duplicate execution
    if (isProcessingRef.current) {
      return;
    }
    
    isProcessingRef.current = true;
    
    try {
      // Get the data needed for the backend
      let ruleFromFooter = "";
      let previousStartPosition = 0;
      let previousRacketValue = "";
      
      if (isBound) {
        const userIndex = getPadIndex(userRow.num);
        ruleFromFooter = userRow.num === "000" ? "Premise" : footerRule;
        
        // Get the previous row's data
        if (userRow.num !== "000") {
          const previousRowIndex = userIndex - 1;
          const padRefs = getPadRefs(showSide, lhsPadRefs, rhsPadRefs);
          
          if (previousRowIndex === 0) {
            // Previous row is the premise
            previousRacketValue = showSide === "LHS" ? leftPremise.racket : rightPremise.racket;
            // Get startPosition from pad ref instead of state
            previousStartPosition = padRefs.current[previousRowIndex]?.getStartPosition() ?? 0;
          } else {
            // Previous row is a regular field
            const previousField = racketRuleFields[showSide][previousRowIndex - 1];
            previousRacketValue = previousField?.racket || "";
            // Get startPosition from pad ref instead of state
            previousStartPosition = padRefs.current[previousRowIndex]?.getStartPosition() ?? 0;
          }
        }
      }
      
      const fullRacket = await addFieldWithApiCheck(showSide, ruleFromFooter, previousStartPosition, previousRacketValue);
      
      // Check if we got a valid response
      if (!fullRacket) {
        console.error("addFieldWithApiCheck returned undefined/null");
        return;
      }
      
      if (fullRacket && fullRacket.isValid) {
        // Add the returned expression to the racketRuleFields state
        setRacketRuleFields((prevFields) => {
          // Check if we already added this field (prevent duplicate additions)
          const hasMatchingField = prevFields[showSide].some(field => 
            field.racket === fullRacket.racket && field.rule === ruleFromFooter && !field.deleted
          );
          
          if (hasMatchingField) {
            return prevFields; // Return unchanged state
          }
          
          const fields = { ...prevFields };
          const newField = {
            racket: fullRacket.racket || "",
            jsonTree: fullRacket.jsonTree || {},
            rule: ruleFromFooter,
            deleted: false
          };
          
          const lastField = fields[showSide][fields[showSide].length - 1];
          const isEmpty = lastField && lastField.racket === "" && lastField.rule === "";
          
          if (isEmpty) {
            // Replace the last empty field with the new field
            fields[showSide][fields[showSide].length - 1] = newField;
            // Add a new empty field at the end
            fields[showSide].push({ racket: '', jsonTree: {}, rule: '', deleted: false });
          } else {
            // Add the new field and ensure there's an empty field at the end
            fields[showSide].push(newField);
            fields[showSide].push({ racket: '', jsonTree: {}, rule: '', deleted: false });
          }
          
          return fields;
        });

        // Unbind the footer after successful generate and check
        if (isBound) {
          unbindFooter();
        }
      }
    } catch (error) {
      console.error("Error in Generate & Check:", error);
    } finally {
      // Always reset the processing flag
      isProcessingRef.current = false;
    }
  };

  const { handleSubmit } = useFormSubmit(
    isFormValid,
    setValidated,
    setAllTouched,
    handleERRacketSubmission
  );

  const convertFormToJSONWrapper = () => {
    // Get current startPosition from the active pad ref
    const padRefs = getPadRefs(showSide, lhsPadRefs, rhsPadRefs);
    const currentStartPosition = padRefs.current[0]?.getStartPosition() ?? 0;
    
    return convertFormToJSON(formValues, racketRuleFields, leftPremise, rightPremise, isGoalChecked, jsonTreeRep, currentStartPosition, showSide);
  };

  const exportJSON = () => {
    if (!isFormComplete(formValues)) {
      alert("Please fill out all required fields before exporting.");
      return;
    }
    exportToLocalMachine(formValues.proofName, convertFormToJSONWrapper());
  };

  // Simplified handleHighlight - removed since not used anymore

  const handleFileUpload = async (file) => {
    if (file) {
      try {
        const data = await readFromFile(file); // Parse the file
        setLoadedProof(data);
      } catch (error) {
        console.error("Error reading file:", error.message);
        alert("Failed to load the file. Please upload a valid .json file.");
      }
    }
  };

  const saveProof = async () => {
    const proof = {
      name: formValues.proofName,
      tag: formValues.proofTag,
      leftRacketsAndRules: racketRuleFields.LHS,
      rightRacketsAndRules: racketRuleFields.RHS,
      lHSGoal: formValues.lHSGoal,
      rHSGoal: formValues.rHSGoal,
      leftPremise,
      rightPremise
    };

    try {
      await toast.promise(erService.saveProof(proof), {
        pending: "Saving proof...",
        success: "Proof saved!",
        error: "Error saving proof!"
      });
    } catch (error) {
      console.error(error);
    }
  };

  useEffect(() => {
    clearSessionData();
    erService.clearProof();
  }, []);

  useEffect(() => {
    updatePremises(formValues, setLeftPremise, setRightPremise);
  }, [formValues.lHSGoal, formValues.rHSGoal]);
  useEffect(() => {
    if (currentLHS && currentRHS && currentLHS === currentRHS) {
      racketRuleFields.LHS.splice(-1);
      racketRuleFields.RHS.splice(-1);
      setProofComplete(true);

      erService.completeProof({
        name: formValues.proofName,
        tag: formValues.proofTag,
        leftRacketsAndRules: racketRuleFields.LHS,
        rightRacketsAndRules: racketRuleFields.RHS,
        lHSGoal: formValues.lHSGoal,
        rHSGoal: formValues.rHSGoal,
        leftPremise,
        rightPremise
      }).catch(console.error);
    }
  }, [currentLHS, currentRHS, racketRuleFields, formValues, leftPremise, rightPremise]);

  useEffect(() => {
    if (location?.state?.id) {
      erService.getRacketProof(location.state.id).then(setLoadedProof);
    }
  }, [location]);

  useEffect(() => {
    if (loadedProof) {
      // Update form values
      Object.assign(formValues, {
        proofName: loadedProof.name,
        proofTag: loadedProof.tag,
        lHSGoal: loadedProof.lHSGoal,
        rHSGoal: loadedProof.rHSGoal
      });

      setLeftPremise(loadedProof.leftPremise);
      setRightPremise(loadedProof.rightPremise);

      sessionStorage.setItem('definitions', JSON.stringify(loadedProof.definitions));

      loadRacketGoal(loadedProof);
      loadRacketProof(loadedProof);

      // Set startPosition on all pad refs after they're created
      setTimeout(() => {
        const padRefs = getPadRefs(showSide, lhsPadRefs, rhsPadRefs);
        
        // Set premise startPosition (pad index 0)
        const premiseStartPosition = loadedProof[showSide === 'LHS' ? 'leftPremise' : 'rightPremise']?.startPosition ?? 0;
        padRefs.current[0]?.setStartPosition(premiseStartPosition);
        
        // Set startPosition for each racket rule field
        const rules = showSide === 'LHS' ? loadedProof.leftRacketsAndRules : loadedProof.rightRacketsAndRules;
        if (rules) {
          rules.forEach((rule, index) => {
            if (rule.startPosition !== undefined && padRefs.current[index + 1]) {
              padRefs.current[index + 1].setStartPosition(rule.startPosition);
            }
          });
        }
      }, 0);
      
      // Restore showSide if available
      if (loadedProof.showSide && loadedProof.showSide !== showSide) {
        toggleSide();
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loadedProof]);

  useEffect(() => {
    const currentSideRackets = racketRuleFields[showSide];

    if (currentSideRackets.length <= 1) {
      setCurrentRacket(formValues[`${showSide[0].toLowerCase()}HSGoal`]);
      return;
    }

    const undeletedRackets = currentSideRackets.filter((line) => !line.deleted && line.racket);
    const lastUndeletedRacket = undeletedRackets[undeletedRackets.length - 1];

    if (lastUndeletedRacket) {
      setCurrentRacket(lastUndeletedRacket.racket);
    }
  }, [showSide, racketRuleFields, formValues.lHSGoal, formValues.rHSGoal]);

  // Global keydown handler for arrow keys when footer is bound
  useEffect(() => {
    const handleGlobalKeyDown = (e) => {
      if (!isBound) return;

      // Check if cursor is in a text input (don't interfere with text editing)
      const activeElement = document.activeElement;
      const isInTextInput = activeElement && (
        activeElement.tagName === 'INPUT' ||
        activeElement.tagName === 'TEXTAREA' ||
        activeElement.isContentEditable
      );

      if (isInTextInput) return;

      const key = e.key;
      if (ARROW_KEYS.includes(key)) {
        e.preventDefault();
        const direction = key.replace("Arrow", "").toLowerCase();
        const userIndex = getPadIndex(userRow.num);
        const mainPadRefs = getPadRefs(showSide, lhsPadRefs, rhsPadRefs);

        // Control the previous row instead of the current bound row
        // But handle premise row (000) specially since it has no previous row
        if (userRow.num === "000") {
          // When bound to premise, arrow keys don't control anything (no previous row exists)
          return;
        } else {
          const previousRowIndex = userIndex - 1;
          if (previousRowIndex >= 0) {
            mainPadRefs.current[previousRowIndex]?.moveSelection(direction);
          }
        }
      }
    };

    document.addEventListener('keydown', handleGlobalKeyDown);

    return () => {
      document.removeEventListener('keydown', handleGlobalKeyDown);
    };
  }, [isBound, userRow.num, showSide, lhsPadRefs, rhsPadRefs]);

  const renderFooterPad = () => {
    const padIndex = getPadIndex(userRow.num);
    
    if (userRow.num === "000") {
      const equation = showSide === "LHS" ? leftPremise.racket : rightPremise.racket;
      
      return (
        <PersistentPad
          ref={footerPadRef}
          equation={equation}
          onHighlightChange={() => {
            // Highlighting handled internally by pad ref
          }}
          side={showSide}
          jsonTree={jsonTreeRep[showSide]}
          lineNum={padIndex}
          tabIndex={0}
          ruleValue="Premise"
          onRuleChange={() => {}}
          isRuleReadOnly={true}
          rulePlaceholder="Rule"
          isEditRow={true}
        />
      );
    } else {
      const field = racketRuleFields[showSide][padIndex - 1];
      if (!field) return null;
      
      return (
        <PersistentPad
          ref={footerPadRef}
          equation={field.racket}
          onHighlightChange={() => {
            // Highlighting handled internally by pad ref
          }}
          side={showSide}
          jsonTree={field.jsonTree || jsonTreeRep[showSide]}
          lineNum={padIndex}
          tabIndex={0}
          ruleValue={footerRule}
          onRuleChange={e => setFooterRule(e.target.value.trim())}
          isRuleReadOnly={false}
          rulePlaceholder="Rule"
          isEditRow={true}
        />
      );
    }
  };

  return (
    <MainLayout>
      <Container fluid className="er-racket-container">
        <OffcanvasRuleSet
          isActive={isOffcanvasActive}
          toggleFunction={toggleOffcanvas}
        ></OffcanvasRuleSet>
        {showDefinitionsWindow && (
          <Definitions toggleDefinitionsWindow={toggleDefinitionsWindow} />
        )}

        {proofComplete && <ProofComplete />}

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
                <h1>Equational Reasoning: Racket</h1>
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
                    isInvalid={!!proofValidationMessage.tag}
                    required
                  />
                  <label htmlFor="eRProofTag"># Tag</label>
                  <Form.Control.Feedback type="invalid" tooltip>
                    {proofValidationMessage.tag}
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
                  <Dropdown.Item onClick={() => document.getElementById("uploadProofInput").click()}>
                    Upload Proof
                  </Dropdown.Item>
                  <input
                    id="uploadProofInput"
                    type="file"
                    accept=".json"
                    style={{ display: "none" }}
                    onChange={(e) => handleFileUpload(e.target.files[0])}
                  />
                  <Dropdown.Item onClick={saveProof}>
                    Save Proof
                  </Dropdown.Item>
                  <Dropdown.Item href="#">Submit Proof</Dropdown.Item>
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
                      !!goalValidationMessage.LHS
                    }
                    required
                  />
                  <label htmlFor="eRProofLHSGoal">LHS Goal</label>
                  <Form.Control.Feedback type="invalid" tooltip>
                    {validationMessages.lHSGoal || goalValidationMessage.LHS}
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
                      !!goalValidationMessage.RHS
                    }
                    required
                  />
                  <label htmlFor="eRProofRHSGoal">RHS Goal</label>
                  <Form.Control.Feedback type="invalid" tooltip>
                    {validationMessages.rHSGoal || goalValidationMessage.RHS}
                  </Form.Control.Feedback>
                </Form.Floating>
              </Form.Group>
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
                    value={currentLHS === "" ? formValues.lHSGoal : currentLHS}
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
                    value={currentRHS === "" ? formValues.rHSGoal : currentRHS}
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
            </Row>

            {!isGoalChecked[showSide] && (
              <Row className="goal-btn-wrap">
                <Button
                  className="orange-btn"
                  onClick={() => {
                    checkGoal(
                      showSide,
                      formValues[`${showSide[0].toLowerCase()}HSGoal`],
                      formValues.proofName,
                      formValues.proofTag,
                      formValues.lHSGoal,
                      formValues.rHSGoal
                    );
                    // Set the premise to the current goal value
                    if (showSide === "LHS") {
                      setLeftPremise(prev => ({
                        ...prev,
                        racket: formValues.lHSGoal
                      }));
                    } else {
                      setRightPremise(prev => ({
                        ...prev,
                        racket: formValues.rHSGoal
                      }));
                    }
                  }}
                >
                  Check {showSide} Goal
                </Button>
              </Row>
            )}

            {isGoalChecked[showSide] && (
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
                  <>
                    {renderPersistentPadRow({
                      side: showSide,
                      isPremise: true,
                      padRefs: getPadRefs(showSide, lhsPadRefs, rhsPadRefs),
                      formValues,
                      jsonTreeRep,
                      setCurrentRacket,
                      validationErrors,
                      isBound,
                      userRow,
                      handleRowNumberClick
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
                          setCurrentRacket,
                          validationErrors,
                          isBound,
                          userRow,
                          handleRowNumberClick
                        })
                    )}
                  </>
                </div>
              </div>
            )}
          </div>
        </Form>
      </Container>
      <div className="floating-footer">
        <Row className="input-row">
          {/* Column 1: Num */}
          <Col md="1">
            <Form.Floating className="mb-3">
              <Form.Control
                id="userRowNum"
                name="userRowNum"
                type="text"
                placeholder="Num"
                value={userRow.num}
                onChange={(e) =>
                  setUserRow({ ...userRow, num: e.target.value })
                }
                disabled={isBound}
              />
              <label htmlFor="userRowNum">Num</label>
            </Form.Floating>
          </Col>

          {/* Column 2: Expression */}
          <Col>
            {isBound && renderFooterPad()}
          </Col>
          {/* Column 6: Button */}
          <Col md="2" className="d-flex align-items-center">
            <Button
              variant="primary"
              onClick={() => {
                if (isBound) {
                  unbindFooter();
                } else {
                  bindFooterToRow(userRow.num);
                }
              }}
            >
              {isBound ? "Cancel" : "Fill Values"}
            </Button>
          </Col>
        </Row>
        <Row className="button-row">
          <Col md="5"></Col>
          <Col md="3" className="rules-btn-grp">
            <Button
              className="orange-btn green-btn"
              onClick={handleGenerateAndCheck}
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
    </MainLayout>
  );
};

function renderPersistentPadRow({
  side,
  index = 0,
  field = {},
  isPremise = false,
  padRefs,
  formValues,
  jsonTreeRep,
  setCurrentRacket,
  validationErrors,
  isBound,
  userRow,
  handleRowNumberClick
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

  return (
    <Row className="racket-rule-row" id={`racket-row-${padIndex}`} key={isPremise ? "premise" : `${side}-field-${padIndex}`}>
      <Col md="1">
        <ClickableRowNumber
          padIndex={padIndex}
          isClickable={!isBound}
          isSelected={isBound && padIndex === parseInt(userRow.num, 10)}
          onClick={() => handleRowNumberClick(padIndex)}
          title={!isBound ? 'Click to bind to footer' : ''}
        />
      </Col>
      <Col md="11">
        <PersistentPad
          ref={el => { padRefs.current[padIndex] = el; }}
          side={side}
          equation={equation}
          jsonTree={jsonTree}
          lineNum={lineNum}
          onHighlightChange={() => {
            // Highlighting handled internally by pad ref
            setCurrentRacket(equation);
          }}
          ruleValue={ruleValue}
          onRuleChange={() => { }}
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

export default ERRacket;