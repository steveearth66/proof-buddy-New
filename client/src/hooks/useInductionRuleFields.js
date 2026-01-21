import { useState, useCallback } from 'react';
import inductionService from '../services/inductionService';
import { useServerError } from '../hooks/useServerError';
import logger from '../utils/logger';

/**
 * A custom React hook for managing induction proof rule operations.
 * This hook is specifically designed for induction mode and calls induction-specific backend endpoints.
 *
 * @param {string} proofId - The ID of the current induction proof
 * @returns {Array} An array with functions for rule operations and error handling
 */
const useInductionRuleFields = (proofId) => {
  const [serverError, handleServerError, clearServerError] = useServerError();
  const [racketErrors, setRacketErrors] = useState([]);
  const [validationErrors, setValidationErrors] = useState({
    LHS: {},
    RHS: {}
  });

  /**
   * Apply a rule to generate the next proof line in induction mode
   */
  const applyRuleForInduction = useCallback(
    async (caseVal, side, currentRacket, rule, startPosition, substitution) => {
      try {
        const payload = {
          case: caseVal,
          side: side,
          currentRacket: currentRacket,
          rule: rule,
          startPosition: startPosition || 0,
          ...(substitution && { substitution: substitution })
        };

        const response = await inductionService.applyRule(payload);

        if (response && response.isValid) {
          setRacketErrors([]);
          clearServerError();
          setValidationErrors((prevErrors) => ({
            ...prevErrors,
            [side]: {}
          }));
          return response;
        } else {
          const errors = response?.errors || ['Invalid rule'];
          setRacketErrors(errors);
          setValidationErrors((prevErrors) => ({
            ...prevErrors,
            [side]: { 0: errors[0] || 'Invalid rule' }
          }));
          return response;
        }
      } catch (error) {
        logger.error('Failed to apply rule:', error);
        handleServerError(error);
        return { isValid: false, errors: [error.message] };
      }
    },
    [clearServerError, handleServerError]
  );

  /**
   * Delete the last line in a specific case and side
   */
  const deleteLineForInduction = useCallback(
    async (caseVal, side) => {
      try {
        await inductionService.deleteLine({ case: caseVal, side: side });
        clearServerError();
        setRacketErrors([]);
      } catch (error) {
        logger.error('Failed to delete line:', error);
        handleServerError(error);
      }
    },
    [clearServerError, handleServerError]
  );

  /**
   * Check/set a goal for a specific case and side
   */
  const checkGoalForInduction = useCallback(
    async (caseVal, side, goal) => {
      try {
        const payload = {
          case: caseVal,
          side: side,
          goal: goal
        };

        const response = await inductionService.checkGoal(payload);

        if (response && response.isValid) {
          setRacketErrors([]);
          clearServerError();
          return response;
        } else {
          const errors = response?.errors || ['Invalid goal'];
          setRacketErrors(errors);
          return response;
        }
      } catch (error) {
        logger.error('Failed to check goal:', error);
        handleServerError(error);
        return { isValid: false, errors: [error.message] };
      }
    },
    [clearServerError, handleServerError]
  );

  return [
    applyRuleForInduction,
    deleteLineForInduction,
    checkGoalForInduction,
    validationErrors,
    serverError,
    racketErrors,
    clearServerError
  ];
};

export { useInductionRuleFields };
