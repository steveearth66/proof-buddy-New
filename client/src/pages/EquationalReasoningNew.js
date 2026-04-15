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
import validateField from "../utils/eRFormValidationUtils";
import OffcanvasRuleSet from "../components/OffcanvasRuleSet";
import { useToggleSide } from "../hooks/useToggleSide";
import { useOffcanvas } from "../hooks/useOffcanvas";
import { useInputState } from "../hooks/useInputState";
import { useFormValidation } from "../hooks/useFormValidation";
import { useGoalCheck } from "../hooks/useGoalCheck";
import { useCurrentRacketValues } from "../hooks/useCurrentRacketValues";
import { useFormSubmit } from "../hooks/useFormSubmit";
import "../scss/_forms.scss";
import "../scss/_er-racket.scss";
import { useRacketRuleFields } from "../hooks/useRacketRuleFields";
import { ProofComplete, Substitution, PersistentPad, RacketInput } from "../components";
import { useParenHighlight } from "../hooks/useParenHighlight";
import {
  Definitions
} from "../components";
import SetParametersModal from "../components/SetParametersModal";
import ClickableRowNumber from "../components/ClickableRowNumber";
import { useDefinitionsWindow } from "../hooks/useDefinitionsWindow";
import { useDynamicHeight } from "../hooks/useDynamicHeight";
import equationalService from "../services/equationalService";
import inductionService from "../services/inductionService";
import {
  ARROW_KEYS,
  INITIAL_FORM_VALUES,
  INITIAL_PREMISE_STATE,
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
import userService from "../services/userService"
import { useLocation, useNavigate } from "react-router-dom";

/**
 * Equational Reasoning component facilitates the Equational Reasoning Racket.
 */
const EquationalReasoningNew = () => {
    const [showSide, toggleSide] = useToggleSide();
    const [formValues, handleChange, setFormValues] = useInputState(INITIAL_FORM_VALUES);
    const [currentUserType, setCurrentUserType] = useState(null);
    
    useEffect(() => {
      async function loadUser() {
        const profile = await userService.getUserProfile();
        setCurrentUserType(profile);
      }
      loadUser();
    }, []);

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

    // Define the logic: Show icon if collapsed OR if the screen is narrow
    const proofUtilsShowIconOnly = isHeaderCollapsed || windowWidth < 1305;

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
    
    const [validationMessages, handleBlur, setAllTouched, isFormValid] =
        useFormValidation(formValues, validateField);
    const [validated, setValidated] = useState(false);
    const [
        ,
        checkGoal,
        goalValidationMessage,
        enhancedHandleChange,
        proofValidationMessage,
        clearProofValidationMessage,
        ,
        jsonTreeRep,
        clearGoalValidationMessage
    ] = useGoalCheck(handleChange);
    const [currentRacket, setCurrentRacket] = useState("");
    const [
        ,
        ,
        ,
        validationErrors,
        ,
        ,
        ,
        updateShowSubstitution,
        showSubstitution,
        closeSubstitution,
        ,
        ,
        ,
        clearValidationErrors
    ] = useRacketRuleFields(
        0, // Default startPosition since we now get it from pad refs
        currentRacket,
        formValues.proofName,
        formValues.proofTag,
        showSide
    );

    // Current values (computed from last line)
    const [currentLHS, setCurrentLHS] = useState("");
    const [currentRHS, setCurrentRHS] = useState("");
    const [racketFields, setRacketFields] = useState({
        LHS: [],
        RHS: []
      });
    const [errors, setErrors] = useState([]);
    const [showOverwriteModal, setShowOverwriteModal] = useState(false);
    const [showStartConfirmModal, setShowStartConfirmModal] = useState(false);
    const [conflictType, setConflictType] = useState(null);
    // Start proof
    const handleStartProof = async (e) => {
      e.preventDefault();
      setErrors([]);

      // --- Basic Form Validation ---
      if (!formValues.proofName.trim()) {
        setErrors(["Name is required"]);
        return;
      }
      const RESERVED_PROOF_NAMES = new Set(["IH", "length", "append", "reverse"]);
      if (RESERVED_PROOF_NAMES.has(formValues.proofName.trim())) {
        setErrors([`'${formValues.proofName.trim()}' is a reserved name and cannot be used as a proof name.`]);
        return;
      }
      if (!formValues.lHSGoal.trim() || !formValues.rHSGoal.trim()) {
        setErrors(["Both LHS and RHS goals are required"]);
        return;
      }
      if (formValues.lHSGoal.trim() === formValues.rHSGoal.trim()) {
        setErrors(["LHS and RHS goals cannot be identical"]);
        return;
      }

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
    
    const proceedWithProofStart = async () => {
      setShowOverwriteModal(false);
      setShowStartConfirmModal(false);
      setErrors([]);

      try {
        // 1. FORCE CLEAN SLATE
        try {
            await equationalService.clearProof();
        } catch (ignore) {
            // Ignore errors if there was no active proof to clear
        }
        
        // Clear frontend memory of the old ID
        sessionStorage.removeItem('current_proof_id');
        sessionStorage.removeItem('erProofActive');
      
        // Clear the browser history state so we don't "remember" the old ID from navigation
        window.history.replaceState({}, document.title);

        // 2. Run checkGoal validation
        await checkGoal(
          showSide,
          formValues[`${showSide[0].toLowerCase()}HSGoal`],
          formValues.proofName,
          formValues.proofTag,
          formValues.lHSGoal,
          formValues.rHSGoal
        );
        
        // 3. PREPARE DEFINITIONS & GENERICS
        const normalizeType = (t) => (t || '').replace(/\s*->\s*/g, ' > ').trim();
        let definitions = [];
        let generics = [];
        try {
          const storedDefs = JSON.parse(sessionStorage.getItem('definitions')) || [];
          definitions = storedDefs.filter(d => d.applied && d.expression);
          const storedGenerics = JSON.parse(sessionStorage.getItem('generics')) || [];
          generics = storedGenerics.filter(g => g.enabled);
        } catch (e) {
          console.error('Error reading session definitions:', e);
          definitions = [];
          generics = [];
        }
        
        // 4. INITIALIZE ENGINE (setCurrentProof)
        const response = await equationalService.setCurrentProof({
          lhsPremise: formValues.lHSGoal.trim(),
          rhsPremise: formValues.rHSGoal.trim(),
          name: formValues.proofName,
          tag: formValues.proofTag,
          definitions: definitions.map(d => ({
              label: d.label || d.name || '',
              type: normalizeType(d.type),
              expression: d.expression
          })),
          generics: generics.map(g => ({
              label: g.label || g.name || '',
              type: normalizeType(g.type),
              restrictions: {
              assumption: g.assumption || g.restrictions?.assumption || 'None',
              neverNull: g.neverNull || g.restrictions?.neverNull || false
              }
          }))
        });

        if (response.isValid) {
          // 5. Construct the Premise lines
          const lhsPremiseLine = {
              racket: formValues.lHSGoal.trim(),
              rule: "Premise",
              lineNumber: 0,
              selectedNode: 0,
              startPosition: 0,
              jsonTree: response.lhsJsonTree || {},
              deleted: false
          };

          const rhsPremiseLine = {
              racket: formValues.rHSGoal.trim(),
              rule: "Premise",
              lineNumber: 0,
              selectedNode: 0,
              startPosition: 0,
              jsonTree: response.rhsJsonTree || {},
              deleted: false
          };

          // 6. SAVE TO DATABASE
          const proofPayload = {
              name: formValues.proofName,
              tag: formValues.proofTag,
              lHSGoal: formValues.lHSGoal.trim(),
              rHSGoal: formValues.rHSGoal.trim(),
              leftPremise: { ...lhsPremiseLine },
              rightPremise: { ...rhsPremiseLine },
              leftRacketsAndRules: [],
              rightRacketsAndRules: [],
              definitions: definitions.map(d => ({
                label: d.label || d.name || '',
                type: normalizeType(d.type),
                expression: d.expression
              })),
              generics: generics.map(g => ({
                label: g.label || g.name || '',
                type: normalizeType(g.type),
                restrictions: {
                assumption: g.assumption || g.restrictions?.assumption || 'None',
                neverNull: g.neverNull || g.restrictions?.neverNull || false
                }
              }))
          };

          const saveResponse = await equationalService.saveProof(proofPayload);
          // 7. STORE PROOF ID
          if (saveResponse && saveResponse.proofId) {
              // call getRacketProof to update the cache
              await equationalService.getRacketProof(saveResponse.proofId);
              sessionStorage.setItem('current_proof_id', saveResponse.proofId);
              sessionStorage.setItem('erProofActive', 'true');

              // Persist any params the user pre-configured before starting the proof.
              const PARAM_KEYS = ['support_errors','support_current_lhs_rhs','support_ih','support_premise','support_rule_set','support_value_mapping'];
              const hasCustomParams = PARAM_KEYS.some(k => proofParams[k] !== true);
              if (hasCustomParams) {
                try {
                  await equationalService.setParameters(
                    { ...Object.fromEntries(PARAM_KEYS.map(k => [k, proofParams[k]])), proof_id: saveResponse.proofId }
                  );
                } catch (e) {
                  console.error('[SetParameters] Failed to persist pre-set params on proof start:', e);
                }
              }
              setProofParams(prev => ({ ...prev, proof_id: saveResponse.proofId }));
          } else {
              throw new Error("Database save failed to return a Proof ID");
          }

          // 8. UPDATE UI STATE
          setRacketRuleFields({
            LHS: [lhsPremiseLine, EMPTY_INITIAL_FIELD],
            RHS: [rhsPremiseLine, EMPTY_INITIAL_FIELD]
          });
          
          setLeftPremise(prev => ({ ...prev, ...lhsPremiseLine }));
          setRightPremise(prev => ({ ...prev, ...rhsPremiseLine }));
          setCurrentLHS(formValues.lHSGoal.trim());
          setCurrentRHS(formValues.rHSGoal.trim());
          
          clearGoalValidationMessage('LHS');
          clearGoalValidationMessage('RHS');
          setProofStarted(true);
          toast.success("Proof started!");
          
        } else {
          setErrors(response.errors || ["Failed to start proof"]);
        }
      } catch (error) {
        console.error("Error starting proof:", error);
        const errorMessages = error.response?.data?.errors || 
                              (error.response?.data?.error ? [error.response.data.error] : null) ||
                              ["Error starting proof"];
        setErrors(errorMessages);
      }
    };
    
    // Computed current racketRuleFields
    const [racketRuleFields, setRacketRuleFields] = useState({
        LHS: [EMPTY_INITIAL_FIELD],
        RHS: [EMPTY_INITIAL_FIELD]
      });

    // Play mode state: tracks per-side progress when opened via "Run Proof"
    const [playState, setPlayState] = useState(() => initPlayState(['base'], ['LHS', 'RHS'], false));

    const [SubErrors, setSubErrors] = useState([]);

  const [lhsValue, setLhsValue] = useState("");
  const [rhsValue, setRhsValue] = useState("");
  const [isOffcanvasActive, toggleOffcanvas] = useOffcanvas();
  const [showDefinitionsWindow, toggleDefinitionsWindow] =
    useDefinitionsWindow();
  const [showProofComplete, setShowProofComplete] = useState(false);
  const [proofComplete, setProofComplete] = useState(false);
  const [showSetParams, setShowSetParams] = useState(false);
  const [proofParams, setProofParams] = useState({
    support_errors: true,
    support_current_lhs_rhs: true,
    support_ih: true,
    support_premise: true,
    support_rule_set: true,
    support_value_mapping: true,
  });
  
  // Separate premises for base and leap cases
  const [leftPremise, setLeftPremise] = useState(INITIAL_PREMISE_STATE);
  const [rightPremise, setRightPremise] = useState(INITIAL_PREMISE_STATE);
  
  const [proofStarted, setProofStarted] = useState(false);
  const [proofStatus, setProofStatus] = useState({ base: null }); // tracks base completeness

  // Footer binding and PersistentPad refs - for interactive proof line highlighting
  const lhsPadRefs = useRef({});
  const rhsPadRefs = useRef({});
  const footerPadRef = useRef(null);
  const isProcessingRef = useRef(false);
  const uploadFileRef = useRef(null);
  const [userRow, setUserRow] = useState({ num: "" });
  const [isBound, setIsBound] = useState(false);
  const navigate = useNavigate();
  const loadErrorShownRef = useRef(false);
  const [loadedProof, setLoadedProof] = useState(null);
  const [footerRule, setFooterRule] = useState("");
  const [footerRuleError, setFooterRuleError] = useState("");
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  
  // Hook for getting available height for scrollable proof area
  const availableHeight = useDynamicHeight();

  const location = useLocation();
  const initializedRef = useRef(false);

  useEffect(() => {
    if (initializedRef.current) return;

    const initializeProofSession = async () => {
      initializedRef.current = true;
      console.log('[Init] Starting session initialization...');
      
      try {
        // -------------------------------------------------------------
        // STEP 1: HYDRATE BACKEND (If coming from "All Proofs" page)
        // -------------------------------------------------------------
        if (location.state && location.state.id) {
          console.log("[Init] Loading specific Proof ID:", location.state.id);
          
          // AWAIT this. We cannot proceed until the backend cache is ready.
          // Note: Ensure 'loadProof' maps to your 'get_user_proof' API endpoint
          await equationalService.getRacketProof(location.state.id);

          // Update Session Storage
          sessionStorage.setItem('current_proof_id', location.state.id);
          sessionStorage.setItem('erProofActive', 'true');
          
          // Capture playMode flag before history state is cleared
          const playModeRequested = location.state?.playMode === true;

          // Clear history so refresh doesn't re-trigger this
          window.history.replaceState({}, document.title);

          // Store flag so we can activate play mode after lines load
          initializeProofSession._playMode = playModeRequested;
        } 
        
        // -------------------------------------------------------------
        // STEP 2: CHECK SESSION VALIDITY
        // -------------------------------------------------------------
        const isActiveSession = sessionStorage.getItem('erProofActive') === 'true';
        
        if (!isActiveSession) {
          console.log("[Init] No active session found. Clearing.");
          await equationalService.clearProof();
          sessionStorage.removeItem('current_proof_id');
          sessionStorage.removeItem('erProofActive');
          return;
        }

        // -------------------------------------------------------------
        // STEP 3: FETCH AND RENDER UI (Restore Logic)
        // -------------------------------------------------------------
        console.log("[Init] Fetching proof lines...");
        const proofData = await equationalService.getProofLines();

        if (proofData.hasProof) {
          console.log("[Init] Proof found. Restoring UI...");
          
          // A. Restore Form Header
          setFormValues(prev => ({
            ...prev,
            lHSGoal: proofData.lhsAnchorGoal || '',
            rHSGoal: proofData.rhsAnchorGoal || '',
            proofName: proofData.proofName || '',
            proofTag: proofData.tag || ''
          }));
          
          // B. Restore Premises State
          setLeftPremise(prev => ({
             ...prev,
             racket: proofData.lhsAnchorGoal || '',
             rule: 'Premise',
             startPosition: 0,
             selectedNode: 0,
             jsonTree: (proofData.LHS && proofData.LHS[0]) ? proofData.LHS[0].jsonTree : {} 
          }));

          setRightPremise(prev => ({
             ...prev,
             racket: proofData.rhsAnchorGoal || '',
             rule: 'Premise',
             startPosition: 0,
             selectedNode: 0,
             jsonTree: (proofData.RHS && proofData.RHS[0]) ? proofData.RHS[0].jsonTree : {} 
          }));

          // C. Helper to Map Database Lines to UI Fields
          const mapLinesToFields = (dbLines) => {
            if (!dbLines || dbLines.length === 0) return [EMPTY_INITIAL_FIELD];
            
            // Calculate array size based on max line number
            const maxLine = Math.max(...dbLines.map(l => l.line_number || l.lineNumber || 0));
            const fields = new Array(maxLine + 1).fill(null).map(() => ({ ...EMPTY_INITIAL_FIELD }));

            dbLines.forEach(line => {
               const idx = line.line_number !== undefined ? line.line_number : line.lineNumber;
               
               // Sanitize empty strings to ensure UI renders cleanly
               const racketVal = line.racket || '';
               const ruleVal = line.rule || '';
               
               fields[idx] = {
                 racket: racketVal,
                 rule: ruleVal,
                 jsonTree: line.json_tree || line.jsonTree || {},
                 startPosition: line.start_position || line.startPosition || 0,
                 selectedNode: line.selected_node || line.selectedNode || 0,
                 resultNode: line.result_node || line.resultNode || 0,
                 deleted: false,
                 hide_expression: line.hide_expression || false,
                 hide_justification: line.hide_justification || false
               };
            });
            
            // Ensure there is always a trailing empty line for new input
            fields.push(EMPTY_INITIAL_FIELD);
            return fields;
          };

          // D. Update Grid State
          setRacketRuleFields({
            LHS: mapLinesToFields(proofData.LHS),
            RHS: mapLinesToFields(proofData.RHS)
          });

          // E. Set Current Racket Context (for the next rule application)
          // Logic: Find last non-empty line or default to goal
          const findLast = (arr) => arr.slice().reverse().find(x => x.racket && x.racket.trim() !== "")?.racket;
          
          setCurrentLHS(findLast(proofData.LHS) || proofData.lhsAnchorGoal);
          setCurrentRHS(findLast(proofData.RHS) || proofData.rhsAnchorGoal);

          // F. Restore support params
          const INIT_PARAM_KEYS = ['proof_id','support_errors','support_current_lhs_rhs','support_ih','support_premise','support_rule_set','support_value_mapping'];
          const initExtracted = {};
          INIT_PARAM_KEYS.forEach(k => { if (k in proofData) initExtracted[k] = proofData[k]; });
          if (Object.keys(initExtracted).length > 0) setProofParams(prev => ({ ...prev, ...initExtracted }));

          setProofStarted(true);

          // Activate play mode if the user clicked "Run Proof"
          if (initializeProofSession._playMode) {
            setPlayState(initPlayState(['base'], ['LHS', 'RHS'], true));
          }

          toast.success("Proof loaded successfully!");
          
        } else {
          console.warn("[Init] getProofLines returned false for hasProof.");
          await equationalService.clearProof();
        }

      } catch (error) {
        console.error("[Init] Error initializing session:", error);
        toast.error("Failed to load proof session.");
        initializedRef.current = false;
      }
    };

    initializeProofSession();
  }, []);

  // Initialize jsonTreeRep as empty object for passing to renderPersistentPadRow
  // It gets populated by the backend when goals are checked
//   const [jsonTreeRep, setJsonTreeRep] = useState({ LHS: {}, RHS: {} });

  const checkCurrentProofStatus = async () => {
    try {
      // Check both base and leap cases
      const result = await equationalService.checkCompletion();
      
      const baseStatus = result.isComplete 
        ? { state: "complete", label: "PROOF" }
        : { state: "incomplete", label: "PROOF" };
      
      setProofStatus({
        base: baseStatus
      });
      
      // Show confetti if case is complete
      if (result.isComplete) {
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

    clearValidationErrors();
    setFooterRuleError('');
    const caseKey = 'base';
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
    console.log('[loadProofLinesFromDatabase] CALLED');
    try {
      const proofLines = await equationalService.getProofLines();
      console.log('[loadProofLinesFromDatabase] Got proof lines from API:', proofLines);
      
      // Build racketRuleFields from database proof lines
      const buildFieldsFromLines = (lines) => {
        console.log('[buildFieldsFromLines] Input lines:', JSON.stringify(lines, null, 2));
        
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
        
        console.log('[buildFieldsFromLines] Max line number:', maxLineNum);
        console.log('[buildFieldsFromLines] Output fields array length:', fields.length);
        console.log('[buildFieldsFromLines] Fields array structure:');
        fields.forEach((field, idx) => {
          if (idx < maxLineNum + 1) {
            console.log(`  [${idx}]: racket="${field.racket?.substring(0, 20)}...", rule="${field.rule}", deleted=${field.deleted}`);
          }
        });
        
        // Always add empty field at the end
        fields.push(EMPTY_INITIAL_FIELD);
        return fields;
      };
      
      // Build the new state
      const newBaseLHS = buildFieldsFromLines(proofLines.LHS || []);
      const newBaseRHS = buildFieldsFromLines(proofLines.RHS || []);
      
      // Update base case fields
      setRacketRuleFields({
        LHS: newBaseLHS,
        RHS: newBaseRHS
      });
      
      // Update premises with selectedNode from database (line 0)
      // Only update if premise exists and selectedNode is valid
      const baseLHSPremise = proofLines.LHS.find(l => l.lineNumber === 0);
      const baseRHSPremise = proofLines.RHS.find(l => l.lineNumber === 0);
      
      if (baseLHSPremise || baseRHSPremise) {
        setLeftPremise(prev => ({
            ...prev,
            racket: formValues.lHSGoal,
            selectedNode: baseLHSPremise.selectedNode || 0
        }));
        setRightPremise(prev => ({
            ...prev,
            racket: formValues.rHSGoal,
            selectedNode: baseRHSPremise.selectedNode || 0
        }));
      }

      // Extract support params and proof_id
      const PARAM_KEYS = ['proof_id','support_errors','support_current_lhs_rhs','support_ih','support_premise','support_rule_set','support_value_mapping'];
      const extracted = {};
      PARAM_KEYS.forEach(k => { if (k in proofLines) extracted[k] = proofLines[k]; });
      if (Object.keys(extracted).length > 0) setProofParams(prev => ({ ...prev, ...extracted }));

    } catch (error) {
      console.error('[loadProofLines] Error loading proof lines:', error);
      // Don't show error to user - this is a background operation
    }
  }, [setRacketRuleFields, setLeftPremise, setRightPremise, setProofParams]);

  // Toggle sides - no database reload needed, state already has both sides
  const handleToggleSide = useCallback(() => {
    // Just toggle to the other side - state already contains both LHS and RHS data
    toggleSide();
    
    // No database reload - we want to preserve current UI state including any highlighting changes
  }, [showSide, toggleSide]);

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
    if (showContinue(playState, 'base', showSide, getLastRealIndex(racketRuleFields?.[showSide] || []))) {
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
    const setFields = setRacketRuleFields;
    
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
    if (side === "LHS") {
        setLeftPremise(prev => ({
            ...prev,
            racket: formValues.lHSGoal,
            selectedNode: selectedNode || 0
        }));
    }
    else {
        setRightPremise(prev => ({
            ...prev,
            racket: formValues.rHSGoal,
            selectedNode: selectedNode || 0
        }));
    }
  };

  const handleNewProof = async () => {
    if (!window.confirm('Start a new proof? Your current proof will remain saved in "All Proofs".')) {
      return;
    }
    try {
      await equationalService.clearProof();
      sessionStorage.removeItem('erProofActive');
      sessionStorage.removeItem('current_proof_id');
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
      await equationalService.discardProof();
      // Clear sessionStorage flag so we don't restore from DB on reload
      sessionStorage.removeItem('erProofActive');
      sessionStorage.removeItem('current_proof_id');
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
      const data = await equationalService.downloadProof(proofParams.proof_id);
      const fileName = `${data.name || 'proof'}.json`;
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
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
      if (proofData.proofType !== 'equational') {
        toast.error('This file is not an equational reasoning proof.');
        return;
      }
      const result = await equationalService.uploadProof(proofData);
      // Pre-load the new proof into the backend cache so the page init can find it.
      await equationalService.getRacketProof(result.proofId);
      sessionStorage.setItem('current_proof_id', String(result.proofId));
      sessionStorage.setItem('erProofActive', 'true');
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
    if (isProcessingRef.current) return;
    isProcessingRef.current = true;

    try {
      let ruleFromFooter = "";
      let previousStartPosition = 0;
      let previousRacketValue = "";
      let currentIndex = undefined;
      let studentSelectedNode = 0; // Initialize default

      if (isBound) {
        const userIndex = getPadIndex(userRow.num);
        ruleFromFooter = userRow.num === "000" ? "Premise" : footerRule;

        if (userRow.num !== "000") {
          const previousRowIndex = userIndex - 1;
          const padRefs = getPadRefs(showSide, lhsPadRefs, rhsPadRefs);

          if (previousRowIndex === 0) {
            // Getting from premise
            previousRacketValue = showSide === "LHS" ? leftPremise.racket : rightPremise.racket;
            const premiseData = showSide === "LHS" ? leftPremise : rightPremise;
            previousStartPosition = premiseData.selectedNode ?? premiseData.startPosition ?? 0;
          } else {
            const previousField = racketRuleFields?.[showSide][previousRowIndex];
            previousRacketValue = previousField?.racket || "";
            const fromField = previousField?.selectedNode;
            const fromPad = padRefs.current[previousRowIndex]?.getStartPosition();
            previousStartPosition = fromField ?? fromPad ?? 0;
          }
          studentSelectedNode = previousStartPosition; // Capture selection!
          currentIndex = userIndex;
        }
      }

      if (!ruleFromFooter || ruleFromFooter.trim() === '') {
        setFooterRuleError('Must enter a rule');
        return;
      }
      setFooterRuleError('');

      // If user typed "rewrite math", open Substitution modal with rule pre-filled
      if (ruleFromFooter.trim().toLowerCase() === 'rewrite math') {
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
          lineNumber: currentIndex,
          studentRule: ruleFromFooter, // Sending the Rule
          studentSelectedNode: studentSelectedNode // Sending the Selection
        };

        try {
          const validationResult = await equationalService.validateHiddenField(validationPayload);
          
          if (validationResult.errors && validationResult.errors.length > 0) {
            validationResult.errors.forEach(error => toast.error(error));
            return;
          }
          
          toast.success(validationResult.message || "Correct!");
          
          // Update both flags based on backend response
          // This handles cases where proving the rule unhides the expression too
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
          return;
          
        } catch (error) {
          toast.error('Error validating your answer.');
          return;
        }
      }

      // EXISTING CODE: No hidden fields, proceed with normal generation
      if (!previousRacketValue || previousRacketValue.trim() === '') {
        toast.error('No source expression found. Make sure the previous line has content.');
        return;
      }

      const payload = {
        side: showSide,
        currentRacket: previousRacketValue,
        rule: ruleFromFooter,
        startPosition: previousStartPosition,
        selectedNode: previousStartPosition,
        ...(typeof currentIndex === 'number' && { lineNumber: currentIndex })
      };

      const caseKey = 'base';
      setProofStatus(prev => ({ ...prev, [caseKey]: null }));

      toast.dismiss();

      const fullRacket = await equationalService.applyRule(payload);

      if (!fullRacket) {
        console.error("applyRule returned undefined/null");
        return;
      }

      if (fullRacket && fullRacket.isValid) {
        setRacketRuleFields((prevFields) => {
          const sideArray = [...(prevFields[showSide] || [])];
          
          const newField = {
            racket: fullRacket.racket || "",
            jsonTree: fullRacket.jsonTree || {},
            rule: ruleFromFooter,
            startPosition: previousStartPosition,
            selectedNode: previousStartPosition,
            resultNode: fullRacket.resultNodeId ?? 0,
            deleted: false,
            // Preserve visibility flags if editing existing line
            hide_expression: (typeof currentIndex === 'number' && sideArray[currentIndex]) 
              ? sideArray[currentIndex].hide_expression 
              : false,
            hide_justification: (typeof currentIndex === 'number' && sideArray[currentIndex])
              ? sideArray[currentIndex].hide_justification
              : false
          };
          
          const hasMatchingField = sideArray.some((field) => (
            field && !field.deleted && field.racket === newField.racket && field.rule === newField.rule
          ));
          if (hasMatchingField) {
            return prevFields;
          }

          const isEditingMiddle = typeof currentIndex === 'number' && currentIndex >= 0 && currentIndex < sideArray.length - 1;

          if (isEditingMiddle) {
            sideArray[currentIndex] = newField;
            const endLast = sideArray[sideArray.length - 1];
            const endIsEmpty = endLast && endLast.racket === "" && endLast.rule === "";
            if (!endIsEmpty) {
              sideArray.push(EMPTY_INITIAL_FIELD);
            }
          } else {
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

        if (isBound) {
          unbindFooter();
        }

      } else {
        const message = (fullRacket && fullRacket.errors && fullRacket.errors[0]) || "Invalid rule";
        toast.error(proofParams.support_errors ? message : "your latest command contains an error"); // support_errors suppression
      }
    } finally {
      isProcessingRef.current = false;
    }
  };

  useEffect(() => {
    // Do not clear definitions here; keep session-applied definitions intact

    if (formValues.rHSGoal !== "") {
      // Only update premise from formValues if proof hasn't started yet
      if (!proofStarted) {
        setRightPremise(prev => ({
            ...prev,
            racket: formValues.rHSGoal,
            rule: "Premise",
            startPosition: 0,
            selectedNode: 0
        }));
      }
    }

    if (formValues.lHSGoal !== "") {
      // Only update premise from formValues if proof hasn't started yet
      if (!proofStarted) {
        setLeftPremise(prev => ({
            ...prev,
            racket: formValues.lHSGoal,
            rule: "Premise",
            startPosition: 0,
            selectedNode: 0
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
      setSubErrors([]);
    }
  }, [showSubstitution]);

  // Unbind footer when switching between base and leap cases
  useEffect(() => {
    if (proofStarted) {
      // Only clear incomplete status, preserve complete status
      const caseKey = 'base';
      setProofStatus(prev => {
        if (prev[caseKey]?.state === 'incomplete') {
          return { ...prev, [caseKey]: null };
        }
        return prev;
      });
      unbindFooter();
      clearValidationErrors();
    }
  }, [proofStarted, unbindFooter, clearValidationErrors]);

  // Update Current LHS/RHS display to show the last non-empty line
  useEffect(() => {
    if (!proofStarted) return;
    
    const targetFields = racketRuleFields;
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
    
    setLhsValue(lastLhsLine?.racket || leftPremise.racket || '');
    setRhsValue(lastRhsLine?.racket || rightPremise.racket || '');
  }, [proofStarted, racketRuleFields, leftPremise, rightPremise]);

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

  const handleSubstitution = useCallback(
    async ({ substitution, rule }) => {
      // Clear previous errors when user attempts a new submission
      setSubErrors([]);
      const caseKey = 'base';
      setProofStatus(prev => ({ ...prev, [caseKey]: null }));
      
      const padRefs = getPadRefs(showSide, lhsPadRefs, rhsPadRefs);
      const padIndex = getPadIndex(userRow.num);
      
      // Get current field states
      const boundField = racketRuleFields?.[showSide][padIndex];
      const hasHiddenRule = boundField?.hide_justification || false;
      const hasHiddenExpression = boundField?.hide_expression || false;
      
      // 1. Calculate sourceSelectedNode (Where the rule is being applied)
      let sourceSelectedNode = 0;
      if (padIndex === 1) {
          // If applying to line 1, source is Premise (Line 0)
          sourceSelectedNode = showSide === "LHS"
            ? (leftPremise?.selectedNode ?? leftPremise?.startPosition ?? 0)
            : (rightPremise?.selectedNode ?? rightPremise?.startPosition ?? 0);
      } else {
          // Otherwise, source is the previous line
          const sourceField = racketRuleFields?.[showSide][padIndex - 1];
          sourceSelectedNode = sourceField?.selectedNode ?? sourceField?.startPosition ?? 0;
      }

      // 2. Validation Logic for Hidden Fields
      // If either field is hidden, we validate the Rule + Selection "Master Key"
      if (hasHiddenRule || hasHiddenExpression) {
        const validationPayload = {
          side: showSide,
          lineNumber: padIndex,
          studentRule: rule,
          studentSelectedNode: sourceSelectedNode // Pass the selection to the backend!
        };
        
        try {
          const validationResult = await equationalService.validateHiddenField(validationPayload);
          
          if (validationResult.errors && validationResult.errors.length > 0) {
            setSubErrors(proofParams.support_errors ? validationResult.errors : ["your latest command contains an error"]); // support_errors suppression
            return false;
          }
          
          // Success! Backend says input is valid.
          toast.success(validationResult.message || "Correct!");

          // 3. Update UI with the new visibility state from Backend
          // The backend might have revealed BOTH fields if Rule+Selection were correct.
          setRacketRuleFields(prev => {
            const updated = { ...prev };
            if (updated[showSide] && updated[showSide][padIndex]) {
              updated[showSide][padIndex] = {
                ...updated[showSide][padIndex],
                hide_justification: validationResult.hide_justification,
                hide_expression: validationResult.hide_expression
              };
            }
            return updated;
          });
          
          // Close modal without applying a "new" substitution line (since we just revealed one)
          closeSubstitution();
          return true;
          
        } catch (error) {
          setSubErrors(proofParams.support_errors ? ["Error validating your answer"] : ["your latest command contains an error"]); // support_errors suppression
          return false;
        }
      }
      
      // ---------------------------------------------------------
      // STANDARD SUBSTITUTION LOGIC (No hidden fields)
      // ---------------------------------------------------------
      let currentRacket;
      let sourcePad;
      
      if (padIndex === 1) {
        currentRacket = showSide === "LHS"
          ? leftPremise?.racket || formValues.lHSGoal
          : rightPremise?.racket || formValues.rHSGoal;
        sourcePad = padRefs.current ? padRefs.current[0] : null;
      } else {
        const sourceField = racketRuleFields?.[showSide][padIndex - 1];
        currentRacket = sourceField?.racket || "";
        sourcePad = padRefs.current ? padRefs.current[padIndex - 1] : null;
      }
      
      const startPos = sourcePad?.getStartPosition?.() ?? 0;
      const selectedNode = sourceSelectedNode; // Reuse calculated node

      const payload = {
        substitution,
        rule,
        startPosition: startPos,
        selectedNode: selectedNode,
        currentRacket: currentRacket,
        side: showSide,
        case: "base",
        lineNumber: padIndex
      };

      try {
        const response = await equationalService.substitution(payload);

        if (response.isValid) {
          setSubErrors([]);
          closeSubstitution();

          const racketStr = response.racket || currentRacket;

          const newField = {
            racket: racketStr,
            rule: response.rule || rule,
            startPosition: startPos,
            selectedNode: selectedNode,
            resultNode: response.resultNodeId ?? 0,
            jsonTree: response.jsonTree || {},
            deleted: false,
            hide_expression: false,
            hide_justification: false
          };

          setRacketRuleFields((prev) => {
            const currentFields = prev[showSide];
            const sideArray = [...currentFields];
            
            const isEditingMiddle = padIndex >= 0 && padIndex < sideArray.length - 1;
            
            if (isEditingMiddle) {
              sideArray[padIndex] = newField;
              const endLast = sideArray[sideArray.length - 1];
              const endIsEmpty = endLast && endLast.racket === "" && endLast.rule === "";
              if (!endIsEmpty) {
                sideArray.push(EMPTY_INITIAL_FIELD);
              }
            } else {
              const lastField = sideArray[sideArray.length - 1];
              const lastIsEmpty = !lastField?.racket || lastField.racket.trim() === '';
              
              if (lastIsEmpty) {
                sideArray[sideArray.length - 1] = newField;
                sideArray.push(EMPTY_INITIAL_FIELD);
              } else {
                sideArray.push(newField);
                sideArray.push(EMPTY_INITIAL_FIELD);
              }
            }
            
            return {
              ...prev,
              [showSide]: sideArray
            };
          });

          setIsBound(false);
          setUserRow({ num: "" });
          setCurrentRacket(racketStr);
          return response;
        }

        setSubErrors(proofParams.support_errors ? (response.errors || ["Substitution failed"]) : ["your latest command contains an error"]); // support_errors suppression
        return false;
      } catch (error) {
        setSubErrors(proofParams.support_errors ? ["Failed to substitute rule"] : ["your latest command contains an error"]); // support_errors suppression
        return false;
      }
    },
    [
      closeSubstitution,
      formValues.lHSGoal,
      formValues.rHSGoal,
      leftPremise,
      rightPremise,
      proofParams,
      showSide,
      userRow.num,
      racketRuleFields,
      lhsPadRefs,
      rhsPadRefs
    ]
  );

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
    const padIndex = index;
    
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
    
    const lineNum = index;
    const ruleValue = isPremise ? "Premise" : field.rule;
    const rulePlaceholder = isPremise ? `${side} Premise` : `${side} Rule`;
    const isRuleInvalid = !isPremise && !!validationErrors[side][index];
    const ruleValidationError = validationErrors[side][index];

    const boundPadIndex = isBound ? parseInt(userRow.num, 10) : -1;
    const isUserBoundToNextLine = boundPadIndex === padIndex + 1;
    
    let startPosition;
    if (isPremise) {
      const nextLineHasContent = racketRuleFields[side] && racketRuleFields[side][1]?.racket;
      const showHighlight = nextLineHasContent || isUserBoundToNextLine;
      startPosition = showHighlight
        ? (isLHS
          ? (leftPremise && (leftPremise.selectedNode ?? leftPremise.startPosition)) ?? 0
          : (rightPremise && (rightPremise.selectedNode ?? rightPremise.startPosition)) ?? 0)
        : undefined;
    } else {
      const nextLineHasContent = racketRuleFields[side] && racketRuleFields[side][index + 1]?.racket;
      const showHighlight = nextLineHasContent || isUserBoundToNextLine;
      startPosition = showHighlight
        ? ((field && (field.selectedNode ?? field.startPosition)) ?? 0)
        : undefined;
    }

    const resultNodeValue = isPremise ? undefined : (field && field.resultNode);
    
    // NEW: Get visibility flags from field
    const hideExpression = isPremise ? false : (field?.hide_expression || false);
    const hideJustification = isPremise ? false : (field?.hide_justification || false);

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
            hideExpression={hideExpression}           // NEW: Pass visibility flag
            hideJustification={hideJustification}     // NEW: Pass visibility flag
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
      // Get the bound line's field
      const field = racketRuleFields?.[showSide][padIndex];
      if (!field) return null;

      const calculatedStartPosition = field.selectedNode || field.startPosition || 0;
      
      // NEW: Check if fields are hidden
      const isExpressionHidden = field.hide_expression || false;
      const isRuleHidden = field.hide_justification || false;
      
      // NEW: If hidden, blank out the display value (but keep field readonly)
      // The actual value stays in memory for validation
      const displayEquation = isExpressionHidden ? "" : field.racket;
      const displayJsonTree = isExpressionHidden ? {} : (field.jsonTree || jsonTreeRep[showSide]);
      
      // For the editable rule field: show blank if hidden, otherwise show current value
      const displayRule = isRuleHidden ? "" : footerRule;

      return (
        <PersistentPad
          ref={footerPadRef}
          equation={displayEquation}  // Blank if hidden, but still readonly
          onHighlightChange={() => {}}
          side={showSide}
          jsonTree={displayJsonTree}  // Empty tree if hidden
          lineNum={padIndex}
          startPosition={calculatedStartPosition}
          tabIndex={0}
          ruleValue={displayRule}  // Blank if hidden
          onRuleChange={e => {
            setFooterRule(e.target.value.trim());
            setFooterRuleError('');
          }}
          onRuleKeyDown={handleRuleKeyDown}
          isRuleReadOnly={false}  // Rule is always editable in footer
          rulePlaceholder={`${showSide} Rule`}
          isRuleInvalid={!!footerRuleError}
          ruleValidationError={footerRuleError}
          isEditRow={true}
        />
      );
    }
  };

  if (!proofValidationMessage) {
    console.log('DEBUG CHECK:', {
        onPage: 'New Page',
        inputParam: handleChange, // Is this undefined?
        hookResult: proofValidationMessage   // Is this undefined or empty object?
    });
    return <div>Loading...</div>;
  }

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
            racketRuleFields={(racketRuleFields?.[showSide] || [])}
            handleSubstitution={handleSubstitution}
            errors={SubErrors}
            initialRule={footerRule}
          />
        )}

        <Form
          noValidate
          validated={validated}
          className="er-racket-form"
          onSubmit={handleStartProof}
        >
          <div className="form-top-section" ref={topSectionRef} >
            <Row className="page-header-row align-items-center" style={{ paddingRight: '40px' }} >
              <Col xs="auto">
                <h1 className="mt-0" style={{ marginBottom: 0, fontSize: isHeaderCollapsed ? '24px' : '36px' }}>Equational Reasoning</h1>
              </Col>
              {/* COMPACT VIEW: Current Values move up to this row when collapsed */}
              {isHeaderCollapsed && (
                <>
                  <Col className={`align-items-center justify-content-center er-proof-current-lhs ${showSide === "LHS" ? "active" : ""}`}>
                    <Form.Floating 
                      style={{ 
                        border: showSide === "LHS" ? '3px solid #0d6efd' : '1px solid #ced4da', 
                        borderRadius: '0.375rem', 
                        minWidth: 'fit-content',
                        flexShrink: 0
                      }}
                    >
                      <Form.Control
                        type="text"
                        value={lhsValue || (proofStarted ? (leftPremise?.racket || currentLHS) : '')}
                        readOnly
                        style={{ cursor: "not-allowed", border: 'none', height: '40px',
                                  minWidth: `${Math.max((lhsValue?.length || 20), 20)}ch` }}
                      />
                      <label>Current LHS</label>
                    </Form.Floating>
                  </Col>
                  <Col className={`align-items-center justify-content-center er-proof-current-rhs ${showSide === "RHS" ? "active" : ""}`}>
                    <Form.Floating 
                      style={{ 
                        border: showSide === "RHS" ? '3px solid #0d6efd' : '1px solid #ced4da', 
                        borderRadius: '0.375rem',
                        minWidth: 'fit-content',
                        flexShrink: 0 
                      }}
                    >
                      <Form.Control
                        type="text"
                        value={rhsValue || (proofStarted ? (rightPremise?.racket || currentRHS) : '')}
                        readOnly
                        style={{ cursor: "not-allowed", border: 'none', height: '40px',
                                  minWidth: `${Math.max((lhsValue?.length || 20), 20)}ch` }}
                      />
                      <label>Current RHS</label>
                    </Form.Floating>
                  </Col>
                  {proofStarted && (
                    <Col xs="auto" className="mb-3 d-flex flex-column align-items-start">
                      <div style={{ color: '#F2A007', fontWeight: 'bold', fontSize: '20px' }}>
                        CURRENT = {showSide}
                      </div>
                      <Button
                        size="lg"
                        className="switch-btn"
                        onClick={handleToggleSide}
                        style={{ backgroundImage: 'linear-gradient(135deg, #07294d 0, #006298 100%)', color: '#ffffff', border: 'none' }}
                      >
                        { showSide === "LHS" ? "Switch Side ⋙" : "⋘ Switch Side" }
                      </Button>
                    </Col>
                  )}
                </>
              )}

              {!isHeaderCollapsed && (
                <>
                <Form.Group as={Col} md="3" className="er-proof-name align-items-center justify-content-center">
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
                    disabled={proofStarted}
                    required
                  />
                  <label htmlFor="eRProofName">Name</label>
                  <Form.Control.Feedback type="invalid">
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
                        !!validationMessages.tag || !!proofValidationMessage.tag
                      }
                      disabled={proofStarted}
                      required
                    />
                    <label htmlFor="eRProofTag"># Tag</label>
                    <Form.Control.Feedback type="invalid">
                      {validationMessages.tag || proofValidationMessage.tag}
                    </Form.Control.Feedback>
                  </Form.Floating>                   
              </Form.Group>
                </>
              )}
              <Col xs="auto" className="d-flex align-items-center p-0">
                <div className="d-flex align-items-center" style={{ gap: '10px' }}>
                  
                  {/* UTILITIES AND STATUS */}
                  <Dropdown 
                    align="end"
                    className="proof-dropdown-btn proof-utilities proof-utils-toggle"
                    onToggle={(isOpen) => handleDropdownToggle(isOpen, 'utils-menu')}
                    style={{ width: 'auto' }}
                  >
                    <Dropdown.Toggle id="dropdown-autoclose-true" style={{ minWidth: proofUtilsShowIconOnly ? '0px' : '200px' }}>
                      {proofUtilsShowIconOnly ?<i className="fas fa-tools"></i> : "Proof Utilities"}
                    </Dropdown.Toggle>

                    <Dropdown.Menu 
                      id="utils-menu" 
                      style={{ minWidth: '200px' }}
                      popperConfig={{
                        strategy: 'fixed',
                        modifiers: [
                          { name: 'preventOverflow', options: { boundary: 'viewport' } }
                        ]
                      }}
                    >
                      {!currentUserType?.is_student && (
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
                      <Dropdown.Item onClick={handleUploadProof} href="#">
                        Upload Proof
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
                  {proofStarted && proofStatus['base'] && (
                    <span style={{ 
                      fontWeight: "700", 
                      color: proofStatus['base'].state === "complete" ? "green" : "red", 
                      fontSize: isHeaderCollapsed ? "16px" : "22px",
                      whiteSpace: 'nowrap',
                      minWidth: isHeaderCollapsed ? 'auto' : '260px', // Prevents layout shift
                      textAlign: 'right'
                    }}>
                      {proofStatus['base'].state === "complete" ? "PROOF COMPLETE" : "PROOF INCOMPLETE"}
                    </span>
                  )}
                </div>
              </Col>
            </Row>
            {!isHeaderCollapsed && (
              <div className="standard-view-content p-0">
                <div className="d-flex flex-wrap align-items-center standard-view-flex-container">
                  {proofStarted && (
                    <div className="d-flex flex-column justify-content-center me-3" style={{ minWidth: 'fit-content' }}>
                      <div style={{ color: '#F2A007', fontWeight: 'bold', fontSize: '20px' }}>
                        CURRENT = {showSide}
                      </div>
                      <Button
                        size="lg"
                        className="switch-btn"
                        onClick={handleToggleSide}
                        style={{ backgroundImage: 'linear-gradient(135deg, #07294d 0, #006298 100%)', color: '#ffffff', border: 'none' }}
                      >
                        {showSide === "LHS" ? (
                          <>
                            Switch
                            <span className="btn-text-long"> to Right Hand</span> Side ⋙
                          </>
                        ) : (
                          <>
                            ⋘ Switch
                            <span className="btn-text-long"> to Left Hand</span> Side
                          </>
                        )}
                      </Button>
                      </div>
                  )}
                  <div className="flex-grow-1 inputs-wrapper">
                    <Row className="g-5 justify-content-center flex-wrap" style={{ paddingRight: '40px' }}>
                      <Form.Group as={Col} md="4" className="mt-0 er-proof-goal-lhs">
                        <div className="mb-3">
                          <label htmlFor="eRProofLHSGoal" className="form-label flex-wrap">LHS Goal</label>
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
                                !!goalValidationMessage?.LHS
                              }
                              disabled={proofStarted}
                              required
                              style={{ minWidth: `${Math.max((formValues.lHSGoal?.length || 20), 20)}ch` }}
                            />
                            <Form.Control.Feedback type="invalid" className={(validationMessages.lHSGoal || goalValidationMessage?.LHS) ? "d-block" : ""}>
                              {validationMessages.lHSGoal ||
                                goalValidationMessage?.LHS}
                            </Form.Control.Feedback>
                          </div>
                        </div>
                      </Form.Group>
                      <Form.Group as={Col} md="4" className="er-proof-goal-rhs mt-0">
                        <div className="mb-3">
                          <label htmlFor="eRProofRHSGoal" className="form-label">RHS Goal</label>
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
                                !!goalValidationMessage?.RHS
                              }
                              disabled={proofStarted}
                              required
                              style={{ minWidth: `${Math.max((formValues.rHSGoal?.length || 20), 20)}ch` }}
                            />
                            <Form.Control.Feedback type="invalid" className={(validationMessages.rHSGoal || goalValidationMessage?.RHS) ? "d-block" : ""}>
                              {validationMessages.rHSGoal ||
                                goalValidationMessage?.RHS}
                            </Form.Control.Feedback>
                          </div>
                        </div>
                      </Form.Group>
                    </Row>

                    <Row className="justify-content-center er-current-state flex-wrap" style={{ alignItems: 'center', position: 'relative', paddingRight: '40px' }}>
                      <Form.Group
                        as={Col}
                        md="4"
                        className={`er-proof-current-lhs ${showSide === "LHS" ? "active" : ""}`}
                      >
                        <Form.Floating 
                          className="mb-3"
                          style={{ 
                            border: showSide === "LHS" ? '3px solid #0d6efd' : '1px solid #ced4da',
                            borderRadius: '0.375rem'
                          }}
                        >
                          <Form.Control
                            id="eRProofCurrentLHS"
                            name="proofCurrentLHS"
                            type="text"
                            placeholder="Current LHS"
                            value={lhsValue || (proofStarted ? (leftPremise?.racket || currentLHS) : '')}
                            readOnly
                            style={{ cursor: "not-allowed", border: 'none', minWidth: `${Math.max(((lhsValue || currentLHS)?.length || 20), 20)}ch` }}
                          />
                          <label htmlFor="eRProofCurrentLHS">Current LHS</label>
                        </Form.Floating>
                      </Form.Group>

                      <Form.Group
                        as={Col}
                        md="4"
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
                            id="eRProofCurrentRHS"
                            name="proofCurrentRHS"
                            type="text"
                            placeholder="Current RHS"
                            value={rhsValue || (proofStarted ? (rightPremise?.racket || currentRHS) : '')}
                            readOnly
                            style={{ cursor: "not-allowed", border: 'none', minWidth: `${Math.max(((rhsValue || currentRHS)?.length || 20), 20)}ch` }}
                          />
                          <label htmlFor="eRProofCurrentRHS">Current RHS</label>
                        </Form.Floating>
                      </Form.Group>
                    </Row>
                  </div>
                </div>
              </div>
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

            {!proofStarted && errors.length > 0 && (
              <Row>
                <Col>
                  <Alert variant="danger" dismissible onClose={() => setErrors([])}>
                    {errors.map((error, index) => (
                      <div key={index}>{error}</div>
                    ))}
                  </Alert>
                </Col>
              </Row>
            )}

            {!proofStarted && (
                <Row className="goal-btn-wrap mt-4">
                  <Button
                    className="orange-btn"
                    type="submit"
                  >
                    Start Equational Reasoning Proof
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
              const erPlayCount = visibleLineCount(playState, 'base', showSide);
              const erLastReal = getLastRealIndex(racketRuleFields?.[showSide] || []);
              return (
                <>
                  {(racketRuleFields?.[showSide] || []).map((field, index) => {
                    // In play mode, hide lines beyond the current visible count
                    if (erPlayCount !== null && index >= erPlayCount) return null;
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
                      caseType: 'base',
                      currentUserType: currentUserType
                    });
                  })}
                  {showContinue(playState, 'base', showSide, erLastReal) && (
                    <Row className="align-items-center" style={{ marginTop: '1rem' }}>
                      <Col xs="auto">
                        {showContinue(playState, 'base', showSide, erLastReal) && (
                          <Button
                            variant="primary"
                            onClick={() => setPlayState(prev =>
                              advancePlay(prev, 'base', showSide, erLastReal)
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
                          onClick={() => setPlayState(prev => cancelPlay(prev, 'base', showSide))}
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

        if (showContinue(playState, 'base', showSide, getLastRealIndex(racketRuleFields?.[showSide] || []))) {
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
                  }}                />
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
                    const fields = (racketRuleFields?.[showSide] || []);
                    
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
            const caseKey = 'base';
            const lineNum = parseInt(userRow.num, 10);
            
            // Reset proof status
            setProofStatus(prev => ({ ...prev, [caseKey]: null }));
            
            try {
                // Call backend to clear line in database and reset completion flags
                await equationalService.deleteLine('base', showSide, lineNum);
                
                // Update local state to clear the line
                const targetFields = racketRuleFields;
                
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
                setLeftPremise(prev => ({
                    ...prev,
                    racket: formValues.lHSGoal
                }));
                setRightPremise(prev => ({
                    ...prev,
                    racket: formValues.rHSGoal
                }));
              
            } catch (e) {
              toast.error('Failed to clear line');
            }
          }}>
            Yes
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Overwrite Proof Confirmation Modal */}
      <Modal show={showOverwriteModal} onHide={() => setShowOverwriteModal(null)} centered>
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

      {/* Start Proof Confirmation Modal - Warn about locking definitions */}
      <Modal show={showStartConfirmModal} onHide={() => setShowStartConfirmModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>Confirm Start Proof</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <p>
            Once you start this proof, the current state of <strong>Definitions</strong> will be locked-in.
            You will not be able to create, edit, enable, or disable definitions until you clear this proof.
          </p>
          <p>
            You can still view definitions, but they cannot be modified during the proof.
          </p>
          <p className="mb-0">
            Do you wish to proceed?
          </p>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowStartConfirmModal(false)}>
            Cancel
          </Button>
          <Button variant="primary" onClick={proceedWithProofStart}>
            Start Proof
          </Button>
        </Modal.Footer>
      </Modal>
      <SetParametersModal
        show={showSetParams}
        onHide={() => setShowSetParams(false)}
        params={proofParams}
        onSave={async (newParams) => {
          setProofParams(prev => ({ ...prev, ...newParams }));
          if (proofParams.proof_id) {
            try {
              await equationalService.setParameters({ ...newParams, proof_id: proofParams.proof_id });
            } catch (e) {
              console.error('[SetParameters] Save failed:', e);
            }
          }
        }}
      />
    </MainLayout>
  );
};

export default EquationalReasoningNew;
