import { useState, useEffect } from 'react';

/**
 * A custom hook that tracks the current LHS and RHS racket values based on the latest entries
 * in the provided dynamic fields arrays for LHS and RHS.
 *
 * @param {Object} racketRuleFields - The current state of the racket and rule fields.
 * @param {Object} formValues - Form values containing goals.
 * @param {Object} isGoalChecked - State tracking whether goals are checked.
 * @returns {Array} Current LHS and RHS racket values.
 */
const useCurrentRacketValues = (racketRuleFields = {}, formValues = {}, isGoalChecked = {}) => {
  const [currentLHS, setCurrentLHS] = useState('');
  const [currentRHS, setCurrentRHS] = useState('');

  useEffect(() => {
    // Safety check for parameters
    if (!racketRuleFields || !formValues) {
      return;
    }

    const findLastNonEmptyRacket = (fields, goalValue) => {
      if (!fields || !Array.isArray(fields)) return goalValue || '';
      
      // Look for the latest racket value that's not empty and not deleted
      for (let i = fields.length - 1; i >= 0; i--) {
        const field = fields[i];
        if (
          field && 
          field.racket && 
          typeof field.racket === 'string' &&
          field.racket.trim() !== "" &&
          !field.deleted
        ) {
          return field.racket;
        }
      }
      
      // Fall back to goal value if no valid racket fields found
      return goalValue || '';
    };

    const lastNonEmptyLHS = findLastNonEmptyRacket(
      racketRuleFields?.LHS, 
      formValues?.lHSGoal
    );
    const lastNonEmptyRHS = findLastNonEmptyRacket(
      racketRuleFields?.RHS, 
      formValues?.rHSGoal
    );

    setCurrentLHS(lastNonEmptyLHS);
    setCurrentRHS(lastNonEmptyRHS);
  }, [racketRuleFields, formValues, isGoalChecked, racketRuleFields?.LHS?.length, racketRuleFields?.RHS?.length]);

  return [ currentLHS, currentRHS ];
};

export { useCurrentRacketValues };
