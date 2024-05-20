import { useState } from "react";

const useInductionCheck = (handleChange) => {
  const [isGoalChecked, setIsGoalChecked] = useState({
    LHS: false,
    RHS: false
  });

  const checkGoal = async (side, goalValue, name, tag) => {};

  return { isGoalChecked, checkGoal };
};

export default useInductionCheck;
