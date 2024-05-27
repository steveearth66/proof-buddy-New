const validateSubstitutionField = (value, message) => {
  if (!value) {
    return message;
  }

  return "";
};

const validatedField = (fieldName, value) => {
  if (fieldName === "substitution") {
    return validateSubstitutionField(value, "Please provide a substitution.");
  } else if (fieldName === "rule") {
    return validateSubstitutionField(value, "Please provide a rule.");
  } else {
    return "";
  }
};

export default validatedField;
