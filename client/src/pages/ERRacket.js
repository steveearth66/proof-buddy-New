import React, { useState, useEffect, useRef } from "react";
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
import { useDefinitionsWindow } from "../hooks/useDefinitionsWindow";
import erService from "../services/erService";
import { useLocation } from "react-router-dom";
import { toast } from "react-toastify";

/**
 * ERRacket component facilitates the Equational Reasoning Racket.
 */
const ARROW_KEYS = ["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"];
function getPadRefs(side, lhsPadRefs, rhsPadRefs) {
  return side === "LHS" ? lhsPadRefs : rhsPadRefs;
}
function getPadIndex(num) {
  return num === "000" ? 0 : parseInt(num, 10);
}

const ERRacket = () => {
  const initialValues = {
    proofName: "",
    proofTag: "",
    lHSGoal: "",
    rHSGoal: ""
  };

  const [footerRule, setFooterRule] = useState("");
  const [userRow, setUserRow] = useState({ num: "" });
  const [showSide, toggleSide] = useToggleSide();
  const [formValues, handleChange] = useInputState(initialValues);
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
    loadRacketProof,
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
  const [leftPremise, setLeftPremise] = useState({
    racket: '',
    rule: 'Premise',
    startPosition: 0
  });
  const [rightPremise, setRightPremise] = useState({
    racket: '',
    rule: 'Premise',
    startPosition: 0
  });
  const [loadedProof, setLoadedProof] = useState(null);
  const location = useLocation();
  const [editableLineNums, setEditableLineNums] = useState({
    LHS: 0,
    RHS: 0
  });
  const [isBound, setIsBound] = useState(false); // State to track if the num field is bound

  const handleERRacketSubmission = async () => {
    alert("We are stilling working on proof submission!");
  };

  const lhsPadRefs = useRef({});
  const rhsPadRefs = useRef({});
  const footerPadRef = useRef(null);

  const { handleSubmit } = useFormSubmit(
    isFormValid,
    setValidated,
    setAllTouched,
    handleERRacketSubmission
  );

  /**
   * Returns a JSON object of the present form
   */
  const convertFormToJSON = () => {
    let EquationalReasoningObject = {
      name: formValues.proofName,
      tag: formValues.proofTag,
      leftRacketsAndRules: racketRuleFields.LHS,
      rightRacketsAndRules: racketRuleFields.RHS,
      lHSGoal: formValues.lHSGoal,
      rHSGoal: formValues.rHSGoal,
      leftPremise: { ...leftPremise, jsonTree: (isGoalChecked.LHS ? jsonTreeRep.LHS : null) },
      rightPremise: { ...rightPremise, jsonTree: (isGoalChecked.RHS ? jsonTreeRep.RHS : null) },
      definitions: JSON.parse(sessionStorage.getItem("definitions") || "[]").filter(isApplied)
    };
    return JSON.stringify(EquationalReasoningObject);
  };

  function isApplied(definition) {
    return definition["applied"];
  }

  const exportJSON = () => {
    if (!formValues.proofName || !formValues.proofTag || !formValues.lHSGoal || !formValues.rHSGoal) {
      alert("Please fill out all required fields before exporting.");
      return;
    }
    exportToLocalMachine(formValues.proofName, convertFormToJSON());
  };

  const handleHighlight = (startPosition) => {
    setStartPosition(startPosition);
  };

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
    sessionStorage.removeItem("highlights");
    sessionStorage.removeItem("definitions");

    const clearProof = async () => {
      await erService.clearProof();
    };

    clearProof();
  }, []);

  useEffect(() => {
    if (formValues.rHSGoal !== "") {
      setRightPremise(prev => ({ ...prev, racket: formValues.rHSGoal }));
    }

    if (formValues.lHSGoal !== "") {
      setLeftPremise(prev => ({ ...prev, racket: formValues.lHSGoal }));
    }
  }, [formValues.lHSGoal, formValues.rHSGoal]);
  useEffect(() => {
    if (isBound && userRow.num !== "000") {
      const padIndex = parseInt(userRow.num, 10);
      const padRefs = showSide === "LHS" ? lhsPadRefs : rhsPadRefs;
      const mainPadRef = padRefs.current[padIndex];
      setFooterRule(mainPadRef?.getRuleValue() || "");
    }
    if (!isBound) {
      setFooterRule("");
    }
  }, [isBound, userRow.num, showSide]);
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
      if (currentLHS === currentRHS) {
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
    formValues,
    leftPremise,
    rightPremise,
    sendProofComplete
  ]);

  useEffect(() => {
    const fetchProof = async (id) => {
      const proof = await erService.getRacketProof(id);
      setLoadedProof(proof);
    };

    if (location?.state?.id) {
      fetchProof(location.state.id);
    }
  }, [location]);

  useEffect(() => {
    if (loadedProof) {
      formValues.proofName = loadedProof.name;
      formValues.proofTag = loadedProof.tag;
      formValues.lHSGoal = loadedProof.lHSGoal;
      formValues.rHSGoal = loadedProof.rHSGoal;

      setLeftPremise(loadedProof.leftPremise);
      setRightPremise(loadedProof.rightPremise);

      sessionStorage.setItem('definitions', JSON.stringify(loadedProof.definitions));

      loadRacketGoal(loadedProof);
      loadRacketProof(loadedProof);

      setEditableLineNums({
        LHS: loadedProof.leftRacketsAndRules.length ? loadedProof.leftRacketsAndRules.length - 1 : 0,
        RHS: loadedProof.rightRacketsAndRules.length ? loadedProof.rightRacketsAndRules.length - 1 : 0
      });

      let loadedStartPosition;
      if (showSide === 'LHS')
        loadedStartPosition = (loadedProof.leftRacketsAndRules.length > 1 ?
          loadedProof.leftRacketsAndRules.at(-2).startPosition : loadedProof.leftPremise.startPosition);
      else
        loadedStartPosition = (loadedProof.rightRacketsAndRules.length > 1 ?
          loadedProof.rightRacketsAndRules.at(-2).startPosition : loadedProof.rightPremise.startPosition);
      setStartPosition(loadedStartPosition ?? 0);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loadedProof]);

  // set startPosition upon switching sides
  useEffect(() => {
    const lastUndeletedFieldIndex = racketRuleFields[showSide].filter(line => !line.deleted).length - 2;
    let correctStartPosition;
    if (lastUndeletedFieldIndex >= 0)
      correctStartPosition = racketRuleFields[showSide][lastUndeletedFieldIndex].startPosition;
    else
      correctStartPosition = showSide === 'LHS' ? leftPremise.startPosition : rightPremise.startPosition;
    correctStartPosition = correctStartPosition ?? 0;
    setStartPosition(correctStartPosition);
  }, [showSide]);

  useEffect(() => {
    const currentSideRackets = racketRuleFields[showSide];
    if (currentSideRackets.length <= 1) {
      setCurrentRacket(formValues[`${showSide[0].toLowerCase()}HSGoal`]);
      return;
    }
    const undeletedRackets = currentSideRackets.filter((line) => !line.deleted && line.racket !== '');
    const lastUndeletedRacket = undeletedRackets[undeletedRackets.length - 1];
    if (lastUndeletedRacket) setCurrentRacket(lastUndeletedRacket.racket);

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [setStartPosition, showSide, racketRuleFields, formValues.lHSGoal, formValues.rHSGoal]);

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
                      editableLineNums,
                      leftPremise,
                      rightPremise,
                      handleHighlight,
                      setCurrentRacket,
                      setLeftPremise,
                      setRightPremise,
                      handleFieldChange,
                      handleChange,
                      validationErrors
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
                            editableLineNums,
                            leftPremise,
                            rightPremise,
                            handleHighlight,
                            setCurrentRacket,
                            setLeftPremise,
                            setRightPremise,
                            handleFieldChange,
                            handleChange,
                            validationErrors
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
            {isBound && (() => {
              const padIndex = getPadIndex(userRow.num);
              const padRefs = getPadRefs(showSide, lhsPadRefs, rhsPadRefs);

              const handleFooterKeyDown = e => {
                const key = e.key;
                if (ARROW_KEYS.includes(key)) {
                  e.preventDefault();
                  const direction = key.replace("Arrow", "").toLowerCase();
                  footerPadRef.current?.moveSelection(direction);
                  padRefs.current[padIndex]?.moveSelection(direction);
                }
              };

              let equation, jsonTree, startPos, onHighlightChange, ruleValue, onRuleChange, isRuleReadOnly;

              if (userRow.num === "000") {
                equation = showSide === "LHS" ? leftPremise.racket : rightPremise.racket;
                jsonTree = jsonTreeRep[showSide];
                startPos = showSide === "LHS" ? leftPremise.startPosition ?? 0 : rightPremise.startPosition ?? 0;
                ruleValue = "Premise";
                isRuleReadOnly = true;
                onRuleChange = () => {};
                onHighlightChange = newStartPosition => {
                  if (showSide === "LHS") {
                    setLeftPremise(prev => ({ ...prev, startPosition: newStartPosition }));
                  } else {
                    setRightPremise(prev => ({ ...prev, startPosition: newStartPosition }));
                  }
                };
              } else {
                const field = racketRuleFields[showSide][padIndex - 1];
                if (!field) return null;
                equation = field.racket;
                jsonTree = field.jsonTree || jsonTreeRep[showSide];
                startPos = field.startPosition ?? 0;
                isRuleReadOnly = false;
                ruleValue = footerRule;
                onRuleChange = e => {
                  setFooterRule(e.target.value);
                  handleFieldChange(showSide, padIndex - 1, "rule", e.target.value);
                  padRefs.current[padIndex]?.setRuleValue(e.target.value);
                };
                onHighlightChange = newStartPosition => {
                  handleFieldChange(showSide, padIndex - 1, "racket", field.racket, newStartPosition);
                };
              }

              return (
                <PersistentPad
                  ref={footerPadRef}
                  equation={equation}
                  onHighlightChange={onHighlightChange}
                  side={showSide}
                  jsonTree={jsonTree}
                  lineNum={padIndex}
                  editableLineNum={editableLineNums[showSide]}
                  startPosition={startPos}
                  tabIndex={0}
                  onKeyDown={handleFooterKeyDown}
                  ruleValue={ruleValue}
                  onRuleChange={onRuleChange}
                  isRuleReadOnly={isRuleReadOnly}
                  rulePlaceholder="Rule"
                  isEditRow={true}
                />
              );
            })()}
          </Col>
          {/* Column 6: Button */}
          <Col md="2" className="d-flex align-items-center">
            <Button
              variant="primary"
              onClick={() => {
                if (isBound) {
                  setUserRow({
                    num: ""
                  });
                  setIsBound(false);
                } else {
                  const userIndex = getPadIndex(userRow.num);
                  const matchingRow = document.getElementById("racket-row-" + userIndex)
                  if (matchingRow) {
                    setUserRow({
                      num: userRow.num
                    });
                    setIsBound(true);
                    setTimeout(() => {
                      footerPadRef.current?.focus();
                    }, 0);
                  } else {
                    alert("No matching row found!");
                  }
                }
              }}
            >
              {isBound ? "Unbind" : "Fill Values"}
            </Button>
          </Col>
        </Row>
        <Row className="button-row">
          <Col md="5"></Col>
          <Col md="3" className="rules-btn-grp">
            <Button
              className="orange-btn green-btn"
              onClick={async () => {
                const fullRacket = await addFieldWithApiCheck(showSide);
                try {
                  if (fullRacket.isValid) {
                    setEditableLineNums((prevEditableLineNums) => ({
                      ...prevEditableLineNums,
                      [showSide]: (fullRacket.lineNum < 1 || fullRacket.lineNum === null ? 0 : fullRacket.lineNum)
                    }));
                    if (racketRuleFields[showSide].filter(line => !line.deleted).length != 0) {
                      setStartPosition(0);
                    }
                  }
                } catch (error) {
                  //console.log("Null because on premise, don't worry about it");
                }
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
  editableLineNums,
  leftPremise,
  rightPremise,
  handleHighlight,
  setCurrentRacket,
  setLeftPremise,
  setRightPremise,
  handleFieldChange,
  handleChange,
  validationErrors
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
  const editableLineNum = editableLineNums[side];
  const startPosition = isPremise
    ? (isLHS ? leftPremise.startPosition : rightPremise.startPosition) ?? 0
    : field.startPosition ?? 0;
  const ruleValue = isPremise ? "Premise" : field.rule;
  const rulePlaceholder = isPremise ? `${side} Premise` : `${side} Rule`;
  const isRuleInvalid = !isPremise && !!validationErrors[side][index];
  const ruleValidationError = validationErrors[side][index];

  return (
    <Row className="racket-rule-row" id={`racket-row-${padIndex}`} key={isPremise ? "premise" : `${side}-field-${padIndex}`}>
      <Col md="1">
        <div className="main-grid-column">
          {padIndex.toString().padStart(3, "0")}
        </div>
      </Col>
      <Col md="5">
        <PersistentPad
          ref={el => { padRefs.current[padIndex] = el; }}
          side={side}
          equation={equation}
          jsonTree={jsonTree}
          lineNum={lineNum}
          editableLineNum={editableLineNum}
          startPosition={startPosition}
          onHighlightChange={startPosition => {
            handleHighlight(startPosition);
            setCurrentRacket(equation);
            if (isPremise) {
              isLHS
                ? setLeftPremise(prev => ({ ...prev, startPosition }))
                : setRightPremise(prev => ({ ...prev, startPosition }));
            } else {
              handleFieldChange(side, index, "racket", field.racket, startPosition);
            }
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