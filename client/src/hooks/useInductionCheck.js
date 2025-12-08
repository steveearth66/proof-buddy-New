import { useState, useCallback } from "react";
import inductionService from "../services/inductionService";

const useInductionCheck = (handleChange) => {
  const [isGoalChecked, setIsGoalChecked] = useState({
    LHS: {
      LeapGoal: false,
      AnchorGoal: false
    },
    RHS: {
      LeapGoal: false,
      AnchorGoal: false
    }
  });

  const [goalValidationMessage, setGoalValidationMessage] = useState({
    LHS: {
      LeapGoal: "",
      AnchorGoal: ""
    },
    RHS: {
      LeapGoal: "",
      AnchorGoal: ""
    }
  });

  const [proofValidationMessage, setProofValidationMessage] = useState({
    name: "",
    tag: "",
    inductionVariable: "",
    inductionValue: "",
    leapVariable: ""
  });

  const clearGoalValidationMessage = useCallback((side) => {
    setGoalValidationMessage((prev) => ({
      ...prev,
      [side]: { LeapGoal: "", AnchorGoal: "" }
    }));
  }, []);

  const clearProofValidationMessage = useCallback(() => {
    setProofValidationMessage({
      name: "",
      tag: "",
      inductionVariable: "",
      inductionValue: "",
      leapVariable: ""
    });
  }, []);

  const enhancedHandleChange = useCallback(
    (event) => {
      handleChange(event);
      const side =
        event.target.name === "lHSLeapGoal" ||
        event.target.name === "lHSAnchorGoal"
          ? "LHS"
          : "RHS";
      clearGoalValidationMessage(side);
      clearProofValidationMessage();
    },
    [clearGoalValidationMessage, handleChange, clearProofValidationMessage]
  );

  const checkGoal = async (
    side,
    name,
    tag,
    leapGoal,
    anchorGoal,
    inductionVariable,
    inductionValue,
    leapVariable,
    inductionType,
    isAnchor,
    inductivehypothesislhs,
    inductivehypothesisrhs

  ) => {
    // Clear previous messages
    clearProofValidationMessage();
    clearGoalValidationMessage(side);

    // Validation checks
    if (!name) {
      setProofValidationMessage({ name: "Please provide a name." });
      return;
    }
    if (!tag) {
      setProofValidationMessage({ tag: "Please provide a tag." });
      return;
    }
    if (!inductionVariable) {
      setProofValidationMessage({
        inductionVariable: "Please provide an induction variable."
      });
      return;
    }
    if (!inductionValue && inductionValue !== 0) {
      setProofValidationMessage({
        inductionValue: "Please provide an induction value."
      });
      return;
    }
    if (!leapVariable) {
      setProofValidationMessage({
        leapVariable: "Please provide a leap variable."
      });
      return;
    }
    if (!leapGoal) {
      setGoalValidationMessage((prev) => ({
        ...prev,
        [side]: {
          ...prev[side],
          LeapGoal: `Please provide a ${side} leap goal.`
        }
      }));
      setIsGoalChecked((prev) => ({
        ...prev,
        [side]: { ...prev[side], LeapGoal: false }
      }));
      return;
    }
    if (!anchorGoal) {
      setGoalValidationMessage((prev) => ({
        ...prev,
        [side]: {
          ...prev[side],
          AnchorGoal: `Please provide a ${side} anchor goal.`
        }
      }));
      setIsGoalChecked((prev) => ({
        ...prev,
        [side]: { ...prev[side], AnchorGoal: false }
      }));
      return;
    }

    const data = {
      proof_name: name,
      proof_tag: tag,
      side: side,
      lhs_leap_goal: side === 'LHS' ? leapGoal : '',
      rhs_leap_goal: side === 'RHS' ? leapGoal : '',
      lhs_anchor_goal: side === 'LHS' ? anchorGoal : '',
      rhs_anchor_goal: side === 'RHS' ? anchorGoal : '',
      induction_variable: inductionVariable,
      anchor_value: Number(inductionValue),
      leap_variable: leapVariable,
      induction_type: inductionType,
      is_anchor: isAnchor,
      inductive_hypothesis_lhs: inductivehypothesislhs,
      inductive_hypothesis_rhs: inductivehypothesisrhs
    };

    try {
      console.log("Sending induction check data:", data);
      const response = await inductionService.checkInduction(data);
      console.log("Induction check response:", response);

      // Handle successful response
      if (response.success || response.valid) {
        setIsGoalChecked((prev) => ({
          ...prev,
          [side]: {
            LeapGoal: true,
            AnchorGoal: true
          }
        }));
        setGoalValidationMessage((prev) => ({
          ...prev,
          [side]: {
            LeapGoal: "Goal validated successfully!",
            AnchorGoal: "Goal validated successfully!"
          }
        }));
      } else {
        // Handle validation failure from server
        const errorMessage = response.message || "Validation failed";
        setGoalValidationMessage((prev) => ({
          ...prev,
          [side]: {
            LeapGoal: errorMessage,
            AnchorGoal: errorMessage
          }
        }));
        setIsGoalChecked((prev) => ({
          ...prev,
          [side]: {
            LeapGoal: false,
            AnchorGoal: false
          }
        }));
      }
    } catch (error) {
      console.error("Error checking induction:", error);
      
      // Extract error message from response
      const errorMessage = 
        error.response?.data?.message || 
        error.response?.data?.error ||
        error.message ||
        "An error occurred during validation";

      // Display error in the UI
      setGoalValidationMessage((prev) => ({
        ...prev,
        [side]: {
          LeapGoal: errorMessage,
          AnchorGoal: errorMessage
        }
      }));
      
      setIsGoalChecked((prev) => ({
        ...prev,
        [side]: {
          LeapGoal: false,
          AnchorGoal: false
        }
      }));

      // If it's a 400 error with details, log them
      if (error.response?.status === 400) {
        console.error("400 Bad Request Details:", {
          data: error.response.data,
          sentData: data
        });
      }
    }
  };

  return {
    isGoalChecked,
    checkGoal,
    goalValidationMessage,
    enhancedHandleChange,
    proofValidationMessage,
    clearProofValidationMessage
  };
};

export default useInductionCheck;
