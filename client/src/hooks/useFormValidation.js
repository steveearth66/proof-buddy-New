import { useState } from 'react';

/**
 * A custom hook for handling form validation in React components.
 * Validation messages are only updated when a field loses focus (onBlur),
 * never keystroke-by-keystroke, so partial input is never flagged live.
 *
 * @param {Object} formValues - An object representing the form's current values.
 * @param {Function} validateField - A function that takes a field name, its value, and all form values, then returns a validation message if the field is invalid.
 * @returns {Array} - An array containing the validation messages object, a handleBlur function to mark fields as touched, a setAllTouched function to mark all fields as touched, and an isFormValid function to check if the form is valid.
 *
 * @example
 * const [formValues, setFormValues] = useState({ name: '', email: '' });
 * const [validationMessages, handleBlur, setAllTouched, isFormValid] = useFormValidation(formValues, validateField);
 */
const useFormValidation = (formValues, validateField) => {
  const [validationMessages, setValidationMessages] = useState({});

  // Validate a single field at the moment the user leaves it.
  const handleBlur = (field) => {
    setValidationMessages(prev => ({
      ...prev,
      [field]: validateField(field, formValues[field], formValues),
    }));
  };

  // Validate every field at once (used on submit when the form hasn't been touched yet).
  const setAllTouched = () => {
    const messages = Object.keys(formValues).reduce((acc, key) => {
      acc[key] = validateField(key, formValues[key], formValues);
      return acc;
    }, {});
    setValidationMessages(messages);
  };

  const isFormValid = () => {
    return !Object.values(validationMessages).some(msg => msg);
  }

  return [
    validationMessages,
    handleBlur,
    setAllTouched,
    isFormValid
  ];
};

export { useFormValidation };
