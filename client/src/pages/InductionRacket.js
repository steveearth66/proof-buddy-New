import React, { useState, useEffect, useRef, useCallback } from "react";
import Dropdown from "react-bootstrap/Dropdown";
import Button from "react-bootstrap/Button";
import Container from "react-bootstrap/Container";
import Form from "react-bootstrap/Form";
import Col from "react-bootstrap/Col";
import Row from "react-bootstrap/Row";
import Alert from "react-bootstrap/Alert";
import Modal from "react-bootstrap/Modal";
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
  Substitution,
  RacketInput
} from "../components";
import { useParenHighlight } from "../hooks/useParenHighlight";
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
import { useLocation } from "react-router-dom";

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
  const [formValues, handleChange, setFormValues] = useInputState(initialValues);
  const [validationMessages, handleBlur, setAllTouched, isFormValid] =
    useFormValidation(formValues, validateField);
  const [validated, setValidated] = useState(false);
  const {
    isGoalChecked,
    checkGoal,
    goalValidationMessage,
    enhancedHandleChange,
    proofValidationMessage,
    clearProofValidationMessage,
    clearGoalValidationMessage
  } = useInductionCheck(handleChange);
  const [startPosition] = useState(0); // removed to clean warnings
  const [currentRacket, setCurrentRacket] = useState("");
  
  // Case state must be declared first since it's used in computed values below
  const [isAnchor, setIsAnchor] = useState(true);
  
  // List induction direction: 'up' or 'down' (only relevant when inductionType === 'lists')
  const [listDirection, setListDirection] = useState('up');
  
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
  const [showOverwriteModal, setShowOverwriteModal] = useState(false);
  const [showStartConfirmModal, setShowStartConfirmModal] = useState(false);

  // Parenthesis highlighting hooks
  const { 
    highlightPositions: inductionVarHighlights, 
    inputRef: inductionVarRef, 
    handleKeyUp: inductionVarKeyUp, 
    handleSelect: inductionVarSelect 
  } = useParenHighlight(formValues.inductionVariable);
  
  const { 
    highlightPositions: inductionValHighlights, 
    inputRef: inductionValRef, 
    handleKeyUp: inductionValKeyUp, 
    handleSelect: inductionValSelect 
  } = useParenHighlight(formValues.inductionValue);
  
  const { 
    highlightPositions: leapVarHighlights, 
    inputRef: leapVarRef, 
    handleKeyUp: leapVarKeyUp, 
    handleSelect: leapVarSelect 
  } = useParenHighlight(formValues.leapVariable);
  
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
  
  const { 
    highlightPositions: ihLhsHighlights, 
    inputRef: ihLhsRef, 
    handleKeyUp: ihLhsKeyUp, 
    handleSelect: ihLhsSelect 
  } = useParenHighlight(inductiveHypothesisLHS);
  
  const { 
    highlightPositions: ihRhsHighlights, 
    inputRef: ihRhsRef, 
    handleKeyUp: ihRhsKeyUp, 
    handleSelect: ihRhsSelect 
  } = useParenHighlight(inductiveHypothesisRHS);

  const [isHeaderCollapsed, setIsHeaderCollapsed] = useState(false);
  const topSectionRef = useRef(null);
  const [topSectionHeight, setTopSectionHeight] = useState(310); // fallback default

  useEffect(() => {
    if (topSectionRef.current) {
      // Measure the actual height of the section whenever it collapses/expands
      const resizeObserver = new ResizeObserver((entries) => {
        for (let entry of entries) {
          setTopSectionHeight(entry.contentRect.height);
        }
      });

      resizeObserver.observe(topSectionRef.current);
      return () => resizeObserver.disconnect();
    }
  }, [isHeaderCollapsed]); // Re-run when toggle changes

  const [windowWidth, setWindowWidth] = React.useState(window.innerWidth);
  
      useEffect(() => {
        const handleResize = () => setWindowWidth(window.innerWidth);
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
      }, []);

  // Footer binding and PersistentPad refs - for interactive proof line highlighting
  const lhsPadRefs = useRef({});
  const rhsPadRefs = useRef({});
  const footerPadRef = useRef(null);
  const isProcessingRef = useRef(false);
  const [userRow, setUserRow] = useState({ num: "" });
  const [isBound, setIsBound] = useState(false);
  const [footerRule, setFooterRule] = useState("");
  const [footerRuleError, setFooterRuleError] = useState("");
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  
  // Hook for getting available height for scrollable proof area
  const availableHeight = useDynamicHeight();

  // Initialize jsonTreeRep as empty object for passing to renderPersistentPadRow
  // It gets populated by the backend when goals are checked
  const [jsonTreeRep, setJsonTreeRep] = useState({ LHS: {}, RHS: {} });

  const handleERRacketSubmission = async (e) => {
    e.preventDefault();
    
    // Check for duplicate proof name/tag first
    try {
      const duplicateCheck = await inductionService.getInductionProofs({ 
        query: formValues.proofName 
      });

      const hasMatch = duplicateCheck.proofs?.some(p => 
        p.name === formValues.proofName && p.tag === formValues.proofTag
      );

      // If a match exists, show overwrite modal
      if (hasMatch) {
        setShowOverwriteModal(true);
        return;
      }
      
      // Show start confirmation modal (definitions will be locked)
      setShowStartConfirmModal(true);
    } catch (error) {
      console.error('Error checking for duplicates:', error);
      // Continue anyway if check fails
      setShowStartConfirmModal(true);
    }
  };
  
  const actuallyStartInductionProof = async () => {
    // Close modals first (matching EquationalReasoningNew pattern)
    setShowOverwriteModal(false);
    setShowStartConfirmModal(false);
    
    // This is the real proof start logic
    // Calling validateAndStart with appropriate parameters
    await validateAndStart(
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
    );
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
      // Check both base and leap cases
      const baseResult = await inductionService.checkCompletion('base');
      const leapResult = await inductionService.checkCompletion('leap');
      
      const baseStatus = baseResult.isComplete 
        ? { state: "complete", label: baseResult.label }
        : { state: "incomplete", label: baseResult.label };
      
      const leapStatus = leapResult.isComplete 
        ? { state: "complete", label: leapResult.label }
        : { state: "incomplete", label: leapResult.label };
      
      setProofStatus({
        base: baseStatus,
        leap: leapStatus
      });
      
      // Show confetti if BOTH cases are complete
      if (baseResult.isComplete && leapResult.isComplete) {
        setShowProofComplete(true);
        setProofComplete(true);
      } else {
        setShowProofComplete(false);
        setProofComplete(false);
      }
    } catch (error) {
      console.error('Error checking proof completion:', error);
      toast.error('Failed to check proof completion');
    }
  };

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
  setFooterRuleError('');
  const caseKey = isAnchor ? 'base' : 'leap';
  setProofStatus(prev => ({ ...prev, [caseKey]: null }));

    setUserRow({ num: paddedRowNum });
    setIsBound(true);

    // Set footer rule initially to what the field has
    if (paddedRowNum !== "000") {
      // Array index now equals line number, so use userIndex directly
      const field = racketRuleFields[showSide]?.[userIndex];
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
        
        // Include ALL lines (including premise at line 0) so array index = database line_number
        const allLines = lines.sort((a, b) => a.lineNumber - b.lineNumber);
        
        if (allLines.length === 0) {
          return [EMPTY_INITIAL_FIELD];
        }
        
        // Find max line number to size array
        const maxLineNum = Math.max(...allLines.map(l => l.lineNumber));
        
        // Create array where index matches database line number
        // Initialize all slots with empty fields to avoid null
        const fields = [];
        for (let i = 0; i <= maxLineNum; i++) {
          fields[i] = { racket: '', rule: '', deleted: false, startPosition: 0, selectedNode: 0, substitution: '', jsonTree: {} };
        }
        
        // Fill in actual line data at correct indices (INCLUDING line 0)
        allLines.forEach(line => {
          fields[line.lineNumber] = {
            racket: line.racket || '',
            rule: line.rule || '',
            startPosition: line.startPosition || 0,
            selectedNode: line.selectedNode || 0,
            substitution: line.substitution || '',
            jsonTree: line.jsonTree || {},
            deleted: false
          };
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
    
    // Find last non-empty, non-premise line (premise is at index 0)
    const findLastNonEmptyLine = (lines) => {
      // Start from the end and work backwards, skipping empties
      for (let i = lines.length - 1; i > 0; i--) {
        if (lines[i] && lines[i].racket && lines[i].racket.trim() !== '') {
          return lines[i];
        }
      }
      // If no non-empty proof line found, return null (will fall back to premise)
      return null;
    };
    
    const lastLhsLine = findLastNonEmptyLine(lhsLines);
    const lastRhsLine = findLastNonEmptyLine(rhsLines);
    
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
    setFooterRuleError('');
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

  const handleClearProof = async () => {
    if (!window.confirm('Are you sure you want to clear this proof? This will archive it and start a new proof.')) {
      return;
    }

    try {
      await inductionService.clearInduction();
      
      // Clear sessionStorage flag so we don't restore from DB on reload
      sessionStorage.removeItem('inductionProofActive');
      
      toast.success('Proof archived successfully');
      
      // Reload the page to start fresh
      window.location.reload();
    } catch (error) {
      console.error('Error clearing proof:', error);
      toast.error('Failed to clear proof');
    }
  };

  const handleRuleKeyDown = (e) => {
    // Check if Enter key is pressed without Shift
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault(); // Prevent newline in textarea
      
      // Only trigger Generate&Check if button would be enabled (isBound is true)
      if (isBound) {
        handleGenerateAndCheck();
      }
    }
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
            // Getting from premise
            previousRacketValue = showSide === "LHS" ? leftPremise.racket : rightPremise.racket;
            // Get the actual selected node from the premise state, not getStartPosition
            const premiseData = showSide === "LHS" ? leftPremise : rightPremise;
            previousStartPosition = premiseData.selectedNode ?? premiseData.startPosition ?? 0;
          } else {
            // Since array index now equals line number, use previousRowIndex directly
            const previousField = racketRuleFields[showSide][previousRowIndex];
            previousRacketValue = previousField?.racket || "";
            // Get the selected node from the field if available (restored), otherwise from PersistentPad's current selection
            const fromField = previousField?.selectedNode;
            const fromPad = padRefs.current[previousRowIndex]?.getStartPosition();
            previousStartPosition = fromField ?? fromPad ?? 0;
          }
          currentIndex = userIndex; // index in array now equals line number
        }
      }

      // Validate rule is entered
      if (!ruleFromFooter || ruleFromFooter.trim() === '') {
        setFooterRuleError('Must enter a rule');
        return;
      }

      // Clear validation error if rule is valid
      setFooterRuleError('');

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
        selectedNode: previousStartPosition,
        ...(typeof currentIndex === 'number' && { lineNumber: currentIndex })
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
        const newField = {
          racket: fullRacket.racket || "",
          jsonTree: fullRacket.jsonTree || {},
          rule: ruleFromFooter,
          startPosition: previousStartPosition,
          selectedNode: previousStartPosition,
          resultNode: fullRacket.resultNodeId ?? 0,
          deleted: false
        };

        setRacketRuleFields((prevFields) => {
          const sideArray = [...(prevFields[showSide] || [])];
          
          // Check for duplicate
          const hasMatchingField = sideArray.some((field) => (
            field && !field.deleted && field.racket === newField.racket && field.rule === newField.rule
          ));
          if (hasMatchingField) {
            return prevFields;
          }

          const isEditingMiddle = typeof currentIndex === 'number' && currentIndex >= 0 && currentIndex < sideArray.length - 1;

          if (isEditingMiddle) {
            // Replace the targeted middle line
            sideArray[currentIndex] = newField;
            // Ensure there's a trailing blank line
            const endLast = sideArray[sideArray.length - 1];
            const endIsEmpty = endLast && endLast.racket === "" && endLast.rule === "";
            if (!endIsEmpty) {
              sideArray.push(EMPTY_INITIAL_FIELD);
            }
          } else {
            // Editing the end
            const lastField = sideArray[sideArray.length - 1];
            const lastIsEmpty = lastField && lastField.racket === "" && lastField.rule === "";
            
            if (lastIsEmpty) {
              sideArray[sideArray.length - 1] = newField;
              sideArray.push(EMPTY_INITIAL_FIELD);
            } else {
              sideArray.push(newField);
              sideArray.push(EMPTY_INITIAL_FIELD);
            }
          }

          return {
            ...prevFields,
            [showSide]: sideArray
          };
        });

        // Note: Current LHS/RHS will be updated by the useEffect that watches racketRuleFields

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
  
  const location = useLocation();
  const initializedRef = useRef(false);
  useEffect(() => {
    if (initializedRef.current) return;

    const restoreProof = async () => {
      try {
        initializedRef.current = true;
        // 1. Determine the ID
        const targetId = location.state?.id || sessionStorage.getItem('induction_current_proof_id');
        const isActiveSession = sessionStorage.getItem('inductionProofActive') === 'true' || !!location.state?.id;

        if (!isActiveSession || !targetId) return;

        // 2. SET the session by ID (Calls the new backend view above)
        // This establishes the proof_id in the Django cache
        await inductionService.setSessionById(targetId);

        // 3. FETCH the data to fill the UI
        const proofData = await inductionService.getInductionProof(targetId);
        
        if (proofData) {
          // 4. Update Session Storage
          sessionStorage.setItem('induction_current_proof_id', targetId);
          sessionStorage.setItem('inductionProofActive', 'true');

          // 5. Populate Form Fields
          setFormValues({
            proofName: proofData.name,
            proofTag: proofData.tag,
            inductionVariable: proofData.induction_variable,
            inductionValue: proofData.anchor_value,
            leapVariable: proofData.leap_variable,
            lHSGoal: proofData.lhs_leap_goal, // Or whichever goal you want as default
            rHSGoal: proofData.rhs_leap_goal,
            inductionType: proofData.induction_type
          });

          setInductiveHypothesisLHS(proofData.inductive_hypothesis_lhs);
          setInductiveHypothesisRHS(proofData.inductive_hypothesis_rhs);

          // 6. Load the Lines (UI components)
          // Since setSessionById already "woke up" the engine, 
          // this will successfully generate the jsonTrees.
          await loadProofLinesFromDatabase();
          
          setProofStarted(true);
          if (location.state?.id) window.history.replaceState({}, document.title);
        }
      } catch (error) {
        console.error('Restoration failed:', error);
      }
    };

    restoreProof();
  }, [loadProofLinesFromDatabase]);

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

  // Update Current LHS/RHS display to show the last non-empty line
  useEffect(() => {
    if (!proofStarted) return;
    
    const targetFields = isAnchor ? baseRacketFields : leapRacketFields;
    const targetPremises = isAnchor ? basePremises : leapPremises;
    const lhsLines = targetFields.LHS || [];
    const rhsLines = targetFields.RHS || [];
    
    // Find last non-empty, non-premise line (premise is at index 0)
    const findLastNonEmptyLine = (lines) => {
      for (let i = lines.length - 1; i > 0; i--) {
        if (lines[i] && lines[i].racket && lines[i].racket.trim() !== '') {
          return lines[i];
        }
      }
      return null;
    };
    
    const lastLhsLine = findLastNonEmptyLine(lhsLines);
    const lastRhsLine = findLastNonEmptyLine(rhsLines);
    
    setLhsValue(lastLhsLine?.racket || targetPremises.LHS?.racket || '');
    setRhsValue(lastRhsLine?.racket || targetPremises.RHS?.racket || '');
  }, [proofStarted, isAnchor, baseRacketFields, leapRacketFields, basePremises, leapPremises]);

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

    // Validate anchor value based on induction type
    if (inductionType === 'lists') {
      // For lists: accept 'null' or quoted list notation like '(1) or '(1 2 3)
      const trimmedVal = (inductionValue || "").trim();
      if (!trimmedVal) {
        toast.error("Anchor value is required for list induction.");
        return;
      }
      // Accept 'null' or expressions starting with quote for lists
      const isValidList = trimmedVal === 'null' || 
                         trimmedVal.startsWith("'(") || 
                         trimmedVal === "'()" ||
                         /^\(\s*list\s+/.test(trimmedVal);
      if (!isValidList) {
        toast.error("Anchor value for lists must be 'null' or a quoted list like '() or '(1 2 3)");
        return;
      }
    } else {
      // For integers: must be a nonnegative integer
      if (!/^\d+$/.test(inductionValue || "")) {
        toast.error("Anchor value must be a nonnegative integer.");
        return;
      }
      const parsedVal = parseInt(inductionValue, 10);
      if (isNaN(parsedVal) || parsedVal < 0) {
        toast.error("Anchor value must be a nonnegative integer.");
        return;
      }
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
      // Validate goal expressions AND inductive hypotheses before starting proof
      // This catches arity mismatches, undefined labels, type errors, etc.
      
      // Validate LHS leap goal
      try {
        const lhsLeapValidation = await inductionService.checkGoal({
          case: 'leap',
          side: 'LHS',
          goal: leftGoal
        });
        
        if (!lhsLeapValidation.isValid) {
          const errorMessage = lhsLeapValidation.errors?.length 
            ? lhsLeapValidation.errors.join('\n') 
            : 'Invalid LHS goal';
          toast.error(`LHS Goal validation failed:\n${errorMessage}`);
          return;
        }
      } catch (validationError) {
        const errorMessage = validationError.response?.data?.errors?.join('\n') 
          || validationError.message 
          || 'Invalid LHS goal';
        toast.error(`LHS Goal validation failed:\n${errorMessage}`);
        return;
      }
      
      // Validate RHS leap goal
      try {
        const rhsLeapValidation = await inductionService.checkGoal({
          case: 'leap',
          side: 'RHS',
          goal: rightGoal
        });
        
        if (!rhsLeapValidation.isValid) {
          const errorMessage = rhsLeapValidation.errors?.length 
            ? rhsLeapValidation.errors.join('\n') 
            : 'Invalid RHS goal';
          toast.error(`RHS Goal validation failed:\n${errorMessage}`);
          return;
        }
      } catch (validationError) {
        const errorMessage = validationError.response?.data?.errors?.join('\n') 
          || validationError.message 
          || 'Invalid RHS goal';
        toast.error(`RHS Goal validation failed:\n${errorMessage}`);
        return;
      }
      
      // Validate LHS Inductive Hypothesis
      try {
        const lhsIHValidation = await inductionService.checkGoal({
          case: 'leap',
          side: 'LHS',
          goal: inductiveHypothesisLHS
        });
        
        if (!lhsIHValidation.isValid) {
          const errorMessage = lhsIHValidation.errors?.length 
            ? lhsIHValidation.errors.join('\n') 
            : 'Invalid LHS Inductive Hypothesis';
          toast.error(`LHS Inductive Hypothesis validation failed:\n${errorMessage}`);
          return;
        }
      } catch (validationError) {
        const errorMessage = validationError.response?.data?.errors?.join('\n') 
          || validationError.message 
          || 'Invalid LHS Inductive Hypothesis';
        toast.error(`LHS Inductive Hypothesis validation failed:\n${errorMessage}`);
        return;
      }
      
      // Validate RHS Inductive Hypothesis
      try {
        const rhsIHValidation = await inductionService.checkGoal({
          case: 'leap',
          side: 'RHS',
          goal: inductiveHypothesisRHS
        });
        
        if (!rhsIHValidation.isValid) {
          const errorMessage = rhsIHValidation.errors?.length 
            ? rhsIHValidation.errors.join('\n') 
            : 'Invalid RHS Inductive Hypothesis';
          toast.error(`RHS Inductive Hypothesis validation failed:\n${errorMessage}`);
          return;
        }
      } catch (validationError) {
        const errorMessage = validationError.response?.data?.errors?.join('\n') 
          || validationError.message 
          || 'Invalid RHS Inductive Hypothesis';
        toast.error(`RHS Inductive Hypothesis validation failed:\n${errorMessage}`);
        return;
      }

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
          // Handle generics created by backend (could be multiple for list induction)
          const genericsCreated = response.data.generics_created || 
                                  (response.data.generic_definition_created ? [response.data.generic_definition_created] : []);
          
          if (genericsCreated.length > 0) {
            let generics = [];
            try {
              const storedGenerics = sessionStorage.getItem('generics');
              generics = storedGenerics ? JSON.parse(storedGenerics) : [];
            } catch (e) {
              console.error('Error parsing generics:', e);
              generics = [];
            }
            
            // Add all created generics
            genericsCreated.forEach(genericDef => {
              const newGeneric = {
                id: genericDef.id || `generic_${Date.now()}_${genericDef.name}`,
                label: genericDef.name,
                type: genericDef.type,
                notes: genericDef.description || `Generic variable ${genericDef.name}`,
                restrictions: {
                  assumption: genericDef.type === 'list' ? 'Non-null' : 'Non-negative',
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
            });
            
            sessionStorage.setItem('generics', JSON.stringify(generics));
            
            const event = new CustomEvent('genericsUpdated', {
              detail: { 
                newGenerics: genericsCreated,
                allGenerics: generics 
              }
            });
            window.dispatchEvent(event);
            
            const genericNames = genericsCreated.map(g => `"${g.name}"`).join(', ');
            toast.success(`Generic variable${genericsCreated.length > 1 ? 's' : ''} ${genericNames} created`);
          }

          const proofId = response.data.proof_id || response.data.id;
          
          if (proofId) {
            toast.success('Induction proof started successfully!');
            sessionStorage.setItem('induction_current_proof_id', proofId);
            
            // Initialize the IndProof engine with UDFs, IH and premises
            try {
              const normalizeType = (t) => (t || '').replace(/\s*->\s*/g, ' > ').trim();
              
              // Get all enabled generics from sessionStorage (including 'a' and lvar)
              let genericsForEngine = [];
              try {
                const storedGenerics = sessionStorage.getItem('generics');
                const allGenerics = storedGenerics ? JSON.parse(storedGenerics) : [];
                genericsForEngine = allGenerics.filter(g => g.enabled);
              } catch (e) {
                console.error('Error reading generics for engine:', e);
                genericsForEngine = [];
              }
              
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
                })),
                generics: genericsForEngine.map(g => ({
                  label: g.label || g.name || '',
                  type: normalizeType(g.type),
                  restrictions: {
                    assumption: g.assumption || g.restrictions?.assumption || 'None',
                    neverNull: g.neverNull || g.restrictions?.neverNull || false
                  }
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

              // Clear any previous validation error messages
              clearGoalValidationMessage('LHS');
              clearGoalValidationMessage('RHS');
              
              setProofStarted(true);
              
              // Mark this as an active proof session for restoration on page refresh
              sessionStorage.setItem('inductionProofActive', 'true');
              
              // Load any existing proof lines from database to restore highlighting
              setTimeout(() => {
                loadProofLinesFromDatabase();
              }, 100);
            } catch (err) {
              console.error('Engine setup failed:', err);
              const errorMsg = err.response?.data?.error 
                || err.response?.data?.message 
                || (err.response?.data?.errors?.length ? err.response.data.errors.join('\n') : null)
                || err.message 
                || 'Unknown error';
              toast.error(`Failed to initialize induction engine: ${errorMsg}`);
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
      let sourceSelectedNode;
      
      if (padIndex === 1) {
        // Source is premise (line 000)
        currentRacket = showSide === "LHS"
          ? leftPremise?.racket || formValues.lHSGoal
          : rightPremise?.racket || formValues.rHSGoal;
        sourcePad = padRefs.current ? padRefs.current[0] : null;
        // Get selectedNode from premise state
        sourceSelectedNode = showSide === "LHS"
          ? (leftPremise?.selectedNode ?? leftPremise?.startPosition ?? 0)
          : (rightPremise?.selectedNode ?? rightPremise?.startPosition ?? 0);
      } else {
        // Source is the previous line (padIndex - 1 in array, since array index = line number)
        const sourceField = racketRuleFields[showSide][padIndex - 1];
        currentRacket = sourceField?.racket || "";
        sourcePad = padRefs.current ? padRefs.current[padIndex - 1] : null;
        // Get selectedNode from the source field state
        sourceSelectedNode = sourceField?.selectedNode ?? sourceField?.startPosition ?? 0;
      }
      
      const startPos = sourcePad?.getStartPosition?.() ?? 0;
      const selectedNode = sourceSelectedNode;

      const payload = {
        substitution,
        rule,
        startPosition: startPos,
        selectedNode: selectedNode,
        currentRacket: currentRacket,
        side: showSide,
        case: isAnchor ? "base" : "leap",
        lineNumber: padIndex  // Tell backend which line to update
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
            resultNode: response.resultNodeId ?? 0,
            jsonTree: response.jsonTree || {},
            deleted: false
          };

          setRacketRuleFields((prev) => {
            const currentFields = prev[showSide];
            const sideArray = [...currentFields];
            
            // If we're editing a middle line (bound line), replace it
            // Otherwise append to the end
            const isEditingMiddle = padIndex >= 0 && padIndex < sideArray.length - 1;
            
            if (isEditingMiddle) {
              // Replace the bound line at padIndex
              sideArray[padIndex] = newField;
              // Ensure there's a trailing blank line
              const endLast = sideArray[sideArray.length - 1];
              const endIsEmpty = endLast && endLast.racket === "" && endLast.rule === "";
              if (!endIsEmpty) {
                sideArray.push(EMPTY_INITIAL_FIELD);
              }
            } else {
              // Editing the end - check if the last field is empty
              const lastField = sideArray[sideArray.length - 1];
              const lastIsEmpty = !lastField?.racket || lastField.racket.trim() === '';
              
              if (lastIsEmpty) {
                sideArray[sideArray.length - 1] = newField;  // Replace last empty field
                sideArray.push(EMPTY_INITIAL_FIELD);  // Add new trailing empty
              } else {
                sideArray.push(newField);  // Append new field
                sideArray.push(EMPTY_INITIAL_FIELD);  // Add trailing empty
              }
            }
            
            return {
              ...prev,
              [showSide]: sideArray
            };
          });

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
    // Since array index now equals database line_number, use index directly as padIndex
    const padIndex = index;
    
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
    
    // Since array index now equals database line_number, use index directly
    const lineNum = index;
    const ruleValue = isPremise ? "Premise" : field.rule;
    const rulePlaceholder = isPremise ? `${side} Premise` : `${side} Rule`;
    const isRuleInvalid = !isPremise && !!validationErrors[side][index];
    const ruleValidationError = validationErrors[side][index];

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

    // Extract resultNode from current line (shows what changed in this line's transformation)
    const resultNodeValue = isPremise ? undefined : (field && field.resultNode);

    return (
      <Row className="racket-rule-row" id={`racket-row-${padIndex}`} key={isPremise ? `premise-${caseType}-${side}` : `${side}-field-${padIndex}`}>
        <Col xs="auto" style={{ minWidth: '50px', paddingRight: '5px', position: 'relative', top: '35px' }}>
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
            resultNode={resultNodeValue}
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
      // Array index now equals line number, so use padIndex directly
      const field = racketRuleFields[showSide][padIndex];
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
          onRuleChange={e => {
            setFooterRule(e.target.value.trim());
            setFooterRuleError('');
          }}
          onRuleKeyDown={handleRuleKeyDown}
          isRuleReadOnly={false}
          rulePlaceholder={`${showSide} Rule`}
          isRuleInvalid={!!footerRuleError}
          ruleValidationError={footerRuleError}
          isEditRow={true}
        />
      );
    }
  };

  const handleDropdownToggle = (isOpen, menuId) => {
    if (isOpen) {
      requestAnimationFrame(() => {
        const menu = document.getElementById(menuId);
        
        if (menu) {
          menu.classList.remove('is-positioned');
          window.dispatchEvent(new Event('resize'));

          setTimeout(() => {
            menu.classList.add('is-positioned');
          }, 70);
        }
      });
    } else {
      const menu = document.getElementById(menuId);
      if (menu) menu.classList.remove('is-positioned');
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
          <Definitions 
            toggleDefinitionsWindow={toggleDefinitionsWindow} 
            isLocked={proofStarted}
          />
        )}

        {showProofComplete && <ProofComplete onDismiss={() => setShowProofComplete(false)} />}

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
          onSubmit={handleERRacketSubmission}
        >
        <div className="form-top-section" ref={topSectionRef}>
            {/* ROW 1: MASTER HEADER */}
            <Row className="page-header-row align-items-center g-0 w-100" style={{ paddingRight: '40px' }}>    
                {isHeaderCollapsed && (
                    <div className="d-flex align-items-center w-100 flex-wrap gap-2 px-3">
                        <Col xs="auto">
                            <h1 style={{ marginBottom: 0, fontSize: '24px', whiteSpace: 'nowrap' }}>Induction: Racket</h1>
                        </Col>
                        <Col xs="auto" className="d-flex gap-2 ms-2">
                            <Button
                                size="sm"
                                onClick={handleToggleSide}
                                style={{ backgroundImage: 'linear-gradient(135deg, #07294d 0, #006298 100%)', color: '#ffffff', border: 'none', height: '40px', width: '40px', flexShrink: 0 }}
                            >
                                {showSide === "LHS" ? "⋘" : "⋙"}
                            </Button>
                            <Button
                                size="sm"
                                onClick={handleToggleCase}
                                style={{ backgroundImage: 'linear-gradient(135deg, #07294d 0, #006298 100%)', color: '#ffffff', border: 'none', height: '40px', width: '40px', flexShrink: 0 }}
                            >
                                {isAnchor ? "B" : "L"}
                            </Button>
                        </Col>

                        <Form.Group as={Col} className={`er-proof-current-lhs ${showSide === "LHS" ? "active" : ""}`}>
                            <Form.Floating style={{ border: showSide === "LHS" ? '3px solid #0d6efd' : '1px solid #ced4da', borderRadius: '0.375rem', minWidth: 'fit-content' }}>
                                <Form.Control 
                                  type="text" value={lhsValue || (proofStarted ? (leftPremise?.racket || currentLHS) : '')} 
                                  readOnly 
                                  style={{ cursor: "not-allowed", border: 'none', height: '40px', minWidth: `${Math.max((lhsValue?.length || 11), 11)}ch` }} 
                                />
                                <label>Current LHS</label>
                            </Form.Floating>
                        </Form.Group>

                        <Form.Group as={Col} className={`er-proof-current-rhs ${showSide === "RHS" ? "active" : ""}`}>
                            <Form.Floating style={{ border: showSide === "RHS" ? '3px solid #0d6efd' : '1px solid #ced4da', borderRadius: '0.375rem', minWidth: 'fit-content' }}>
                                <Form.Control 
                                  type="text" 
                                  value={rhsValue || (proofStarted ? (rightPremise?.racket || currentRHS) : '')} 
                                  readOnly 
                                  style={{ cursor: "not-allowed", border: 'none', height: '40px', minWidth: `${Math.max((lhsValue?.length || 11), 11)}ch` }} 
                                />
                                <label>Current RHS</label>
                            </Form.Floating>
                        </Form.Group>
                        
                        <Col xs="auto">
                            <Dropdown 
                              align="end"
                              className="proof-dropdown-btn proof-utilities"
                              onToggle={(isOpen) => handleDropdownToggle(isOpen, 'menu-collapsed')}
                            >
                              <Dropdown.Toggle variant="success" id="toggle-collapsed" style={{ minWidth: '50px' }}>
                                <i className="fas fa-tools"></i>
                              </Dropdown.Toggle>
                              <Dropdown.Menu
                                id="menu-collapsed"
                                popperConfig={{
                                  strategy: 'fixed',
                                  modifiers: [
                                    { name: 'preventOverflow', options: { boundary: 'viewport' } }
                                  ]
                                }}
                              >
                                  <Dropdown.Item onClick={toggleDefinitionsWindow} href="#">
                                    Definitions
                                  </Dropdown.Item>
                                  <Dropdown.Item onClick={toggleOffcanvas} href="#">
                                    View Rule Set
                                  </Dropdown.Item>
                                  <Dropdown.Item 
                                    onClick={checkCurrentProofStatus} 
                                    href="#" 
                                    disabled={!proofStarted}
                                    style={{ opacity: proofStarted ? 1 : 0.4, cursor: proofStarted ? 'pointer' : 'not-allowed' }}
                                  >
                                    Check Current Proof
                                  </Dropdown.Item>
                                  <Dropdown.Divider />
                                  <Dropdown.Item 
                                    onClick={handleClearProof} 
                                    href="#" 
                                    disabled={!proofStarted}
                                    style={{ 
                                      color: proofStarted ? 'red' : '#999', 
                                      opacity: proofStarted ? 1 : 0.4,
                                      cursor: proofStarted ? 'pointer' : 'not-allowed'
                                    }}
                                  >
                                    Clear Proof
                                  </Dropdown.Item>
                                </Dropdown.Menu>
                            </Dropdown>
                        </Col>
                        {proofStarted && proofStatus[isAnchor ? 'base' : 'leap'] && (
                              <span
                                style={{
                                  fontWeight: "700",
                                  color: proofStatus[isAnchor ? 'base' : 'leap'].state === "complete" ? "green" : "red",
                                  fontSize: "16px"
                                }}
                              >
                                {proofStatus[isAnchor ? 'base' : 'leap'].state === "complete"
                                  ? `${proofStatus[isAnchor ? 'base' : 'leap'].label} COMPLETE`
                                  : `${proofStatus[isAnchor ? 'base' : 'leap'].label} INCOMPLETE`}
                              </span>
                            )}
                    </div>
                )}
            </Row>

            {/* EXPANDED VIEW: 3-COLUMN DASHBOARD */}
            {!isHeaderCollapsed && (
              <Row className="proof-dashboard align-items-stretch g-0 mt-1 d-flex flex-row flex-wrap justify-content-center align-items-start w-100">
                  {/* COLUMN 1: SIDE SWITCH (Sidebar) */}
                  <Col xs={12} md="auto" className="d-flex flex-column justify-content-center align-items-center px-4 mb-3 mb-md-0" style={{ minWidth: '300px', borderRight: windowWidth >= 768 ? '1px solid #dee2e6' : 'none' }}>
                      <Row className="mb-2 mt-4">
                        <h1 style={{ marginBottom: '10px', fontSize: '36px', whiteSpace: 'nowrap' }}>Induction: Racket</h1>
                      </Row>
                      {proofStarted && (
                        <Row className="mb-3">
                          <div className="text-center">
                              <div style={{ color: '#F2A007', fontWeight: 'bold', fontSize: '20px' }}>SIDE = {showSide}</div>
                              <Button size="lg" className="switch-btn w-auto px-4 mt-2" onClick={handleToggleSide} style={{ backgroundImage: 'linear-gradient(135deg, #07294d 0, #006298 100%)', color: '#ffffff', border: 'none', whiteSpace: 'nowrap' }}>
                                  {showSide === "LHS" ? "Switch Side ⋙" : "⋘ Switch Side"}
                              </Button>
                          </div>
                        </Row>
                      )}
                  </Col>

                  {/* COLUMN 2: CENTER DATA (Wrappable) */}
                  <Col xs={12} md className="px-4 flex-grow-1" style={{ minWidth: '350px' }}>
                      <Row className="g-2 mb-1">
                          <Form.Group as={Col} sm="6"><Form.Floating><Form.Control id="eRProofName" name="proofName" type="text" placeholder="Name" value={formValues.proofName} onBlur={() => handleBlur("proofName")} onChange={handleChange} disabled={proofStarted} required />
                            <label>Proof Name</label>
                            </Form.Floating>
                            </Form.Group>
                          <Form.Group as={Col} sm="6"><Form.Floating>
                            <Form.Control id="eRProofTag" name="proofTag" type="text" placeholder="Tag" value={formValues.proofTag} onBlur={() => handleBlur("proofTag")} onChange={handleChange} disabled={proofStarted} required /><label># Tag</label></Form.Floating></Form.Group>
                      </Row>
                      <Row className="g-2 mb-1">
                          <Form.Group as={Col} md="4"><label className="form-label small fw-bold mb-0">IVar</label><RacketInput id="eRInductionVariable" name="inductionVariable" value={formValues.inductionVariable} onBlur={() => handleBlur("inductionVariable")} onChange={handleChange} onKeyUp={inductionVarKeyUp} onClick={inductionVarSelect} ref={inductionVarRef} highlightPositions={inductionVarHighlights} disabled={proofStarted} /></Form.Group>
                          <Form.Group as={Col} md="4"><label className="form-label small fw-bold mb-0">AVal</label><RacketInput id="eRInductionValue" name="inductionValue" value={formValues.inductionValue} onBlur={() => handleBlur("inductionValue")} onChange={handleChange} onKeyUp={inductionValKeyUp} onClick={inductionValSelect} ref={inductionValRef} highlightPositions={inductionValHighlights} disabled={proofStarted} /></Form.Group>
                          <Form.Group as={Col} md="4"><label className="form-label small fw-bold mb-0">LVar</label><RacketInput id="eRLeapVariable" name="leapVariable" value={formValues.leapVariable} onBlur={() => handleBlur("leapVariable")} onChange={handleChange} onKeyUp={leapVarKeyUp} onClick={leapVarSelect} ref={leapVarRef} highlightPositions={leapVarHighlights} disabled={proofStarted} /></Form.Group>
                      </Row>
                      <Row className={`g-5 mb-${(!proofStarted || !isAnchor) ? "1" : "3"}`}>
                          <Form.Group as={Col} md="6" className="er-proof-goal-lhs">
                            <label className="form-label small fw-bold mb-0">LHS Goal</label>
                            <RacketInput id="eRProofLHSGoal" name="lHSGoal" value={formValues.lHSGoal} onBlur={() => handleBlur("lHSGoal")} onChange={enhancedHandleChange} onKeyUp={lhsGoalKeyUp} onClick={lhsGoalSelect} ref={lhsGoalRef} highlightPositions={lhsGoalHighlights} disabled={proofStarted} />
                            </Form.Group>
                          <Form.Group as={Col} md="6" className="er-proof-goal-rhs">
                            <label className="form-label small fw-bold mb-0">RHS Goal</label>
                            <RacketInput id="eRProofRHSGoal" name="rHSGoal" value={formValues.rHSGoal} onBlur={() => handleBlur("rHSGoal")} onChange={enhancedHandleChange} onKeyUp={rhsGoalKeyUp} onClick={rhsGoalSelect} ref={rhsGoalRef} highlightPositions={rhsGoalHighlights} disabled={proofStarted} />
                            </Form.Group>
                      </Row>
                      {(!proofStarted || !isAnchor) && (
                        <Row className="g-5 mb-3">
                          <Form.Group as={Col} md="6" className="er-inductive-hypothesis-lhs">
                              <label htmlFor="eRInductiveHypothesisLHS" className="form-label small fw-bold mb-0">IH LHS</label>
                              <RacketInput
                                id="eRInductiveHypothesisLHS"
                                name="inductiveHypothesisLHS"
                                type="text"
                                placeholder="Inductive Hypothesis LHS"
                                value={inductiveHypothesisLHS}
                                onChange={(e) => setInductiveHypothesisLHS(e.target.value)}
                                onKeyUp={ihLhsKeyUp}
                                onClick={ihLhsSelect}
                                ref={ihLhsRef}
                                highlightPositions={ihLhsHighlights}
                                disabled={proofStarted}
                              />
                          </Form.Group>
                          <Form.Group as={Col} md="6" className="er-inductive-hypothesis-rhs">
                              <label htmlFor="eRInductiveHypothesisRHS" className="form-label small fw-bold mb-0">IH RHS</label>
                              <RacketInput
                                id="eRInductiveHypothesisRHS"
                                name="inductiveHypothesisRHS"
                                type="text"
                                placeholder="Inductive Hypothesis RHS"
                                value={inductiveHypothesisRHS}
                                onChange={(e) => setInductiveHypothesisRHS(e.target.value)}
                                onKeyUp={ihRhsKeyUp}
                                onClick={ihRhsSelect}
                                ref={ihRhsRef}
                                highlightPositions={ihRhsHighlights}
                                disabled={proofStarted}
                              />
                          </Form.Group>
                        </Row>
                      )}
                      <Row className="justify-content-center er-current-state g-2 mb-0">
                          <Form.Group as={Col} sm="6" className={showSide === "LHS" ? "active" : ""}><Form.Floating style={{ border: showSide === "LHS" ? '3px solid #0d6efd' : '1px solid #ced4da', borderRadius: '0.375rem' }}><Form.Control type="text" value={lhsValue || (proofStarted ? (leftPremise?.racket || currentLHS) : '')} readOnly style={{ border: 'none' }} /><label>Current LHS</label></Form.Floating></Form.Group>
                          <Form.Group as={Col} sm="6" className={showSide === "RHS" ? "active" : ""}><Form.Floating style={{ border: showSide === "RHS" ? '3px solid #0d6efd' : '1px solid #ced4da', borderRadius: '0.375rem' }}><Form.Control type="text" value={rhsValue || (proofStarted ? (rightPremise?.racket || currentRHS) : '')} readOnly style={{ border: 'none' }} /><label>Current RHS</label></Form.Floating></Form.Group>
                      </Row>
                  </Col>

                  {/* COLUMN 3: CASE SWITCH (Wraps and stays horizontally aligned) */}
                  <Col 
                      xs={12} 
                      xl="auto" 
                      className="d-flex flex-row flex-xl-column flex-wrap justify-content-center align-items-center px-4 mt-3 mt-xl-0"
                      style={{ minWidth: '300px', borderLeft: windowWidth >= 1200 ? '1px solid #dee2e6' : 'none', gap: '20px', minHeight: '100%' }}
                    >
                    {/* Item 1: Dropdown */}
                    <Dropdown 
                      align="end"
                      className="proof-dropdown-btn proof-utilities"
                      onToggle={(isOpen) => handleDropdownToggle(isOpen, 'menu-expanded')}
                    >
                      <Dropdown.Toggle id="toggle-expanded" style={{ minWidth: '200px' }}>
                        Proof Utilities
                      </Dropdown.Toggle>
                      <Dropdown.Menu 
                        id="menu-expanded"
                        style={{ minWidth: '200px' }}
                        popperConfig={{
                          strategy: 'fixed',
                          modifiers: [
                            { name: 'preventOverflow', options: { boundary: 'viewport' } }
                          ]
                        }}
                      >
                        <Dropdown.Item onClick={toggleDefinitionsWindow} href="#">Definitions</Dropdown.Item>
                        <Dropdown.Item onClick={toggleOffcanvas} href="#">View Rule Set</Dropdown.Item>
                        <Dropdown.Item 
                          onClick={checkCurrentProofStatus} 
                          disabled={!proofStarted}
                          style={{ opacity: proofStarted ? 1 : 0.4 }}
                        >
                          Check Current Proof
                        </Dropdown.Item>
                        <Dropdown.Divider />
                        <Dropdown.Item onClick={handleClearProof} disabled={!proofStarted} style={{ color: 'red' }}>
                          Clear Proof
                        </Dropdown.Item>
                      </Dropdown.Menu>
                    </Dropdown>
                    {proofStarted && proofStatus[isAnchor ? 'base' : 'leap'] && (
                      <span
                        style={{
                          fontWeight: "700",
                          color: proofStatus[isAnchor ? 'base' : 'leap'].state === "complete" ? "green" : "red",
                          fontSize: "20px"
                        }}
                      >
                        {proofStatus[isAnchor ? 'base' : 'leap'].state === "complete"
                          ? `${proofStatus[isAnchor ? 'base' : 'leap'].label} COMPLETE`
                          : `${proofStatus[isAnchor ? 'base' : 'leap'].label} INCOMPLETE`}
                      </span>
                    )}

                    {/* Item 2: Radios */}
                    <div className="check-row d-flex align-items-center px-3 border rounded bg-light" style={{ height: '58px' }}>
                      <Form.Check 
                        type="radio" id="integers" label="Integers" name="inductionType" 
                        value="integers" className="me-3" onChange={handleChange} defaultChecked 
                      />
                      <Form.Check 
                        type="radio" id="lists" label="Lists" name="inductionType" 
                        value="lists" onChange={handleChange} 
                      />
                    </div>

                    {/* Item 3: Case Switch */}
                    {proofStarted && (
                      <div className="text-center d-flex flex-column align-items-center">
                        <div style={{ color: '#F2A007', fontWeight: 'bold', fontSize: '20px', whiteSpace: 'nowrap' }}>
                          CASE = {isAnchor ? "BASE" : "LEAP"}
                        </div>
                        <Button 
                          size="lg" 
                          className="switch-btn w-auto px-4 mt-1" 
                          onClick={handleToggleCase} 
                          style={{ backgroundImage: 'linear-gradient(135deg, #07294d 0, #006298 100%)', color: '#ffffff', border: 'none', whiteSpace: 'nowrap' }}
                        >
                          {isAnchor ? "Switch to Leap Case" : "Switch to Base Case"}
                        </Button>
                      </div>
                    )}
                  </Col>
              </Row>
            )}

            {/* ARROW CONTROLS - Positioned at bottom right of the flow */}
            {proofStarted && (
              <div className="d-flex justify-content-end pr-2" style={{ marginTop: '-40px' }}>
                <Button
                  variant="link"
                  className="p-0 text-decoration-none"
                  onClick={() => setIsHeaderCollapsed(!isHeaderCollapsed)}
                  size="lg"
                  style={{ color: '#6c757d', zIndex: 1050 }}
                >
                  <i className={`fas ${isHeaderCollapsed ? 'fa-angles-down' : 'fa-angles-up'}`}></i>
                </Button>
              </div>
            )}

            <Form.Text
              as={"div"}
              id="formSeparator"
              className="form-separator"
            ></Form.Text>
        </div>

          <div className="form-bottom-part" style={{ paddingTop: `${topSectionHeight}px` }}>

            {!proofStarted && 
              !isGoalChecked[showSide]?.LeapGoal &&
              !isGoalChecked[showSide]?.AnchorGoal && (
                <Row className="goal-btn-wrap mt-4">
                  <Button
                    className="orange-btn"
                    type="submit"
                  >
                    Start Induction Proof
                  </Button>
                </Row>
              )}
          </div>
        </Form>
      </Container>
      
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
            {racketRuleFields[showSide].map((field, index) =>
              field.deleted
                ? null
                : renderPersistentPadRow({
                  side: showSide,
                  isPremise: index === 0,
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
          }}
        >
          <Row className="input-row mb-0 align-items-center">
            <Col 
              xs 
              className="flex-shrink-1" 
              style={{ 
                maxWidth: `${Math.max(7, (userRow.num || "").length) + 4}ch`,
                minWidth: '7ch'
              }}
            >
              <Form.Floating className="mb-3">
                <Form.Control
                  id="userRowNum"
                  name="userRowNum"
                  type="text"
                  placeholder="Num"
                  value={userRow.num}
                  onChange={(e) => setUserRow({ ...userRow, num: e.target.value })}
                  disabled={isBound}
                  style={{ 
                    maxWidth: `${Math.max(7, (userRow.num || "").length) + 4}ch`,
                    minWidth: '7ch' 
                  }}
                />
                <label htmlFor="userRowNum">Num</label>
              </Form.Floating>
            </Col>

            {!isBound && (
              <Col xs="auto" className="d-flex flex-shrink-0">
                <Button
                  variant="primary"
                  onClick={() => bindFooterToRow(userRow.num)}
                  style={{ textWrap: "nowrap" }}
                >
                  Fill Values
                </Button>
              </Col>
            )}

            <Col className="flex-grow-1">
              {isBound && renderFooterPad()}
            </Col>

            {isBound && (
              <Col xs="auto" className="d-flex flex-shrink-0">
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
            <Row className="button-row mt-0">
              <Col md="3" className="d-none d-md-block"></Col>
              <Col xs="12" md="8" className="rules-btn-grp">
                <Button
                  className="orange-btn delete-btn"
                  disabled={(() => {
                    // Disabled if not bound
                    if (!isBound) {
                      return true;
                    }
                    
                    const lineNum = parseInt(userRow.num, 10);
                    
                    // Disabled if premise line (line 0)
                    if (lineNum === 0) {
                      return true;
                    }
                    
                    // Disabled if line is blank
                    const fields = racketRuleFields[showSide];
                    
                    if (!fields || !fields[lineNum]) {
                      return true;
                    }
                    
                    const racket = (fields[lineNum].racket || '').trim();
                    
                    if (racket === '') {
                      return true;
                    }
                    
                    // Enable for non-blank, non-premise lines
                    return false;
                  })()}
                  onClick={() => setShowClearConfirm(true)}
                >
                  Clear Line
                </Button>
                <Button
                  className="orange-btn green-btn"
                  onClick={handleGenerateAndCheck}
                  disabled={!isBound}
                >
                  {windowWidth < 576 ? "Gen & Check" : "Generate & Check"}
                </Button>
                <Button
                  className="orange-btn green-btn"
                  onClick={() => updateShowSubstitution()}
                  disabled={!isBound}
                >
                  {windowWidth < 576 ? "Sub" : "Substitution"}
                </Button>
              </Col>
            </Row>
          )}
        </div>
        );
      })()}

      {/* Clear Line Confirmation Modal */}
      <Modal show={showClearConfirm} onHide={() => setShowClearConfirm(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>Clear Line</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          This will clear the racket expression and rule justifications for line {userRow.num}. Do you wish to proceed?
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowClearConfirm(false)}>
            No
          </Button>
          <Button variant="danger" onClick={async () => {
            setShowClearConfirm(false);
            const caseKey = isAnchor ? 'base' : 'leap';
            const lineNum = parseInt(userRow.num, 10);
            
            // Reset proof status
            setProofStatus(prev => ({ ...prev, [caseKey]: null }));
            
            try {
              // Call backend to clear line in database and reset completion flags
              await inductionService.deleteLine(isAnchor ? 'base' : 'leap', showSide, lineNum);
              
              // Update local state to clear the line
              const targetFields = isAnchor ? baseRacketFields : leapRacketFields;
              
              const updatedFields = { ...targetFields };
              updatedFields[showSide] = [...updatedFields[showSide]];
              
              // Clear the line at lineNum index
              updatedFields[showSide][lineNum] = {
                racket: '',
                jsonTree: {},
                rule: '',
                startPosition: 0,
                selectedNode: 0,
                resultNode: 0,
                deleted: false
              };
              
              // Clear result-highlight on next line if it exists
              if (updatedFields[showSide][lineNum + 1]) {
                updatedFields[showSide][lineNum + 1] = {
                  ...updatedFields[showSide][lineNum + 1],
                  rule: '',
                  resultNode: 0
                };
              }
              
              // Clear selectedNode on previous line if it exists and isn't premise
              if (lineNum > 0 && updatedFields[showSide][lineNum - 1]) {
                updatedFields[showSide][lineNum - 1] = {
                  ...updatedFields[showSide][lineNum - 1],
                  selectedNode: 0
                };
              }
              
              // Update the appropriate state
              if (isAnchor) {
                setBaseRacketFields(updatedFields);
              } else {
                setLeapRacketFields(updatedFields);
              }
            } catch (e) {
              toast.error('Failed to clear line');
            }
          }}>
            Yes
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Overwrite Proof Confirmation Modal */}
      <Modal show={showOverwriteModal} onHide={() => setShowOverwriteModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>Confirm Overwrite of Proof</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          A proof with the name "<strong>{formValues.proofName}</strong>" and tag "<strong>{formValues.proofTag}</strong>" 
          already exists. Starting this proof will overwrite the existing one. Do you wish to proceed?
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowOverwriteModal(false)}>
            Cancel
          </Button>
          <Button variant="danger" onClick={() => {
            setShowOverwriteModal(false);
            setShowStartConfirmModal(true);
          }}>
            Overwrite & Start
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Start Proof Confirmation Modal */}
      <Modal show={showStartConfirmModal} onHide={() => setShowStartConfirmModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>Start Proof</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <p>
            Starting this proof will lock the current state of your Definitions. 
            You will not be able to create, edit, enable, or disable definitions until you clear the proof.
          </p>
          <p>Are you sure you want to continue?</p>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowStartConfirmModal(false)}>
            Cancel
          </Button>
          <Button variant="primary" onClick={actuallyStartInductionProof}>
            Start Proof
          </Button>
        </Modal.Footer>
      </Modal>
    </MainLayout>
  );
};

export default InductionRacket;
