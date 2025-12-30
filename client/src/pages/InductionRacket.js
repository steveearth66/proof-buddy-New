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
  
  // Case state must be declared first since it's used in computed values below
  const [isAnchor, setIsAnchor] = useState(true);
  
  // Separate proof lines for base and leap cases
  const [baseRacketFields, setBaseRacketFields] = useState({
    LHS: [EMPTY_INITIAL_FIELD],
    RHS: [EMPTY_INITIAL_FIELD]
  });
  const [leapRacketFields, setLeapRacketFields] = useState({
    LHS: [EMPTY_INITIAL_FIELD],
    RHS: [EMPTY_INITIAL_FIELD]
  });
  
  // Computed current racketRuleFields based on isAnchor
  const racketRuleFields = isAnchor ? baseRacketFields : leapRacketFields;
  const setRacketRuleFields = isAnchor ? setBaseRacketFields : setLeapRacketFields;
  
  // Induction-specific state (no dependency on useRacketRuleFields hook)
  const [validationErrors, setValidationErrors] = useState({ LHS: [], RHS: [] });
  const [inductionSubErrors, setInductionSubErrors] = useState([]);
  const [showSubstitution, setShowSubstitution] = useState(false);
  
  const clearValidationErrors = useCallback(() => {
    setValidationErrors({ LHS: [], RHS: [] });
  }, []);

  const closeSubstitution = useCallback(() => {
    setShowSubstitution(false);
  }, []);

  const updateShowSubstitution = useCallback(() => {
    setShowSubstitution(true);
  }, []);

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
  
  // Separate premises for base and leap cases
  const [basePremises, setBasePremises] = useState({ LHS: {}, RHS: {} });
  const [leapPremises, setLeapPremises] = useState({ LHS: {}, RHS: {} });
  
  // Computed current premises based on isAnchor
  const leftPremise = (isAnchor ? basePremises : leapPremises).LHS;
  const rightPremise = (isAnchor ? basePremises : leapPremises).RHS;
  
  const [proofStarted, setProofStarted] = useState(false);
  const [proofStatus, setProofStatus] = useState({ base: null, leap: null }); // tracks base/leap completeness separately

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

  const getLastNonEmpty = (arr = []) => {
    for (let i = arr.length - 1; i >= 0; i--) {
      const racket = (arr[i]?.racket || "").trim();
      if (racket) return { index: i, racket };
    }
    return { index: -1, racket: "" };
  };

  const hasInternalBlanks = (arr = []) => {
    const { index: lastIdx } = getLastNonEmpty(arr);
    if (lastIdx <= 0) return false;
    for (let i = 0; i < lastIdx; i++) {
      const racket = (arr[i]?.racket || "").trim();
      if (!racket) return true;
    }
    return false;
  };

  const checkCurrentProofStatus = async () => {
    try {
      const caseName = isAnchor ? 'base' : 'leap';
      console.log('[CHECK PROOF] Checking case:', caseName);
      const result = await inductionService.checkCompletion(caseName);
      console.log('[CHECK PROOF] Result:', result);
      
      const status = result.isComplete 
        ? { state: "complete", label: result.label }
        : { state: "incomplete", label: result.label };
      console.log('[CHECK PROOF] Setting status:', status);
      setProofStatus(prev => ({ ...prev, [caseName]: status }));
    } catch (error) {
      console.error('Error checking proof completion:', error);
      toast.error('Failed to check proof completion');
    }
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

  // Clear validation errors and proof status when binding to a new row
  clearValidationErrors();
  const caseKey = isAnchor ? 'base' : 'leap';
  setProofStatus(prev => ({ ...prev, [caseKey]: null }));

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
  }, [showSide, lhsPadRefs, rhsPadRefs, racketRuleFields, clearValidationErrors]);

  // Control body overflow when proof is started
  useEffect(() => {
    if (proofStarted) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [proofStarted]);

  /**
   * Load proof lines from the database and populate racketRuleFields with highlighting data.
   * This ensures that when switching sides/cases, the highlighting persists.
   */
  const loadProofLinesFromDatabase = useCallback(async () => {
    try {
      const proofLines = await inductionService.getProofLines();
      
      // Build racketRuleFields from database proof lines
      const buildFieldsFromLines = (lines) => {
        if (!lines || lines.length === 0) {
          return [EMPTY_INITIAL_FIELD];
        }
        
        // Skip the premise (line 0) - it's displayed separately at the top
        // racketRuleFields contains only the generated proof lines (1, 2, 3, ...)
        const fields = lines
          .filter(line => line.lineNumber > 0)
          .sort((a, b) => a.lineNumber - b.lineNumber)  // Ensure correct order
          .map(line => {
            const field = {
              racket: line.racket || '',
              rule: line.rule || '',
              startPosition: line.startPosition || 0,
              selectedNode: line.selectedNode || 0,  // This is the key field for highlighting!
              substitution: line.substitution || '',
              jsonTree: line.jsonTree || {},  // Include jsonTree from backend for rendering
              deleted: false
            };
            return field;
          });
        
        // Always add empty field at the end
        fields.push(EMPTY_INITIAL_FIELD);
        return fields;
      };
      
      // Build the new state
      const newBaseLHS = buildFieldsFromLines(proofLines.base?.LHS || []);
      const newBaseRHS = buildFieldsFromLines(proofLines.base?.RHS || []);
      const newLeapLHS = buildFieldsFromLines(proofLines.leap?.LHS || []);
      const newLeapRHS = buildFieldsFromLines(proofLines.leap?.RHS || []);
      
      // Update base case fields
      setBaseRacketFields({
        LHS: newBaseLHS,
        RHS: newBaseRHS
      });
      
      // Update leap case fields
      setLeapRacketFields({
        LHS: newLeapLHS,
        RHS: newLeapRHS
      });
      
      // Update premises with selectedNode from database (line 0)
      // Only update if premise exists and selectedNode is valid
      const baseLHSPremise = proofLines.base?.LHS?.find(l => l.lineNumber === 0);
      const baseRHSPremise = proofLines.base?.RHS?.find(l => l.lineNumber === 0);
      const leapLHSPremise = proofLines.leap?.LHS?.find(l => l.lineNumber === 0);
      const leapRHSPremise = proofLines.leap?.RHS?.find(l => l.lineNumber === 0);
      
      if (baseLHSPremise || baseRHSPremise) {
        setBasePremises(prev => ({
          LHS: baseLHSPremise && prev.LHS ? { ...prev.LHS, selectedNode: baseLHSPremise.selectedNode || 0 } : prev.LHS,
          RHS: baseRHSPremise && prev.RHS ? { ...prev.RHS, selectedNode: baseRHSPremise.selectedNode || 0 } : prev.RHS
        }));
      }
      
      if (leapLHSPremise || leapRHSPremise) {
        setLeapPremises(prev => ({
          LHS: leapLHSPremise && prev.LHS ? { ...prev.LHS, selectedNode: leapLHSPremise.selectedNode || 0 } : prev.LHS,
          RHS: leapRHSPremise && prev.RHS ? { ...prev.RHS, selectedNode: leapRHSPremise.selectedNode || 0 } : prev.RHS
        }));
      }

    } catch (error) {
      console.error('[loadProofLines] Error loading proof lines:', error);
      // Don't show error to user - this is a background operation
    }
  }, [setBaseRacketFields, setLeapRacketFields, setBasePremises, setLeapPremises]);

  // Toggle sides - no database reload needed, state already has both sides
  const handleToggleSide = useCallback(() => {
    // Just toggle to the other side - state already contains both LHS and RHS data
    toggleSide();
    
    // No database reload - we want to preserve current UI state including any highlighting changes
  }, [showSide, toggleSide]);

  /**
   * Toggle between base and leap cases - state already contains both cases
   */
  const handleToggleCase = useCallback(() => {
    // Toggle the case - baseRacketFields and leapRacketFields are separate in state
    const newIsAnchor = !isAnchor;
    setIsAnchor(newIsAnchor);
    
    // Update Current LHS/RHS to match the new case's last non-empty line (or premise)
    const targetFields = newIsAnchor ? baseRacketFields : leapRacketFields;
    const targetPremises = newIsAnchor ? basePremises : leapPremises;
    const lhsLines = targetFields.LHS || [];
    const rhsLines = targetFields.RHS || [];
    
    // Find last non-empty line (skip trailing blank)
    const lastLhsLine = lhsLines.length > 0 && lhsLines[lhsLines.length - 1].racket === '' 
      ? (lhsLines.length > 1 ? lhsLines[lhsLines.length - 2] : null)
      : (lhsLines.length > 0 ? lhsLines[lhsLines.length - 1] : null);
    const lastRhsLine = rhsLines.length > 0 && rhsLines[rhsLines.length - 1].racket === '' 
      ? (rhsLines.length > 1 ? rhsLines[rhsLines.length - 2] : null)
      : (rhsLines.length > 0 ? rhsLines[rhsLines.length - 1] : null);
    
    setLhsValue(lastLhsLine?.racket || targetPremises.LHS?.racket || '');
    setRhsValue(lastRhsLine?.racket || targetPremises.RHS?.racket || '');
    
    // No database reload - state already contains both base and leap cases
    // Reloading would reset any highlighting changes made by clicking (not applying rules)
  }, [isAnchor, baseRacketFields, leapRacketFields, basePremises, leapPremises]);

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
   * Updates the field's selectedNode so highlighting persists across toggles.
   */
  const handleFieldHighlight = (side, index, selectedNode) => {
    const caseKey = isAnchor ? 'base' : 'leap';
    const setFields = caseKey === 'base' ? setBaseRacketFields : setLeapRacketFields;
    
    setFields(prev => {
      const updated = { ...prev };
      if (updated[side] && updated[side][index]) {
        updated[side][index] = {
          ...updated[side][index],
          selectedNode: selectedNode || 0
        };
      }
      return updated;
    });
  };

  /**
   * Handle premise highlighting change.
   * Updates the premise's selectedNode so highlighting persists across toggles.
   */
  const handlePremiseHighlight = (side, selectedNode) => {
    const caseKey = isAnchor ? 'base' : 'leap';
    const setPremises = caseKey === 'base' ? setBasePremises : setLeapPremises;
    
    setPremises(prev => ({
      ...prev,
      [side]: {
        ...prev[side],
        selectedNode: selectedNode || 0
      }
    }));
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

      // Validate payload before sending
      if (!previousRacketValue || previousRacketValue.trim() === '') {
        toast.error('No source expression found. Make sure the previous line has content.');
        return;
      }

      const payload = {
        side: showSide,
        case: isAnchor ? 'base' : 'leap',
        currentRacket: previousRacketValue,
        rule: ruleFromFooter,
        startPosition: previousStartPosition,
        selectedNode: previousStartPosition
      };

      // Reset status when new line generated
      const caseKey = isAnchor ? 'base' : 'leap';
      setProofStatus(prev => ({ ...prev, [caseKey]: null }));

      // Dismiss any previous error toasts before trying again
      toast.dismiss();

      const fullRacket = await inductionService.applyRule(payload);

      // If the backend returned a valid generated line, append it to the UI
      if (!fullRacket) {
        console.error("applyRule returned undefined/null");
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
            selectedNode: previousStartPosition,
            deleted: false
          };

          const sideArray = fields[showSide] || [];
          const hasMatchingField = sideArray.some((field) => (
            field && !field.deleted && field.racket === newField.racket && field.rule === newField.rule
          ));
          if (hasMatchingField) {
            return prevFields;
          }
          const lastField = sideArray[sideArray.length - 1];
          const lastIsEmpty = lastField && lastField.racket === "" && lastField.rule === "";
          const isEditingMiddle = typeof currentIndex === 'number' && currentIndex >= 0 && currentIndex < sideArray.length - 1;

          if (isEditingMiddle) {
            // Replace the targeted middle line without adding a new blank
            sideArray[currentIndex] = newField;
            // Ensure there's a trailing blank line; add one only if missing
            const endLast = sideArray[sideArray.length - 1];
            const endIsEmpty = endLast && endLast.racket === "" && endLast.rule === "";
            if (!endIsEmpty) {
              sideArray.push(EMPTY_INITIAL_FIELD);
            }
          } else {
            // Editing the end (or no specific index): maintain trailing blank behavior
            if (lastIsEmpty) {
              // Replace the last empty with the new line and add a new empty at the end
              sideArray[sideArray.length - 1] = newField;
              sideArray.push(EMPTY_INITIAL_FIELD);
            } else {
              // No empty at end; append new line and then an empty for next input
              sideArray.push(newField);
              sideArray.push(EMPTY_INITIAL_FIELD);
            }
          }

          fields[showSide] = sideArray;
          return fields;
        });

        // Update the Current LHS/RHS field to show the newly generated expression
        if (showSide === "LHS") {
          setLhsValue(fullRacket.racket || "");
        } else {
          setRhsValue(fullRacket.racket || "");
        }

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
    // Keep user-defined UDFs and highlights in session; do not clear

    const clearProof = async () => {
      await inductionService.clearInduction();
    };

    clearProof();
  }, []);

  useEffect(() => {
    // Do not clear definitions here; keep session-applied definitions intact

    if (formValues.rHSGoal !== "") {
      // Only update premise from formValues if proof hasn't started yet
      if (!proofStarted) {
        setBasePremises(prev => ({
          ...prev,
          RHS: {
            racket: formValues.rHSGoal,
            rule: "Premise",
            startPosition: 0,
            selectedNode: 0
          }
        }));
      }
    }

    if (formValues.lHSGoal !== "") {
      // Only update premise from formValues if proof hasn't started yet
      if (!proofStarted) {
        setBasePremises(prev => ({
          ...prev,
          LHS: {
            racket: formValues.lHSGoal,
            rule: "Premise",
            startPosition: 0,
            selectedNode: 0
          }
        }));
      }
    }

    // keep currentRacket in sync with active side goal for payloads
    if (!proofStarted) {
      const sideGoal = showSide === "LHS" ? formValues.lHSGoal : formValues.rHSGoal;
      if (sideGoal !== undefined) {
        setCurrentRacket(sideGoal);
      }
    }
  }, [showSide, formValues.lHSGoal, formValues.rHSGoal, proofStarted]);

  // Debug: log when leftPremise changes
  useEffect(() => {
    if (proofStarted) {
      // Premises set after proof start; leftPremise/rightPremise updated via engine response
    }
  }, [proofStarted, leftPremise, rightPremise]);

  useEffect(() => {
    if (showSubstitution) {
      setInductionSubErrors([]);
    }
  }, [showSubstitution]);

  // Unbind footer when switching between base and leap cases
  useEffect(() => {
    if (proofStarted) {
      // Only clear incomplete status, preserve complete status
      const caseKey = isAnchor ? 'base' : 'leap';
      setProofStatus(prev => {
        if (prev[caseKey]?.state === 'incomplete') {
          return { ...prev, [caseKey]: null };
        }
        return prev;
      });
      unbindFooter();
      clearValidationErrors();
    }
  }, [isAnchor, proofStarted, unbindFooter, clearValidationErrors]);

  useEffect(() => {
    // Disabled: Confetti should only show when BOTH base AND leap cases are complete
    // Currently this triggers when just one case/side matches, which is incorrect
    // TODO: Re-enable when we have proper full proof completion detection
    
    // const removeBlankRackets = () => {
    //   racketRuleFields.LHS.splice(-1);
    //   racketRuleFields.RHS.splice(-1);
    // };

    // const sendProofComplete = async () => {};

    // if (lhsValue !== "" && rhsValue !== "" && currentLHS !== "") {
    //   if (currentLHS === currentRHS || currentLHS === rhsValue) {
    //     removeBlankRackets();
    //     setShowProofComplete(true);
    //     setProofComplete(true);
    //     sendProofComplete();
    //     setTimeout(() => {
    //       setShowProofComplete(false);
    //     }, 5000);
    //   }
    // }
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
    rightPremise
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
      // Prefer session definitions; include only enabled/applied ones
      let definitions = [];
      try {
        const storedDefs = JSON.parse(sessionStorage.getItem('definitions')) || [];
        definitions = storedDefs.filter(d => d.applied);
      } catch (e) {
        console.error('Error reading session definitions:', e);
        definitions = [];
      }
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
        inductive_hypothesis_rhs: inductiveHypothesisRHS,
        definitions
      };

      const response = await inductionService.startInductionProof(inductionData);

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
            
            // Initialize the IndProof engine with UDFs, IH and premises
            try {
              const normalizeType = (t) => (t || '').replace(/\s*->\s*/g, ' > ').trim();
              const engineSetup = await inductionService.setCurrentProof({
                struct: (inductionType || 'integers').toLowerCase() === 'lists' ? 'list' : 'int',
                ivar: inductionVariable,
                aval: String(inductionValue),
                lvar: leapVariable,
                lhsPremise: formValues.lHSGoal,
                rhsPremise: formValues.rHSGoal,
                definitions: definitions.map(d => ({
                  label: d.label || d.name || '',
                  type: normalizeType(d.type),
                  expression: d.expression
                }))
              });

              // Use engine response to set premises and trees for both base and leap
              if (engineSetup && engineSetup.base && engineSetup.leap) {
                const baseL = engineSetup.base.LHS || {};
                const baseR = engineSetup.base.RHS || {};
                const leapL = engineSetup.leap.LHS || {};
                const leapR = engineSetup.leap.RHS || {};

                // Set base case premises
                setBasePremises({
                  LHS: {
                    racket: baseL.racket || formValues.lHSGoal,
                    rule: 'Premise',
                    startPosition: 0,
                    selectedNode: 0,
                    jsonTree: baseL.jsonTree || {}
                  },
                  RHS: {
                    racket: baseR.racket || formValues.rHSGoal,
                    rule: 'Premise',
                    startPosition: 0,
                    selectedNode: 0,
                    jsonTree: baseR.jsonTree || {}
                  }
                });

                // Set leap case premises
                setLeapPremises({
                  LHS: {
                    racket: leapL.racket || '',
                    rule: 'Premise',
                    startPosition: 0,
                    selectedNode: 0,
                    jsonTree: leapL.jsonTree || {}
                  },
                  RHS: {
                    racket: leapR.racket || '',
                    rule: 'Premise',
                    startPosition: 0,
                    selectedNode: 0,
                    jsonTree: leapR.jsonTree || {}
                  }
                });

                // Preserve separate premise trees; jsonTreeRep will be used as a fallback for non-premise lines
                setJsonTreeRep(prev => ({
                  ...prev,
                  LHS: baseL.jsonTree || prev.LHS,
                  RHS: baseR.jsonTree || prev.RHS
                }));
              }

              setProofStarted(true);
              
              // Load any existing proof lines from database to restore highlighting
              setTimeout(() => {
                loadProofLinesFromDatabase();
              }, 100);
            } catch (err) {
              console.error('Engine setup failed:', err);
              toast.error('Failed to initialize induction engine');
            }
          }
          
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

  const handleInductionSubstitution = useCallback(
    async ({ substitution, rule }) => {
      // Clear previous errors when user attempts a new submission
      setInductionSubErrors([]);
      const caseKey = isAnchor ? 'base' : 'leap';
      setProofStatus(prev => ({ ...prev, [caseKey]: null }));
      
      const padRefs = getPadRefs(showSide, lhsPadRefs, rhsPadRefs);
      const padIndex = getPadIndex(userRow.num);
      
      // Source is the PREVIOUS line to the bound line
      // If binding line 001, source is line 000 (premise)
      // If binding line 002, source is line 001, etc.
      let currentRacket;
      let sourcePad;
      
      if (padIndex === 1) {
        // Source is premise (line 000)
        currentRacket = showSide === "LHS"
          ? leftPremise?.racket || formValues.lHSGoal
          : rightPremise?.racket || formValues.rHSGoal;
        sourcePad = padRefs.current ? padRefs.current[0] : null;
      } else {
        // Source is the previous line (padIndex - 1 in the pads, which is padIndex - 2 in racketRuleFields)
        const sourceField = racketRuleFields[showSide][padIndex - 2];
        currentRacket = sourceField?.racket || "";
        sourcePad = padRefs.current ? padRefs.current[padIndex - 1] : null;
      }
      
      const startPos = sourcePad?.getStartPosition?.() ?? 0;
      const selectedNode = sourcePad?.getStartPosition?.() ?? 0;

      const payload = {
        substitution,
        rule,
        startPosition: startPos,
        selectedNode: selectedNode,
        currentRacket: currentRacket,
        side: showSide,
        case: isAnchor ? "base" : "leap"
      };

      try {
        const response = await inductionService.substitution(payload);

        if (response.isValid) {
          setInductionSubErrors([]);
          closeSubstitution();

          const racketStr = response.racket || currentRacket;

          // Add a new proof line instead of modifying the premise
          const newField = {
            racket: racketStr,
            rule: response.rule || rule,
            startPosition: startPos,
            selectedNode: selectedNode,
            jsonTree: response.jsonTree || {},
            deleted: false
          };

          setRacketRuleFields((prev) => {
            const currentFields = prev[showSide];
            
            // Check if the last field is empty - if so, replace it; otherwise append
            const lastField = currentFields[currentFields.length - 1];
            const lastIsEmpty = !lastField?.racket || lastField.racket.trim() === '';
            
            const updatedFields = lastIsEmpty 
              ? [...currentFields.slice(0, -1), newField]  // Replace last empty field
              : [...currentFields, newField];  // Append new field
            
            // Add a new empty field at the end only if the last field is not already empty
            const finalField = updatedFields[updatedFields.length - 1];
            const needsEmptyField = finalField && finalField.racket && finalField.racket.trim() !== '';
            
            return {
              ...prev,
              [showSide]: needsEmptyField ? [...updatedFields, EMPTY_INITIAL_FIELD] : updatedFields
            };
          });

          // Update the Current LHS/RHS field to show the newly generated expression
          if (showSide === "LHS") {
            setLhsValue(racketStr || "");
          } else {
            setRhsValue(racketStr || "");
          }

          // Unbind the footer
          setIsBound(false);
          setUserRow({ num: "" });

          if (response.jsonTree) {
            setJsonTreeRep((prev) => ({ ...prev, [showSide]: response.jsonTree }));
          }

          setCurrentRacket(racketStr);
          return response;
        }

        setInductionSubErrors(response.errors || ["Substitution failed"]);
        return false;
      } catch (error) {
        setInductionSubErrors(["Failed to substitute rule"]);
        return false;
      }
    },
    [
      closeSubstitution,
      formValues.lHSGoal,
      formValues.rHSGoal,
      isAnchor,
      leftPremise,
      rightPremise,
      setJsonTreeRep,
      showSide,
      userRow.num,
      racketRuleFields,
      lhsPadRefs,
      rhsPadRefs
    ]
  );

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
    rightPremise,
    caseType
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
      ? (isLHS ? leftPremise?.jsonTree : rightPremise?.jsonTree)
      : (field.jsonTree || jsonTreeRep[side]);
    
    const lineNum = isPremise ? 0 : index + 1;
    const ruleValue = isPremise ? "Premise" : field.rule;
    const rulePlaceholder = isPremise ? `${side} Premise` : `${side} Rule`;
    const isRuleInvalid = !isPremise && !!validationErrors[side][index];
    const ruleValidationError = validationErrors[side][index];

    // Prefer selectedNode (persisted) over startPosition; hard fallback to 0
    const startPosition = isPremise
      ? (isLHS
        ? (leftPremise && (leftPremise.selectedNode ?? leftPremise.startPosition)) ?? 0
        : (rightPremise && (rightPremise.selectedNode ?? rightPremise.startPosition)) ?? 0)
      : ((field && (field.selectedNode ?? field.startPosition)) ?? 0);

    return (
      <Row className="racket-rule-row" id={`racket-row-${padIndex}`} key={isPremise ? `premise-${caseType}-${side}` : `${side}-field-${padIndex}`}>
        <Col xs="auto" style={{ minWidth: '50px', paddingRight: '5px' }}>
          <ClickableRowNumber
            padIndex={padIndex}
            isClickable={!isBound}
            isSelected={isBound && padIndex === parseInt(userRow.num, 10)}
            onClick={() => handleRowNumberClick(padIndex)}
            title={!isBound ? "Click to bind to footer" : ""}
          />
        </Col>
        <Col>
          <PersistentPad
            ref={(el) => { padRefs.current[padIndex] = el; }}
            side={side}
            equation={equation}
            jsonTree={jsonTree}
            lineNum={lineNum}
            startPosition={startPosition}
            onHighlightChange={(selected) => isPremise ? handlePremiseHighlight(side, selected) : handleFieldHighlight(side, index, selected)}
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
          jsonTree={showSide === "LHS" ? leftPremise?.jsonTree : rightPremise?.jsonTree}
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

      const calculatedStartPosition = field.selectedNode || field.startPosition || 0;

      return (
        <PersistentPad
          ref={footerPadRef}
          equation={field.racket}
          onHighlightChange={() => {}}
          side={showSide}
          jsonTree={field.jsonTree || jsonTreeRep[showSide]}
          lineNum={padIndex}
          startPosition={calculatedStartPosition}
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
            handleSubstitution={handleInductionSubstitution}
            errors={inductionSubErrors}
          />
        )}

        <Form
          noValidate
          validated={validated}
          className="er-racket-form"
          onSubmit={handleSubmit}
        >
          <div className="form-top-section">
            <Row className="page-header-row" style={{ alignItems: 'center' }}>
              <Col xs="auto">
                <h1 style={{ marginBottom: 0 }}>Induction: Racket</h1>
              </Col>
              <Col xs="auto" className="check-row">
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
              <Form.Group as={Col} md="auto" className="er-proof-name">
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
              <Form.Group as={Col} md="auto" className="er-proof-tag">
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
              <Form.Group as={Col} md="auto" className="er-induction-variable">
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
              <Form.Group as={Col} md="auto" className="er-induction-value">
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
              <Form.Group as={Col} md="auto" className="er-leap-variable">
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
            </Row>

            <Row className="g-5">
              <Form.Group as={Col} md="4" className="er-proof-goal-lhs" style={{ marginLeft: '450px' }}>
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
              <Form.Group as={Col} md="4" className="er-proof-goal-rhs">
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

            {(!proofStarted || !isAnchor) && (
              <Row className="g-5">
                <Form.Group as={Col} md="4" className="er-inductive-hypothesis-lhs" style={{ marginLeft: '450px' }}>
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
                <Form.Group as={Col} md="4" className="er-inductive-hypothesis-rhs">
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

            <Row className="er-current-state" style={{ alignItems: 'center', position: 'relative' }}>
              <Form.Group
                as={Col}
                md="4"
                className={`er-proof-current-lhs ${showSide === "LHS" ? "active" : ""}`}
                style={{ marginLeft: '450px' }}
              >
                <Form.Floating className="mb-3">
                  <Form.Control
                    id="eRProofCurrentLHS"
                    name="proofCurrentLHS"
                    type="text"
                    placeholder="Current LHS"
                    value={lhsValue || (proofStarted ? (leftPremise?.racket || currentLHS) : '')}
                    readOnly
                    style={{ cursor: "not-allowed" }}
                  />
                  <label htmlFor="eRProofCurrentLHS">Current LHS</label>
                </Form.Floating>
              </Form.Group>

              <Form.Group
                as={Col}
                md="4"
                className={`er-proof-current-rhs ${showSide === "RHS" ? "active" : ""}`}
              >
                <Form.Floating className="mb-3">
                  <Form.Control
                    id="eRProofCurrentRHS"
                    name="proofCurrentRHS"
                    type="text"
                    placeholder="Current RHS"
                    value={rhsValue || (proofStarted ? (rightPremise?.racket || currentRHS) : '')}
                    readOnly
                    style={{ cursor: "not-allowed" }}
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
              <div style={{ position: 'fixed', right: '10px', top: '215px', zIndex: 9999, color: '#F2A007', fontWeight: 'bold', fontSize: '20px' }}>
                CURRENT = {isAnchor ? "BASE" : "LEAP"}
              </div>
              <div style={{ position: 'fixed', right: '10px', top: '245px', zIndex: 9999 }}>
                <Button
                  size="lg"
                  className="switch-btn"
                  onClick={handleToggleCase}
                  style={{ backgroundImage: 'linear-gradient(135deg, #07294d 0, #006298 100%)', color: '#ffffff', borderColor: 'transparent' }}
                >
                  {isAnchor ? "Switch to Leap Case" : "Switch to Base Case"}
                </Button>
              </div>
            </>
          )}

          <div className="form-bottom-part">

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
          </div>
        </Form>
      </Container>
      
      <div style={{ position: 'fixed', right: '375px', top: '65px', zIndex: 9999 }}>
        <Dropdown className="proof-dropdown-btn proof-utilities">
          <Dropdown.Toggle id="dropdown-autoclose-true" style={{ minWidth: '200px' }}>
            Proof Utilities
          </Dropdown.Toggle>

          <Dropdown.Menu style={{ minWidth: '200px' }}>
            <Dropdown.Item onClick={toggleDefinitionsWindow} href="#">
              Definitions
            </Dropdown.Item>
            <Dropdown.Item onClick={toggleOffcanvas} href="#">
              View Rule Set
            </Dropdown.Item>
            <Dropdown.Item onClick={checkCurrentProofStatus} href="#">
              Check Current Proof
            </Dropdown.Item>
          </Dropdown.Menu>
        </Dropdown>
      </div>
      
      {proofStarted && proofStatus[isAnchor ? 'base' : 'leap'] && (
        <div style={{ position: 'fixed', right: '50px', top: '65px', zIndex: 9999 }}>
          <span
            style={{
              fontWeight: "700",
              color: proofStatus[isAnchor ? 'base' : 'leap'].state === "complete" ? "green" : "red",
              fontSize: "28px"
            }}
          >
            {proofStatus[isAnchor ? 'base' : 'leap'].state === "complete"
              ? `${proofStatus[isAnchor ? 'base' : 'leap'].label} COMPLETE`
              : `${proofStatus[isAnchor ? 'base' : 'leap'].label} INCOMPLETE`}
          </span>
        </div>
      )}
      
      {proofStarted && (
        <div 
          className="racket-rule-container-wrap"
          style={{ 
            height: `${availableHeight}px`, 
            width: '100%', 
            padding: '0 25px', 
            margin: 0,
            overflowY: 'auto',
            overflowX: 'hidden'
          }}
        >
          <div className="racket-rule-wrap" id="racket-rule" style={{ paddingTop: '20px', paddingBottom: '150px' }}>
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
              rightPremise,
              caseType: isAnchor ? 'base' : 'leap'
            })}
            {racketRuleFields[showSide].map((field, index) =>
              field.deleted
                ? null
                : renderPersistentPadRow({
                  side: showSide,
                  isPremise: false,
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
                  rightPremise,
                  caseType: isAnchor ? 'base' : 'leap'
                })
            )}
          </>
        </div>
        </div>
      )}
      
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
                disabled={!isBound}
                onClick={async () => {
                  const caseKey = isAnchor ? 'base' : 'leap';
                  setProofStatus(prev => ({ ...prev, [caseKey]: null }));
                  try {
                    await inductionService.deleteLine(isAnchor ? 'base' : 'leap', showSide);
                    setRacketRuleFields(prev => {
                      const fields = { ...prev };
                      const arr = [...fields[showSide]];
                      for (let i = arr.length - 1; i >= 0; i--) {
                        if (arr[i] && arr[i].racket && arr[i].racket.trim() !== '') {
                          arr.splice(i, 1);
                          break;
                        }
                      }
                      const last = arr[arr.length - 1];
                      const endIsEmpty = last && (!last.racket || last.racket.trim() === '') && (!last.rule || last.rule.trim() === '');
                      if (!endIsEmpty) arr.push(EMPTY_INITIAL_FIELD);
                      fields[showSide] = arr;
                      return fields;
                    });
                  } catch (e) {
                    toast.error('Failed to delete line');
                  }
                }}
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
                disabled={!isBound}
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
