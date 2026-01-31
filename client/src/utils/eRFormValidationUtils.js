/**
 * ER Form validations.
 */

const VALIDATION_MESSAGES = {
  proofName: 'Please provide a proof name.',
  lHSGoal: 'Please provide a LHS goal.',
  rHSGoal: 'Please provide a RHS goal.'
};

/**
 * Validates a specific ER form field.
 * @param {string} fieldName - The name of the field to validate
 * @param {string} value - The value of the field to validate
 * @returns {string} Empty string if valid, otherwise an error message
 */
const validateField = (fieldName, value) => {
  if (!value && VALIDATION_MESSAGES[fieldName]) {
    return VALIDATION_MESSAGES[fieldName];
  }
  return '';
};

export default validateField;
