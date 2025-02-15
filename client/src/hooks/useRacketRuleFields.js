import { useState, useCallback } from 'react';
import erService from '../services/erService';
import { useServerError } from '../hooks/useServerError';
import logger from '../utils/logger';

/**
 * A custom React hook designed to manage racket rule fields within a component.
 * It encapsulates logic for fetching racket values based on rules, adding new fields dynamically,
 * and handling changes to existing fields. Additionally, it integrates error handling
 * through a custom hook for server errors.
 *
 * @param {string} startPosition - Start position for the highlighted keyword.
 *
 * @returns {Object} An object containing the racket rule fields state, functions to manipulate these fields,
 * and any server error encountered during operations.
 *
 * @example
 * const { racketRuleFields, addField, handleFieldChange, serverError } = useRacketRuleFields();
 */
const useRacketRuleFields = (startPosition, currentRacket, name, tag, side) => {
  const [serverError, handleServerError, clearServerError] = useServerError();
  const [racketErrors, setRacketErrors] = useState([]);
  const [showSubstitution, setShowSubstitution] = useState(false);
  const [racketRuleFields, setRacketRuleFields] = useState({
    LHS: [],
    RHS: []
  });
  const [validationErrors, setValidationErrors] = useState({
    LHS: [],
    RHS: []
  });
  const [substitutionErrors, setSubstitutionErrors] = useState([]);

  // Function to update the showSubstitution state
  const updateShowSubstitution = () => {
    setSubstitutionErrors([]);

    if (startPosition < 1) {
      alert('Please select a keyword to substitute!');
      return;
    }

    const sideFields = racketRuleFields[side];
    const undeletedProofLines = sideFields.filter((line) => {
      return !line.deleted;
    });
    const lastUnDeletedFieldIndex = undeletedProofLines.length - 1;

    if (undeletedProofLines.length > 0) {
      const ruleValue = undeletedProofLines[lastUnDeletedFieldIndex].rule;
      if (ruleValue.trim().length > 0) {
        alert('Rule for Substitution entered in different window');
      }
    }

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
   * @returns {Promise<string|undefined>} A promise that resolves to the racket value or undefined if an error occurs.
   */
  const fetchRacketValue = useCallback(
    async (ruleValue) => {
      const payLoad = {
        rule: ruleValue,
        startPosition: startPosition,
        currentRacket: currentRacket,
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
    [handleServerError, startPosition, currentRacket, name, tag, side]
  );

  /**
   * A callback function to add a new field to either the LHS or RHS side.
   * It checks the last field of the specified side to ensure it's not empty before fetching its racket value.
   * A new empty field is always added after the fetch operation or directly if no previous fields exist.
   *
   * @param {string} side - Specifies the side (LHS or RHS) to add the new field to.
   */
  const addFieldWithApiCheck = useCallback(
    async (side) => {
      const sideFields = racketRuleFields[side];
      const undeletedProofLines = sideFields.filter((line) => {
        return !line.deleted;
      });
      const lastUnDeletedFieldIndex = undeletedProofLines.length - 1;
      const indexToUpdate = racketRuleFields[side].findIndex((line) => line === undeletedProofLines[lastUnDeletedFieldIndex]);

      // Only proceed if there is at least one field and the last rule is not empty.
      if (undeletedProofLines.length > 0) {
        if (undeletedProofLines[lastUnDeletedFieldIndex].rule.trim() === '') {
          setValidationErrors((prevErrors) => ({
            ...prevErrors,
            [side]: {
              ...prevErrors[side],
              [lastUnDeletedFieldIndex]: 'Rule field cannot be empty!'
            }
          }));
        } else {
          try {
            const ruleValue = undeletedProofLines[lastUnDeletedFieldIndex].rule;
            const racket = await fetchRacketValue(ruleValue);

            if (racket.isValid) {
              setRacketErrors([]);
              clearServerError();
              console.log("log1", racketRuleFields); // added console.log to check
              setRacketRuleFields((prevFields) => ({
                ...prevFields,
                [side]: prevFields[side].map((field, index) => {
                  if (index === indexToUpdate) {
                    return {
                      ...field,
                      racket: racket.racket,
                      jsonTree: racket.jsonTree // added new line to return jsonTree data
                    };
                  }
                  return field;
                })
              }));
              console.log("log2", racketRuleFields.LHS[0].jsonTree); // added console.log to check
              setRacketRuleFields((prevFields) => ({
                ...prevFields,
                [side]: [
                  ...prevFields[side],
                  { racket: '', rule: '', deleted: false, errors: [] }
                ]
              }));

              setValidationErrors((prevErrors) => ({
                ...prevErrors,
                [side]: {}
              }));
            } else {
              setRacketErrors(racket.errors);
              const errors = undeletedProofLines[lastUnDeletedFieldIndex].errors || [];
    
              for (const error of racket.errors) {
                if (!errors.includes(error)) {
                  errors.push(error);
                }
              }

              setRacketRuleFields((prevFields) => ({
                ...prevFields,
                [side]: prevFields[side].map((field, index) => {
                  if (index === indexToUpdate) {
                    return {
                      ...field,
                      errors
                    };
                  }
                  return field;
                })
              }));
            }
          } catch (error) {
            logger.error('Failed to fetch racket value:', error);
          }
        }
      } else {
        setRacketRuleFields((prevFields) => ({
          ...prevFields,
          [side]: [
            ...prevFields[side],
            { racket: '', rule: '', deleted: false }
          ]
        }));
      }
    },
    [fetchRacketValue, racketRuleFields, clearServerError]
  );

  /**
   * A callback function to handle changes to any field within the racket rule fields.
   * It updates the specified field's value based on user input.
   *
   * @param {string} side - The side (LHS or RHS) where the field is located.
   * @param {number} index - The index of the field within its side.
   * @param {string} fieldName - The name of the field property to update (e.g., 'racket' or 'rule').
   * @param {any} value - The new value to set for the field property.
   * @param {string} startPosition - The start position for the highlighted keyword.
   */
  const handleFieldChange = useCallback(
    (side, index, fieldName, value, startPosition) => {
      setRacketRuleFields((prevFields) => {
        const fieldsCopy = { ...prevFields };
        if (fieldsCopy[side] && fieldsCopy[side][index]) {
          fieldsCopy[side][index] = {
            ...fieldsCopy[side][index],
            [fieldName]: value,
            startPosition
          };
        }
        return fieldsCopy;
      });

      setValidationErrors((prevErrors) => {
        const updatedErrors = { ...prevErrors };
        if (updatedErrors[side][index]) {
          delete updatedErrors[side][index];
        }
        return updatedErrors;
      });
    },
    []
  );

  /**
   * A callback function that removes the last proof line after premise.
   * It sets the `deleted` flag to true for the last line that is not already deleted.
   * This so that the deleted lines are saved in the database.
   * @param {string} side - Specifies the active side ('LHS' or 'RHS') to perform the cleanup on.
   */
  const deleteLastLine = useCallback(async (side) => {
    const lastUnDeletedFieldIndex = [...racketRuleFields[side]].reverse().findIndex((line) => !line.deleted && line.racket !== '');
    if (lastUnDeletedFieldIndex !== -1) {
      await erService.deleteLine(side);
      const lastFieldIndex = racketRuleFields[side].length - 1 - lastUnDeletedFieldIndex;
      setRacketRuleFields((prevFields) => {
        const sideFields = prevFields[side];
        const newFields = [...sideFields];
        newFields[lastFieldIndex] = {
          ...newFields[lastFieldIndex],
          deleted: true
        };

        return {
          ...prevFields,
          [side]: newFields
        };
      });
    }
  }, [racketRuleFields]);

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
          setRacketRuleFields((prevFields) => ({
            ...prevFields,
            [side]: [
              ...prevFields[side].slice(0, -1),
              {
                racket: response.racket,
                rule: rule + '(SUB)',
                deleted: false
              },
              { racket: '', rule: '', deleted: false }
            ]
          }));
          closeSubstitution();
          return true;
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

  const loadRacketProof = useCallback((proofLines, isComplete) => {
    const leftRackets = proofLines.filter((line) => line.leftSide === true);
    const rightRackets = proofLines.filter((line) => line.leftSide === false);

    const leftFields = leftRackets.map((line) => ({
      racket: line.racket,
      rule: line.rule,
      deleted: line.deleted,
      startPosition: line.startPosition,
      errors: line.errors
    }));

    const rightFields = rightRackets.map((line) => ({
      racket: line.racket,
      rule: line.rule,
      deleted: line.deleted,
      startPosition: line.startPosition,
      errors: line.errors
    }));

    if (!isComplete) {
      leftFields.push({ racket: '', rule: '', deleted: false, errors: [] });
      rightFields.push({ racket: '', rule: '', deleted: false, errors: [] });
    }

    setRacketRuleFields({
      LHS: leftFields,
      RHS: rightFields
    });
  }, []);

  return [
    racketRuleFields,
    addFieldWithApiCheck,
    handleFieldChange,
    validationErrors,
    serverError,
    racketErrors,
    deleteLastLine,
    updateShowSubstitution,
    showSubstitution,
    closeSubstitution,
    substituteFieldWithApiCheck,
    substitutionErrors,
    loadRacketProof
  ];
};

export { useRacketRuleFields };
