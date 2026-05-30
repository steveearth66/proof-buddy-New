import React, { useState, useEffect, useRef, useCallback, useMemo } from "react";
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
import userService from "../services/userService";
import erService from "../services/erService";
import SetParametersModal from "../components/SetParametersModal";
import {
  ARROW_KEYS,
  EMPTY_INITIAL_FIELD,
  getPadRefs,
  getPadIndex
} from "../utils/erRacketUtils";
import {
  initPlayState,
  isActive as playIsActive,
  visibleLineCount,
  showContinue,
  advancePlay,
  cancelPlay,
  getLastRealIndex
} from "../utils/playModeUtils";
import { useLocation } from "react-router-dom";
import CommentsModal from "../components/CommentsModal";

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

  // Play mode state: tracks per-case per-side progress when opened via "Run Proof"
  const [playState, setPlayState] = useState(() => initPlayState(['base', 'leap'], ['LHS', 'RHS'], false));

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
  const [lhsHidden, setLhsHidden] = useState(false);
  const [rhsHidden, setRhsHidden] = useState(false);
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
  const [conflictType, setConflictType] = useState(null);
  const [currentUserType, setCurrentUserType] = useState(null);
  const [proofOwner, setProofOwner] = useState(null);
  const [showSetParams, setShowSetParams] = useState(false);
  const [proofParams, setProofParams] = useState({
    proof_id: null,
    support_errors: true,
    support_current_lhs_rhs: true,
    support_ih: true,
    support_premise: true,
    support_rule_set: true,
    support_value_mapping: true,
    visible_rules: {},
    support_rewrite_complexity: true
  });
  const [showIHModal, setShowIHModal] = useState(false);
  const [showCommentsModal, setShowCommentsModal] = useState(false);
  const [comments, setComments] = useState({});
  const [activePadIndex, setActivePadIndex] = useState(null);
  const [activeSide, setActiveSide] = useState(null);
  const [studentComment, setStudentComment] = useState("");
  const [instructorComment, setInstructorComment] = useState("");
  const [commentStatus, setCommentStatus] = useState({})

  const rulesInProof = useMemo(() => {
    if (!proofStarted) return [];

    const extractRules = (sideArray) => {
      return (sideArray || [])
        .filter(field => 
          field && 
          !field.deleted && 
          field.rule && 
          field.rule.trim() !== "" && 
          field.rule !== "Premise"
        )
        .map(field => field.rule.trim());
    };

    const baseLHS = extractRules(baseRacketFields?.LHS);
    const baseRHS = extractRules(baseRacketFields?.RHS);
    const leapLHS = extractRules(leapRacketFields?.LHS);
    const leapRHS = extractRules(leapRacketFields?.RHS);

    return [...new Set([...baseLHS, ...baseRHS, ...leapLHS, ...leapRHS])];
  }, [baseRacketFields, leapRacketFields, proofStarted]);

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
  const uploadFileRef = useRef(null);
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
    
    // Check for duplicate proof name (across both Induction and ER proof tables)
    try {
      const conflictCheck = await inductionService.checkNameConflict(formValues.proofName);

      // If a match exists, show overwrite modal
      if (conflictCheck.conflict) {
        setConflictType(conflictCheck.type);
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
    // In play mode, block the check until all lines have been revealed across all cases/sides
    const anyStillActive = ['base', 'leap'].some(ck =>
      ['LHS', 'RHS'].some(s => playIsActive(playState, ck, s))
    );
    if (anyStillActive) {
      toast.warning('Finish reviewing all proof lines before checking completion.');
      return;
    }
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
      const field = (racketRuleFields?.[showSide] || [])[userIndex];
      
      // Only set the rule if it's NOT hidden
      if (field?.hide_justification) {
        setFooterRule("");  // Keep it blank if hidden
      } else {
        setFooterRule(field?.rule || "");
      }
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
        
        // Filter out Line 0 (Premise) for the grid
        const maxLineNum = Math.max(...lines.map(l => l.lineNumber));
        const fields = [];
        
        // Initialize empty
        for (let i = 0; i <= maxLineNum; i++) {
          fields[i] = { ...EMPTY_INITIAL_FIELD };
        }
        
        // Fill data
        lines.forEach(line => {
          fields[line.lineNumber] = {
            racket: line.racket || '',
            rule: line.rule || '',
            startPosition: line.startPosition || 0,
            selectedNode: line.selectedNode || 0,
            substitution: line.substitution || '',
            jsonTree: line.jsonTree || {},
            resultNode: line.resultNode || 0,
            hide_expression: line.hide_expression || false,
            hide_justification: line.hide_justification || false,
            deleted: false
          };
        });
        
        // Always add empty field at the end
        fields.push(EMPTY_INITIAL_FIELD);
        return fields;
      };
      
      // 1. Update the Lines (Base & Leap)
      setBaseRacketFields({
        LHS: buildFieldsFromLines(proofLines.base?.LHS || []),
        RHS: buildFieldsFromLines(proofLines.base?.RHS || [])
      });
      
      setLeapRacketFields({
        LHS: buildFieldsFromLines(proofLines.leap?.LHS || []),
        RHS: buildFieldsFromLines(proofLines.leap?.RHS || [])
      });
      
      // 2. Update the Premises State
      const updatePremiseState = (linesArray, prevPremiseState) => {
        const line0 = linesArray?.find(l => l.lineNumber === 0);
        if (line0) {
            return {
                racket: line0.racket,
                rule: 'Premise',
                startPosition: 0,
                selectedNode: line0.selectedNode || 0,
                jsonTree: line0.jsonTree || {}
            };
        }
        return prevPremiseState; // Fallback to existing if Line 0 missing
      };

      setBasePremises(prev => ({
        LHS: updatePremiseState(proofLines.base?.LHS, prev.LHS),
        RHS: updatePremiseState(proofLines.base?.RHS, prev.RHS)
      }));

      setLeapPremises(prev => ({
        LHS: updatePremiseState(proofLines.leap?.LHS, prev.LHS),
        RHS: updatePremiseState(proofLines.leap?.RHS, prev.RHS)
      }));

    } catch (error) {
      console.error('[loadProofLines] Error loading proof lines:', error);
    }

    // Load support params from getCurrentProof
    try {
      const proofMeta = await inductionService.getCurrentProof();
      if (proofMeta?.hasProof) {
        const PARAM_KEYS = ['proof_id','support_errors','support_current_lhs_rhs','support_ih','support_premise','support_rule_set','support_value_mapping','visible_rules','support_rewrite_complexity'];
        const extracted = {};
        PARAM_KEYS.forEach(k => { if (k in proofMeta) extracted[k] = proofMeta[k]; });
        if (Object.keys(extracted).length > 0) setProofParams(prev => ({ ...prev, ...extracted }));
      }
    } catch (e) {
      // non-critical — params will remain at defaults
    }
  }, [setBaseRacketFields, setLeapRacketFields, setBasePremises, setLeapPremises, setProofParams]);

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

    // Update Current LHS/RHS to match the new case's last DISPLAYED non-empty line (or premise)
    const newCaseKey = newIsAnchor ? 'base' : 'leap';
    const targetFields = newIsAnchor ? baseRacketFields : leapRacketFields;
    const targetPremises = newIsAnchor ? basePremises : leapPremises;
    const lhsLines = targetFields.LHS || [];
    const rhsLines = targetFields.RHS || [];

    // In play mode, clamp scan to only revealed lines; null means show all
    const lhsLimit = visibleLineCount(playState, newCaseKey, 'LHS');
    const rhsLimit = visibleLineCount(playState, newCaseKey, 'RHS');

    // Find last non-empty, non-premise line up to maxVisible (premise is at index 0)
    const findLastNonEmptyLine = (lines, maxVisible) => {
      const limit = maxVisible !== null ? Math.min(maxVisible, lines.length) : lines.length;
      for (let i = limit - 1; i > 0; i--) {
        if (lines[i] && lines[i].racket && lines[i].racket.trim() !== '') {
          return lines[i];
        }
      }
      return null;
    };

    const lastLhsLine = findLastNonEmptyLine(lhsLines, lhsLimit);
    const lastRhsLine = findLastNonEmptyLine(rhsLines, rhsLimit);

    setLhsValue(lastLhsLine?.racket || targetPremises.LHS?.racket || '');
    setRhsValue(lastRhsLine?.racket || targetPremises.RHS?.racket || '');

    // No database reload - state already contains both base and leap cases
    // Reloading would reset any highlighting changes made by clicking (not applying rules)
  }, [isAnchor, baseRacketFields, leapRacketFields, basePremises, leapPremises, playState]);

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
    // Block editing while play mode is active (hidden lines still exist)
    const indCaseKey = isAnchor ? 'base' : 'leap';
    if (showContinue(playState, indCaseKey, showSide, getLastRealIndex(racketRuleFields[showSide] || []))) {
      toast.warning('Lines cannot be edited while still in play mode.');
      return;
    }
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

  const handleNewProof = async () => {
    if (!window.confirm('Start a new proof? Your current proof will remain saved in "All Proofs".')) {
      return;
    }
    try {
      await inductionService.newProof();
      sessionStorage.removeItem('inductionProofActive');
      sessionStorage.removeItem('induction_current_proof_id');
      sessionStorage.removeItem('temp_definitions');
      sessionStorage.removeItem('temp_generics');
      toast.success('Ready to start a new proof!');
      window.location.reload();
    } catch (error) {
      console.error('Error clearing session:', error);
      toast.error('Failed to clear session');
    }
  };

  const handleClearProof = async () => {
    if (!window.confirm('Are you sure you want to discard this proof? It will be archived and hidden from your proofs.')) {
      return;
    }

    try {
      await inductionService.clearInduction();
      
      // Clear sessionStorage flag so we don't restore from DB on reload
      sessionStorage.removeItem('inductionProofActive');
      sessionStorage.removeItem('induction_current_proof_id');
      toast.success('Proof archived successfully');
      
      // Reload the page to start fresh
      window.location.reload();
    } catch (error) {
      console.error('Error clearing proof:', error);
      toast.error('Failed to clear proof');
    }
  };

  const handleDownloadProof = async () => {
    try {
      const data = await inductionService.downloadProof(proofParams.proof_id);
      const fileName = `${data.name || 'proof'}.json`;
      const jsonStr = JSON.stringify(data, null, 2)
          .replace(/[\u0080-\uFFFF]/g, c => '\\u' + c.charCodeAt(0).toString(16).padStart(4, '0'));
      const blob = new Blob([jsonStr], { type: 'application/json; charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = fileName;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading proof:', error);
      toast.error('Failed to download proof.');
    }
  };

  const handleUploadProof = () => {
    if (uploadFileRef.current) {
      uploadFileRef.current.value = '';
      uploadFileRef.current.click();
    }
  };

  const handleUploadFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const text = await file.text();
      const proofData = JSON.parse(text);
      if (proofData.proofType !== 'induction') {
        toast.error('This file is not an induction proof.');
        return;
      }
      const result = await inductionService.uploadProof(proofData);
      // Pre-load the new proof into the backend cache so the page init can find it.
      await inductionService.setSessionById(result.proofId);
      sessionStorage.setItem('induction_current_proof_id', String(result.proofId));
      sessionStorage.setItem('inductionProofActive', 'true');
      toast.success(`Proof "${result.proofName}" uploaded successfully.`);
      window.location.reload();
    } catch (error) {
      console.error('Error uploading proof:', error);
      toast.error('Failed to upload proof. The file may be invalid or corrupted.');
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
      let expressionFromFooter = "";
      let previousStartPosition = 0;
      let previousRacketValue = "";
      let currentIndex = undefined;
      let studentSelectedNode = 0;

      if (isBound) {
        const userIndex = getPadIndex(userRow.num);
        ruleFromFooter = userRow.num === "000" ? "Premise" : footerRule;

        // --- FOOTER EXPRESSION REFERENCE ---
        if (footerPadRef.current) {
            expressionFromFooter = footerPadRef.current.getEquationValue() || "";
        }

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
          studentSelectedNode = previousStartPosition;
          currentIndex = userIndex; // index in array now equals line number
        }
      }

      // Validate rule is entered
      if (!ruleFromFooter || ruleFromFooter.trim() === '') {
        setFooterRuleError('Must enter a rule');
        isProcessingRef.current = false;
        return;
      }

      // Clear validation error if rule is valid
      setFooterRuleError('');

      // If user typed "rewrite math" or "rewrite logic", open Substitution modal with rule pre-filled
      if (ruleFromFooter.trim().toLowerCase() === 'rewrite math' || ruleFromFooter.trim().toLowerCase() === 'rewrite logic') {
        updateShowSubstitution();
        return;
      }

       // --- VALIDATION BLOCK ---
            const boundField = racketRuleFields?.[showSide][currentIndex];
            const hasHiddenRule = boundField?.hide_justification || false;
            const hasHiddenExpression = boundField?.hide_expression || false;
      
            if (hasHiddenRule || hasHiddenExpression) {
              const validationPayload = {
                side: showSide,
                case: isAnchor ? "base" : "leap",
                lineNumber: currentIndex,
                studentRule: ruleFromFooter, // Sending the Rule
                studentExpression: expressionFromFooter, // Sending the Expression
                studentSelectedNode: studentSelectedNode // Sending the Selection
              };
      
              try {
                const validationResult = await inductionService.validateHiddenField(validationPayload);
                
                if (validationResult.errors && validationResult.errors.length > 0) {
                  validationResult.errors.forEach(error => toast.error(error));
                  isProcessingRef.current = false;
                  return;
                }
                
                toast.success(validationResult.message || "Correct!");
                
                setRacketRuleFields(prev => {
                  const updated = { ...prev };
                  if (updated[showSide] && updated[showSide][currentIndex]) {
                    updated[showSide][currentIndex] = {
                      ...updated[showSide][currentIndex],
                      hide_justification: validationResult.hide_justification,
                      hide_expression: validationResult.hide_expression
                    };
                  }
                  return updated;
                });
                
                setFooterRule(boundField.rule);
                unbindFooter();
                return;
                
              } catch (error) {
                toast.error('Error validating your answer.');
                isProcessingRef.current = false;
                return;
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
        selectedNode: previousStartPosition,
        supportRewriteComplexity: proofParams.support_rewrite_complexity,
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
          rule: fullRacket.rule || ruleFromFooter,
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
        toast.error(proofParams.support_errors ? message : "your latest command contains an error"); // support_errors suppression
      }
    } finally {
      isProcessingRef.current = false;
    }
  };
  
  const location = useLocation();
  const initializedRef = useRef(false);
  useEffect(() => {
    if (initializedRef.current) return;

    const initializeProofSession = async () => {
      initializedRef.current = true;
      
      try {
        const profile = await userService.getUserProfile();
        setCurrentUserType(profile);

        // -------------------------------------------------------------
        // STEP 1: NEGOTIATE SESSION ID & WAKE UP BACKEND
        // -------------------------------------------------------------
        const navId = location.state?.id || sessionStorage.getItem('induction_current_proof_id');
        // Capture playMode flag before history state is cleared
        const playModeRequested = location.state?.playMode === true;

        if (navId) {
          // This call is critical: it tells the backend "Load Proof #123 into memory"
          // Without this, subsequent calls like getProofLines would fail or return empty
          await inductionService.setSessionById(navId);

          sessionStorage.setItem('induction_current_proof_id', navId);
          sessionStorage.setItem('inductionProofActive', 'true');
          window.history.replaceState({}, document.title);
        }

        // Store flag so we can activate play mode after lines load
        initializeProofSession._playMode = playModeRequested;

        const isActiveSession = sessionStorage.getItem('inductionProofActive') === 'true';
        
        // If no session is active (fresh page load), stop here and let the UI render blank
        if (!isActiveSession) {
            return;
        }

        // -------------------------------------------------------------
        // STEP 2: HYDRATE FORM METADATA & SANITIZE GENERICS
        // (loadProofLinesFromDatabase does NOT do this part)
        // -------------------------------------------------------------
        if (navId) {
            const metaData = await inductionService.getInductionProof(navId);
            if (metaData?.user?.username) {
                setProofOwner(metaData.user);
            }

            const rawDefinitions = metaData.definition || [];

            // Separate the raw data into generics and definitions (generics have is_generic: true)
            const rawGenerics = rawDefinitions.filter(d => d.is_generic);
            const rawDefs = rawDefinitions.filter(d => !d.is_generic);
            // --- Helper to generate a unique key for generics based on usable fields ---
            const getGenericKey = (g) => `${g.label}|${g.type || ''}`;

            // -------------------------------------------------------------------------
            // GENERICS PROCESSING
            // -------------------------------------------------------------------------
            // 1. Fetch User's permanent generics 
            const userGenerics = await erService.getUserGenerics(); 

            // Sanitize proof generics
            const proofGenerics = rawGenerics.map(g => ({
                ...g,
                label: g.label || g.name,
                name: g.name || g.label,
                restrictions: g.restrictions || { assumption: 'None', neverNull: false }
            }));

            // 2. Identify active IDs from the loaded proof
            const activeProofGenericKeys = new Set(proofGenerics.map(getGenericKey));

            // 3. Process Permanent Generics: Toggle 'applied' based on proof contents
            const updatedPermanentGenerics = userGenerics.map(gen => ({
                ...gen,
                enabled: activeProofGenericKeys.has(getGenericKey(gen))
            }));

            // 4. Filter for Temporary items (those in proofData but NOT in user's DB)
            const tempGenerics = proofGenerics.filter(
                proofGen => !userGenerics.some(userGen => getGenericKey(proofGen) === getGenericKey(userGen))
            );

            // 5. Commit lists to Session Storage
            sessionStorage.setItem('generics', JSON.stringify(updatedPermanentGenerics));

            if (tempGenerics.length > 0) {
                sessionStorage.setItem('temp_generics', JSON.stringify(tempGenerics));
            } else {
                sessionStorage.removeItem('temp_generics');
            }

            // Notify other components that generics are ready
            window.dispatchEvent(new CustomEvent('genericsUpdated', { 
                detail: { allGenerics: [...updatedPermanentGenerics] } 
            }));

            // -------------------------------------------------------------------------
            // DEFINITIONS PROCESSING
            // -------------------------------------------------------------------------
            // 1. Fetch User's permanent definitions
            const userDefs = await erService.getUserDefinitions();

            // 2. Identify active IDs from the loaded proof
            const activeProofDefKeys = new Set(
                rawDefs.map(d => `${d.label}|${d.expression}`)
            );

            // 3. Process Permanent Definitions: Toggle 'applied' based on proof contents
            const updatedPermanentDefs = userDefs.map(def => ({
                ...def,
                applied: activeProofDefKeys.has(`${def.label}|${def.expression}`)
            }));

            // 4. Filter for Temporary items (those in proofData but NOT in user's DB)
            const tempDefinitions = rawDefs.filter(
                dbDef => !userDefs.some(d => dbDef.label === d.label && dbDef.expression === d.expression)
            );

            // 5. Commit lists to Session Storage
            sessionStorage.setItem('definitions', JSON.stringify(updatedPermanentDefs));

            if (tempDefinitions.length > 0) {
                sessionStorage.setItem('temp_definitions', JSON.stringify(tempDefinitions));
            } else {
                sessionStorage.removeItem('temp_definitions');
            }

            // Hydrate the Top-Level Form Inputs
            setFormValues(prev => ({
                ...prev,
                proofName: metaData.name || prev.proofName,
                proofTag: metaData.tag || prev.proofTag,
                lHSGoal: metaData.lhs_leap_goal || prev.lHSGoal,
                rHSGoal: metaData.rhs_leap_goal || prev.rHSGoal,
                inductionVariable: metaData.induction_variable || prev.inductionVariable,
                inductionValue: metaData.anchor_value || prev.inductionValue,
                leapVariable: metaData.leap_variable || prev.leapVariable,
                inductionType: metaData.induction_type || prev.inductionType
            }));

            setInductiveHypothesisLHS(metaData.inductive_hypothesis_lhs || "");
            setInductiveHypothesisRHS(metaData.inductive_hypothesis_rhs || "");
        }

        // -------------------------------------------------------------
        // STEP 3: LOAD PROOF LINES (Delegated)
        // This function handles fetching lines, mapping fields, and updating state
        // -------------------------------------------------------------
        await loadProofLinesFromDatabase();

        // Activate play mode if the user clicked "Run Proof"
        if (initializeProofSession._playMode) {
          setPlayState(initPlayState(['base', 'leap'], ['LHS', 'RHS'], true));
        }

        setProofStarted(true);

      } catch (error) {
        console.error("Failed to restore session", error);
        toast.error("Failed to load previous session.");
      }
    };

    initializeProofSession();
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

  // Update Current LHS/RHS display to show the last non-empty DISPLAYED line
  useEffect(() => {
    if (!proofStarted) return;

    const indCaseKey = isAnchor ? 'base' : 'leap';
    const targetFields = isAnchor ? baseRacketFields : leapRacketFields;
    const targetPremises = isAnchor ? basePremises : leapPremises;
    const lhsLines = targetFields.LHS || [];
    const rhsLines = targetFields.RHS || [];

    // In play mode, clamp scan to only revealed lines; null means show all
    const lhsLimit = visibleLineCount(playState, indCaseKey, 'LHS');
    const rhsLimit = visibleLineCount(playState, indCaseKey, 'RHS');

    // Find last non-empty, non-premise line up to maxVisible (premise is at index 0)
    const findLastNonEmptyLine = (lines, maxVisible) => {
      const limit = maxVisible !== null ? Math.min(maxVisible, lines.length) : lines.length;
      for (let i = limit - 1; i > 0; i--) {
        if (lines[i] && lines[i].racket && lines[i].racket.trim() !== '') {
          return lines[i];
        }
      }
      return null;
    };

    const lastLhsLine = findLastNonEmptyLine(lhsLines, lhsLimit);
    const lastRhsLine = findLastNonEmptyLine(rhsLines, rhsLimit);
    setLhsValue(lastLhsLine?.racket || targetPremises.LHS?.racket || '');
    setLhsHidden(((isReviewMode ? proofOwner.is_student : !currentUserType.is_student) && lastLhsLine?.hide_expression) || false);
    setRhsValue(lastRhsLine?.racket || targetPremises.RHS?.racket || '');
    setRhsHidden(((isReviewMode ? proofOwner?.is_student : !currentUserType?.is_student) && lastRhsLine?.hide_expression) || false);

  }, [proofStarted, isAnchor, baseRacketFields, leapRacketFields, basePremises, leapPremises, playState]);

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

  // Clear inductive hypotheses when switching to high support
  useEffect(() => {
  if (proofParams.support_ih) {
    setInductiveHypothesisLHS('');
    setInductiveHypothesisRHS('');
  }
  }, [proofParams.support_ih]);

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
   * - anchor/induction value is a nonnegative integer
   * - leap variable does not appear in LHS, RHS, or equal induction variable
   *
   * On success, calls checkGoal(...) to proceed.
   *
   * Uses exact error messages requested:
   * "Anchor value must be a nonnegative integer."
   * "Leap variable must not overlap with variables in the goal."
   * 
   * Note: Induction variable parameter validation removed - backend handles this correctly
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

    const RESERVED_PROOF_NAMES = new Set(["IH", "length", "append", "reverse"]);
    if (RESERVED_PROOF_NAMES.has((proofName || "").trim())) {
      toast.error(`'${(proofName || "").trim()}' is a reserved name and cannot be used as a proof name.`);
      return;
    }
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

    // Ensure induction variable is provided
    const ivar = inductionVariable ? inductionVariable.trim() : "";
    if (!ivar) {
      toast.error("Induction variable is required.");
      return;
    }

    if ((!inductiveHypothesisLHS || inductiveHypothesisLHS.trim() === "") && !proofParams?.support_ih) {
      toast.error("Inductive hypothesis for LHS must be provided.");
      return;
    }

    if ((!inductiveHypothesisRHS || inductiveHypothesisRHS.trim() === "") && !proofParams?.support_ih){
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
      // if IH support is set to high, skip this and send the blanks to backend
      if (!proofParams?.support_ih){
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
        definitions: definitions
      };

      const response = await inductionService.startInductionProof(inductionData);

      if (response && response.data) {
        if (response.status === 201 || response.status === 200) {
          setInductiveHypothesisLHS(response.data.inductive_hypothesis_lhs);
          setInductiveHypothesisRHS(response.data.inductive_hypothesis_rhs);

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
                name: genericDef.name,  // Include both 'label' and 'name' for DB compatibility
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

              // Persist any params the user pre-configured before starting the proof.
              // Must be done BEFORE loadProofLinesFromDatabase reads them back from DB.
              const PARAM_KEYS = ['support_errors','support_current_lhs_rhs','support_ih','support_premise','support_rule_set','support_value_mapping', 'visible_rules','support_rewrite_complexity'];
              const hasCustomParams = PARAM_KEYS.some(k => proofParams[k] !== true && (typeof proofParams[k] === 'object' && proofParams[k].length > 0));
              if (hasCustomParams) {
                try {
                  await inductionService.setParameters(
                    { ...Object.fromEntries(PARAM_KEYS.map(k => [k, proofParams[k]])), proof_id: proofId }
                  );
                } catch (e) {
                  console.error('[SetParameters] Failed to persist pre-set params on proof start:', e);
                }
              }
              setProofParams(prev => ({ ...prev, proof_id: proofId }));

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
        lineNumber: padIndex,  // Tell backend which line to update
        supportRewriteComplexity: proofParams.support_rewrite_complexity
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

        setInductionSubErrors(proofParams.support_errors ? (response.errors || ["Substitution failed"]) : ["your latest command contains an error"]); // support_errors suppression
        return false;
      } catch (error) {
        setInductionSubErrors(proofParams.support_errors ? ["Failed to substitute rule"] : ["your latest command contains an error"]); // support_errors suppression
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
      proofParams,
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
    caseType,
    currentUserType
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
    const hideExpression = field?.hide_expression || false;
    const hideJustification = field?.hide_justification || false;

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
            showEyeButtons={true}
            currentUserType={currentUserType}
            hideExpression={hideExpression}
            hideJustification={hideJustification}
            onRuleHiddenToggle={() => handleRuleHiddenToggle(side, index)}
            onExpressionHiddenToggle={() => handleExpressionHiddenToggle(side, index)} 
          />
        </Col>
        <Col xs="auto" className="d-flex align-items-center">
          <Button   
          variant= "secondary" //{hasComments ? "warning" : "secondary"}
          onClick={async() => {
            const data = await inductionService.getComments({
              side: side,
              line_number: padIndex
            });

            setActivePadIndex(padIndex);
            setActiveSide(side);
            setStudentComment(data.student || "");
            setInstructorComment(data.instructor || "");

            //if either a student or instructor comment exists, make button a dif color

            setShowCommentsModal(true);
          }}
          >
            <i className="fa-regular fa-message"></i>
          </Button>
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
      const field = racketRuleFields?.[showSide][padIndex];
      const isExpressionHidden = field.hide_expression || false;
      const displayEquation = isExpressionHidden ? "" : equation;

      return (
        <PersistentPad
          ref={footerPadRef}
          equation={displayEquation}
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
          currentUserType={currentUserType}
          hideExpression={isExpressionHidden}
        />
      );
    } else {
      // Array index now equals line number, so use padIndex directly
      const field = racketRuleFields[showSide][padIndex];
      if (!field) return null;

      const calculatedStartPosition = field.selectedNode || field.startPosition || 0;
      
      // Check if fields are hidden
      const isExpressionHidden = field.hide_expression || false;
      const isRuleHidden = field.hide_justification || false;
      
      // If hidden, blank out the display value
      // The actual value stays in memory for validation
      const displayEquation = isExpressionHidden ? "" : field.racket;
      const displayJsonTree = isExpressionHidden ? {} : (field.jsonTree || jsonTreeRep[showSide]);
      
      // For the editable rule field: show blank if hidden, otherwise show current value
      const displayRule = isRuleHidden ? "" : footerRule;

      return (
        <PersistentPad
          ref={footerPadRef}
          equation={displayEquation}
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
          currentUserType={currentUserType}
          hideExpression={isExpressionHidden}
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

  const handleRuleHiddenToggle = async (side, index) => {
    try {
      const result = await inductionService.toggleVisibility({
        side: side,
        case: isAnchor ? 'base' : 'leap',
        lineNumber: index,
        field: 'justification'
      });

      const actualStatus = result.new_value; 

      setRacketRuleFields(prev => ({
        ...prev,
        [side]: prev[side].map((field, idx) => 
          idx === index ? { ...field, hide_justification: actualStatus } : field
        )
      }));

      return actualStatus; 

    } catch (error) {
      toast.error("Database update failed.");
      throw error;
    }
  };

  const handleExpressionHiddenToggle = async (side, index) => {
    try {
      const result = await inductionService.toggleVisibility({
        side: side,
        case: isAnchor ? 'base' : 'leap',
        lineNumber: index,
        field: 'expression'
      });

      const actualStatus = result.new_value;

      setRacketRuleFields(prev => ({
        ...prev,
        [side]: prev[side].map((field, idx) => 
          idx === index ? { ...field, hide_expression: actualStatus } : field
        )
      }));

      return actualStatus;

    } catch (error) {
      toast.error("Failed to update expression visibility");
      throw error;
    }
  };

  const isReviewMode = useMemo(() => {
    return !!(
      proofStarted && 
      proofOwner && 
      currentUserType && 
      currentUserType.username !== proofOwner.username
    );
  }, [proofStarted, proofOwner, currentUserType]);

  return (
    <MainLayout>
      {isReviewMode && (
        <Alert 
          variant="warning" 
          className="d-flex align-items-center py-1 mb-0 justify-content-center shadow-sm border-warning rounded-0"
        >
          <div className="d-flex align-items-center gap-2">
            <i className="fa-solid fa-user-shield text-warning fs-5"></i>
            <div>
              <strong className="text-dark">Review Mode:</strong> Viewing proof owned by 
              <span className="badge bg-dark mx-1 fs-6">{proofOwner.username}</span>.
            </div>
          </div>
        </Alert>
      )}
      <Container className="er-racket-container">
        <OffcanvasRuleSet
          isActive={isOffcanvasActive}
          toggleFunction={toggleOffcanvas}            
          visibleRules={proofParams.visible_rules}
          supportRuleSet={proofParams.support_rule_set}
        ></OffcanvasRuleSet>
        {showDefinitionsWindow && (
          <Definitions 
            toggleDefinitionsWindow={toggleDefinitionsWindow} 
            isLocked={proofStarted}
            isStudent={currentUserType?.is_student}
            validateHiddenDefinitionFn={inductionService.validateHiddenDefinition}
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
            initialRule={footerRule}
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
                                  style={{ cursor: "not-allowed", border: 'none', height: '40px', minWidth: `${Math.max((lhsValue?.length || 11), 11)}ch`, WebkitTextSecurity: proofStarted && lhsHidden ? "disc" : "none" }} 
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
                                  style={{ cursor: "not-allowed", border: 'none', height: '40px', minWidth: `${Math.max((lhsValue?.length || 11), 11)}ch`, WebkitTextSecurity: proofStarted && rhsHidden ? "disc" : "none" }} 
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
                                  {isReviewMode ? proofOwner?.is_student : !currentUserType?.is_student && (
                                    <Dropdown.Item onClick={() => setShowSetParams(true)} href="#">
                                      Set Parameters
                                    </Dropdown.Item>
                                  )}
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
                                  <Dropdown.Item 
                                    onClick={handleNewProof} 
                                    href="#" 
                                    disabled={!proofStarted}
                                    style={{ opacity: proofStarted ? 1 : 0.4, cursor: proofStarted ? 'pointer' : 'not-allowed' }}
                                  >
                                    New Proof
                                  </Dropdown.Item>
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
                                    Discard Proof
                                  </Dropdown.Item>
                                  <Dropdown.Item
                                    onClick={handleDownloadProof}
                                    href="#"
                                    disabled={!proofStarted}
                                    style={{ opacity: proofStarted ? 1 : 0.4, cursor: proofStarted ? 'pointer' : 'not-allowed' }}
                                  >
                                    Download Proof
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
                          <Form.Group as={Col} sm="6">
                            <Form.Floating>
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
                                disabled={proofStarted}
                                required
                              />
                              <label>Proof Name</label>
                              <Form.Control.Feedback type="invalid">
                                {validationMessages.proofName ||
                                  proofValidationMessage.name}
                              </Form.Control.Feedback>
                            </Form.Floating>
                          </Form.Group>
                        <Form.Group as={Col} sm="6">
                          <Form.Floating>
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
                              disabled={proofStarted}
                              required
                            />
                            <label htmlFor="eRProofTag"># Tag</label>
                            <Form.Control.Feedback type="invalid">
                              {proofValidationMessage.tag || validationMessages.tag}
                            </Form.Control.Feedback>
                          </Form.Floating>
                        </Form.Group>
                      </Row>
                      <Row className="g-2 mb-1">
                          <Form.Group as={Col} md="4">
                            <label className="form-label small fw-bold mb-0">IVar</label>
                            <div className="position-relative">
                              <RacketInput
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
                                onKeyUp={inductionVarKeyUp}
                                onClick={inductionVarSelect}
                                ref={inductionVarRef}
                                highlightPositions={inductionVarHighlights}
                                isInvalid={
                                  !!validationMessages.inductionVariable ||
                                  !!proofValidationMessage.inductionVariable
                                }
                                disabled={proofStarted}
                                required
                              />
                              <Form.Control.Feedback type="invalid" className={( !!validationMessages.inductionVariable || !!proofValidationMessage.inductionVariable) ? "d-block" : ""}>
                                {validationMessages.inductionVariable ||
                                  proofValidationMessage.inductionVariable}
                              </Form.Control.Feedback>
                            </div>
                          </Form.Group>
                          <Form.Group as={Col} md="4">
                            <label className="form-label small fw-bold mb-0">AVal</label>
                            <div className="position-relative">
                              <RacketInput
                                id="eRInductionValue"
                                name="inductionValue"
                                type="text"
                                placeholder="Anchor Value"
                                value={formValues.inductionValue}
                                onBlur={() => {
                                  handleBlur("inductionValue");
                                  clearProofValidationMessage();
                                }}
                                onChange={handleChange}
                                onKeyUp={inductionValKeyUp}
                                onClick={inductionValSelect}
                                ref={inductionValRef}
                                highlightPositions={inductionValHighlights}
                                isInvalid={
                                  !!validationMessages.inductionValue ||
                                  !!proofValidationMessage.inductionValue
                                }
                                disabled={proofStarted}
                                required
                              />
                              <Form.Control.Feedback type="invalid" className={( !!validationMessages.inductionValue || !!proofValidationMessage.inductionValue) ? "d-block" : ""}>
                                {validationMessages.inductionValue ||
                                  proofValidationMessage.inductionValue}
                              </Form.Control.Feedback>
                            </div>
                          </Form.Group>
                          <Form.Group as={Col} md="4">
                            <label className="form-label small fw-bold mb-0">LVar</label>
                            <div className="position-relative">
                              <RacketInput
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
                                onKeyUp={leapVarKeyUp}
                                onClick={leapVarSelect}
                                ref={leapVarRef}
                                highlightPositions={leapVarHighlights}
                                isInvalid={
                                  !!validationMessages.leapVariable ||
                                  !!proofValidationMessage.leapVariable
                                }
                                disabled={proofStarted}
                                required
                              />
                              <Form.Control.Feedback type="invalid" className={( !!validationMessages.leapVariable || !!proofValidationMessage.leapVariable) ? "d-block" : ""}>
                                {validationMessages.leapVariable ||
                                  proofValidationMessage.leapVariable}
                              </Form.Control.Feedback>
                            </div>
                          </Form.Group>
                      </Row>
                      <Row className={`g-5 mb-${(!proofStarted || !isAnchor) ? "1" : "3"}`}>
                          <Form.Group as={Col} md="6" className="er-proof-goal-lhs">
                            <label className="form-label small fw-bold mb-0">LHS Goal</label>
                            <div className="position-relative">
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
                                isInvalid={
                                  !!validationMessages.lHSGoal ||
                                  !!goalValidationMessage.LHS.Goal
                                }
                                disabled={proofStarted}
                                required
                              />
                              <Form.Control.Feedback type="invalid" className={( !!validationMessages.lHSGoal || !!goalValidationMessage.LHS.Goal) ? "d-block" : ""}>
                                {validationMessages.lHSGoal ||
                                  goalValidationMessage.LHS.Goal}
                              </Form.Control.Feedback>
                            </div>
                          </Form.Group>
                          <Form.Group as={Col} md="6" className="er-proof-goal-rhs">
                            <label className="form-label small fw-bold mb-0">RHS Goal</label>
                            <div className="position-relative">
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
                                isInvalid={
                                  !!validationMessages.rHSGoal ||
                                  !!goalValidationMessage.RHS.Goal
                                }
                                disabled={proofStarted}
                                required
                              />
                              <Form.Control.Feedback type="invalid" className={(validationMessages.rHSGoal || goalValidationMessage.RHS.Goal) ? "d-block" : ""}>
                                {validationMessages.rHSGoal ||
                                  goalValidationMessage.RHS.Goal}
                              </Form.Control.Feedback>
                            </div>
                          </Form.Group>
                      </Row>
                      {(proofParams?.support_ih || !proofStarted) && (!proofStarted || !isAnchor) && (
                        <Row className="g-5 mb-3">
                          <Form.Group as={Col} md="6" className="er-inductive-hypothesis-lhs">
                              <label htmlFor="eRInductiveHypothesisLHS" className="form-label small fw-bold mb-0">IH LHS</label>
                              <RacketInput
                                id="eRInductiveHypothesisLHS"
                                name="inductiveHypothesisLHS"
                                type="text"
                                placeholder={(proofParams.support_ih) ? "This field will be autogenerated" : "Enter Inductive Hypothesis LHS"}
                                value={inductiveHypothesisLHS}
                                onChange={(e) => setInductiveHypothesisLHS(e.target.value)}
                                onKeyUp={ihLhsKeyUp}
                                onClick={ihLhsSelect}
                                ref={ihLhsRef}
                                highlightPositions={ihLhsHighlights}
                                disabled={proofStarted || proofParams.support_ih}
                              />
                          </Form.Group>
                          <Form.Group as={Col} md="6" className="er-inductive-hypothesis-rhs">
                              <label htmlFor="eRInductiveHypothesisRHS" className="form-label small fw-bold mb-0">IH RHS</label>
                              <RacketInput
                                id="eRInductiveHypothesisRHS"
                                name="inductiveHypothesisRHS"
                                type="text"
                                placeholder={(proofParams.support_ih) ? "This field will be autogenerated" : "Enter Inductive Hypothesis RHS"}
                                value={inductiveHypothesisRHS}
                                onChange={(e) => setInductiveHypothesisRHS(e.target.value)}
                                onKeyUp={ihRhsKeyUp}
                                onClick={ihRhsSelect}
                                ref={ihRhsRef}
                                highlightPositions={ihRhsHighlights}
                                disabled={proofStarted || proofParams.support_ih}
                              />
                          </Form.Group>
                        </Row>
                      )}
                      {(proofParams.support_current_lhs_rhs && (
                        <>
                          <Row className="justify-content-center er-current-state g-2 mb-0">
                            <Form.Group as={Col} sm="6" className={showSide === "LHS" ? "active" : ""}>
                              <Form.Floating style={{ border: showSide === "LHS" ? '3px solid #0d6efd' : '1px solid #ced4da', borderRadius: '0.375rem' }}>
                                <Form.Control 
                                  type="text" 
                                  value={lhsValue || (proofStarted ? (leftPremise?.racket || currentLHS) : '')} 
                                  readOnly 
                                  style={{ border: 'none', WebkitTextSecurity: proofStarted && lhsHidden ? "disc" : "none" }} 
                                />
                                <label>Current LHS</label></Form.Floating></Form.Group>
                            <Form.Group as={Col} sm="6" className={showSide === "RHS" ? "active" : ""}>
                              <Form.Floating style={{ border: showSide === "RHS" ? '3px solid #0d6efd' : '1px solid #ced4da', borderRadius: '0.375rem' }}>
                                <Form.Control 
                                  type="text" 
                                  value={rhsValue || (proofStarted ? (rightPremise?.racket || currentRHS) : '')} 
                                  readOnly 
                                  style={{ border: 'none', WebkitTextSecurity: proofStarted && rhsHidden ? "disc" : "none" }} 
                                />
                                <label>Current RHS</label></Form.Floating></Form.Group>
                          </Row>
                        </>
                      )

                      )}
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
                        {isReviewMode ? proofOwner?.is_student : !currentUserType?.is_student && (
                          <Dropdown.Item onClick={() => setShowSetParams(true)} href="#">
                            Set Parameters
                          </Dropdown.Item>
                        )}
                        <Dropdown.Item onClick={toggleDefinitionsWindow} href="#">Definitions</Dropdown.Item>
                        <Dropdown.Item onClick={toggleOffcanvas} href="#">View Rule Set</Dropdown.Item>
                        {!isAnchor && !proofParams?.support_ih && proofStarted && (
                          <Dropdown.Item 
                          onClick={() => setShowIHModal(true)}
                          /* disabled={isAnchor || proofParams?.support_ih} style={{ opacity: !isAnchor && !proofParams.support_ih ? 1 : 0.4 }} */
                          >
                            Show IH
                          </Dropdown.Item>
                        )}
                        
                        <Dropdown.Item 
                          onClick={checkCurrentProofStatus} 
                          disabled={!proofStarted}
                          style={{ opacity: proofStarted ? 1 : 0.4 }}
                        >
                          Check Current Proof
                        </Dropdown.Item>
                        <Dropdown.Item onClick={handleNewProof} disabled={!proofStarted} style={{ opacity: proofStarted ? 1 : 0.4, cursor: proofStarted ? 'pointer' : 'not-allowed' }}>
                          New Proof
                        </Dropdown.Item>
                        <Dropdown.Item onClick={handleClearProof} disabled={!proofStarted} style={{ color: proofStarted ? 'red' : '#999', opacity: proofStarted ? 1 : 0.4, cursor: proofStarted ? 'pointer' : 'not-allowed' }}>
                          Discard Proof
                        </Dropdown.Item>
                        <Dropdown.Item
                          onClick={handleDownloadProof}
                          href="#"
                          disabled={!proofStarted}
                          style={{ opacity: proofStarted ? 1 : 0.4, cursor: proofStarted ? 'pointer' : 'not-allowed' }}
                        >
                          Download Proof
                        </Dropdown.Item>
                      </Dropdown.Menu>
                    </Dropdown>
                    <input
                      type="file"
                      accept=".json"
                      ref={uploadFileRef}
                      onChange={handleUploadFileChange}
                      style={{ display: 'none' }}
                    />
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
                        disabled={proofStarted}
                      />
                      <Form.Check 
                        type="radio" id="lists" label="Lists" name="inductionType" 
                        value="lists" onChange={handleChange} 
                        disabled={proofStarted}
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

            {(() => {
              const indCaseKey = isAnchor ? 'base' : 'leap';
              const indPlayCount = visibleLineCount(playState, indCaseKey, showSide);
              const indLastReal = getLastRealIndex(racketRuleFields[showSide] || []);
              return (
                <>
                  {racketRuleFields[showSide].map((field, index) => {
                    // In play mode, hide lines beyond the current visible count
                    if (indPlayCount !== null && index >= indPlayCount) return null;
                    if (field.deleted) return null;
                    return renderPersistentPadRow({
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
                      caseType: indCaseKey,
                      currentUserType: isReviewMode ? proofOwner : !currentUserType
                    });
                  })}
                  {showContinue(playState, indCaseKey, showSide, indLastReal) && (
                    <Row className="align-items-center" style={{ marginTop: '1rem' }}>
                      <Col xs="auto">
                        {showContinue(playState, indCaseKey, showSide, indLastReal) && (
                          <Button
                            variant="primary"
                            onClick={() => setPlayState(prev =>
                              advancePlay(prev, indCaseKey, showSide, indLastReal)
                            )}
                          >
                            <i className="fa-solid fa-play" style={{ marginRight: '0.4rem' }}></i>
                            Continue
                          </Button>
                        )}
                      </Col>
                      <Col className="d-flex justify-content-end">
                        <Button
                          variant="outline-danger"
                          size="sm"
                          onClick={() => setPlayState(prev => cancelPlay(prev, indCaseKey, showSide))}
                        >
                          <i className="fa-solid fa-xmark" style={{ marginRight: '0.4rem' }}></i>
                          Cancel Play Mode
                        </Button>
                      </Col>
                    </Row>
                  )}
                </>
              );
            })()}
        </div>
        </div>
      )}
      
      {proofStarted && (() => {
        // Calculate bicolor border based on bound row
        const colors = ['#DAA520', '#0066cc', '#cc0000', '#228B22']; // yellow, blue, red, green
        const padIndex = userRow.num && userRow.num !== "" ? parseInt(userRow.num, 10) : 0;
        const currentColor = colors[padIndex % 4];
        const nextColor = colors[(padIndex + 1) % 4];
        const footerStyle = {
          borderTop: `3px solid transparent`,
          borderImage: `linear-gradient(to right, ${currentColor} 50%, ${nextColor} 50%) 1`
        };

        const indCaseKeyForFooter = isAnchor ? 'base' : 'leap';
        if (showContinue(playState, indCaseKeyForFooter, showSide, getLastRealIndex(racketRuleFields[showSide] || []))) {
          return (
            <div className="floating-footer" style={footerStyle}>
              <div className="text-center py-2" style={{ color: '#6c757d', fontStyle: 'italic' }}>
                Lines cannot be edited while in Play Mode
              </div>
            </div>
          );
        }

        return (
        <div 
          className="floating-footer"
          style={footerStyle}
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
          An <strong>{conflictType}</strong> proof with the name "<strong>{formValues.proofName}</strong>" 
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
      <SetParametersModal
        show={showSetParams}
        onHide={() => setShowSetParams(false)}
        params={proofParams}
        rulesInProof={rulesInProof}
        onSave={async (newParams) => {
          setProofParams(prev => ({ ...prev, ...newParams }));
          if (proofParams.proof_id) {
            try {
              await inductionService.setParameters({ ...newParams, proof_id: proofParams.proof_id });
            } catch (e) {
              console.error('[SetParameters] Save failed:', e);
            }
          }
        }}
      />

      {/* Show IH Modal */}
      <Modal show={showIHModal} onHide={() => setShowIHModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>Induction Hypothesis</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <div className="mb-3">
            <strong>IH LHS</strong>
            <div>{inductiveHypothesisLHS || "-"}</div>
          </div>
          <div>
            <strong>IH RHS</strong>
            <div>{inductiveHypothesisRHS || "-"}</div>
          </div>
        </Modal.Body>
      </Modal>

      <CommentsModal
        show={showCommentsModal}
        onHide={() => setShowCommentsModal(false)}
        studentComment={studentComment}
        instructorComment={instructorComment}
        onStudentCommentChange={setStudentComment}
        OnInstructorCommentChange={setInstructorComment}
        isStudent={currentUserType?.is_student}
        onSave={async () => {
          await inductionService.saveComment({
            side: activeSide,
            line_number: activePadIndex,
            role: "student",
            comment: studentComment
          });

          await inductionService.saveComment({
            side: activeSide,
            line_number: activePadIndex,
            role: "instructor",
            comment: instructorComment
          });
          
          setShowCommentsModal(false);
        }}
      />
    </MainLayout>
  );
};

export default InductionRacket;
