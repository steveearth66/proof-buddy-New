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
import { ProofComplete, Substitution, PersistentPad } from "../components";
import {
  Definitions
} from "../components";
import ClickableRowNumber from "../components/ClickableRowNumber";
import { useDefinitionsWindow } from "../hooks/useDefinitionsWindow";
import { useDynamicHeight } from "../hooks/useDynamicHeight";
import equationalService from "../services/equationalService";
import erService from "../services/erService";
import {
  ARROW_KEYS,
  INITIAL_FORM_VALUES,
  INITIAL_PREMISE_STATE,
  EMPTY_INITIAL_FIELD,
  getPadRefs,
  getPadIndex,
  isFormComplete,
  convertFormToJSON,
  clearSessionData,
  updatePremises
} from "../utils/erRacketUtils";

/**
 * Equational Reasoning component facilitates the Equational Reasoning Racket.
 */
const EquationalReasoningNew = () => {
    const [showSide, toggleSide] = useToggleSide();
    const [formValues, handleChange, setFormValues] = useInputState(INITIAL_FORM_VALUES);
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
        loadProofInServer,
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
    // Start proof
  const handleStartProof = async (e) => {
    e.preventDefault();
    setErrors([]);

    if (!formValues.lHSGoal.trim() || !formValues.rHSGoal.trim()) {
      setErrors(["Both LHS and RHS goals are required"]);
      return;
    }

    if (formValues.lHSGoal.trim() === formValues.rHSGoal.trim()) {
      setErrors(["LHS and RHS goals cannot be identical"]);
      return;
    }

    try {
      // 1. Run checkGoal validation
      await checkGoal(
        showSide,
        formValues[`${showSide[0].toLowerCase()}HSGoal`],
        formValues.proofName,
        formValues.proofTag,
        formValues.lHSGoal,
        formValues.rHSGoal
      );
      const normalizeType = (t) => (t || '').replace(/\s*->\s*/g, ' > ').trim();
      let definitions = [];
      let generics = [];
      try {
        const storedDefs = JSON.parse(sessionStorage.getItem('definitions')) || [];
        // Only include UDFs (definitions with expressions), not generics
        definitions = storedDefs.filter(d => d.applied && d.expression);
        
        const storedGenerics = JSON.parse(sessionStorage.getItem('generics')) || [];
        // Include enabled generics (note: generics use 'enabled' not 'applied')
        generics = storedGenerics.filter(g => g.enabled);
      } catch (e) {
        console.error('Error reading session definitions/generics:', e);
        definitions = [];
        generics = [];
      }
      // 2. Initialize backend
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
        // 3. Construct the Premise lines (Line 000)
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

        // 4. Update State: [Premise, EmptyField]
        // This ensures Line 000 (Premise) and Line 001 (Empty) both appear
        setRacketRuleFields({
          LHS: [lhsPremiseLine, EMPTY_INITIAL_FIELD],
          RHS: [rhsPremiseLine, EMPTY_INITIAL_FIELD]
        });
        
        // Explicitly set the separate premise state variables as well
        // (These are still used in some parts of your render logic)
        setLeftPremise(prev => ({ ...prev, ...lhsPremiseLine }));
        setRightPremise(prev => ({ ...prev, ...rhsPremiseLine }));

        setCurrentLHS(formValues.lHSGoal.trim());
        setCurrentRHS(formValues.rHSGoal.trim());
        if (response.proofId || response.id) {
          sessionStorage.setItem('current_proof_id', response.proofId || response.id);
        }
        setProofStarted(true);
        toast.success("Proof started!");
      } else {
        setErrors(response.errors || ["Failed to start proof"]);
      }
    } catch (error) {
      console.error("Error starting proof:", error);
      // Extract error messages from backend response if available
      const errorMessages = error.response?.data?.errors || 
                           (error.response?.data?.error ? [error.response.data.error] : null) ||
                           ["Error starting proof"];
      setErrors(errorMessages);
    }
  };

    // const [proofValidationMessage, setProofValidationMessage] = useState({
    //     name: "",
    //     tag: ""
    // });

//     const clearProofValidationMessage = useCallback(() => {
//     setProofValidationMessage({
//       name: "",
//       tag: ""
//     });
//   }, []);
    
    // Computed current racketRuleFields
    const [racketRuleFields, setRacketRuleFields] = useState({
        LHS: [EMPTY_INITIAL_FIELD],
        RHS: [EMPTY_INITIAL_FIELD]
      });
  
    // Induction-specific state (no dependency on useRacketRuleFields hook)
    //const [validationErrors, setValidationErrors] = useState({ LHS: [], RHS: [] });
    const [inductionSubErrors, setInductionSubErrors] = useState([]);
    //const [showSubstitution, setShowSubstitution] = useState(false);
  
    // const clearValidationErrors = useCallback(() => {
    //     setValidationErrors({ LHS: [], RHS: [] });
    // }, []);

    // const closeSubstitution = useCallback(() => {
    //     setShowSubstitution(false);
    // }, []);

    // const updateShowSubstitution = useCallback(() => {
    //     setShowSubstitution(true);
    // }, []);

  const [lhsValue, setLhsValue] = useState("");
  const [rhsValue, setRhsValue] = useState("");
  const [isOffcanvasActive, toggleOffcanvas] = useOffcanvas();
  const [showDefinitionsWindow, toggleDefinitionsWindow] =
    useDefinitionsWindow();
  const [showProofComplete, setShowProofComplete] = useState(false);
  const [proofComplete, setProofComplete] = useState(false);
  
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
  const [userRow, setUserRow] = useState({ num: "" });
  const [isBound, setIsBound] = useState(false);
  const [footerRule, setFooterRule] = useState("");
  const [footerRuleError, setFooterRuleError] = useState("");
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  
  // Hook for getting available height for scrollable proof area
  const availableHeight = useDynamicHeight();

  // Initialize jsonTreeRep as empty object for passing to renderPersistentPadRow
  // It gets populated by the backend when goals are checked
//   const [jsonTreeRep, setJsonTreeRep] = useState({ LHS: {}, RHS: {} });

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
  setFooterRuleError('');
  const caseKey = 'base';
  setProofStatus(prev => ({ ...prev, [caseKey]: null }));

    setUserRow({ num: paddedRowNum });
    setIsBound(true);

    // Set footer rule initially to what the field has
    if (paddedRowNum !== "000") {
      // Array index now equals line number, so use userIndex directly
      const field = (racketRuleFields?.[showSide] || [])[userIndex];
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
            selectedNode: baseLHSPremise.selectedNode || 0
        }));
      }

    } catch (error) {
      console.error('[loadProofLines] Error loading proof lines:', error);
      // Don't show error to user - this is a background operation
    }
  }, [setRacketRuleFields, setLeftPremise, setRightPremise]);

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

  const handleClearProof = async () => {
    if (!window.confirm('Are you sure you want to clear this proof? This will archive it and start a new proof.')) {
      return;
    }

    try {
      await erService.clearProof();
      
      // Clear sessionStorage flag so we don't restore from DB on reload
      sessionStorage.removeItem('erProofActive');
      
      toast.success('Proof archived successfully');
      
      // Reload the page to start fresh
      window.location.reload();
    } catch (error) {
      console.error('Error clearing proof:', error);
      toast.error('Failed to clear proof');
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
            const previousField = racketRuleFields?.[showSide][previousRowIndex];
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
        currentRacket: previousRacketValue,
        rule: ruleFromFooter,
        startPosition: previousStartPosition,
        selectedNode: previousStartPosition,
        ...(typeof currentIndex === 'number' && { lineNumber: currentIndex })
      };

      // Reset status when new line generated
      const caseKey = 'base';
      setProofStatus(prev => ({ ...prev, [caseKey]: null }));

      // Dismiss any previous error toasts before trying again
      toast.dismiss();

      const fullRacket = await equationalService.applyRule(payload);

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

        await checkCurrentProofStatus();
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
    // On mount, attempt to restore proof from database only if we're in an active session
    // Use sessionStorage to distinguish between page refresh (restore) and new navigation (clear)
    const restoreProof = async () => {
      try {
        const isActiveSession = sessionStorage.getItem('erProofActive') === 'true';
        
        if (!isActiveSession) {
          // New session - clear any old proof data and start fresh
          await erService.clearProof();
          return;
        }
        
        // Active session - attempt to restore from database (page refresh scenario)
        const proofData = await equationalService.getProofLines();
        
        if (proofData.hasProof) {
          // Restore form values
          setFormValues(prev => ({
            ...prev,
            lHSGoal: proofData.lhsAnchorGoal || '',
            rHSGoal: proofData.rhsAnchorGoal || '',
            proofName: proofData.proofName || '',
            proofTag: proofData.tag || ''
          }));
          
          // Re-initialize the proof engine to get proper jsonTrees for premises
          try {
            const normalizeType = (t) => (t || '').replace(/\s*->\s*/g, ' > ').trim();
            const definitions = JSON.parse(sessionStorage.getItem('definitions') || '[]');
            
            const engineSetup = await equationalService.setCurrentProof({
              lhsPremise: proofData.lhsAnchorGoal,
              rhsPremise: proofData.rhsAnchorGoal,
              definitions: definitions.map(d => ({
                label: d.label || d.name || '',
                type: normalizeType(d.type),
                expression: d.expression
              }))
            });

            if (engineSetup && engineSetup.base && engineSetup.leap) {
              const baseL = engineSetup.base.LHS || {};
              const baseR = engineSetup.base.RHS || {};
              // Set base case premises with proper jsonTrees
              setLeftPremise(prev => ({
                    ...prev,
                    racket: baseL.racket || proofData.lhsAnchorGoal || '',
                    jsonTree: baseL.jsonTree || {}, 
                    rule: 'Premise', 
                    startPosition: 0, 
                    selectedNode: 0
                }));
                setRightPremise(prev => ({
                    ...prev,
                    racket: baseR.racket || proofData.rhsAnchorGoal || '',
                    jsonTree: baseR.jsonTree || {}, 
                    rule: 'Premise', 
                    startPosition: 0, 
                    selectedNode: 0
                }));

            //   setJsonTreeRep({
            //     LHS: baseL.jsonTree || {},
            //     RHS: baseR.jsonTree || {}
            //   });
            }
          } catch (engineError) {
            // Fall back to simple initialization without jsonTrees
            setLeftPremise(prev => ({
                ...prev,
                racket: formValues.lHSGoal,
                jsonTree: {}, 
                rule: 'Premise', 
                startPosition: 0, 
                selectedNode: 0
            }));
            setRightPremise(prev => ({
                ...prev,
                racket: formValues.rHSGoal,
                jsonTree: {}, 
                rule: 'Premise', 
                startPosition: 0, 
                selectedNode: 0
            }));
          }
          
          // Initialize fields
          setRacketFields({ LHS: [EMPTY_INITIAL_FIELD], RHS: [EMPTY_INITIAL_FIELD] });
          
          // Get proof lines and restore them
          try {
            const lines = await equationalService.getProofLines();
            
            if (lines && typeof lines === 'object') {
              // Helper function to convert database lines to UI field format
              const convertLinesToFields = (dbLines) => {
                if (!Array.isArray(dbLines) || dbLines.length === 0) {
                  return [EMPTY_INITIAL_FIELD];
                }
                
                // Find the highest line number to size the array
                const maxLineNum = Math.max(...dbLines.map(line => line.lineNumber));
                
                // Create array where index = database line_number
                // Start with empty fields for all positions
                const fields = [];
                for (let i = 0; i <= maxLineNum; i++) {
                  fields[i] = { ...EMPTY_INITIAL_FIELD };
                }
                
                // Fill in the actual data from database
                dbLines.forEach(line => {
                  fields[line.lineNumber] = {
                    racket: line.racket || '',
                    jsonTree: line.jsonTree || {},
                    rule: line.rule || '',
                    startPosition: line.startPosition || 0,
                    selectedNode: line.selectedNode || 0,
                    resultNode: line.resultNode || 0,
                    deleted: false
                  };
                });
                
                // Add trailing empty field for next line
                fields.push(EMPTY_INITIAL_FIELD);
                
                return fields;
              };
              
              // Restore base case fields
              if (lines.base) {
                const baseLHS = convertLinesToFields(lines.base.LHS);
                const baseRHS = convertLinesToFields(lines.base.RHS);

                setRacketFields({ LHS: baseLHS, RHS: baseRHS });
              }
            }
          } catch (linesError) {
            // Continue anyway - at least form values and IH are restored
          }
          
          setProofStarted(true);
          sessionStorage.setItem('erProofActive', 'true');
        } else {
          // No existing proof, clear to start fresh
          await erService.clearProof();
        }
      } catch (error) {
        // On error, clear to start fresh
        try {
          await erService.clearProof();
        } catch (clearError) {
          // Silent fail
        }
      }
    };

    restoreProof();
  }, []);

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
      setInductionSubErrors([]);
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

  const handleInductionSubstitution = useCallback(
    async ({ substitution, rule }) => {
      // Clear previous errors when user attempts a new submission
      setInductionSubErrors([]);
      const caseKey = 'base';
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
        const sourceField = racketRuleFields?.[showSide][padIndex - 1];
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
        case: "base",
        lineNumber: padIndex  // Tell backend which line to update
      };

      try {
        const response = await equationalService.substitution(payload);

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

        //   if (response.jsonTree) {
        //     setJsonTreeRep((prev) => ({ ...prev, [showSide]: response.jsonTree }));
        //   }

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
      leftPremise,
      rightPremise,
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
      const field = racketRuleFields?.[showSide][padIndex];
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
          isRuleReadOnly={false}
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

        {showProofComplete && <ProofComplete onDismiss={() => setShowProofComplete(false)} />}

        {showSubstitution && (
          <Substitution
            show={showSubstitution}
            handleClose={() => closeSubstitution()}
            racketRuleFields={(racketRuleFields?.[showSide] || [])}
            handleSubstitution={handleInductionSubstitution}
            errors={inductionSubErrors}
          />
        )}

        <Form
          noValidate
          validated={validated}
          className="er-racket-form"
          onSubmit={handleStartProof}
        >
          <div className="form-top-section">
            <Row className="page-header-row" style={{ alignItems: 'center' }}>
              <Col xs="auto">
                <h1 style={{ marginBottom: 0 }}>Equational Reasoning</h1>
              </Col>
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
                    disabled={proofStarted}
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
                      !!validationMessages.tag || !!proofValidationMessage.tag
                    }
                    disabled={proofStarted}
                    required
                  />
                  <label htmlFor="eRProofTag"># Tag</label>
                  <Form.Control.Feedback type="invalid" tooltip>
                    {validationMessages.tag || proofValidationMessage.tag}
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
                      !!goalValidationMessage?.LHS
                    }
                    disabled={proofStarted}
                    required
                  />
                  <label htmlFor="eRProofLHSGoal">LHS Goal</label>
                  <Form.Control.Feedback type="invalid" tooltip>
                    {validationMessages.lHSGoal ||
                      goalValidationMessage?.LHS}
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
                      !!goalValidationMessage?.RHS
                    }
                    disabled={proofStarted}
                    required
                  />
                  <label htmlFor="eRProofRHSGoal">RHS Goal</label>
                  <Form.Control.Feedback type="invalid" tooltip>
                    {validationMessages.rHSGoal ||
                      goalValidationMessage?.RHS}
                  </Form.Control.Feedback>
                </Form.Floating>
              </Form.Group>
            </Row>

            <Row className="er-current-state" style={{ alignItems: 'center', position: 'relative' }}>
              <Form.Group
                as={Col}
                md="4"
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
                    id="eRProofCurrentLHS"
                    name="proofCurrentLHS"
                    type="text"
                    placeholder="Current LHS"
                    value={lhsValue || (proofStarted ? (leftPremise?.racket || currentLHS) : '')}
                    readOnly
                    style={{ cursor: "not-allowed", border: 'none' }}
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
                    style={{ cursor: "not-allowed", border: 'none' }}
                  />
                  <label htmlFor="eRProofCurrentRHS">Current RHS</label>
                </Form.Floating>
              </Form.Group>
            </Row>

            <Form.Text
              as={"div"}
              id="formSeparator"
              className="form-separator"
              style={{ marginTop: '10px' }}
            ></Form.Text>
          </div>

          {proofStarted && (
            <>
              <div style={{ position: 'fixed', left: '10px', top: '215px', zIndex: 1020, color: '#F2A007', fontWeight: 'bold', fontSize: '20px' }}>
                CURRENT = {showSide}
              </div>
              <div style={{ position: 'fixed', left: '10px', top: '245px', zIndex: 1020 }}>
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

          <div className="form-bottom-part">

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
                <Row className="goal-btn-wrap">
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
      
      <div style={{ position: 'fixed', right: '375px', top: '65px', zIndex: 1020 }}>
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
      </div>
      
      {proofStarted && proofStatus['base'] && (
        <div style={{ position: 'fixed', right: '50px', top: '65px', zIndex: 1020 }}>
          <span
            style={{
              fontWeight: "700",
              color: proofStatus['base'].state === "complete" ? "green" : "red",
              fontSize: "28px"
            }}
          >
            {proofStatus['base'].state === "complete"
              ? `${proofStatus['base'].label} COMPLETE`
              : `${proofStatus['base'].label} INCOMPLETE`}
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
            {(racketRuleFields?.[showSide] || []).map((field, index) =>
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
                  caseType: 'base'
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
    </MainLayout>
  );
};

export default EquationalReasoningNew;
