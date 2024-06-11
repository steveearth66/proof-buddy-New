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
    lhsGoal,
    rhsGoal,
    inductionVariable,
    inductionValue,
    leapVariable,
    inductionType,
    isAnchor
  ) => {
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

    if (!inductionValue) {
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

    if (!lhsGoal) {
      setGoalValidationMessage((prev) => ({
        ...prev,
        [side]: {
          ...prev[side],
          LeapGoal: `Please provide a LHS goal.`
        }
      }));
      setIsGoalChecked((prev) => ({
        ...prev,
        [side]: { ...prev[side], LeapGoal: false }
      }));
      return;
    }

    if (!rhsGoal) {
      setGoalValidationMessage((prev) => ({
        ...prev,
        [side]: {
          ...prev[side],
          AnchorGoal: `Please provide a RHS goal.`
        }
      }));
      setIsGoalChecked((prev) => ({
        ...prev,
        [side]: { ...prev[side], AnchorGoal: false }
      }));
      return;
    }

    const data = {
      name,
      tag,
      side,
      lhsGoal,
      rhsGoal,
      inductionVariable,
      inductionValue,
      leapVariable,
      inductionType,
      isAnchor
    };

    const response = await inductionService.checkInduction(data);
    if (response.isValid) {
      setIsGoalChecked((prev) => ({
        ...prev,
        [side]: { ...prev[side], LeapGoal: true, AnchorGoal: true }
      }));
      setGoalValidationMessage((prev) => ({
        ...prev,
        [side]: { LeapGoal: "", AnchorGoal: "" }
      }));
      setProofValidationMessage("");
    } else {
      setIsGoalChecked((prev) => ({
        ...prev,
        [side]: { ...prev[side], LeapGoal: false, AnchorGoal: false }
      }));
      const errorMessage = response.errors?.length
        ? response.errors.join("\n")
        : "An unknown error occurred.";
      setGoalValidationMessage((prev) => ({
        ...prev,
        [side]: {
          LeapGoal: `The LHS goal is not valid.\nError(s):\n${errorMessage}`,
          AnchorGoal: `The RHS goal is not valid.\nError(s):\n${errorMessage}`
        }
      }));
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
