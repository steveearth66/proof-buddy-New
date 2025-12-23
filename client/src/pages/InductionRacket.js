import React, { useState, useEffect, useRef, useCallback } from "react";
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
  PersistentPad,
  Substitution
} from "../components";
import ClickableRowNumber from "../components/ClickableRowNumber";
import { useDefinitionsWindow } from "../hooks/useDefinitionsWindow";
import { useDynamicHeight } from "../hooks/useDynamicHeight";
import inductionService from "../services/inductionService";
// import erService from "../services/erService"; // removed to clean warnings
import {
  ARROW_KEYS,
  EMPTY_INITIAL_FIELD,
  getPadRefs,
  getPadIndex
} from "../utils/erRacketUtils";

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
  const [startPosition] = useState(0); // removed to clean warnings
  const [currentRacket, setCurrentRacket] = useState("");
  const [racketRuleFields, setRacketRuleFields] = useState({
    LHS: [EMPTY_INITIAL_FIELD],
    RHS: [EMPTY_INITIAL_FIELD]
  });
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
    , // racketRuleFields - now managed in state above
    addFieldWithApiCheck,
    , // handleFieldChange
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

  // Footer binding and PersistentPad refs - for interactive proof line highlighting
  const lhsPadRefs = useRef({});
  const rhsPadRefs = useRef({});
  const footerPadRef = useRef(null);
  const isProcessingRef = useRef(false);
  const [userRow, setUserRow] = useState({ num: "" });
  const [isBound, setIsBound] = useState(false);
  const [footerRule, setFooterRule] = useState("");
  
  // Hook for getting available height for scrollable proof area
  const availableHeight = useDynamicHeight();

  // Initialize jsonTreeRep as empty object for passing to renderPersistentPadRow
  // It gets populated by the backend when goals are checked
  const [jsonTreeRep, setJsonTreeRep] = useState({ LHS: {}, RHS: {} });

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
  // const convertToJSON = (target) => {
  //   return JSON.stringify(target);
  // }; // removed to clean warnings

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

  /**
   * Bind footer to a specific proof line row number.
   * This allows arrow keys to control highlighting in the previous row.
   */
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

    // Set footer rule initially to what the field has
    if (paddedRowNum !== "000") {
      const fieldIndex = userIndex - 1; // Convert line number to array index
      const field = racketRuleFields[showSide]?.[fieldIndex];
      setFooterRule(field?.rule || "");
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
  }, [showSide, lhsPadRefs, rhsPadRefs, racketRuleFields]);

  /**
   * Unbind footer from current proof line.
   */
  const unbindFooter = useCallback(() => {
    setUserRow({ num: "" });
    setIsBound(false);
  }, []);

  /**
   * Handle row number click to bind footer (only if not already bound).
   */
  const handleRowNumberClick = (rowNum) => {
    // Only allow binding if footer is currently unbound
    if (!isBound) {
      bindFooterToRow(rowNum);
    }
  };

  /**
   * Handle field highlighting change for proof lines.
   */
  const handleFieldHighlight = () => {
    // No-op handler for PersistentPad - removed params to clean warnings
  };

  const handleGenerateAndCheck = async () => {
    if (isProcessingRef.current) {
      return;
    }

    isProcessingRef.current = true;

    try {
      let ruleFromFooter = "";
      let previousStartPosition = 0;
      let previousRacketValue = "";
      let currentIndex = undefined;

      if (isBound) {
        const userIndex = getPadIndex(userRow.num);
        ruleFromFooter = userRow.num === "000" ? "Premise" : footerRule;

        if (userRow.num !== "000") {
          const previousRowIndex = userIndex - 1;
          const padRefs = getPadRefs(showSide, lhsPadRefs, rhsPadRefs);

          if (previousRowIndex === 0) {
            previousRacketValue = showSide === "LHS" ? leftPremise.racket : rightPremise.racket;
            previousStartPosition = padRefs.current[previousRowIndex]?.getStartPosition() ?? 0;
          } else {
            const previousField = racketRuleFields[showSide][previousRowIndex - 1];
            previousRacketValue = previousField?.racket || "";
            previousStartPosition = padRefs.current[previousRowIndex]?.getStartPosition() ?? 0;
          }
          currentIndex = userIndex - 1; // index of the field being edited in footer
        }
      }

      const fullRacket = await addFieldWithApiCheck(
        showSide,
        ruleFromFooter,
        previousStartPosition,
        previousRacketValue,
        currentIndex
      );

      // If the backend returned a valid generated line, append it to the UI
      if (!fullRacket) {
        console.error("addFieldWithApiCheck returned undefined/null");
        return;
      }

      if (fullRacket && fullRacket.isValid) {
        setRacketRuleFields((prevFields) => {
          const fields = { ...prevFields };

          const newField = {
            racket: fullRacket.racket || "",
            jsonTree: fullRacket.jsonTree || {},
            rule: ruleFromFooter,
            startPosition: previousStartPosition,
            deleted: false
          };

          const sideArray = fields[showSide] || [];
          const lastField = sideArray[sideArray.length - 1];
          const isEmpty = lastField && lastField.racket === "" && lastField.rule === "";

          if (isEmpty) {
            // Replace the last empty field with the new field
            sideArray[sideArray.length - 1] = newField;
            // Add a new empty field at the end for the next entry
            sideArray.push(EMPTY_INITIAL_FIELD);
          } else {
            // Append the new field and an empty one for the next step
            sideArray.push(newField);
            sideArray.push(EMPTY_INITIAL_FIELD);
          }

          fields[showSide] = sideArray;
          return fields;
        });

        // Unbind the footer after successful generation to reset UI state
        if (isBound) {
          unbindFooter();
        }
      } else {
        // Show a toast on invalid rule
        const message = (fullRacket && fullRacket.errors && fullRacket.errors[0]) || "Invalid rule";
        toast.error(message);
      }
    } finally {
      isProcessingRef.current = false;
    }
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

    // keep currentRacket in sync with active side goal for payloads
    const sideGoal = showSide === "LHS" ? formValues.lHSGoal : formValues.rHSGoal;
    if (sideGoal !== undefined) {
      setCurrentRacket(sideGoal);
    }
  }, [showSide, formValues.lHSGoal, formValues.rHSGoal]);

  // Debug: log when leftPremise changes
  useEffect(() => {
    if (proofStarted) {
      console.log("Proof started - leftPremise:", leftPremise);
      console.log("Proof started - rightPremise:", rightPremise);
    }
  }, [proofStarted, leftPremise, rightPremise]);

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

  // Global arrow-key navigation to move highlighting when footer is bound
  useEffect(() => {
    const handleGlobalKeyDown = (e) => {
      if (!isBound) return;

      const activeElement = document.activeElement;
      const isInTextInput = activeElement && (
        activeElement.tagName === "INPUT" ||
        activeElement.tagName === "TEXTAREA" ||
        activeElement.isContentEditable
      );

      if (isInTextInput) return;

      const key = e.key;
      if (ARROW_KEYS.includes(key)) {
        e.preventDefault();
        const direction = key.replace("Arrow", "").toLowerCase();
        const userIndex = getPadIndex(userRow.num);
        const mainPadRefs = getPadRefs(showSide, lhsPadRefs, rhsPadRefs);

        if (userRow.num === "000") {
          return;
        } else {
          const previousRowIndex = userIndex - 1;
          if (previousRowIndex >= 0) {
            mainPadRefs.current[previousRowIndex]?.moveSelection(direction);
          }
        }
      }
    };

    document.addEventListener("keydown", handleGlobalKeyDown);
    return () => {
      document.removeEventListener("keydown", handleGlobalKeyDown);
    };
  }, [isBound, userRow.num, showSide, lhsPadRefs, rhsPadRefs]);

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

            // Initialize the ER proof engine with the premise by calling checkGoal
            // This is required so the backend has a premise line to work from
            const erService = (await import('../services/erService')).default;
            try {
              const checkGoalResponse = await erService.checkGoal({
                side: side,
                goal: side === 'LHS' ? substitutedLHS : substitutedRHS,
                name: proofName,
                tag: proofTag
              });
              
              // Update jsonTreeRep with the parsed tree from backend
              if (checkGoalResponse && checkGoalResponse.jsonTree) {
                setJsonTreeRep(prev => ({
                  ...prev,
                  [side]: checkGoalResponse.jsonTree
                }));
              }
            } catch (error) {
              console.error('Failed to initialize ER premise:', error);
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
    const isLHS = side === "LHS";
    const padIndex = isPremise ? 0 : index + 1;
    
    // For premise in Induction, use the substituted premise from state
    let equation;
    if (isPremise) {
      if (isLHS) {
        equation = leftPremise?.racket || formValues.lHSGoal;
      } else {
        equation = rightPremise?.racket || formValues.rHSGoal;
      }
    } else {
      equation = field.racket;
    }
    
    const jsonTree = isPremise
      ? jsonTreeRep[side]
      : field.jsonTree || jsonTreeRep[side];
    const lineNum = isPremise ? 0 : index + 1;
    const ruleValue = isPremise ? "Premise" : field.rule;
    const rulePlaceholder = isPremise ? `${side} Premise` : `${side} Rule`;
    const isRuleInvalid = !isPremise && !!validationErrors[side][index];
    const ruleValidationError = validationErrors[side][index];

    const startPosition = isPremise
      ? (isLHS ? leftPremise?.startPosition || 0 : rightPremise?.startPosition || 0)
      : (field.startPosition || 0);

    return (
      <Row className="racket-rule-row" id={`racket-row-${padIndex}`} key={isPremise ? "premise" : `${side}-field-${padIndex}`}>
        <Col md="1">
          <ClickableRowNumber
            padIndex={padIndex}
            isClickable={!isBound}
            isSelected={isBound && padIndex === parseInt(userRow.num, 10)}
            onClick={() => handleRowNumberClick(padIndex)}
            title={!isBound ? "Click to bind to footer" : ""}
          />
        </Col>
        <Col md="11">
          <PersistentPad
            ref={(el) => { padRefs.current[padIndex] = el; }}
            side={side}
            equation={equation}
            jsonTree={jsonTree}
            lineNum={lineNum}
            startPosition={startPosition}
            onHighlightChange={(selected) => handleFieldHighlight()}
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

  const renderFooterPad = () => {
    const padIndex = getPadIndex(userRow.num);
    
    if (!userRow.num || userRow.num === "") {
      return null;
    }

    if (userRow.num === "000") {
      const equation = showSide === "LHS" ? leftPremise?.racket : rightPremise?.racket;
      
      if (!equation) {
        return <div className="alert alert-warning">No equation available</div>;
      }

      return (
        <PersistentPad
          ref={footerPadRef}
          equation={equation}
          onHighlightChange={() => {}}
          side={showSide}
          jsonTree={jsonTreeRep[showSide]}
          lineNum={padIndex}
          startPosition={0}
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
          onHighlightChange={() => {}}
          side={showSide}
          jsonTree={field.jsonTree || jsonTreeRep[showSide]}
          lineNum={padIndex}
          startPosition={0}
          tabIndex={0}
          ruleValue={footerRule}
          onRuleChange={e => setFooterRule(e.target.value.trim())}
          isRuleReadOnly={false}
          rulePlaceholder={`${showSide} Rule`}
          isRuleInvalid={!!validationErrors[showSide][padIndex - 1]}
          ruleValidationError={validationErrors[showSide][padIndex - 1]}
          isEditRow={true}
        />
      );
    }
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
                <div 
                  className="racket-rule-container-wrap"
                  style={{ maxHeight: `${availableHeight}px` }}
                >
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
                        handleFieldHighlight,
                        validationErrors,
                        isBound,
                        userRow,
                        handleRowNumberClick,
                        leftPremise,
                        rightPremise
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
                            handleFieldHighlight,
                            validationErrors,
                            isBound,
                            userRow,
                            handleRowNumberClick,
                            leftPremise,
                            rightPremise
                          })
                      )}
                    </>
                  </div>
                </div>
              )}
          </div>
        </Form>
      </Container>
      {proofStarted && (
        <div className="floating-footer">
          <Row className="input-row">
            <Col md="1">
              <Form.Floating className="mb-3">
                <Form.Control
                  id="userRowNum"
                  name="userRowNum"
                  type="text"
                  placeholder="Num"
                  value={userRow.num}
                  onChange={(e) => setUserRow({ ...userRow, num: e.target.value })}
                  disabled={isBound}
                />
                <label htmlFor="userRowNum">Num</label>
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
          <Row className="button-row">
            <Col md="5"></Col>
            <Col md="3" className="rules-btn-grp">
              <Button
                className="orange-btn delete-btn"
                onClick={() => deleteLastLine(showSide)}
              >
                Delete Line
              </Button>
            </Col>
            <Col md="2" className="rules-btn-grp">
              <Button
                className="orange-btn green-btn"
                onClick={handleGenerateAndCheck}
                disabled={!isBound}
              >
                Generate & Check
              </Button>
            </Col>
            <Col md="2" className="rules-btn-grp">
              <Button
                className="orange-btn green-btn"
                onClick={() => updateShowSubstitution()}
              >
                Substitution
              </Button>
            </Col>
          </Row>
        </div>
      )}
    </MainLayout>
  );
};

export default InductionRacket;
