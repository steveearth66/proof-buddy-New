import { useState, useCallback } from "react";
import erService from "../services/erService";
import { useServerError } from "../hooks/useServerError";
import logger from "../utils/logger";

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
  const [racketRuleFields, setRacketRuleFields] = useState({
    LHS: [],
    RHS: []
  });
  const [validationErrors, setValidationErrors] = useState({
    LHS: [],
    RHS: []
  });

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

      // Only proceed if there is at least one field and the last rule is not empty.
      if (sideFields.length > 0) {
        if (sideFields[lastUnDeletedFieldIndex].rule.trim() === "") {
          setValidationErrors((prevErrors) => ({
            ...prevErrors,
            [side]: {
              ...prevErrors[side],
              [lastUnDeletedFieldIndex]: "Rule field cannot be empty!"
            }
          }));
        } else {
          try {
            const ruleValue = sideFields[lastUnDeletedFieldIndex].rule;
            const racket = await fetchRacketValue(ruleValue);

            if (racket.isValid) {
              setRacketErrors([]);
              clearServerError();
              setRacketRuleFields((prevFields) => ({
                ...prevFields,
                [side]: [
                  ...prevFields[side].slice(0, -1),
                  {
                    ...sideFields[lastUnDeletedFieldIndex],
                    racket: racket.racket,
                    deleted: false
                  },
                  { racket: "", rule: "", deleted: false }
                ]
              }));
              setValidationErrors((prevErrors) => ({
                ...prevErrors,
                [side]: {}
              }));
            } else {
              setRacketErrors(racket.errors);
            }
          } catch (error) {
            logger.error("Failed to fetch racket value:", error);
          }
        }
      } else {
        setRacketRuleFields((prevFields) => ({
          ...prevFields,
          [side]: [
            ...prevFields[side],
            { racket: "", rule: "", deleted: false }
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
  const deleteLastLine = useCallback((side) => {
    setRacketRuleFields((prevFields) => {
      const sideFields = prevFields[side];
      let lastFieldIndex = sideFields.length - 1;

      for (let i = sideFields.length - 1; i >= 0; i--) {
        if (!sideFields[i].deleted) {
          lastFieldIndex = i;
          break;
        }
      }

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
  }, []);

  return [
    racketRuleFields,
    addFieldWithApiCheck,
    handleFieldChange,
    validationErrors,
    serverError,
    racketErrors,
    deleteLastLine
  ];
};

export { useRacketRuleFields };
