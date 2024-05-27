import { useState, useCallback } from "react";
import erService from "../services/erService";

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
    inductionType
  ) => {
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
      name,
      tag,
      side,
      leapGoal,
      anchorGoal,
      inductionVariable,
      inductionValue,
      leapVariable,
      inductionType
    };

    console.log(data);
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
