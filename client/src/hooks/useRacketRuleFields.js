import { useState, useCallback } from 'react';
import erService from '../services/erService';
import { useServerError } from '../hooks/useServerError';
import logger from '../utils/logger';

/**
 * A custom React hook for managing API communication, validation, and error handling 
 * for proof rule operations. Simplified to work with padRefs as source of truth.
 *
 * This hook provides functions for API calls, validation, and error management without
 * maintaining its own state for proof data.
 *
 * @param {string} startPosition - Start position for the highlighted keyword.
 * @param {string} currentRacket - Current racket expression being worked with.
 * @param {string} name - Name identifier for the proof context.
 * @param {string} tag - Tag identifier for the proof context.
 * @param {string} side - Side identifier ('LHS' or 'RHS').
 *
 * @returns {Array} An array with functions and state for API communication and error handling.
 *
 * @example
 * const [,addFieldWithApiCheck,,validationErrors,serverError] = useRacketRuleFields(startPosition, currentRacket, name, tag, side);
 */
const useRacketRuleFields = (startPosition, currentRacket, name, tag, side) => {
  const [serverError, handleServerError, clearServerError] = useServerError();
  const [racketErrors, setRacketErrors] = useState([]);
  const [showSubstitution, setShowSubstitution] = useState(false);
  const [validationErrors, setValidationErrors] = useState({
    LHS: [],
    RHS: []
  });
  const [substitutionErrors, setSubstitutionErrors] = useState([]);

  // Function to update the showSubstitution state
  const updateShowSubstitution = () => {
    setSubstitutionErrors([]);
    setShowSubstitution((prev) => !prev);
  };

  const closeSubstitution = () => {
    setShowSubstitution(false);
  };

  /**
   * A callback function to fetch a racket value for a given rule.
   * Utilizes the custom service `erService` to make an external request.
   *
   * @param {string} ruleValue - The value of the rule for which to fetch the racket value.
   * @param {number} previousStartPosition - The start position from the padRef on the line before.
   * @param {string} previousRacketValue - The racket value from the padRef on the line before.
   * @returns {Promise<string|undefined>} A promise that resolves to the racket value or undefined if an error occurs.
   */
  const fetchRacketValue = useCallback(
    async (ruleValue, previousStartPosition, previousRacketValue) => {
      const payLoad = {
        rule: ruleValue,
        startPosition: previousStartPosition,
        currentRacket: previousRacketValue,
        name,
        tag,
        side
      };

      try {
        const response = await erService.racketGeneration(payLoad);
        if (response) return response;
      } catch (error) {
        handleServerError(error);
      }
    },
    [handleServerError, name, tag, side]
  );

  /**
   * A callback function to load proof data in the server.
   * Utilizes the custom service `erService` to make an external request.
   *
   * @param {Object} loadedProof - The loaded proof data.
   * @returns {Promise<string|undefined>} A promise that resolves to the response or undefined if an error occurs.
   */
  const loadProofInServer = useCallback(
    async (loadedProof) => {

      let currentRacket = loadedProof.lHSGoal
      let startPosition = loadedProof.leftPremise["startPosition"]
      let LHS = []
      for (let i = 0; i < loadedProof.leftRacketsAndRules.length; i++) {
        let rule = loadedProof.leftRacketsAndRules[i]["rule"]
        if (i + 1 === loadedProof.leftRacketsAndRules.length)
          break;
        LHS.push({ currentRacket, startPosition, rule })
        currentRacket = loadedProof.leftRacketsAndRules[i]["racket"];
        startPosition = loadedProof.leftRacketsAndRules[i]["startPosition"]
      }

      currentRacket = loadedProof.rHSGoal
      startPosition = loadedProof.rightPremise["startPosition"]
      let RHS = []
      for (let i = 0; i < loadedProof.rightRacketsAndRules.length; i++) {
        let rule = loadedProof.rightRacketsAndRules[i]["rule"]
        if (i + 1 === loadedProof.rightRacketsAndRules.length)
          break;
        RHS.push({ currentRacket, startPosition, rule })
        currentRacket = loadedProof.rightRacketsAndRules[i]["racket"];
        startPosition = loadedProof.rightRacketsAndRules[i]["startPosition"]
      }

      const payLoad = {
        lHSGoal: loadedProof.lHSGoal,
        rHSGoal: loadedProof.rHSGoal,
        definitions: loadedProof.definitions,
        generics: loadedProof.generics,
        leftGoalChecked: loadedProof.isGoalChecked?.LHS || false,
        rightGoalChecked: loadedProof.isGoalChecked?.RHS || false,
        LHS,
        RHS,
        name: loadedProof.name,
        tag: loadedProof.tag
      };

      try {
        const response = await erService.loadProof(payLoad);
        if (response) return response;
      } catch (error) {
        handleServerError(error);
      }
    },
    []
  );

  /**
   * A callback function to add a new field to either the LHS or RHS side.
   * It checks the last field of the specified side to ensure it's not empty before fetching its racket value.
   * A new empty field is always added after the fetch operation or directly if no previous fields exist.
   *
   * @param {string} side - Specifies the side (LHS or RHS) to add the new field to.
   * @param {string} footerRule - The rule value from the footer.
   * @param {number} previousStartPosition - The start position from the padRef on the line before.
   * @param {string} previousRacketValue - The racket value from the padRef on the line before.
   */
  const addFieldWithApiCheck = useCallback(
    async (side, footerRule, previousStartPosition, previousRacketValue) => {
      try {
        const racket = await fetchRacketValue(footerRule, previousStartPosition, previousRacketValue);

        if (racket.isValid) {
          setRacketErrors([]);
          clearServerError();
          setValidationErrors((prevErrors) => ({
            ...prevErrors,
            [side]: {}
          }));
        } else {
          setRacketErrors(racket.errors);
        }

        return racket;
      } catch (error) {
        logger.error('Failed to fetch racket value:', error);
        return null;
      }
    },
    [fetchRacketValue, clearServerError]
  );

  /**
   * A callback function that removes the last proof line after premise.
   * Now relies on padRefs as source of truth instead of racketRuleFields.
   * @param {string} side - Specifies the active side ('LHS' or 'RHS') to perform the cleanup on.
   */
  const deleteLastLine = useCallback(async (side) => {
    try {
      await erService.deleteLine(side);
    } catch (error) {
      logger.error('Failed to delete line:', error);
    }
  }, []);

  const substituteFieldWithApiCheck = useCallback(
    async ({ substitution, rule }) => {
      const data = {
        substitution,
        rule,
        startPosition,
        currentRacket,
        side
      };

      try {
        const response = await erService.substitution(data);

        if (response.isValid) {
          setSubstitutionErrors([]);
          closeSubstitution();
          return response; // Return the response for the component to handle
        } else {
          setSubstitutionErrors(response.errors);
          return false;
        }
      } catch (error) {
        setSubstitutionErrors(['Failed to substitute rule']);
        logger.error('Failed to fetch racket value:', error);
        return false;
      }
    },
    [currentRacket, side, startPosition]
  );

  return [
    null, // racketRuleFields removed
    addFieldWithApiCheck,
    null, // handleFieldChange removed
    validationErrors,
    serverError,
    racketErrors,
    deleteLastLine,
    updateShowSubstitution,
    showSubstitution,
    closeSubstitution,
    substituteFieldWithApiCheck,
    substitutionErrors,
    loadProofInServer
  ];
};

export { useRacketRuleFields };
