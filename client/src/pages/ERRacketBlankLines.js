import React, { useState, useEffect } from "react";
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
import "../scss/_er-racket-blank-lines.scss";
import { useExportBlankLinesToLocalMachine } from "../hooks/useExportBlankLinesToLocalMachine";
import {
  Definitions,
  ProofComplete,
  Substitution
} from "../components";
import { useDefinitionsWindow } from "../hooks/useDefinitionsWindow";
import erService from "../services/erService";
import { useLocation } from "react-router-dom";
import { toast } from "react-toastify";

/**
 * ERRacket component facilitates the Equational Reasoning Racket.
 */
const ERRacketBlankLines = () => {
  const initialValues = {
    proofName: "",
    proofTag: "",
    lHSGoal: "",
    rHSGoal: ""
  };

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
    loadRacket,
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
  const [leftPremise, setLeftPremise] = useState({});
  const [rightPremise, setRightPremise] = useState({});
  const [loadedProof, setLoadedProof] = useState(null);
  const location = useLocation();
  const rowObject = { num: "", expression: "", rule: "", validity: false, highlightStartIndex: 0, highlightLength: 0 };
  const [userRow, setUserRow] = useState({ ...rowObject });
    const handleERRacketSubmission = async () => {
    alert("We are stilling working on proof submission!");
  };

  const [rows, setRows] = useState([ rowObject ]);
  const addRow = () => {
    setRows([...rows, { ...rowObject }]);
  };
  
  const deleteRow = (index = -1) => {
    if (index === -1) {
      // Remove the last row
      setRows(rows.slice(0, -1));
    } else {
      // Remove the row at the specified index
      setRows((rows || []).filter((_, i) => i !== index));
    }
  };

  const exportGridValues = () => {
    const gridValues = rows.map((row) => [
      row.expression,
      row.rule,
      row.validity
    ]);
    console.log(gridValues); // Replace with actual export logic
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

  const { exportBlankLinesToLocalMachine } = useExportBlankLinesToLocalMachine(); // Call the hook at the top level
  const exportJSON = () => {  
    // Ensure formValues and its properties are defined
    if (!formValues.proofName || !formValues.proofTag || !formValues.lHSGoal || !formValues.rHSGoal) {
      alert("Please fill out all required fields before exporting.");
      return;
    }
  
    exportBlankLinesToLocalMachine({
      name: formValues.proofName || "Unnamed Proof",
      tag: formValues.proofTag || "",
      lhsGoal: formValues.lHSGoal || "No LHS Goal Specified",
      rhsGoal: formValues.rHSGoal || "No RHS Goal Specified",
      rows: rows || []
    });
  };

  const { readBlankLinesFromFile } = useExportBlankLinesToLocalMachine(); // Call the hook at the top level

  const handleFileUpload = async (file) => {
    if (file) {
      try {
        const data = await readBlankLinesFromFile(file); // Parse the file
  
        // Update the `loadedProof` state with the parsed data
        setLoadedProof({
          name: data.name || "",
          tag: data.tag || "",
          lhs: data.lhsGoal || "",
          rhs: data.rhsGoal || "",
          proofLines: [], // fix later
          isComplete: false // change if needed
        });
        setRows(data.rows);
        } catch (error) {
        console.error("Error reading file:", error.message);
        alert("Failed to load the file. Please upload a valid .txt file.");
      }
    }
  };

  const [isBound, setIsBound] = useState(false); // State to track if the num field is bound

  const handleHighlight = (startPosition) => {
    setStartPosition(startPosition);
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
  }, [formValues.lHSGoal, formValues.rHSGoal]);

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
    formValues,
    leftPremise,
    rightPremise,
    sendProofComplete
  ]);

  useEffect(() => {
    const fetchProof = async (id) => {
      const proof = await erService.getRacketProof(id);
      sessionStorage.setItem('definitions', JSON.stringify(proof.definitions));
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
      formValues.lHSGoal = loadedProof.lhs;
      formValues.rHSGoal = loadedProof.rhs;

      loadRacketProof(loadedProof.proofLines, loadedProof.isComplete);
      loadRacket();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loadedProof, loadRacketProof]);

  useEffect(() => {
    const currentSideRackets = showSide === "LHS" ? racketRuleFields.LHS : racketRuleFields.RHS;
    if (currentSideRackets.length === 0) {
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
            {/* switch to __ side btn */}
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
                <div className="proof-opr-wrap">
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
                            accept=".txt"
                            style={{ display: "none" }}
                            onChange={(e) => handleFileUpload(e.target.files[0])}
                          />
                          <Dropdown.Item onClick={saveProof}>
                            Save Proof
                          </Dropdown.Item>
                          <Dropdown.Item href="#">Submit Proof</Dropdown.Item>
                        </Dropdown.Menu>
                      </Dropdown>
                  </div>
                </Col>

            </Row>
            
            {/* Main Grid */}
            <div className="main-grid-container">
              {(rows || []).map((row, index) => (
                <Row className="main-grid" key={index}>
                  {/* Column 1: Line Number */}
                  <Col md="1">
                    <div className="main-grid-column">
                      {(index + 1).toString().padStart(3, "0")}
                    </div>
                  </Col>

                  {/* Column 2: Expression */}
                  <Col md="5">
                    <div className="main-grid-column">
                      {row.expression.split("").map((char, charIndex) => {
                        const isHighlighted =
                          charIndex >= parseInt(row.highlightStartIndex, 10) &&
                          charIndex < parseInt(row.highlightStartIndex, 10) + parseInt(row.highlightLength, 10);
                        return (
                          <span
                            key={charIndex}
                            style={{
                              backgroundColor: isHighlighted ? "yellow" : "transparent"
                            }}
                          >
                            {char}
                          </span>
                        );
                      })}
                    </div>
                  </Col>

                  {/* Column 3: Rule */}
                  <Col md="3">
                    <div className="main-grid-column">{row.rule}</div>
                  </Col>
                </Row>
              ))}
            </div>
          </div>
        </Form>
      </Container>
               {/* Floating Footer */}
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
                    disabled={isBound} // Disable the field when isBound is true
                  />
                  <label htmlFor="userRowNum">Num</label>
                </Form.Floating>
              </Col>

              {/* Column 2: Expression */}
              <Col md="5">
                <Form.Floating className="mb-3">
                  <Form.Control
                    id="userRowExpression"
                    name="userRowExpression"
                    type="text"
                    placeholder="Expression"
                    value={userRow.expression}
                    onChange={(e) => {
                      const updatedExpression = e.target.value;
                      setUserRow({ ...userRow, expression: updatedExpression });

                      // Automatically update the corresponding row in the grid
                      const rowIndex = parseInt(userRow.num, 10) - 1;
                      if (isBound && rowIndex >= 0 && rowIndex < rows.length) {
                        const updatedRows = [...rows];
                        updatedRows[rowIndex].expression = updatedExpression;
                        setRows(updatedRows);
                      }
                    }}
                  />
                  <label htmlFor="userRowExpression">Expression</label>
                </Form.Floating>
              </Col>

              {/* Column 3: Rule */}
              <Col md="2">
                <Form.Floating className="mb-3">
                  <Form.Control
                    id="userRowRule"
                    name="userRowRule"
                    type="text"
                    placeholder="Rule"
                    value={userRow.rule}
                    onChange={(e) => {
                      const updatedRule = e.target.value;
                      setUserRow({ ...userRow, rule: updatedRule });

                      // Automatically update the corresponding row in the grid
                      const rowIndex = parseInt(userRow.num, 10) - 1;
                      if (isBound && rowIndex >= 0 && rowIndex < rows.length) {
                        const updatedRows = [...rows];
                        updatedRows[rowIndex].rule = updatedRule;
                        setRows(updatedRows);
                      }
                    }}
                  />
                  <label htmlFor="userRowRule">Rule</label>
                </Form.Floating>
              </Col>
                {/* Highlight Start Index */}
              <Col md="1">
                <Form.Floating className="mb-3">
                  <Form.Control
                    id="highlightStartIndex"
                    name="highlightStartIndex"
                    type="number"
                    placeholder="Start Index"
                    value={userRow.highlightStartIndex}
                    onChange={(e) => {
                      const updatedHighlightStartIndex = e.target.value;
                      setUserRow({ ...userRow, highlightStartIndex: updatedHighlightStartIndex });

                      // Automatically update the corresponding row in the grid
                      const rowIndex = parseInt(userRow.num, 10) - 1;
                      if (isBound && rowIndex >= 0 && rowIndex < rows.length) {
                        const updatedRows = [...rows];
                        updatedRows[rowIndex].highlightStartIndex = updatedHighlightStartIndex;
                        setRows(updatedRows);
                      }
                    }}                  />
                  <label htmlFor="highlightStartIndex">Start Index</label>
                </Form.Floating>
              </Col>

              {/* Highlight Length */}
              <Col md="1">
                <Form.Floating className="mb-3">
                  <Form.Control
                    id="highlightLength"
                    name="highlightLength"
                    type="number"
                    placeholder="Length"
                    value={userRow.highlightLength}
                    onChange={(e) => {
                      const updatedHighlightLength = e.target.value;
                      setUserRow({ ...userRow, highlightLength: updatedHighlightLength });

                      // Automatically update the corresponding row in the grid
                      const rowIndex = parseInt(userRow.num, 10) - 1;
                      if (isBound && rowIndex >= 0 && rowIndex < rows.length) {
                        const updatedRows = [...rows];
                        updatedRows[rowIndex].highlightLength = updatedHighlightLength;
                        setRows(updatedRows);
                      }
                    }}                  />
                  <label htmlFor="highlightLength">Length</label>
                </Form.Floating>
              </Col>
              {/* Column 6: Button */}
              <Col md="2" className="d-flex align-items-center">
                <Button
                  variant="primary"
                  onClick={() => {
                    if (!isBound) {
                      // Fill Values mode
                      const matchingRow = rows.find(
                        (row, index) => index + 1 === parseInt(userRow.num, 10)
                      );
                      if (matchingRow) {
                        setUserRow({
                          num: userRow.num,
                          expression: matchingRow.expression,
                          rule: matchingRow.rule,
                          highlightStartIndex: matchingRow.highlightStartIndex,
                          highlightLength: matchingRow.highlightLength
                        });
                        setIsBound(true); // Switch to Unbind mode
                      } else {
                        alert("No matching row found!");
                      }
                    } else {
                      // Unbind mode
                      setUserRow({
                        num: "",
                        expression: "",
                        rule: "",
                        highlightStartIndex: 0,
                        highlightLength: 0
                      });
                      setIsBound(false); // Switch back to Fill Values mode
                    }
                  }}
                >
                  {isBound ? "Unbind" : "Fill Values"}
                </Button>
              </Col>
            </Row>
            <Row className="button-row">
                    <Col md="3" className="rules-btn-grp">
                      <Button
                        className="orange-btn delete-btn"
                        onClick={addRow}>
                        Add Row
                      </Button>
                      <Button
                        className="orange-btn delete-btn"
                        onClick={() => deleteRow()}>
                        Delete Line
                      </Button>
                    </Col>
                    <Col md="5"></Col>
                    <Col md="3" className="rules-btn-grp">
                      <Button
                        className="orange-btn green-btn"
                        onClick={() => {
                          addFieldWithApiCheck(showSide);
                          //racketRuleFields?.LHS[0]?.jsonTree && console.log("the tree is: ", racketRuleFields.LHS[0].jsonTree);                          
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

export default ERRacketBlankLines;