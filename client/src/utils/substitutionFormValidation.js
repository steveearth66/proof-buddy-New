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
    const trimmed = (value || "").trim().toLowerCase();
    if (!trimmed) {
      return "Please provide a rule.";
    }
    if (!trimmed.startsWith("rewrite") && !trimmed.startsWith("eval")) {
      return "Rule must start with 'rewrite' or 'eval' (e.g., 'rewrite math', 'eval if')";
    }
    return "";
  } else {
    return "";
  }
};

export default validatedField;
