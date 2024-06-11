const validateProofField = (value, errorMessage) => {
  if (!value) {
    return errorMessage;
  }
  return "";
};

const validateField = (fieldName, value) => {
  if (fieldName === "proofName") {
    return validateProofField(value, "Please provide a proof name.");
  } else if (fieldName === "proofTag") {
    return validateProofField(value, "Please provide a proof tag.");
  } else if (fieldName === "lHSLeapGoal") {
    return validateProofField(value, "Please provide a LHS Leap goal.");
  } else if (fieldName === "rHSLeapGoal") {
    return validateProofField(value, "Please provide a RHS Leap goal.");
  } else if (fieldName === "lHSAnchorGoal") {
    return validateProofField(value, "Please provide a LHS Anchor goal.");
  } else if (fieldName === "rHSAnchorGoal") {
    return validateProofField(value, "Please provide a RHS Anchor goal.");
  } else if (fieldName === "inductionVariable") {
    return validateProofField(value, "Please provide an induction variable.");
  } else if (fieldName === "inductionValue") {
    return validateProofField(value, "Please provide an induction value.");
  } else if (fieldName === "leapVariable") {
    return validateProofField(value, "Please provide a leap variable.");
  }
};

export default validateField;
