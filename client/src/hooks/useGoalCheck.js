import { useState, useCallback } from 'react';
import erService from '../services/erService';
import logger from '../utils/logger';

/**
 * Custom React hook for checking if a goal (LHS or RHS) is valid.
 */
const useGoalCheck = (handleChange) => {
  const [isGoalChecked, setIsGoalChecked] = useState({ LHS: false, RHS: false });
  const [goalValidationMessage, setGoalValidationMessage] = useState({ LHS: '', RHS: '' });
  const [proofValidationMessage, setProofValidationMessage] = useState({ name: '', tag: '' });
  const [jsonTreeRep, setJsonTreeRep] = useState({ LHS: {}, RHS: {} });

  const clearGoalValidationMessage = useCallback((side) => {
    setGoalValidationMessage(prev => ({ ...prev, [side]: '' }));
  }, []);

  const clearProofValidationMessage = useCallback(() => {
    setProofValidationMessage({ name: '', tag: '' });
  }, []);

  const enhancedHandleChange = useCallback((event) => {
    handleChange(event);
    const side = event.target.name === 'lHSGoal' ? 'LHS' : 'RHS';
    clearGoalValidationMessage(side);
    clearProofValidationMessage();
  }, [clearGoalValidationMessage, handleChange, clearProofValidationMessage]);

  const checkGoal = async (side, goalValue, name, tag, lHSGoal, rHSGoal) => {
    // Validation checks
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
      
      setIsGoalChecked(prev => ({ ...prev, [side]: result.isValid }));
      
      if (result.isValid) {
        setGoalValidationMessage(prev => ({ ...prev, [side]: '' }));
        setProofValidationMessage({ name: '', tag: '' });
        setJsonTreeRep(prev => ({ ...prev, [side]: result.jsonTree }));
      } else {
        const errorMessage = result.errors?.length ? result.errors.join('\n') : 'An unknown error occurred.';
        setGoalValidationMessage(prev => ({
          ...prev,
          [side]: `The ${side} goal is not valid.\nError(s):\n${errorMessage}`
        }));
      }
    } catch (error) {
      logger.error(`Error validating the ${side} Goal: ${error}`);
      setIsGoalChecked(prev => ({ ...prev, [side]: false }));
    }
  };

  const loadRacketGoal = (loadedProof) => {
    const newGoalChecked = { LHS: false, RHS: false };
    const newJsonTreeRep = { LHS: {}, RHS: {} };

    if (loadedProof.leftPremise.jsonTree) {
      newGoalChecked.LHS = true;
      newJsonTreeRep.LHS = loadedProof.leftPremise.jsonTree;
    }
    if (loadedProof.rightPremise.jsonTree) {
      newGoalChecked.RHS = true;
      newJsonTreeRep.RHS = loadedProof.rightPremise.jsonTree;
    }

    setIsGoalChecked(newGoalChecked);
    setJsonTreeRep(newJsonTreeRep);
  };

  return [
    isGoalChecked,
    checkGoal,
    goalValidationMessage,
    enhancedHandleChange,
    proofValidationMessage,
    clearProofValidationMessage,
    loadRacketGoal,
    jsonTreeRep
  ];
};

export { useGoalCheck };
