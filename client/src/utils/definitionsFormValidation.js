/**
 * Validates creating a new definition.
 *
 * @param {string} value - The field value.
 * @returns {string} An empty string if the field name is valid, otherwise an error message.
 */
const validateDefinitionField = (value, message) => {
  let errorMessage = "";
  if (!value) {
    errorMessage = message;
  }

  return errorMessage;
};

/**
 * Validates a specific definition form field.
 *
 * @param {string} fieldName - The name of the field to validate.
 * @param {string} value - The value of the field to validate.
 * @returns {string} An empty string if the field is valid, otherwise an error message.
 */
const validateField = (fieldName, value) => {
  if (fieldName === "label") {
    return validateDefinitionField(value, "Please provide a label.");
  } else if (fieldName === "type") {
    return validateDefinitionField(value, "Please provide a type.");
  } else if (fieldName === "expression") {
    return validateDefinitionField(value, "Please provide an expression.");
  } else {
    return "";
  }
};

export default validateField;
