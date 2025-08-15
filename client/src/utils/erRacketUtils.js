/**
 * Utility functions for ERRacket component
 */

// Constants
export const ARROW_KEYS = ["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"];

export const INITIAL_FORM_VALUES = {
  proofName: "",
  proofTag: "",
  lHSGoal: "",
  rHSGoal: ""
};

export const INITIAL_PREMISE_STATE = {
  racket: '',
  rule: 'Premise',
  startPosition: 0
};

export const EMPTY_INITIAL_FIELD = { 
  racket: '', 
  jsonTree: {}, 
  rule: '', 
  startPosition: 0,
  deleted: false 
}

// Helper functions
export const getPadRefs = (side, lhsPadRefs, rhsPadRefs) => 
  side === "LHS" ? lhsPadRefs : rhsPadRefs;

export const getPadIndex = (num) => 
  num === "000" ? 0 : parseInt(num, 10);

export const isApplied = (definition) => definition["applied"];

// Form validation
export const isFormComplete = (formValues) => 
  formValues.proofName && formValues.proofTag && formValues.lHSGoal && formValues.rHSGoal;

// Proof data conversion
export const convertFormToJSON = (formValues, racketRuleFields, leftPremise, rightPremise, isGoalChecked, jsonTreeRep, startPosition, showSide) => {
  const definitions = JSON.parse(sessionStorage.getItem("definitions") || "[]").filter(isApplied);
  
  return JSON.stringify({
    name: formValues.proofName,
    tag: formValues.proofTag,
    leftRacketsAndRules: racketRuleFields.LHS,
    rightRacketsAndRules: racketRuleFields.RHS,
    lHSGoal: formValues.lHSGoal,
    rHSGoal: formValues.rHSGoal,
    leftPremise: { ...leftPremise, jsonTree: isGoalChecked.LHS ? jsonTreeRep.LHS : null },
    rightPremise: { ...rightPremise, jsonTree: isGoalChecked.RHS ? jsonTreeRep.RHS : null },
    definitions,
    // Additional UI state for proper import
    startPosition,
    showSide,
    isGoalChecked,
    loadedInServer: false
  });
};

// Start position calculation helper
export const getStartPosition = (loadedProof, side) => {
  const rules = side === 'LHS' ? loadedProof.leftRacketsAndRules : loadedProof.rightRacketsAndRules;
  const premise = side === 'LHS' ? loadedProof.leftPremise : loadedProof.rightPremise;
  return rules.length > 1 ? rules.at(-2).startPosition : premise.startPosition;
};

// Session storage helpers
export const clearSessionData = () => {
  sessionStorage.removeItem("highlights");
  sessionStorage.removeItem("definitions");
};

// Premise update helper
export const updatePremises = (formValues, setLeftPremise, setRightPremise) => {
  if (formValues.lHSGoal) {
    setLeftPremise(prev => ({ ...prev, racket: formValues.lHSGoal }));
  }
  if (formValues.rHSGoal) {
    setRightPremise(prev => ({ ...prev, racket: formValues.rHSGoal }));
  }
};
