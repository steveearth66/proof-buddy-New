import { useState } from "react";

const useDefinitionsWindow = (initialState = false) => {
  const [isDefinitionsWindowActive, setIsDefinitionsWindowActive] =
    useState(initialState);

  const toggleDefinitionsWindow = () => {
    setIsDefinitionsWindowActive((previousState) =>
      previousState === false ? true : false
    );
  };

  return [isDefinitionsWindowActive, toggleDefinitionsWindow];
};

export { useDefinitionsWindow };
