import { useState, useCallback } from 'react';
import erService from '../services/erService';
import logger from '../utils/logger';

/**
 * Custom React hook for checking if a goal (LHS or RHS) is valid.
 *
 * @param {Function} handleChange - The existing handleChange function from useInputState hook
 * to be enhanced with goal validation logic.
 * @returns {Array} An array containing the goal check states.
 * - isGoalChecked: Object tracking validation status for LHS and RHS.
 * - checkGoal: Function to validate a goal.
 * - goalValidationMessage: Object holding validation messages for LHS and RHS.
 * - enhancedHandleChange: Function to handle input changes and clear validation messages.
 */
const useGoalCheck = (handleChange) => {
  const [isGoalChecked, setIsGoalChecked] = useState({ LHS: false, RHS: false });
  const [goalValidationMessage, setGoalValidationMessage] = useState({ LHS: '', RHS: '' });
  const [proofValidationMessage, setProofValidationMessage] = useState({ name: '', tag: '' });

  /**
   * Clears the validation message for a specific goal side (LHS or RHS).
   *
   * @param {string} side - The side of the goal (LHS or RHS) for which to clear the validation message.
   */
  const clearGoalValidationMessage = useCallback((side) => {
    setGoalValidationMessage(prev => ({ ...prev, [side]: '' }));
  }, []);

  const clearProofValidationMessage = useCallback(() => {
    setProofValidationMessage({ name: '', tag: '' });
  }, []);

  /**
   * Enhances the provided handleChange function with additional logic to clear
   * validation messages for goals when the user starts typing.
   *
   * @param {Object} event - The event object from the input change event.
   */
  const enhancedHandleChange = useCallback((event) => {
    handleChange(event);
    const side = event.target.name === 'lHSGoal' ? 'LHS' : 'RHS';
    clearGoalValidationMessage(side);
    clearProofValidationMessage();
  }, [clearGoalValidationMessage, handleChange, clearProofValidationMessage]);

  /**
   * Validates a goal value for a specific side (LHS or RHS) by making a server-side request.
   * Updates the validation status and message based on the server response.
   *
   * @param {string} side - The side of the goal (LHS or RHS) to validate.
   * @param {string} goalValue - The value of the goal to validate.
   */
  const checkGoal = async (side, goalValue, name, tag, lHSGoal, rHSGoal) => {
    if (!name) {
      setProofValidationMessage({ name: 'Please provide a name.' });
      return;
    }

    if (!tag) {
      setProofValidationMessage({ tag: 'Please provide a tag.' });
      return;
    }

    if (!goalValue.trim()) {
      setGoalValidationMessage(prev => ({ ...prev, [side]: `Please provide a ${side} goal.` }));
      setIsGoalChecked(prev => ({ ...prev, [side]: false }));
      return;
    }

    try {
      const result = await erService.checkGoal({ goal: goalValue, name, tag, lHSGoal, rHSGoal, side });
      if (result.isValid) {
        setIsGoalChecked({ ...isGoalChecked, [side]: true });
        setGoalValidationMessage({ ...goalValidationMessage, [side]: '' });
        setProofValidationMessage('');
      } else {
        setIsGoalChecked({ ...isGoalChecked, [side]: false });
        const errorMessage = result.errors?.length ? result.errors.join('\n') : 'An unknown error occurred.';
        setGoalValidationMessage({
          ...goalValidationMessage,
          [side]: `The ${side} goal is not valid.\nError(s):\n${errorMessage}`
        });
      }
    } catch (error) {
      logger.error(`Error validating the ${side} Goal: ${error}`);
      setIsGoalChecked({ ...isGoalChecked, [side]: false });
    }
  };

  const loadRacket = () => {
    setIsGoalChecked({ LHS: true, RHS: true });
  };

  return [
    isGoalChecked,
    checkGoal,
    goalValidationMessage,
    enhancedHandleChange,
    proofValidationMessage,
    clearProofValidationMessage,
    loadRacket
  ];
};

export { useGoalCheck };
